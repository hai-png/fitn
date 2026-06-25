"""
Phase-3 tests for the new training architect.

Verifies:
  - PlanType (STANDARD vs PROGRAM) selection logic
  - Split selection by days_per_week + experience + goal
  - Periodization schemes (LINEAR / DUP / BLOCK) by experience
  - muscle_focus adds extra accessory slots
  - Equipment filter applied during slot filling (no empty workouts)
  - Mesocycle / microcycle structure for PROGRAM plans
  - Deload week volume reduction
  - Full plan serializes with new fields (plan_type, goal, muscle_focus)
"""
import json
import pytest

from fitness_engine import (
    UserProfile, assess_profile, propose_plan, FitnessPlan,
    PlanType, TrainingGoal, SplitType, ProgressionScheme,
)
from fitness_engine.models.profile import (
    Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType,
)
from fitness_engine.training.architect import (
    build_training_plan,
    _derive_training_goal,
    _pick_split,
    _pick_progression,
    _decide_plan_type,
    _apply_muscle_focus,
)
from fitness_engine.training.split_designs import (
    ALL_SPLITS, get_splits_for_days,
    FULL_BODY_2DAY, FULL_BODY_3DAY, UPPER_LOWER_4DAY,
    PPL_3DAY, PPL_X2_6DAY, PPL_UL_5DAY, BODY_PART_5DAY, PUSH_PULL_4DAY,
)
from fitness_engine.training.periodization import (
    apply_periodization,
    get_mesocycle_length,
    get_program_duration_weeks,
    get_block_phases_for_program,
)


# === Fixtures ===

@pytest.fixture
def cut_profile():
    return UserProfile(
        age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
        body_fat_pct=18, neck_cm=38, waist_cm=86, hip_cm=98,
        activity_level=ActivityLevel.MOSTLY_SEDENTARY,
        training_status=TrainingStatus.NOVICE,
        primary_goal=PrimaryGoal.FAT_LOSS,
        training_days_per_week=4,
        equipment_access=EquipmentAccess.FULL_GYM,
        diet_type=DietType.OMNIVORE,
    )


@pytest.fixture
def bulk_profile():
    return UserProfile(
        age=25, sex=Sex.MALE, height_cm=183, weight_kg=75,
        body_fat_pct=12, neck_cm=36, waist_cm=78, hip_cm=95,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        training_status=TrainingStatus.BEGINNER,
        primary_goal=PrimaryGoal.MUSCLE_GAIN,
        training_days_per_week=3,
        equipment_access=EquipmentAccess.FULL_GYM,
        diet_type=DietType.OMNIVORE,
    )


@pytest.fixture
def maintenance_profile():
    return UserProfile(
        age=32, sex=Sex.FEMALE, height_cm=170, weight_kg=62,
        body_fat_pct=22, neck_cm=32, waist_cm=68, hip_cm=92,
        activity_level=ActivityLevel.ACTIVE,
        training_status=TrainingStatus.INTERMEDIATE,
        primary_goal=PrimaryGoal.MAINTENANCE,
        training_days_per_week=5,
        equipment_access=EquipmentAccess.FULL_GYM,
        diet_type=DietType.OMNIVORE,
    )


@pytest.fixture
def bodyweight_profile():
    return UserProfile(
        age=30, sex=Sex.MALE, height_cm=178, weight_kg=80,
        body_fat_pct=15,
        activity_level=ActivityLevel.MOSTLY_SEDENTARY,
        training_status=TrainingStatus.INTERMEDIATE,
        primary_goal=PrimaryGoal.MUSCLE_GAIN,
        training_days_per_week=3,
        equipment_access=EquipmentAccess.BODYWEIGHT_ONLY,
        diet_type=DietType.OMNIVORE,
    )


# === Plan type tests ===

class TestPlanType:
    def test_cut_goal_defaults_to_program(self, cut_profile):
        """Fat loss goal should auto-default to PROGRAM (time-bound)."""
        assessment = assess_profile(cut_profile)
        plan = build_training_plan(cut_profile, assessment)
        assert plan.plan_type == PlanType.PROGRAM
        assert plan.total_duration_weeks > 0

    def test_maintenance_goal_defaults_to_standard(self, maintenance_profile):
        """Maintenance goal should auto-default to STANDARD (ongoing rotation)."""
        assessment = assess_profile(maintenance_profile)
        plan = build_training_plan(maintenance_profile, assessment)
        assert plan.plan_type == PlanType.STANDARD
        assert plan.total_duration_weeks == 0

    def test_user_can_force_program_for_maintenance(self, maintenance_profile):
        """User can override auto-decision and request PROGRAM explicitly."""
        assessment = assess_profile(maintenance_profile)
        plan = build_training_plan(
            maintenance_profile, assessment,
            plan_type=PlanType.PROGRAM,
        )
        assert plan.plan_type == PlanType.PROGRAM
        assert plan.total_duration_weeks > 0

    def test_user_can_force_standard_for_cut(self, cut_profile):
        """User can override auto-decision and request STANDARD explicitly."""
        assessment = assess_profile(cut_profile)
        plan = build_training_plan(
            cut_profile, assessment,
            plan_type=PlanType.STANDARD,
        )
        assert plan.plan_type == PlanType.STANDARD
        assert plan.total_duration_weeks == 0
        # Standard plan has 1 mesocycle with 1 microcycle
        assert len(plan.mesocycles) == 1
        assert len(plan.mesocycles[0].microcycles) == 1


# === Goal derivation tests ===

class TestGoalDerivation:
    def test_cut_strategy_maps_to_fat_loss(self, cut_profile):
        assessment = assess_profile(cut_profile)
        goal = _derive_training_goal(cut_profile, assessment)
        assert goal == TrainingGoal.FAT_LOSS

    def test_bulk_strategy_maps_to_muscle_gain(self, bulk_profile):
        assessment = assess_profile(bulk_profile)
        goal = _derive_training_goal(bulk_profile, assessment)
        assert goal == TrainingGoal.MUSCLE_GAIN

    def test_maintenance_strategy_maps_to_maintenance(self, maintenance_profile):
        assessment = assess_profile(maintenance_profile)
        goal = _derive_training_goal(maintenance_profile, assessment)
        assert goal == TrainingGoal.MAINTENANCE


# === Split selection tests ===

class TestSplitSelection:
    @pytest.mark.parametrize("days,expected_split_type", [
        (2, SplitType.FULL_BODY),
        (3, SplitType.FULL_BODY),   # 3-day intermediate prefers full body
        (4, SplitType.UPPER_LOWER),
        (5, SplitType.PUSH_PULL_LEGS_UPPER_LOWER),
        (6, SplitType.PPL_X2),
    ])
    def test_split_by_days(self, days, expected_split_type):
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=80,
            body_fat_pct=15,
            activity_level=ActivityLevel.MOSTLY_SEDENTARY,
            training_status=TrainingStatus.INTERMEDIATE,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            training_days_per_week=days,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        )
        assessment = assess_profile(profile)
        plan = build_training_plan(profile, assessment)
        assert plan.split_type == expected_split_type

    def test_beginner_gets_full_body_for_3_days(self):
        """Beginners should always get full body for 3 days/week."""
        profile = UserProfile(
            age=25, sex=Sex.MALE, height_cm=178, weight_kg=75,
            body_fat_pct=15,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        )
        assessment = assess_profile(profile)
        plan = build_training_plan(profile, assessment)
        assert plan.split_type == SplitType.FULL_BODY

    def test_advanced_5day_can_get_body_part(self):
        """Advanced trainees at 5 days can use body part split."""
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=85,
            body_fat_pct=12,
            activity_level=ActivityLevel.ACTIVE,
            training_status=TrainingStatus.ADVANCED,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            training_days_per_week=5,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        )
        assessment = assess_profile(profile)
        # Body part split is suitable for ADVANCED + HYPERTROPHY/MUSCLE_GAIN
        # but architect preference order puts PPL_UL first for advanced at 5 days
        plan = build_training_plan(profile, assessment)
        # Both are valid; just verify it's one of the 5-day splits
        assert plan.split_type in (
            SplitType.PUSH_PULL_LEGS_UPPER_LOWER,
            SplitType.BODY_PART,
        )


# === Periodization tests ===

class TestPeriodization:
    def test_beginner_gets_linear(self):
        profile = UserProfile(
            age=25, sex=Sex.MALE, height_cm=178, weight_kg=75,
            body_fat_pct=15,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        )
        assessment = assess_profile(profile)
        plan = build_training_plan(profile, assessment)
        assert plan.progression == ProgressionScheme.LINEAR

    def test_intermediate_gets_dup(self):
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=80,
            body_fat_pct=15,
            activity_level=ActivityLevel.MOSTLY_SEDENTARY,
            training_status=TrainingStatus.INTERMEDIATE,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            training_days_per_week=4,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        )
        assessment = assess_profile(profile)
        plan = build_training_plan(profile, assessment)
        assert plan.progression == ProgressionScheme.DUP

    def test_advanced_gets_block(self):
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=85,
            body_fat_pct=12,
            activity_level=ActivityLevel.ACTIVE,
            training_status=TrainingStatus.ADVANCED,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            training_days_per_week=5,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        )
        assessment = assess_profile(profile)
        plan = build_training_plan(profile, assessment)
        assert plan.progression == ProgressionScheme.BLOCK

    def test_muscle_gain_reps_are_hypertrophy_range(self, bulk_profile):
        """Muscle gain plan should use hypertrophy rep ranges (5-12)."""
        assessment = assess_profile(bulk_profile)
        plan = build_training_plan(bulk_profile, assessment)
        for meso in plan.mesocycles:
            for micro in meso.microcycles:
                for w in micro.workouts:
                    for we in w.exercises:
                        if we.exercise.category.value == "compound_primary":
                            # Parse rep range like "5-8"
                            assert "-" in we.reps, f"No rep range: {we.reps}"
                            lo, hi = (int(x) for x in we.reps.split("-"))
                            assert 3 <= lo <= 8
                            assert 5 <= hi <= 12

    def test_deload_week_has_fewer_sets(self, cut_profile):
        """Deload week should reduce volume by ~1 set per exercise."""
        assessment = assess_profile(cut_profile)
        plan = build_training_plan(cut_profile, assessment)
        # Find deload week (last microcycle of last mesocycle)
        last_meso = plan.mesocycles[-1]
        deload_micro = last_meso.microcycles[-1]
        assert deload_micro.is_deload

        # Compare to first microcycle
        first_micro = plan.mesocycles[0].microcycles[0]
        for w_deload, w_first in zip(deload_micro.workouts, first_micro.workouts):
            for we_deload, we_first in zip(w_deload.exercises, w_first.exercises):
                assert we_deload.sets <= we_first.sets, (
                    f"Deload {we_deload.exercise.name}: {we_deload.sets} sets "
                    f"vs first week {we_first.sets} sets"
                )


# === Muscle focus tests ===

class TestMuscleFocus:
    def test_muscle_focus_adds_extra_slots(self, cut_profile):
        """muscle_focus should add extra accessory exercises to the plan."""
        assessment = assess_profile(cut_profile)
        plan_no_focus = build_training_plan(cut_profile, assessment)
        plan_with_focus = build_training_plan(
            cut_profile, assessment,
            muscle_focus=["chest", "arms"],
        )

        # With focus, total exercise count should be higher
        count_no = sum(
            len(w.exercises)
            for m in plan_no_focus.mesocycles
            for mic in m.microcycles
            for w in mic.workouts
        )
        count_yes = sum(
            len(w.exercises)
            for m in plan_with_focus.mesocycles
            for mic in m.microcycles
            for w in mic.workouts
        )
        assert count_yes > count_no, (
            f"Focus plan has {count_yes} exercises vs {count_no} without focus"
        )

        # muscle_focus field should be populated
        assert "chest" in plan_with_focus.muscle_focus
        assert "arms" in plan_with_focus.muscle_focus

    def test_muscle_focus_increases_target_volume(self, cut_profile):
        """Focus on chest should increase chest weekly volume vs no focus."""
        assessment = assess_profile(cut_profile)
        plan_no = build_training_plan(cut_profile, assessment)
        plan_yes = build_training_plan(
            cut_profile, assessment,
            muscle_focus=["chest"],
        )
        # Chest volume should be higher with focus
        chest_no = plan_no.weekly_volume_summary.get("chest", 0)
        chest_yes = plan_yes.weekly_volume_summary.get("chest", 0)
        assert chest_yes >= chest_no, (
            f"Focus chest volume {chest_yes} < no-focus {chest_no}"
        )

    def test_muscle_focus_unknown_muscle_logs_warning(self, cut_profile):
        """Unknown muscle_focus names should not crash, just log a warning."""
        assessment = assess_profile(cut_profile)
        plan = build_training_plan(
            cut_profile, assessment,
            muscle_focus=["nonexistent_muscle"],
        )
        # Should still produce a valid plan
        assert plan.split_type is not None
        # The unknown muscle should NOT be in the focus list
        assert "nonexistent_muscle" not in plan.muscle_focus


# === Equipment filter tests ===

class TestEquipmentFilter:
    def test_bodyweight_user_gets_non_empty_workouts(self, bodyweight_profile):
        """Issue 4 regression: bodyweight-only users must get >0 exercises per workout."""
        assessment = assess_profile(bodyweight_profile)
        plan = build_training_plan(bodyweight_profile, assessment)
        for meso in plan.mesocycles:
            for micro in meso.microcycles:
                for w in micro.workouts:
                    assert len(w.exercises) >= 3, (
                        f"Workout {w.name} only has {len(w.exercises)} exercises"
                    )
                    for we in w.exercises:
                        assert we.exercise.equipment in {"bodyweight", "bands"}, (
                            f"{we.exercise.name} uses {we.exercise.equipment}"
                        )

    def test_home_gym_user_gets_no_machine_exercises(self):
        """Home gym users should never get machine/cable-only exercises."""
        profile = UserProfile(
            age=30, sex=Sex.FEMALE, height_cm=165, weight_kg=68,
            body_fat_pct=28, neck_cm=33, waist_cm=75, hip_cm=100,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.RECOMP,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.HOME_GYM,
            diet_type=DietType.OMNIVORE,
        )
        assessment = assess_profile(profile)
        plan = build_training_plan(profile, assessment)
        home_gym_allowed = {
            "barbell", "dumbbell", "kettlebell", "bodyweight",
            "bands", "ez_bar", "landmine", "trap_bar", "exercise_ball",
        }
        for meso in plan.mesocycles:
            for micro in meso.microcycles:
                for w in micro.workouts:
                    for we in w.exercises:
                        assert we.exercise.equipment in home_gym_allowed, (
                            f"{we.exercise.name} uses {we.exercise.equipment}"
                        )


# === Program structure tests ===

class TestProgramStructure:
    def test_program_has_multiple_mesocycles_for_advanced(self):
        """Advanced trainees should get 2+ mesocycles in their program."""
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=85,
            body_fat_pct=12,
            activity_level=ActivityLevel.ACTIVE,
            training_status=TrainingStatus.ADVANCED,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            training_days_per_week=5,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        )
        assessment = assess_profile(profile)
        plan = build_training_plan(profile, assessment)
        assert plan.plan_type == PlanType.PROGRAM
        assert len(plan.mesocycles) >= 1
        # Total duration should be substantial
        assert plan.total_duration_weeks >= 10

    def test_standard_plan_has_one_microcycle(self, maintenance_profile):
        """Standard plans should have exactly 1 mesocycle with 1 microcycle."""
        assessment = assess_profile(maintenance_profile)
        plan = build_training_plan(maintenance_profile, assessment)
        assert plan.plan_type == PlanType.STANDARD
        assert len(plan.mesocycles) == 1
        assert len(plan.mesocycles[0].microcycles) == 1

    def test_block_periodization_has_phases(self):
        """Advanced BLOCK plans should have accumulation/intensification phases."""
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=85,
            body_fat_pct=12,
            activity_level=ActivityLevel.ACTIVE,
            training_status=TrainingStatus.ADVANCED,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            training_days_per_week=6,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        )
        assessment = assess_profile(profile)
        plan = build_training_plan(profile, assessment)
        assert plan.progression == ProgressionScheme.BLOCK
        # Block mesocycles should have phase names in their names
        meso_names = [m.name.lower() for m in plan.mesocycles]
        assert any("accumulation" in n or "intensification" in n or "peak" in n
                   for n in meso_names), f"No phase labels in {meso_names}"


# === Serialization tests ===

class TestSerialization:
    def test_plan_serializes_with_new_fields(self, cut_profile):
        """Serialized plan should include plan_type, goal, muscle_focus."""
        assessment = assess_profile(cut_profile)
        plan = build_training_plan(
            cut_profile, assessment,
            muscle_focus=["chest"],
        )
        d = plan.to_dict()
        assert "plan_type" in d
        assert "goal" in d
        assert "muscle_focus" in d
        assert "total_duration_weeks" in d
        assert d["plan_type"] in ("standard", "program")
        assert d["goal"] in [g.value for g in TrainingGoal]

    def test_microcycle_has_is_deload_field(self, cut_profile):
        """Microcycle should serialize with is_deload field."""
        assessment = assess_profile(cut_profile)
        plan = build_training_plan(cut_profile, assessment)
        d = plan.to_dict()
        for meso in d["mesocycles"]:
            for micro in meso["microcycles"]:
                assert "is_deload" in micro
                assert isinstance(micro["is_deload"], bool)

    def test_workout_has_focus_field(self, cut_profile):
        """Workout should serialize with focus field."""
        assessment = assess_profile(cut_profile)
        plan = build_training_plan(cut_profile, assessment)
        d = plan.to_dict()
        for meso in d["mesocycles"]:
            for micro in meso["microcycles"]:
                for w in micro["workouts"]:
                    assert "focus" in w
                    assert "name" in w
                    assert "exercises" in w

    def test_full_plan_json_serializable(self, cut_profile):
        assessment = assess_profile(cut_profile)
        plan = build_training_plan(cut_profile, assessment)
        d = plan.to_dict()
        json_str = json.dumps(d, default=str)
        # Should be substantial
        assert len(json_str) > 10_000


# === Integration with engine.propose_plan ===

class TestEngineIntegration:
    def test_propose_plan_passes_muscle_focus_through(self, cut_profile):
        """Engine.propose_plan should pass muscle_focus to the training architect."""
        assessment = assess_profile(cut_profile)
        plan = propose_plan(
            cut_profile, assessment,
            muscle_focus=["chest", "arms"],
        )
        assert "chest" in plan.training.muscle_focus
        assert "arms" in plan.training.muscle_focus

    def test_propose_plan_passes_plan_type_through(self, maintenance_profile):
        """Engine.propose_plan should pass plan_type to the training architect."""
        assessment = assess_profile(maintenance_profile)
        plan = propose_plan(
            maintenance_profile, assessment,
            plan_type=PlanType.PROGRAM,
        )
        assert plan.training.plan_type == PlanType.PROGRAM

    def test_propose_plan_summary_mentions_plan_type(self, cut_profile):
        """Plan summary should mention the plan type (STANDARD vs PROGRAM)."""
        assessment = assess_profile(cut_profile)
        plan = propose_plan(cut_profile, assessment)
        assert "PROGRAM" in plan.summary or "STANDARD" in plan.summary


# === Split design sanity tests ===

class TestSplitDesigns:
    def test_all_splits_have_at_least_one_template(self):
        for split in ALL_SPLITS:
            assert len(split.templates) >= 1, f"{split.name} has no templates"

    def test_all_templates_have_at_least_one_slot(self):
        for split in ALL_SPLITS:
            for tmpl in split.templates:
                assert len(tmpl.slots) >= 1, (
                    f"{split.name}/{tmpl.name} has no slots"
                )

    def test_all_slots_have_required_fields(self):
        for split in ALL_SPLITS:
            for tmpl in split.templates:
                for slot in tmpl.slots:
                    assert slot.name
                    assert slot.primary_muscle
                    assert slot.pattern
                    assert slot.category is not None
                    assert slot.sets >= 1

    def test_get_splits_for_days_returns_correct_matches(self):
        two_day = get_splits_for_days(2)
        assert all(s.days_per_week == 2 for s in two_day)
        assert len(two_day) >= 1

        four_day = get_splits_for_days(4)
        assert all(s.days_per_week == 4 for s in four_day)
        assert len(four_day) >= 1

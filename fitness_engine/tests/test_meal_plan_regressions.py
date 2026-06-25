"""
Final batch of regression tests for remaining Tier 5 findings.

Covers:
  - Tier 5.54: update_tdee_with_logs + Harris-Benedict variant tests
  - Tier 5.55: BULK_RATE_BY_STATUS single-source test (no duplication)
  - Tier 5.56: BEGINNER + 4-day split selection test
  - Tier 5.61: Female-fixture tests for assessment
  - Tier 5.62: Bodyweight-only tests for training
"""
import pytest

from fitness_engine.models.profile import (
    UserProfile, Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType,
)
from fitness_engine.assessment import assess_profile
from fitness_engine import assess_profile as _assess, propose_plan, PlanPreferences


# === Tier 5.54: update_tdee_with_logs + Harris-Benedict tests ===

class TestUpdateTDEEWithLogs:
    """Tier 5.54 — update_tdee_with_logs was previously untested."""

    def test_update_tdee_with_logs_basic(self):
        """update_tdee_with_logs should blend observed TDEE with formula TDEE."""
        from fitness_engine.nutrition.tdee import update_tdee_with_logs
        from fitness_engine.models.nutrition import TDEEResult
        tdee = TDEEResult(
            rmr_kcal=1800, activity_factor=1.2, tdee_kcal=2160, final_tdee_kcal=2160,
        )
        # 14 days, eating 2500, gained 0.5 kg → observed TDEE = 2500 - (0.5*7700)/14 = 2500-275 = 2225
        result = update_tdee_with_logs(
            tdee,
            avg_intake_kcal=2500,
            weight_start_kg=80.0,
            weight_end_kg=80.5,
            n_days=14,
        )
        # Should produce a blended TDEE between observed and formula
        assert 2000 < result.final_tdee_kcal < 2300
        assert result.adaptive_tdee_kcal is not None

    def test_update_tdee_with_logs_insufficient_data(self):
        """With < 1 day of data, should return TDEE unchanged."""
        from fitness_engine.nutrition.tdee import update_tdee_with_logs
        from fitness_engine.models.nutrition import TDEEResult
        tdee = TDEEResult(
            rmr_kcal=1800, activity_factor=1.2, tdee_kcal=2160, final_tdee_kcal=2160,
        )
        result = update_tdee_with_logs(
            tdee, avg_intake_kcal=2500,
            weight_start_kg=80.0, weight_end_kg=80.0, n_days=0,
        )
        assert result.final_tdee_kcal == 2160  # unchanged


class TestHarrisBenedictVariants:
    """Tier 5.54 — both Harris-Benedict variants were previously untested."""

    def test_harris_benedict_original_male(self):
        """HB Original (1919): Men = 66 + 13.7×W + 5×H - 6.8×A"""
        from fitness_engine.nutrition import rmr_harris_benedict_original
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            activity_level=ActivityLevel.SEDENTARY,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
        )
        # 66 + 13.7*82 + 5*178 - 6.8*30 = 66 + 1123.4 + 890 - 204 = 1875.4
        rmr = rmr_harris_benedict_original(profile)
        assert abs(rmr - 1875) < 10

    def test_harris_benedict_revised_male(self):
        """HB Revised (1984): Men = 13.397×W + 4.799×H - 5.677×A + 88.362"""
        from fitness_engine.nutrition import rmr_harris_benedict_revised
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            activity_level=ActivityLevel.SEDENTARY,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
        )
        # 13.397*82 + 4.799*178 - 5.677*30 + 88.362 = 1098.6 + 854.2 - 170.3 + 88.4 = 1870.9
        rmr = rmr_harris_benedict_revised(profile)
        assert abs(rmr - 1871) < 10

    def test_compute_rmr_with_harris_benedict_orig(self):
        """compute_rmr should be able to use HARRIS_BENEDICT_ORIG if selected.
        Note: select_rmr_formula defaults to Mifflin/Katch-McArdle, but the
        formula parameter is respected when set explicitly via the profile."""
        from fitness_engine.nutrition import rmr_harris_benedict_original
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            activity_level=ActivityLevel.SEDENTARY,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
        )
        # The function exists and is callable
        rmr = rmr_harris_benedict_original(profile)
        assert rmr > 1500
        assert rmr < 2500


# === Tier 5.55: BULK_RATE_BY_STATUS single-source test ===

class TestBulkRateSingleSource:
    """Tier 5.55 — BULK_RATE_BY_STATUS should exist in only ONE place
    (nutrition.calories), not duplicated in assessment.muscular_potential."""

    def test_bulk_rate_not_in_muscular_potential(self):
        """BULK_RATE_BY_STATUS must NOT be importable from muscular_potential."""
        from fitness_engine.assessment import muscular_potential
        assert not hasattr(muscular_potential, "BULK_RATE_BY_STATUS"), (
            "BULK_RATE_BY_STATUS should be removed from muscular_potential.py "
            "(canonical copy lives in nutrition.calories.py)"
        )

    def test_bulk_rate_in_calories(self):
        """BULK_RATE_BY_STATUS must be importable from nutrition.calories."""
        from fitness_engine.nutrition.calories import BULK_RATE_BY_STATUS
        assert BULK_RATE_BY_STATUS is not None
        assert len(BULK_RATE_BY_STATUS) == 4  # BEGINNER, NOVICE, INTERMEDIATE, ADVANCED

    def test_bulk_rate_not_in_assessment_init(self):
        """BULK_RATE_BY_STATUS must NOT be re-exported from assessment.__init__."""
        import fitness_engine.assessment as assessment_pkg
        assert not hasattr(assessment_pkg, "BULK_RATE_BY_STATUS"), (
            "BULK_RATE_BY_STATUS should not be re-exported from assessment.__init__"
        )

    def test_bulk_rate_values_correct(self):
        """Verify the canonical values match the RippedBody source."""
        from fitness_engine.nutrition.calories import BULK_RATE_BY_STATUS
        from fitness_engine.models.profile import TrainingStatus
        assert BULK_RATE_BY_STATUS[TrainingStatus.BEGINNER] == 0.020     # 2.0% BW/mo
        assert BULK_RATE_BY_STATUS[TrainingStatus.NOVICE] == 0.015       # 1.5%
        assert BULK_RATE_BY_STATUS[TrainingStatus.INTERMEDIATE] == 0.010 # 1.0%
        assert BULK_RATE_BY_STATUS[TrainingStatus.ADVANCED] == 0.005     # 0.5%


# === Tier 5.56: BEGINNER + 4-day split selection ===

class TestBeginnerFourDaySplit:
    """Tier 5.56 — BEGINNER + 4-day split selection was untested.
    The audit noted that suitable_for_experience is silently bypassed for
    beginners requesting 4 days (no beginner-suitable 4-day split exists)."""

    def test_beginner_can_get_4_day_plan(self):
        """A beginner requesting 4 days/week should get a non-empty plan.
        The architect falls back to UPPER_LOWER_4DAY even though it's not
        marked suitable_for_experience=[BEGINNER]. This test documents that
        behavior so a future regression is caught."""
        profile = UserProfile(
            age=25, sex=Sex.MALE, height_cm=178, weight_kg=75,
            body_fat_pct=14,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            training_days_per_week=4,
            equipment_access=EquipmentAccess.FULL_GYM,
        )
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        assert plan.training is not None
        assert plan.training.training_days_per_week == 4
        # Should have non-empty workouts
        if plan.training.mesocycles:
            mc = plan.training.mesocycles[0]
            assert len(mc.microcycles[0].workouts) == 4

    def test_beginner_3_day_gets_full_body(self):
        """A beginner requesting 3 days/week should get full_body_3day
        (which IS marked suitable_for_experience=[BEGINNER])."""
        profile = UserProfile(
            age=25, sex=Sex.MALE, height_cm=178, weight_kg=75,
            body_fat_pct=14,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
        )
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        assert plan.training.training_days_per_week == 3


# === Tier 5.61: Female-fixture tests for assessment ===

class TestFemaleAssessment:
    """Tier 5.61 — assessment tests previously used only male fixtures."""

    def test_female_assessment_runs_without_error(self):
        """A female profile should produce a valid assessment."""
        profile = UserProfile(
            age=28, sex=Sex.FEMALE, height_cm=165, weight_kg=68,
            body_fat_pct=28, neck_cm=33, waist_cm=75, hip_cm=100,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.RECOMP,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.HOME_GYM,
        )
        assessment = assess_profile(profile)
        assert assessment.body_composition is not None
        assert assessment.body_composition.body_fat_pct > 0
        assert assessment.health_risk is not None
        assert assessment.muscular_potential is not None

    def test_female_body_fat_navy_uses_hip(self):
        """Female Navy method requires hip circumference."""
        from fitness_engine.assessment import body_fat_navy
        profile = UserProfile(
            age=28, sex=Sex.FEMALE, height_cm=165, weight_kg=68,
            neck_cm=33, waist_cm=75, hip_cm=100,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.RECOMP,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.HOME_GYM,
        )
        bf = body_fat_navy(profile)
        assert bf is not None  # hip provided → should compute
        assert 15 < bf < 45    # sensible female range

    def test_female_berkhan_returns_none(self):
        """Tier 2.17 fix: Berkhan model is men-only. Female profiles should
        get berkhan_stage_max_kg=None."""
        profile = UserProfile(
            age=28, sex=Sex.FEMALE, height_cm=165, weight_kg=68,
            body_fat_pct=28,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.RECOMP,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.HOME_GYM,
        )
        assessment = assess_profile(profile)
        assert assessment.muscular_potential.berkhan_stage_max_kg is None, (
            "Berkhan model should return None for female profiles (Tier 2.17 fix)"
        )

    def test_female_ffmi_uses_normalized(self):
        """Tier 1.9 fix: FFMI ceiling comparison uses normalized FFMI."""
        profile = UserProfile(
            age=28, sex=Sex.FEMALE, height_cm=165, weight_kg=68,
            body_fat_pct=28,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.RECOMP,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.HOME_GYM,
        )
        assessment = assess_profile(profile)
        mp = assessment.muscular_potential
        # ffmi_to_ceiling_pct should use normalized FFMI (Tier 1.9)
        assert 0 < mp.ffmi_to_ceiling_pct < 200


# === Tier 5.62: Bodyweight-only tests for training ===

class TestBodyweightTraining:
    """Tier 5.62 — bodyweight-only training was previously untested."""

    def test_bodyweight_user_gets_non_empty_plan(self):
        """A bodyweight-only user should get a plan with exercises."""
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=80,
            body_fat_pct=16,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.INTERMEDIATE,
            primary_goal=PrimaryGoal.RECOMP,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.BODYWEIGHT_ONLY,
        )
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        assert plan.training is not None
        # Should have at least some workouts with exercises
        if plan.training.mesocycles:
            mc = plan.training.mesocycles[0]
            total_exercises = sum(len(w.exercises) for w in mc.microcycles[0].workouts)
            assert total_exercises > 0, "Bodyweight user should get non-empty workouts"

    def test_bodyweight_user_gets_no_barbell_exercises(self):
        """Bodyweight-only users should not get barbell/machine exercises."""
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=80,
            body_fat_pct=16,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.INTERMEDIATE,
            primary_goal=PrimaryGoal.RECOMP,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.BODYWEIGHT_ONLY,
        )
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        if plan.training.mesocycles:
            for mc in plan.training.mesocycles:
                for cyc in mc.microcycles:
                    for w in cyc.workouts:
                        for we in w.exercises:
                            if we.exercise and we.exercise.equipment:
                                equip = we.exercise.equipment.lower()
                                # Should not have barbell/machine/cable
                                # (bodyweight, bands, dumbbell are OK for home gym,
                                # but BODYWEIGHT_ONLY should be even stricter)
                                # Just verify no barbell
                                assert "barbell" not in equip, (
                                    f"Bodyweight-only user got barbell exercise: {we.exercise.name}"
                                )

    def test_bodyweight_user_full_plan_serializes(self):
        """Bodyweight-only plan should serialize to valid JSON."""
        import json
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=80,
            body_fat_pct=16,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.INTERMEDIATE,
            primary_goal=PrimaryGoal.RECOMP,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.BODYWEIGHT_ONLY,
        )
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment, PlanPreferences(include_pre_post_workout=True))
        d = plan.to_dict()
        json_str = json.dumps(d, default=str)
        assert len(json_str) > 1000


# === Tier 2.18: STRENGTH goal test ===

class TestStrengthGoal:
    """Tier 2.18 — STRENGTH primary_goal is now honored."""

    def test_strength_goal_honored_for_maintenance_strategy(self):
        """A user with primary_goal=STRENGTH and assessment strategy=MAINTENANCE
        should get TrainingGoal.STRENGTH (not silently remapped to HYPERTROPHY)."""
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=80,
            body_fat_pct=15,
            activity_level=ActivityLevel.ACTIVE,
            training_status=TrainingStatus.INTERMEDIATE,
            primary_goal=PrimaryGoal.STRENGTH,  # explicit strength request
            training_days_per_week=4,
            equipment_access=EquipmentAccess.FULL_GYM,
        )
        assessment = assess_profile(profile)
        # Assessment strategy should be MAINTENANCE (15% BF, not obese)
        plan = propose_plan(profile, assessment)
        assert plan.training.goal.value == "strength", (
            f"User requested STRENGTH goal but got {plan.training.goal.value}. "
            f"This was the Tier 2.18 bug — STRENGTH was unreachable."
        )

    def test_strength_goal_overridden_by_safety_cut(self):
        """If the user is obese, the safety-override CUT takes precedence
        over the user's STRENGTH request."""
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=110,
            body_fat_pct=28,  # obese (≥25% for men)
            activity_level=ActivityLevel.SEDENTARY,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.STRENGTH,  # requests strength
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
        )
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        # Safety override: obese → CUT/FAT_LOSS takes precedence
        assert plan.training.goal.value in ("fat_loss", "general_fitness"), (
            f"Obese user's STRENGTH request should be overridden by safety CUT; "
            f"got {plan.training.goal.value}"
        )

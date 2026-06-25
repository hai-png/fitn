"""
Phase-4 tests for RippedBody-informed training system enhancements.

Verifies:
  - Exercise categorization: 24 movement patterns detected correctly
  - Swap system: get_swappable_exercises returns valid variations
  - Environment-aware equipment preference (full_gym vs home_gym vs bodyweight)
  - Volume landmarks: MEV/MAV/MRV/ML per muscle
  - Fractional set counting (primary=1.0, secondary=0.5)
  - 11-set per-session cap check
  - Volume tier → recommended weekly sets
  - RIR-based intensity model (per rep range × intensity tier)
  - RIR ↔ RPE conversion
  - Warm-up set generator (≤6 reps vs ≥6 reps recipes)
  - Reactive deload self-assessment (≥2 Yes triggers deload)
  - Reactive deload recipe (-40% sets, RPE unchanged)
  - Strength block phases (Volume → Load → Peak)
  - Peak phase duration scales with prior phase length
"""
import pytest

from fitness_engine import (
    UserProfile, assess_profile, propose_plan,
)
from fitness_engine.models.profile import (
    Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType,
)
from fitness_engine.training import (
    EXERCISES, get_exercise_by_slug,
    categorize_exercise, get_movement_pattern, get_pattern_family,
    get_environment_preferred_equipment, get_swappable_exercises,
    PatternFamily, MOVEMENT_PATTERNS,
    VolumeTier, TIER_SET_RANGES,
    get_muscle_landmarks, get_recommended_frequency,
    PER_SESSION_SET_CAP, check_session_volume_cap,
    count_sets_toward_muscle, compute_weekly_volume_per_muscle,
    get_recommended_weekly_sets, validate_weekly_volume,
    # Phase-6 cleanup: removed ``get_specialization_program`` (dead code).
    # The underlying constants are still tested directly in TestSpecialization.
    SPECIALIZATION_BALANCED, SPECIALIZATION_FOCUS,
    ExerciseIntensityTier, get_exercise_intensity_tier,
    RIR_TABLE, get_rir_range, rir_to_rpe, rpe_to_rir,
    WarmUpSet, WARMUP_LEQ_6_REP, WARMUP_GEQ_6_REP,
    generate_warmup_sets, generate_warmup_for_workout,
    REACTIVE_DELOAD_QUESTIONS, should_deload,
    # Phase-6 cleanup: removed ``apply_deload`` (dead code).
    StrengthPhase, STRENGTH_PHASE_SPECS,
    # Phase-6 cleanup: removed ``get_peak_phase_duration`` (dead code).
)
from fitness_engine.models.training import (
    Workout, WorkoutExercise, Exercise, ExerciseCategory,
    TrainingGoal,
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


# === Exercise categorization tests ===

class TestExerciseCategorization:
    def test_all_exercises_get_categorized(self):
        """Every exercise in the library should get a movement pattern."""
        for ex in EXERCISES[:100]:  # sample first 100 for speed
            pattern = get_movement_pattern(ex)
            assert pattern in MOVEMENT_PATTERNS, (
                f"{ex.name} got unknown pattern: {pattern}"
            )

    def test_squat_pattern_detected_for_squats(self):
        """Barbell back squat should be categorized as 'squat' pattern."""
        ex = get_exercise_by_slug("high-bar-back-squat")
        assert ex is not None
        assert get_movement_pattern(ex) == "squat"

    def test_hinge_pattern_detected_for_deadlifts(self):
        """Deadlift should be categorized as 'hinge' pattern."""
        ex = get_exercise_by_slug("deadlifts")
        assert ex is not None
        assert get_movement_pattern(ex) == "hinge"

    def test_horizontal_push_detected_for_bench_press(self):
        """Barbell bench press should be 'horizontal_push'."""
        ex = get_exercise_by_slug("barbell-bench-press")
        assert ex is not None
        assert get_movement_pattern(ex) == "horizontal_push"

    def test_vertical_pull_detected_for_pull_up(self):
        """Pull-up should be 'vertical_pull'."""
        ex = get_exercise_by_slug("pull-up")
        assert ex is not None
        assert get_movement_pattern(ex) == "vertical_pull"

    def test_pattern_family_is_valid_enum(self):
        """Every pattern should map to a valid PatternFamily."""
        for pattern_name, spec in MOVEMENT_PATTERNS.items():
            assert isinstance(spec.family, PatternFamily)

    def test_categorize_exercise_returns_full_info(self):
        """categorize_exercise should return ExerciseCategoryInfo with all fields."""
        ex = get_exercise_by_slug("military-press")
        info = categorize_exercise(ex)
        assert info.exercise == ex
        assert info.movement_pattern
        assert isinstance(info.pattern_family, PatternFamily)
        assert isinstance(info.primary_muscles, list)
        assert isinstance(info.environment_preferences, dict)

    def test_all_24_patterns_defined(self):
        """The taxonomy should have at least 24 canonical patterns."""
        assert len(MOVEMENT_PATTERNS) >= 24


# === Environment preference tests ===

class TestEnvironmentPreference:
    def test_squat_prefers_barbell_in_full_gym(self):
        """In a full gym, squat pattern should prefer barbell first."""
        pref = get_environment_preferred_equipment("squat", "full_gym")
        assert pref[0] == "barbell"

    def test_squat_prefers_barbell_in_home_gym(self):
        """In a home gym, squat should still prefer barbell (if available)."""
        pref = get_environment_preferred_equipment("squat", "home_gym")
        assert pref[0] == "barbell"

    def test_squat_falls_back_to_bodyweight(self):
        """Bodyweight-only users should get bodyweight as first preference."""
        pref = get_environment_preferred_equipment("squat", "bodyweight_only")
        assert pref[0] == "bodyweight"

    def test_horizontal_push_prefers_barbell_in_full_gym(self):
        pref = get_environment_preferred_equipment("horizontal_push", "full_gym")
        assert pref[0] == "barbell"

    def test_horizontal_push_falls_back_to_pushup(self):
        """Bodyweight users should get bodyweight push-ups for horizontal push."""
        pref = get_environment_preferred_equipment("horizontal_push", "bodyweight_only")
        assert pref[0] == "bodyweight"

    def test_leg_press_machine_only_in_full_gym(self):
        """Leg press should prefer machine in full gym."""
        pref = get_environment_preferred_equipment("leg_press", "full_gym")
        assert pref[0] == "machine"

    def test_leg_press_substitutes_dumbbell_in_home_gym(self):
        """Home gym users should get dumbbell substitute for leg press."""
        pref = get_environment_preferred_equipment("leg_press", "home_gym")
        assert pref[0] == "dumbbell"


# === Swap system tests ===

class TestSwapSystem:
    def test_get_swappable_returns_variations(self):
        """get_swappable_exercises should return exercises of the same pattern."""
        ex = get_exercise_by_slug("high-bar-back-squat")
        swaps = get_swappable_exercises(
            ex,
            equipment_allowed={"barbell", "dumbbell", "bodyweight", "machine"},
        )
        assert len(swaps) > 0
        # All swaps should be squat pattern
        for swap in swaps:
            assert get_movement_pattern(swap) == "squat"

    def test_swappable_excludes_original(self):
        """The original exercise should not be in its own swap list."""
        ex = get_exercise_by_slug("barbell-bench-press")
        swaps = get_swappable_exercises(
            ex,
            equipment_allowed={"barbell", "dumbbell", "cable", "bodyweight"},
        )
        assert ex.slug not in [s.slug for s in swaps if s.slug]

    def test_swappable_respects_equipment_filter(self):
        """Swap list should only include exercises with allowed equipment."""
        ex = get_exercise_by_slug("barbell-bench-press")
        # Bodyweight-only equipment
        swaps = get_swappable_exercises(
            ex,
            equipment_allowed={"bodyweight", "bands"},
        )
        for swap in swaps:
            assert swap.equipment in {"bodyweight", "bands"}

    def test_swappable_returns_at_least_3_for_common_patterns(self):
        """Common patterns (squat, bench, row) should have ≥3 swaps in full gym."""
        full_gym = {
            "barbell", "dumbbell", "bodyweight", "cable", "machine",
            "kettlebell", "bands", "ez_bar", "landmine", "trap_bar",
        }
        test_cases = [
            ("high-bar-back-squat", "squat"),
            ("barbell-bench-press", "horizontal_push"),
            ("bent-over-barbell-row", "horizontal_pull"),
            ("military-press", "vertical_push"),
            ("pull-up", "vertical_pull"),
        ]
        for slug, pattern in test_cases:
            ex = get_exercise_by_slug(slug)
            assert ex is not None, f"Exercise {slug} not found"
            swaps = get_swappable_exercises(ex, equipment_allowed=full_gym, limit=20)
            assert len(swaps) >= 3, (
                f"{slug} ({pattern}) only has {len(swaps)} swaps in full gym"
            )

    def test_swappable_bodyweight_user_gets_bodyweight_swaps(self):
        """Bodyweight-only users should get bodyweight swap options."""
        ex = get_exercise_by_slug("barbell-bench-press")
        swaps = get_swappable_exercises(
            ex,
            equipment_allowed={"bodyweight", "bands"},
        )
        assert len(swaps) > 0
        # At least one should be bodyweight
        assert any(s.equipment == "bodyweight" for s in swaps)

    def test_swappable_sorts_by_equipment_preference(self):
        """Swaps should be sorted with environment-preferred equipment first."""
        ex = get_exercise_by_slug("high-bar-back-squat")
        # In full gym, barbell should be preferred first for squats
        swaps = get_swappable_exercises(
            ex,
            equipment_allowed={
                "barbell", "dumbbell", "bodyweight", "machine", "kettlebell",
            },
            limit=10,
        )
        if swaps:
            # First swap should use barbell (preferred for squat in full gym)
            assert swaps[0].equipment == "barbell", (
                f"Expected barbell first, got {swaps[0].equipment} ({swaps[0].name})"
            )


# === Volume landmarks tests ===

class TestVolumeLandmarks:
    def test_chest_landmarks_are_reasonable(self):
        """Chest landmarks should align with RP consensus.

        Phase-6 fix: values updated from the previous flat MEV=4 heuristic
        to Renaissance Periodization consensus (Israetel):
          MEV=8, MAV=10-22, MRV=24, ML=8.
        """
        lm = get_muscle_landmarks("chest")
        assert lm.mev == 8
        assert lm.mav_lo == 10
        assert lm.mav_hi == 22
        assert lm.mrv == 24

    def test_back_mev_greater_than_chest_mev(self):
        """Phase-6: back needs ~2-3x chest MEV per RP consensus."""
        chest = get_muscle_landmarks("chest")
        back = get_muscle_landmarks("back")
        assert back.mev > chest.mev
        assert back.mev >= chest.mev * 1.2  # at least 20% more

    def test_unknown_muscle_returns_default(self):
        """Unknown muscles should get sensible defaults."""
        lm = get_muscle_landmarks("nonexistent_muscle")
        assert lm.mev >= 4
        assert lm.mav_lo >= 8
        assert lm.mrv >= 20

    def test_recommended_frequency_low_volume(self):
        """4-10 sets/muscle/wk → 1-2x frequency."""
        assert get_recommended_frequency(8) == 2
        assert get_recommended_frequency(10) == 2

    def test_recommended_frequency_medium_volume(self):
        """11-20 sets/muscle/wk → 2-3x frequency."""
        assert get_recommended_frequency(15) == 3
        assert get_recommended_frequency(20) == 3

    def test_recommended_frequency_high_volume(self):
        """21+ sets/muscle/wk → 3+x frequency."""
        assert get_recommended_frequency(25) == 4
        assert get_recommended_frequency(30) == 4

    def test_strength_frequency_floor_is_2(self):
        """Strength training should have ≥2x/lift/wk frequency."""
        assert get_recommended_frequency(3, is_strength=True) == 2
        assert get_recommended_frequency(1, is_strength=True) == 2


# === Fractional set counting tests ===

class TestFractionalSetCounting:
    def test_primary_muscle_counts_as_1(self):
        """Primary muscle should get full credit (1.0 sets)."""
        # Bench press: primary=chest, secondary=shoulders, triceps
        ex = get_exercise_by_slug("barbell-bench-press")
        count = count_sets_toward_muscle(ex, "chest", sets=4)
        assert count == 4.0

    def test_secondary_muscle_counts_as_half(self):
        """Secondary muscle should get 0.5x credit."""
        ex = get_exercise_by_slug("barbell-bench-press")
        count = count_sets_toward_muscle(ex, "triceps", sets=4)
        assert count == 2.0

    def test_unrelated_muscle_counts_as_zero(self):
        """Muscle not in primary or secondary = 0 sets."""
        ex = get_exercise_by_slug("barbell-bench-press")
        count = count_sets_toward_muscle(ex, "quads", sets=4)
        assert count == 0.0


# === 11-set session cap tests ===

class TestSessionVolumeCap:
    def test_cap_is_11(self):
        """The per-session cap should be 11 sets per muscle."""
        assert PER_SESSION_SET_CAP == 11

    def test_cap_not_triggered_under_11(self):
        """No warning when volume is ≤11 sets."""
        session_vol = {"chest": 10, "triceps": 5}
        warnings = check_session_volume_cap(session_vol)
        assert len(warnings) == 0

    def test_cap_triggered_over_11(self):
        """Warning when volume exceeds 11 sets."""
        session_vol = {"chest": 15, "triceps": 5}
        warnings = check_session_volume_cap(session_vol)
        assert len(warnings) == 1
        assert "chest" in warnings[0]


# === Weekly volume computation tests ===

class TestWeeklyVolume:
    def test_compute_weekly_volume_counts_primary_muscles(self):
        """Weekly volume should count primary muscles at 1.0."""
        # Build a minimal workout with one bench press @ 4 sets
        ex = get_exercise_by_slug("barbell-bench-press")
        we = WorkoutExercise(exercise=ex, sets=4, reps="5-8", rest_sec=180)
        w = Workout(day_number=1, name="Test", focus="test", exercises=[we])
        vol = compute_weekly_volume_per_muscle([w])
        assert vol.get("chest", 0) >= 4

    def test_compute_weekly_volume_counts_secondary_at_half(self):
        """Secondary muscles should get 0.5x credit."""
        ex = get_exercise_by_slug("barbell-bench-press")
        we = WorkoutExercise(exercise=ex, sets=4, reps="5-8", rest_sec=180)
        w = Workout(day_number=1, name="Test", focus="test", exercises=[we])
        vol = compute_weekly_volume_per_muscle([w])
        # Triceps is secondary to bench press
        assert vol.get("triceps", 0) == 2.0


# === Volume tier tests ===

class TestVolumeTiers:
    def test_tier_set_ranges_correct(self):
        """Each tier should have the correct set range from Table 7.4."""
        assert TIER_SET_RANGES[VolumeTier.MINIMAL] == (4, 8)
        assert TIER_SET_RANGES[VolumeTier.LOW] == (9, 12)
        assert TIER_SET_RANGES[VolumeTier.MEDIUM] == (13, 16)
        assert TIER_SET_RANGES[VolumeTier.HIGH] == (17, 20)
        assert TIER_SET_RANGES[VolumeTier.VERY_HIGH] == (21, 30)

    def test_recommended_sets_for_beginner_is_lower(self):
        """Beginners should get fewer sets than advanced."""
        beginner_sets = get_recommended_weekly_sets(
            "chest", TrainingGoal.HYPERTROPHY,
            TrainingStatus.BEGINNER, VolumeTier.MEDIUM,
        )
        advanced_sets = get_recommended_weekly_sets(
            "chest", TrainingGoal.HYPERTROPHY,
            TrainingStatus.ADVANCED, VolumeTier.MEDIUM,
        )
        assert beginner_sets < advanced_sets

    def test_maintenance_reduces_volume(self):
        """Maintenance goal should reduce volume vs hypertrophy."""
        hypertrophy_sets = get_recommended_weekly_sets(
            "chest", TrainingGoal.HYPERTROPHY,
            TrainingStatus.INTERMEDIATE, VolumeTier.MEDIUM,
        )
        maintenance_sets = get_recommended_weekly_sets(
            "chest", TrainingGoal.MAINTENANCE,
            TrainingStatus.INTERMEDIATE, VolumeTier.MEDIUM,
        )
        assert maintenance_sets < hypertrophy_sets


# === Validation tests ===

class TestVolumeValidation:
    def test_below_mev_warns(self):
        """Volume below MEV should generate a warning."""
        warnings = validate_weekly_volume(
            {"chest": 2},  # well below MEV of 4
            TrainingGoal.HYPERTROPHY,
            TrainingStatus.INTERMEDIATE,
        )
        assert any("below MEV" in w for w in warnings)

    def test_above_mrv_warns(self):
        """Volume above MRV should generate a warning."""
        warnings = validate_weekly_volume(
            {"chest": 35},  # above MRV of 30
            TrainingGoal.HYPERTROPHY,
            TrainingStatus.ADVANCED,
        )
        assert any("above MRV" in w for w in warnings)

    def test_in_range_no_warnings(self):
        """Volume in the recommended range should have no warnings."""
        warnings = validate_weekly_volume(
            {"chest": 15},  # in MAV range
            TrainingGoal.HYPERTROPHY,
            TrainingStatus.INTERMEDIATE,
        )
        assert len(warnings) == 0


# === Specialization tests ===

class TestSpecialization:
    # Phase-6 cleanup: removed ``get_specialization_program`` (dead code).
    # The two tests below now exercise the underlying SPECIALIZATION_BALANCED
    # and SPECIALIZATION_FOCUS constants directly (the deleted function was a
    # constant-returning wrapper around them).
    def test_specialization_balanced_then_focus_then_balanced(self):
        """Specialization template should be balanced → focus → balanced."""
        program = [
            SPECIALIZATION_BALANCED,
            SPECIALIZATION_FOCUS,
            SPECIALIZATION_BALANCED,
        ]
        assert len(program) == 3
        assert program[0].phase == "balanced"
        assert program[1].phase == "specialization"
        assert program[2].phase == "balanced"

    def test_specialization_focus_has_higher_volume(self):
        """Focus phase should have higher volume for focus muscles."""
        focus_lo, focus_hi = SPECIALIZATION_FOCUS.focus_muscles_sets
        balanced_lo, balanced_hi = SPECIALIZATION_BALANCED.focus_muscles_sets
        assert focus_lo > balanced_lo


# === RIR / intensity model tests ===

class TestRIRModel:
    def test_intensity_tier_for_barbell_squat(self):
        """Barbell back squat should be LOWER_FREE_WEIGHT_COMPOUND."""
        ex = get_exercise_by_slug("high-bar-back-squat")
        tier = get_exercise_intensity_tier(ex)
        assert tier == ExerciseIntensityTier.LOWER_FREE_WEIGHT_COMPOUND

    def test_intensity_tier_for_bicep_curl(self):
        """Bicep curl should be ISOLATION."""
        ex = get_exercise_by_slug("standing-dumbbell-curl")
        tier = get_exercise_intensity_tier(ex)
        assert tier == ExerciseIntensityTier.ISOLATION

    def test_rir_range_for_heavy_compound(self):
        """Heavy compound (1-3 reps) should have 0-1 RIR."""
        ex = get_exercise_by_slug("high-bar-back-squat")
        rir_lo, rir_hi = get_rir_range(ex, reps_lo=1, reps_hi=3)
        assert rir_lo == 0
        assert rir_hi == 1

    def test_rir_range_for_moderate_compound(self):
        """Moderate compound (7-10 reps) should have 2-4 RIR."""
        ex = get_exercise_by_slug("high-bar-back-squat")
        rir_lo, rir_hi = get_rir_range(ex, reps_lo=7, reps_hi=10)
        assert rir_lo == 2
        assert rir_hi == 4

    def test_rir_range_for_isolation(self):
        """Isolation at 7-10 reps should have 2-4 RIR."""
        ex = get_exercise_by_slug("standing-dumbbell-curl")
        rir_lo, rir_hi = get_rir_range(ex, reps_lo=7, reps_hi=10)
        assert rir_lo == 2
        assert rir_hi == 4

    def test_rir_to_rpe_conversion(self):
        """RIR 2 → RPE 8 for reps ≤ 12."""
        assert rir_to_rpe(2, reps=8) == 8.0
        assert rir_to_rpe(0, reps=5) == 10.0
        assert rir_to_rpe(5, reps=10) == 5.0

    def test_rir_to_rpe_high_reps_not_capped(self):
        """Tier 5.65 fix: previously RPE was capped at 8 for reps > 12, which
        under-reported intensity. A 20-rep set at RIR 0 is RPE 10 (true
        failure), not RPE 8. The cap was removed."""
        # RIR 0 at 20 reps = RPE 10 (true failure, not capped to 8)
        assert rir_to_rpe(0, reps=20) == 10.0
        # RIR 1 at 15 reps = RPE 9 (not capped to 8)
        assert rir_to_rpe(1, reps=15) == 9.0
        # RIR 2 at 25 reps = RPE 8 (correct, not a cap)
        assert rir_to_rpe(2, reps=25) == 8.0

    def test_rpe_to_rir_conversion(self):
        """RPE 8 → RIR 2."""
        assert rpe_to_rir(8.0, reps=8) == 2
        assert rpe_to_rir(10.0, reps=5) == 0


# === Warm-up generator tests ===

class TestWarmupGenerator:
    def test_leq_6_rep_recipe_for_low_reps(self):
        """Target reps ≤6 should use LEQ_6_REP recipe."""
        warmup = generate_warmup_sets(target_reps=5)
        assert len(warmup) == 4  # 4 sets in LEQ recipe
        # Last set should be ~90% 1RM
        assert warmup[-1].percentage_1rm == 0.90

    def test_geq_6_rep_recipe_for_high_reps(self):
        """Target reps ≥6 should use GEQ_6_REP recipe."""
        warmup = generate_warmup_sets(target_reps=8)
        assert len(warmup) == 4
        # Last set should be ~87.5% 1RM (PAPE)
        assert warmup[-1].percentage_1rm == 0.875

    def test_optional_first_set_can_be_excluded(self):
        """The 40% 1RM first set should be excludable."""
        warmup = generate_warmup_sets(target_reps=5, include_optional=False)
        assert len(warmup) == 3  # skips the 40% set
        assert warmup[0].percentage_1rm == 0.60

    def test_warmup_for_workout_generates_per_muscle(self):
        """Warm-up should be generated for first exercise of each muscle group."""
        ex = get_exercise_by_slug("barbell-bench-press")
        we = WorkoutExercise(exercise=ex, sets=4, reps="5-8", rest_sec=180)
        w = Workout(day_number=1, name="Test", focus="test", exercises=[we])
        warmup_map = generate_warmup_for_workout(w)
        assert len(warmup_map) >= 1
        assert ex.name in warmup_map


# === Reactive deload tests ===

class TestReactiveDeload:
    def test_5_questions_exist(self):
        """The self-assessment should have exactly 5 questions."""
        assert len(REACTIVE_DELOAD_QUESTIONS) == 5

    def test_deload_not_triggered_with_0_yes(self):
        """0 Yes answers → no deload."""
        assert should_deload([False, False, False, False, False]) == False

    def test_deload_not_triggered_with_1_yes(self):
        """1 Yes answer → no deload (threshold is ≥2)."""
        assert should_deload([True, False, False, False, False]) == False

    def test_deload_triggered_with_2_yes(self):
        """2 Yes answers → deload triggered."""
        assert should_deload([True, True, False, False, False]) == True

    def test_deload_triggered_with_all_yes(self):
        """5 Yes answers → deload triggered."""
        assert should_deload([True, True, True, True, True]) == True

    # Phase-6 cleanup: removed ``test_apply_deload_reduces_volume`` and
    # ``test_apply_deload_minimum_2_sets`` — the underlying ``apply_deload``
    # function was dead code (architect uses ``apply_periodization`` with
    # ``is_deload=True``) and has been deleted from ``intensity_model.py``.


# === Strength block phase tests ===

class TestStrengthPhases:
    def test_3_strength_phases_exist(self):
        """Volume, Load, Peak phases should all be defined."""
        assert StrengthPhase.VOLUME in STRENGTH_PHASE_SPECS
        assert StrengthPhase.LOAD in STRENGTH_PHASE_SPECS
        assert StrengthPhase.PEAK in STRENGTH_PHASE_SPECS

    def test_volume_phase_duration_6_to_12_weeks(self):
        """Volume phase should be 6-12 weeks (Table 7.11)."""
        spec = STRENGTH_PHASE_SPECS[StrengthPhase.VOLUME]
        assert spec.duration_weeks == (6, 12)

    def test_load_phase_duration_4_to_8_weeks(self):
        """Load phase should be 4-8 weeks (Table 7.12)."""
        spec = STRENGTH_PHASE_SPECS[StrengthPhase.LOAD]
        assert spec.duration_weeks == (4, 8)

    def test_peak_phase_duration_2_to_4_weeks(self):
        """Peak phase should be 2-4 weeks (Table 7.13)."""
        spec = STRENGTH_PHASE_SPECS[StrengthPhase.PEAK]
        assert spec.duration_weeks == (2, 4)

    # Phase-6 cleanup: removed ``test_peak_duration_scales_with_prior`` —
    # the underlying ``get_peak_phase_duration`` function was dead code
    # (architect uses ``get_program_duration_weeks`` in periodization.py)
    # and has been deleted from ``intensity_model.py``.

    def test_volume_phase_has_high_secondary_volume(self):
        """Volume phase should have 10-20 secondary sets/wk."""
        spec = STRENGTH_PHASE_SPECS[StrengthPhase.VOLUME]
        assert spec.secondary_sets_per_week == (10, 20)

    def test_peak_phase_has_low_secondary_volume(self):
        """Peak phase should have 0-4 secondary sets/wk."""
        spec = STRENGTH_PHASE_SPECS[StrengthPhase.PEAK]
        assert spec.secondary_sets_per_week == (0, 4)

    def test_load_phase_has_backoff_sets(self):
        """Load phase should have 2 back-off sets per single."""
        spec = STRENGTH_PHASE_SPECS[StrengthPhase.LOAD]
        assert spec.backoff_sets_per_single == (2, 2)


# === Integration: exercise categorization + swap in full plan ===

class TestIntegration:
    def test_plan_exercises_can_be_swapped(self, cut_profile):
        """Every exercise in a generated plan should have swappable alternatives."""
        assessment = assess_profile(cut_profile)
        plan = propose_plan(cut_profile, assessment)
        full_gym = {
            "barbell", "dumbbell", "bodyweight", "cable", "machine",
            "kettlebell", "bands", "ez_bar", "landmine", "trap_bar",
        }
        for meso in plan.training.mesocycles:
            for micro in meso.microcycles:
                for w in micro.workouts:
                    for we in w.exercises:
                        swaps = get_swappable_exercises(
                            we.exercise, equipment_allowed=full_gym, limit=5
                        )
                        # Most compound exercises should have ≥2 swaps
                        if we.exercise.category.value == "compound_primary":
                            assert len(swaps) >= 2, (
                                f"{we.exercise.name} has only {len(swaps)} swaps"
                            )

    def test_bodyweight_user_gets_swappable_bodyweight_exercises(self):
        """Bodyweight-only user should get bodyweight swap options for every exercise."""
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=80,
            body_fat_pct=15,
            activity_level=ActivityLevel.MOSTLY_SEDENTARY,
            training_status=TrainingStatus.INTERMEDIATE,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.BODYWEIGHT_ONLY,
            diet_type=DietType.OMNIVORE,
        )
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        bodyweight_equipment = {"bodyweight", "bands"}
        for meso in plan.training.mesocycles:
            for micro in meso.microcycles:
                for w in micro.workouts:
                    for we in w.exercises:
                        swaps = get_swappable_exercises(
                            we.exercise,
                            equipment_allowed=bodyweight_equipment,
                            limit=5,
                        )
                        # Should have at least 1 bodyweight-compatible swap
                        assert len(swaps) >= 1, (
                            f"{we.exercise.name} has no bodyweight swaps"
                        )

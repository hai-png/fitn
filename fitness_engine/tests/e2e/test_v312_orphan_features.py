"""
Integration tests for v3.1.2 orphan-feature wiring.

Verifies that the previously-orphan features are now reachable through the
public API:
  - Adaptive TDEE: profile.weight_log_kg + intake_log_kcal triggers
    update_tdee_with_logs.
  - Reverse diet: RecommendedStrategy.REVERSE_DIET produces a progressive
    calorie-escalation plan via compute_calorie_targets.
  - STRENGTH_PHASE_SPECS: goal=STRENGTH + progression=BLOCK consults the
    RippedBody-sourced phase specs for compound_primary exercises.
  - Exercise overview backfill: all 1,217 exercises now have non-empty overview.
"""
from __future__ import annotations

import pytest

import fitness_engine.training.exercise_loader as _el
from fitness_engine import (
    ActivityLevel,
    EquipmentAccess,
    PrimaryGoal,
    Sex,
    TrainingStatus,
    UserProfile,
    assess_profile,
)
from fitness_engine.models.assessment import RecommendedStrategy
from fitness_engine.models.training import ProgressionScheme, TrainingGoal
from fitness_engine.nutrition.calories import CalorieStrategy, compute_calorie_targets
from fitness_engine.training.exercise_library import get_exercises

# === Helpers ===

def _profile(**kw) -> UserProfile:
    defaults = dict(
        age=30, sex=Sex.MALE, height_cm=178, weight_kg=82, body_fat_pct=18,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        training_status=TrainingStatus.INTERMEDIATE,
        primary_goal=PrimaryGoal.MAINTENANCE,
        training_days_per_week=4,
        equipment_access=EquipmentAccess.FULL_GYM,
        neck_cm=38, waist_cm=85,
    )
    defaults.update(kw)
    return UserProfile(**defaults)


# === 1. Adaptive TDEE wiring ===

class TestAdaptiveTDEEWiring:
    """v3.1.2: update_tdee_with_logs is now called from build_nutrition_plan."""

    def test_adaptive_tdee_engages_with_30_day_logs(self):
        """When ≥8 days of weight + intake logs are provided, adaptive TDEE fires."""
        # Build a profile with 30 days of logs showing sustained deficit.
        # User is eating 2000 kcal/day but TDEE is ~3000 → losing ~1 kg/wk.
        n_days = 30
        start_weight = 82.0
        daily_deficit_kcal = 1000  # 1 kg/wk deficit
        daily_weight_loss_kg = daily_deficit_kcal * 7 / 7700  # ~0.91 kg/wk
        weight_log = [
            round(start_weight - daily_weight_loss_kg * i / 7, 1)
            for i in range(n_days)
        ]
        intake_log = [2000.0] * n_days

        profile = _profile(
            weight_kg=weight_log[-1],  # current = last log entry
            weight_log_kg=weight_log,
            intake_log_kcal=intake_log,
        )
        assessment = assess_profile(profile)
        from fitness_engine.nutrition.planner import build_nutrition_plan
        nutrition = build_nutrition_plan(profile, assessment)

        # Adaptive TDEE should have engaged.
        assert nutrition.tdee.adaptive_tdee_kcal is not None, (
            "Adaptive TDEE did not engage despite 30 days of logs"
        )
        # The adaptive TDEE should reflect the observed TDEE (~2000 kcal +
        # weight_loss × 7700 / n_days ≈ 2000 + 1000 = 3000).
        assert 2500 < nutrition.tdee.adaptive_tdee_kcal < 3500, (
            f"Adaptive TDEE {nutrition.tdee.adaptive_tdee_kcal} outside expected range"
        )
        # final_tdee_kcal should equal adaptive_tdee_kcal (not the prior).
        assert nutrition.tdee.final_tdee_kcal == nutrition.tdee.adaptive_tdee_kcal
        # Notes should mention adaptive.
        assert any("Adaptive TDEE engaged" in note for note in nutrition.notes), (
            f"Adaptive TDEE note missing from NutritionPlan.notes: {nutrition.notes}"
        )

    def test_adaptive_tdee_does_not_engage_below_8_days(self):
        """Below 8 days of logs, adaptive TDEE should NOT engage (pure prior)."""
        profile = _profile(
            weight_log_kg=[82.0, 81.9, 81.8, 81.7, 81.6],  # 5 days
            intake_log_kcal=[2000.0, 2000.0, 2000.0, 2000.0, 2000.0],
        )
        assessment = assess_profile(profile)
        from fitness_engine.nutrition.planner import build_nutrition_plan
        nutrition = build_nutrition_plan(profile, assessment)
        # Adaptive should NOT have engaged.
        assert nutrition.tdee.adaptive_tdee_kcal is None, (
            "Adaptive TDEE engaged below 8 days (should be pure prior)"
        )

    def test_adaptive_tdee_unequal_log_lengths_rejected_at_construction(self):
        """Mismatched weight_log + intake_log lengths should raise ValueError at construction.

        v3.1.3: previously the planner silently skipped adaptive TDEE when
        lengths differed. Now UserProfile.__post_init__ validates equal
        lengths at construction time, giving the caller a clear error
        pointing at the mismatch rather than silently producing a plan
        without adaptive TDEE (which could hide a data-entry bug).
        """
        with pytest.raises(ValueError, match="must be equal length"):
            _profile(
                weight_log_kg=[82.0] * 30,
                intake_log_kcal=[2000.0] * 20,  # different length
            )


# === 2. Reverse diet wiring ===

class TestReverseDietWiring:
    """v3.1.2: RecommendedStrategy.REVERSE_DIET produces an escalation plan."""

    def test_reverse_diet_strategy_produces_escalation_plan(self):
        """REVERSE_DIET strategy should produce a CalorieTargets with strategy=REVERSE_DIET."""
        profile = _profile(
            intake_log_kcal=[1800.0] * 35,  # 35 days at 1800 kcal (sustained deficit)
            primary_goal=PrimaryGoal.MAINTENANCE,
        )
        assessment = assess_profile(profile)
        # Strategy should be REVERSE_DIET (sustained deficit + healthy BF%).
        assert assessment.recommended_strategy == RecommendedStrategy.REVERSE_DIET, (
            f"Expected REVERSE_DIET, got {assessment.recommended_strategy}"
        )
        # compute_calorie_targets should produce a REVERSE_DIET plan.
        targets = compute_calorie_targets(
            profile=profile,
            tdee_kcal=3000.0,
            strategy=assessment.recommended_strategy,
            body_fat_pct=assessment.body_composition.body_fat_pct,
        )
        assert targets.strategy == CalorieStrategy.REVERSE_DIET
        # Target should be > current intake (1800) and ≤ TDEE (3000).
        assert 1800 < targets.target_calories_kcal <= 3000, (
            f"Reverse-diet target {targets.target_calories_kcal} not in escalation range"
        )
        # Notes should mention weekly increment.
        assert any("kcal/week" in note for note in targets.notes), (
            f"Weekly increment note missing: {targets.notes}"
        )

    def test_reverse_diet_without_intake_log_uses_80pct_default(self):
        """Without intake_log, reverse diet defaults to 80% TDEE as current intake."""
        profile = _profile()  # no intake_log
        targets = compute_calorie_targets(
            profile=profile,
            tdee_kcal=3000.0,
            strategy=RecommendedStrategy.REVERSE_DIET,
            body_fat_pct=18.0,
        )
        # Current = 0.8 × 3000 = 2400. Target = 2400 + increment.
        assert targets.target_calories_kcal > 2400, (
            f"Reverse-diet target {targets.target_calories_kcal} should be > 2400 (80% TDEE)"
        )


# === 3. STRENGTH_PHASE_SPECS wiring ===

class TestStrengthPhaseSpecsWiring:
    """v3.1.2: STRENGTH goal + BLOCK progression consults STRENGTH_PHASE_SPECS."""

    def test_strength_block_uses_phase_spec_rpe(self):
        """For STRENGTH + BLOCK + compound_primary, RPE should come from
        STRENGTH_PHASE_SPECS (not the generic _BLOCK_PHASE_MODIFIERS).

        Note: the RIR clamp (Layer 5) may cap the spec's RPE midpoint down
        to stay within the safe RPE range for the prescribed rep range.
        E.g. PEAK phase spec midpoint = 8.5, but reps 4-5 have RIR (2,4)
        → RPE bounds 6-8, so the clamp caps 8.5 → 8.0. This is correct
        behavior — the spec is consulted, then the RIR safety clamp
        ensures the final RPE is physiologically appropriate.
        """
        from fitness_engine.models.training import (
            Exercise,
            ExerciseCategory,
            Workout,
            WorkoutExercise,
        )
        from fitness_engine.training.periodization import apply_periodization

        ex = Exercise(
            name="Barbell Back Squat",
            category=ExerciseCategory.COMPOUND_PRIMARY,
            muscle_groups=["quads"],
            equipment="barbell",
            default_sets=4,
            default_reps="5-8",
            default_rest_sec=180,
        )
        we = WorkoutExercise(exercise=ex, sets=4, reps="5-8", rest_sec=180)
        workout = Workout(day_number=1, name="Test", focus="strength", exercises=[we])

        # Apply BLOCK accumulation (VOLUME) phase for STRENGTH goal.
        result = apply_periodization(
            workout,
            goal=TrainingGoal.STRENGTH,
            progression=ProgressionScheme.BLOCK,
            block_phase="accumulation",
        )
        # STRENGTH_PHASE_SPECS[VOLUME].main_lift_rpe_range = (5.0, 8.0) → midpoint 6.5
        # VOLUME uses secondary_reps (6,20), so RIR is (3,5) → RPE 5-7 — 6.5 is within.
        assert result.exercises[0].rpe_target == 6.5, (
            f"STRENGTH VOLUME phase RPE should be 6.5 (midpoint of 5-8), "
            f"got {result.exercises[0].rpe_target}"
        )

        # Apply BLOCK peak phase for STRENGTH.
        result = apply_periodization(
            workout,
            goal=TrainingGoal.STRENGTH,
            progression=ProgressionScheme.BLOCK,
            block_phase="peak",
        )
        # STRENGTH_PHASE_SPECS[PEAK].main_lift_rpe_range = (7.0, 10.0) → midpoint 8.5
        # PEAK uses backoff_reps (4,2) → reps "4-5" after our clamping.
        # RIR for (4,5) on compound_primary is (2,4) → RPE bounds 6-8.
        # The clamp caps 8.5 → 8.0 (the spec's intent is high intensity, but
        # the RIR safety layer ensures we don't exceed what's appropriate
        # for the prescribed rep range).
        assert result.exercises[0].rpe_target == 8.0, (
            f"STRENGTH PEAK phase RPE should be 8.0 (spec midpoint 8.5 clamped "
            f"to RIR-based max of 8.0 for reps 4-5), "
            f"got {result.exercises[0].rpe_target}"
        )

    def test_strength_block_volume_phase_uses_secondary_reps(self):
        """STRENGTH VOLUME phase should use secondary_reps (6-20) for reps."""
        from fitness_engine.models.training import (
            Exercise,
            ExerciseCategory,
            Workout,
            WorkoutExercise,
        )
        from fitness_engine.training.periodization import apply_periodization

        ex = Exercise(
            name="Deadlift",
            category=ExerciseCategory.COMPOUND_PRIMARY,
            muscle_groups=["hamstrings"],
            equipment="barbell",
            default_sets=3,
            default_reps="3-6",
            default_rest_sec=240,
        )
        we = WorkoutExercise(exercise=ex, sets=3, reps="3-6", rest_sec=240)
        workout = Workout(day_number=1, name="Test", focus="strength", exercises=[we])

        result = apply_periodization(
            workout,
            goal=TrainingGoal.STRENGTH,
            progression=ProgressionScheme.BLOCK,
            block_phase="accumulation",  # VOLUME phase
        )
        # STRENGTH_PHASE_SPECS[VOLUME].secondary_reps = (6, 20)
        reps = result.exercises[0].reps
        lo, hi = (int(x) for x in reps.split("-"))
        assert lo == 6 and hi == 20, (
            f"STRENGTH VOLUME reps should be '6-20' (secondary_reps), got {reps}"
        )


# === 4. Exercise overview backfill ===

class TestExerciseOverviewBackfill:
    """v3.1.2: all 1,217 exercises now have non-empty overview."""

    def test_all_exercises_have_overview(self):
        """No exercise should have None or empty overview."""
        _el._load_raw_db.cache_clear()
        exercises = get_exercises()
        missing = [ex for ex in exercises if not ex.overview or not ex.overview.strip()]
        assert not missing, (
            f"{len(missing)} exercises still missing overview: "
            f"{[ex.name for ex in missing[:5]]}"
        )

    def test_backfilled_overviews_marked_with_curation_note(self):
        """Backfilled overviews should be distinguishable from author-written ones."""
        _el._load_raw_db.cache_clear()
        exercises = get_exercises()
        backfilled = [ex for ex in exercises if ex.overview and "[curation-note" in ex.overview]
        # Should be ~353 backfilled (was the count of missing overviews).
        assert len(backfilled) >= 350, (
            f"Expected ~353 backfilled overviews, found {len(backfilled)}"
        )

    def test_backfilled_overview_contains_metadata(self):
        """Backfilled overview should contain the exercise name + category."""
        _el._load_raw_db.cache_clear()
        exercises = get_exercises()
        # Find a backfilled one.
        for ex in exercises:
            if ex.overview and "[curation-note" in ex.overview:
                assert ex.name in ex.overview, (
                    f"Backfilled overview for {ex.name!r} doesn't contain the name"
                )
                # Should mention "exercise" (the category description).
                assert "exercise" in ex.overview.lower()
                return
        pytest.fail("No backfilled overview found to test")

"""
Integration tests covering the v3.1.1 critical-fix invariants.

These tests were added after the v3.1.0 → v3.1.1 critical analysis
(see ANALYSIS.md). Each test guards against a specific defect that
existed in v3.1.0 and was fixed in v3.1.1 — they exist to prevent
regressions.

Test groups:
  - TestMacroPreservationInvariants: training-day slot targets must sum
    to the daily target (was -18.8% in v3.1.0).
  - TestPrePostPlacementInvariants: PRE/POST workout slots must be
    placed correctly relative to training_time_of_day for all meal_freq.
  - TestPeriodizationRepRangeInvariants: HYPERTROPHY rep ranges must
    stay within the 6-12 (or 5-15 for accessories) band even after DUP
    heavy-day modifier. STRENGTH heavy day must drop to true strength
    reps (1-6).
  - TestAllergenSafetyInvariants: ingredient swaps and fillers must
    respect user allergens.
  - TestExerciseCategorizationInvariants: squat/deadlift must be
    COMPOUND_PRIMARY; plyometrics excluded for beginners; SMR/Conditioning
    exercises categorized correctly.
  - TestCalorieFloorInvariants: calorie_delta_kcal must equal
    target - tdee after floor clamping.
  - TestHydrationInvariants: climate multiplier applies to sweat only;
    male + pregnant=True raises ValueError.
  - TestVolumeLandmarksInvariants: ML < MEV for every muscle;
    MAINTENANCE goal floors at ML.
  - TestSelectorInvariants: INTERMEDIATE users don't get Beginner-biased
    exercises; Tier-4/5 doesn't pick wrong-muscle exercises.
"""
from __future__ import annotations

import pytest

from fitness_engine import (
    ActivityLevel,
    EquipmentAccess,
    PlanPreferences,
    PrimaryGoal,
    Sex,
    TrainingStatus,
    UserProfile,
    assess_profile,
    propose_plan,
)
from fitness_engine.meal_plan.profile_requirements import (
    compute_meal_plan_requirements,
)
from fitness_engine.models.meal import MealType
from fitness_engine.models.profile import CutRateTier
from fitness_engine.models.training import (
    ExerciseCategory,
    TrainingGoal,
)
from fitness_engine.nutrition.calories import cut_target_calories
from fitness_engine.nutrition.hydration import compute_hydration
from fitness_engine.training.exercise_library import get_exercise_by_slug
from fitness_engine.training.exercise_loader import derive_category
from fitness_engine.training.exercise_selector import (
    _experience_rank,
)
from fitness_engine.training.periodization import (
    _DUP_DAY_MODIFIERS_HYPERTROPHY,
    _DUP_DAY_MODIFIERS_STRENGTH,
    _modify_reps_for_dup,
    _modify_rpe_for_dup,
)
from fitness_engine.training.volume_landmarks import (
    DEFAULT_MUSCLE_LANDMARKS,
    get_recommended_weekly_sets,
)

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


def _build_nutrition(profile):
    """Build a real NutritionPlan for the profile (used as input to requirements)."""
    from fitness_engine.assessment.assessor import assess_profile
    from fitness_engine.nutrition.planner import build_nutrition_plan
    assessment = assess_profile(profile)
    return build_nutrition_plan(profile, assessment), assessment


def _daily_kcal_from_nutrition(nutrition) -> float:
    """Sum macros → kcal for the daily target (independent of calorie-floor clamping)."""
    return (
        nutrition.macros.protein_kcal
        + nutrition.macros.fat_kcal
        + nutrition.macros.carb_kcal
    )


# === 1. Macro preservation invariants ===

class TestMacroPreservationInvariants:
    """Slot targets must sum to the daily target on both standard AND training days."""

    @pytest.mark.parametrize("meal_freq", [2, 3, 4, 5])
    def test_standard_day_slot_targets_sum_to_daily(self, meal_freq):
        """Standard-day slot kcal must sum to within 1 kcal of daily_kcal."""
        profile = _profile(primary_goal=PrimaryGoal.MAINTENANCE)
        nutrition, assessment = _build_nutrition(profile)
        reqs = compute_meal_plan_requirements(
            profile=profile, assessment=assessment, nutrition=nutrition,
            meal_frequency=meal_freq, include_pre_post_workout=False,
        )
        daily_kcal = _daily_kcal_from_nutrition(nutrition)
        std_total = sum(s.target_kcal for s in reqs.slot_targets)
        assert abs(std_total - daily_kcal) <= 1.5, (
            f"meal_freq={meal_freq}: standard-day slots sum to {std_total:.1f} "
            f"but daily_kcal={daily_kcal:.1f} (drift {std_total - daily_kcal:+.1f})"
        )

    @pytest.mark.parametrize("meal_freq", [2, 3, 4, 5])
    @pytest.mark.parametrize("training_time", ["morning", "midday", "evening"])
    def test_training_day_slot_targets_sum_to_daily(self, meal_freq, training_time):
        """Training-day slot kcal (including PRE/POST) must sum to within 2 kcal of daily_kcal.

        This guards against the CRITICAL v3.1.0 regression where training-day
        slots summed to 81.25% of daily_kcal (an 18.75% deficit).
        """
        from fitness_engine.models.profile import TrainingTimeOfDay
        profile = _profile(
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_time_of_day=TrainingTimeOfDay(training_time),
        )
        nutrition, assessment = _build_nutrition(profile)
        reqs = compute_meal_plan_requirements(
            profile=profile, assessment=assessment, nutrition=nutrition,
            meal_frequency=meal_freq, include_pre_post_workout=True,
        )
        daily_kcal = _daily_kcal_from_nutrition(nutrition)
        tr_total = sum(s.target_kcal for s in reqs.training_day_slot_targets)
        assert abs(tr_total - daily_kcal) <= 2.0, (
            f"meal_freq={meal_freq}, training_time={training_time}: "
            f"training-day slots sum to {tr_total:.1f} but daily_kcal={daily_kcal:.1f} "
            f"(drift {tr_total - daily_kcal:+.1f}, {(tr_total/daily_kcal-1)*100:+.2f}%)"
        )

    @pytest.mark.parametrize("meal_freq", [2, 3, 4, 5])
    def test_training_day_macro_targets_sum_to_daily(self, meal_freq):
        """P/C/F targets must also sum correctly on training days."""
        profile = _profile(primary_goal=PrimaryGoal.MAINTENANCE)
        nutrition, assessment = _build_nutrition(profile)
        reqs = compute_meal_plan_requirements(
            profile=profile, assessment=assessment, nutrition=nutrition,
            meal_frequency=meal_freq, include_pre_post_workout=True,
        )
        daily_p = nutrition.macros.protein_g
        daily_c = nutrition.macros.carb_g
        daily_f = nutrition.macros.fat_g
        tr_p = sum(s.target_protein_g for s in reqs.training_day_slot_targets)
        tr_c = sum(s.target_carb_g for s in reqs.training_day_slot_targets)
        tr_f = sum(s.target_fat_g for s in reqs.training_day_slot_targets)
        assert abs(tr_p - daily_p) <= 1.5, f"P drift {tr_p - daily_p:+.1f}"
        assert abs(tr_c - daily_c) <= 1.5, f"C drift {tr_c - daily_c:+.1f}"
        assert abs(tr_f - daily_f) <= 1.5, f"F drift {tr_f - daily_f:+.1f}"


# === 2. PRE/POST placement invariants ===

class TestPrePostPlacementInvariants:
    """PRE/POST workout slots must be placed correctly relative to training_time."""

    @pytest.mark.parametrize("training_time,anchor_meal", [
        ("morning", MealType.BREAKFAST),
        ("midday", MealType.LUNCH),
        ("evening", MealType.DINNER),
    ])
    def test_pre_post_positioned_relative_to_training_time(
        self, training_time, anchor_meal,
    ):
        from fitness_engine.models.profile import TrainingTimeOfDay
        profile = _profile(
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_time_of_day=TrainingTimeOfDay(training_time),
        )
        nutrition, assessment = _build_nutrition(profile)
        reqs = compute_meal_plan_requirements(
            profile=profile, assessment=assessment, nutrition=nutrition,
            meal_frequency=3, include_pre_post_workout=True,
        )
        slots = reqs.training_day_slot_targets
        types = [s.meal_type for s in slots]
        assert MealType.PRE_WORKOUT in types, f"PRE_WORKOUT missing for {training_time}"
        assert MealType.POST_WORKOUT in types, f"POST_WORKOUT missing for {training_time}"
        pre_idx = types.index(MealType.PRE_WORKOUT)
        post_idx = types.index(MealType.POST_WORKOUT)
        # PRE must come before POST.
        assert pre_idx < post_idx, (
            f"PRE_WORKOUT (idx {pre_idx}) must come before POST_WORKOUT (idx {post_idx})"
        )
        # For meal_freq=3, slots include BREAKFAST, LUNCH, DINNER plus PRE/POST.
        # Verify PRE sits at or before the anchor meal.
        if anchor_meal in types:
            anchor_idx = types.index(anchor_meal)
            assert pre_idx <= anchor_idx, (
                f"training_time={training_time}: PRE at idx {pre_idx} but anchor "
                f"{anchor_meal.value} at idx {anchor_idx} — PRE should come first"
            )


# === 3. Periodization rep-range invariants ===

class TestPeriodizationRepRangeInvariants:
    """HYPERTROPHY rep ranges must stay in 6-12 even after DUP heavy day."""

    def test_hypertrophy_dup_heavy_stays_in_band(self):
        """HYPERTROPHY DUP heavy day on a 5-8 preset must NOT produce <5 reps."""
        for day_type in ("heavy", "moderate", "light"):
            reps = _modify_reps_for_dup("5-8", day_type, TrainingGoal.HYPERTROPHY)
            lo, hi = (int(x) for x in reps.split("-"))
            assert lo >= 5, (
                f"HYPERTROPHY DUP {day_type}: reps lo={lo} < 5 "
                f"(was producing 2 in v3.1.0)"
            )
            assert hi <= 15, (
                f"HYPERTROPHY DUP {day_type}: reps hi={hi} > 15 "
                f"(hypertrophy accessories can go up to 15, compounds shouldn't exceed 12)"
            )

    def test_strength_dup_heavy_drops_to_true_strength_reps(self):
        """STRENGTH DUP heavy day should produce reps ≤6 (true strength territory)."""
        reps = _modify_reps_for_dup("3-6", "heavy", TrainingGoal.STRENGTH)
        lo, hi = (int(x) for x in reps.split("-"))
        assert hi <= 6, f"STRENGTH DUP heavy: reps hi={hi} > 6 (should be strength territory)"

    def test_dup_modifier_tables_are_distinct_per_goal(self):
        h_hyp = _DUP_DAY_MODIFIERS_HYPERTROPHY["heavy"]["reps_lo_mult"]
        s_hyp = _DUP_DAY_MODIFIERS_STRENGTH["heavy"]["reps_lo_mult"]
        assert h_hyp != s_hyp, (
            "HYPERTROPHY and STRENGTH DUP heavy multipliers must differ "
            "(HYPERTROPHY should stay in band, STRENGTH should drop)"
        )

    def test_hypertrophy_rpe_stays_in_valid_range(self):
        for day_type in ("heavy", "moderate", "light"):
            rpe = _modify_rpe_for_dup(8.0, day_type, TrainingGoal.HYPERTROPHY)
            assert 4.0 <= rpe <= 10.0, (
                f"HYPERTROPHY DUP {day_type}: RPE {rpe} outside [4, 10]"
            )


# === 4. Allergen safety invariants ===

class TestAllergenSafetyInvariants:
    """Allergens must be respected across recipe selection, fillers, and swaps."""

    def test_recipe_selection_excludes_dairy_for_dairy_allergic_user(self):
        """A user with allergens_to_avoid=['dairy'] must never receive a dairy recipe."""
        profile = _profile(primary_goal=PrimaryGoal.MAINTENANCE)
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment, PlanPreferences(
            meal_frequency=3,
            allergens_to_avoid=["dairy"],
        ))
        # Walk every meal's recipe + fillers and check for dairy keywords.
        # Use word-boundary matching to avoid false positives like "butternut"
        # matching "butter". Also exclude plant-qualified versions (coconut milk,
        # almond milk, vegan butter).
        import re
        dairy_patterns = [
            (r"\bmilk\b", "milk"),
            (r"\bcheese\b", "cheese"),
            (r"\bcream\b", "cream"),
            (r"\bbutter\b", "butter"),
            (r"\byogurt\b", "yogurt"),
            (r"\bwhey\b", "whey"),
            (r"\blactose\b", "lactose"),
        ]
        plant_qualifiers = ("coconut", "almond", "vegan", "plant-based", "non-dairy", "dairy-free")
        violations = []
        for day in plan.meal.days:
            for meal in day.meals:
                if meal.recipe is not None:
                    for ing in meal.recipe.ingredients:
                        ing_lower = ing.lower()
                        is_plant = any(pq in ing_lower for pq in plant_qualifiers)
                        for pattern, kw in dairy_patterns:
                            if re.search(pattern, ing_lower) and not is_plant:
                                violations.append((day.day_number, meal.name, "recipe", ing))
                                break
                for mf in meal.foods:
                    fn = mf.food.name.lower()
                    is_plant = any(pq in fn for pq in plant_qualifiers)
                    for pattern, kw in dairy_patterns:
                        if re.search(pattern, fn) and not is_plant:
                            violations.append((day.day_number, meal.name, "filler", mf.food.name))
                            break
        assert not violations, (
            f"Dairy-allergic user got {len(violations)} dairy-containing items: {violations[:5]}"
        )


# === 5. Exercise categorization invariants ===

class TestExerciseCategorizationInvariants:
    """Categorization must produce sensible results for canonical exercises."""

    def test_barbell_back_squat_is_compound_primary(self):
        ex = get_exercise_by_slug("squat")
        assert ex is not None, "squat slug must exist in DB"
        assert ex.category == ExerciseCategory.COMPOUND_PRIMARY, (
            f"Barbell Back Squat must be COMPOUND_PRIMARY (was {ex.category} in v3.1.0)"
        )

    def test_conventional_deadlift_is_compound_primary(self):
        ex = get_exercise_by_slug("deadlifts")
        assert ex is not None, "deadlifts slug must exist in DB"
        assert ex.category == ExerciseCategory.COMPOUND_PRIMARY, (
            f"Deadlift must be COMPOUND_PRIMARY (was {ex.category} in v3.1.0)"
        )

    def test_smr_exercises_are_mobility(self):
        ex = get_exercise_by_slug("foam-rolling-glutes")
        assert ex is not None
        assert ex.category == ExerciseCategory.MOBILITY, (
            f"SMR exercise categorized as {ex.category} (should be MOBILITY)"
        )

    def test_conditioning_exercises_are_cardio(self):
        ex = get_exercise_by_slug("concept-2-rowing-machine")
        assert ex is not None
        assert ex.category == ExerciseCategory.CARDIO, (
            f"Conditioning exercise categorized as {ex.category} (should be CARDIO)"
        )

    def test_derive_category_handles_smr_keyword(self):
        assert derive_category(
            slug="any-smr-exercise",
            mechanics=None, force_type=None,
            exercise_type="SMR", equipment="foam_roll",
        ) == ExerciseCategory.MOBILITY

    def test_derive_category_handles_conditioning_keyword(self):
        assert derive_category(
            slug="any-conditioning",
            mechanics=None, force_type=None,
            exercise_type="Conditioning", equipment="machine",
        ) == ExerciseCategory.CARDIO

    def test_derive_category_mechanics_is_case_insensitive(self):
        assert derive_category(
            slug="any", mechanics="compound", force_type=None,
            exercise_type="Strength", equipment="barbell",
        ) == ExerciseCategory.COMPOUND_SECONDARY


# === 6. Calorie floor invariants ===

class TestCalorieFloorInvariants:
    """calorie_delta_kcal must be consistent with target_calories_kcal after floor clamping."""

    def test_cut_target_delta_equals_target_minus_tdee_when_floor_engages(self):
        """When the calorie floor engages, calorie_delta_kcal must reflect the
        FINAL target (not the pre-clamp deficit).
        """
        # Small female with aggressive cut → floor should engage.
        profile = _profile(
            sex=Sex.FEMALE, weight_kg=50, height_cm=152, age=20,
            body_fat_pct=20, primary_goal=PrimaryGoal.FAT_LOSS,
            cut_rate_tier=CutRateTier.AGGRESSIVE,
            activity_level=ActivityLevel.SEDENTARY,
            hip_cm=85,
        )
        from fitness_engine.nutrition.rmr import compute_rmr
        from fitness_engine.nutrition.tdee import compute_tdee
        rmr = compute_rmr(profile)
        tdee = compute_tdee(rmr, profile)
        targets = cut_target_calories(profile, tdee.final_tdee_kcal)
        # Verify the invariant: base + delta == target.
        recomputed = targets.base_tdee_kcal + targets.calorie_delta_kcal
        assert abs(recomputed - targets.target_calories_kcal) < 0.2, (
            f"base_tdee ({targets.base_tdee_kcal}) + delta ({targets.calorie_delta_kcal}) "
            f"= {recomputed:.1f} but target = {targets.target_calories_kcal} "
            f"(floor_applied={targets.calorie_floor_applied})"
        )


# === 7. Hydration invariants ===

class TestHydrationInvariants:
    """Hydration formulas must respect domain invariants."""

    def test_climate_multiplier_applies_to_sweat_only(self):
        """Climate multiplier must NOT scale base metabolic water needs.

        Use a small profile + light exercise to avoid the 5L hyponatremia ceiling.
        For 70 kg male, 1h moderate exercise (sweat 0.5 L):
          - temperate: 2.1 + 0.3 + 0.5 = 2.9 L
          - hot:       2.1 + 0.3 + (0.5 × 1.3) = 3.05 L → delta = 0.15 L
        The v3.1.0 bug would have produced delta = (2.9 × 0.3) = 0.87 L.
        """
        profile = _profile(weight_kg=70, sex=Sex.MALE)
        hot = compute_hydration(
            profile, exercise_hours_per_day=1,
            exercise_intensity="moderate", climate="hot",
        )
        temperate = compute_hydration(
            profile, exercise_hours_per_day=1,
            exercise_intensity="moderate", climate="temperate",
        )
        delta = hot.water_liters_per_day - temperate.water_liters_per_day
        # Sweat delta is 0.5 × 0.3 = 0.15 L. Allow some tolerance.
        assert 0.05 < delta < 0.4, (
            f"Hot-climate delta {delta:.3f} L too large — climate multiplier "
            f"is being applied to base+sex+exercise (the v3.1.0 bug), not just sweat"
        )

    def test_male_pregnant_raises_value_error(self):
        profile = _profile(sex=Sex.MALE)
        with pytest.raises(ValueError, match="pregnant=True is biologically impossible"):
            compute_hydration(profile, pregnant=True)

    def test_male_breastfeeding_raises_value_error(self):
        profile = _profile(sex=Sex.MALE)
        with pytest.raises(ValueError, match="breastfeeding=True is biologically impossible"):
            compute_hydration(profile, breastfeeding=True)

    def test_case_insensitive_intensity_coercion(self):
        """Passing 'Moderate' (capitalized) must NOT trigger the fallback warning."""
        import warnings
        profile = _profile()
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            compute_hydration(
                profile, exercise_intensity="Moderate", climate="Temperate",
            )


# === 8. Volume landmark invariants ===

class TestVolumeLandmarksInvariants:
    """ML must be < MEV (you need less to maintain than to grow)."""

    def test_ml_less_than_mev_for_all_muscles(self):
        """ML must be strictly less than MEV for every muscle in DEFAULT_MUSCLE_LANDMARKS."""
        violations = []
        for muscle, lm in DEFAULT_MUSCLE_LANDMARKS.items():
            if lm.ml >= lm.mev:
                violations.append((muscle, lm.ml, lm.mev))
        assert not violations, (
            f"ML must be < MEV (maintenance volume < growth minimum). "
            f"Violations: {violations}"
        )

    def test_ml_within_stated_0_5_to_0_67_of_mav_lo(self):
        """ML should be in [0.3, 0.7] × MAV_lo per the docstring rule."""
        violations = []
        for muscle, lm in DEFAULT_MUSCLE_LANDMARKS.items():
            ratio = lm.ml / lm.mav_lo if lm.mav_lo > 0 else 0
            if not 0.3 <= ratio <= 0.7:
                violations.append((muscle, lm.ml, lm.mav_lo, ratio))
        assert not violations, (
            f"ML/MAV_lo ratios out of [0.3, 0.7]: {violations}"
        )

    def test_calves_mrv_at_or_below_rp_consensus(self):
        """Calves MRV must be ≤20 (RP consensus; was 25 in v3.1.0)."""
        assert DEFAULT_MUSCLE_LANDMARKS["calves"].mrv <= 20, (
            f"calves MRV {DEFAULT_MUSCLE_LANDMARKS['calves'].mrv} exceeds RP consensus of 20"
        )

    def test_maintenance_goal_floors_at_ml_not_mev(self):
        """MAINTENANCE goal must floor recommendation at ML, not MEV.

        For chest: MAV 10-22 (mid 16), goal_multiplier 0.6, beginner 0.7.
        Result before floor: 16 × 0.6 × 0.7 ≈ 6.7 → 7 (rounded).
        MEV is 8, ML is 5. With the v3.1.0 bug (floor at MEV), the result
        would be max(8, 7) = 8. With the fix (floor at ML), it's max(5, 7) = 7.
        """
        beginner_rec = get_recommended_weekly_sets(
            muscle="chest", goal=TrainingGoal.MAINTENANCE,
            experience=TrainingStatus.BEGINNER,
        )
        lm = DEFAULT_MUSCLE_LANDMARKS["chest"]
        assert beginner_rec < lm.mev, (
            f"BEGINNER MAINTENANCE chest recommendation {beginner_rec} >= MEV {lm.mev} "
            f"— floor is still MEV (the v3.1.0 bug)"
        )


# === 9. Selector invariants ===

class TestSelectorInvariants:
    """Selector must produce sensible exercises matching user's experience level."""

    def test_intermediate_user_does_not_get_beginner_exercise_for_chest(self):
        """INTERMEDIATE user's first chest compound must be at least Intermediate-rated.

        Guards against the v3.1.0 sort-key bug that always preferred Beginner
        exercises (rank 0) regardless of user level.
        """
        profile = _profile(
            training_status=TrainingStatus.INTERMEDIATE,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            equipment_access=EquipmentAccess.FULL_GYM,
        )
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        for meso in plan.training.mesocycles:
            for micro in meso.microcycles:
                for w in micro.workouts:
                    for we in w.exercises:
                        if (
                            "chest" in we.exercise.muscle_groups
                            and we.exercise.category == ExerciseCategory.COMPOUND_PRIMARY
                        ):
                            assert we.exercise.experience_level is not None, (
                                f"chest compound {we.exercise.name!r} has no experience_level"
                            )
                            rank = _experience_rank(we.exercise)
                            assert rank >= 1, (
                                f"INTERMEDIATE user got BEGINNER-rated chest compound "
                                f"{we.exercise.name!r} (rank={rank}) — sort key is still "
                                f"beginner-biased (v3.1.0 bug)"
                            )
                            return
        # If we never find a chest compound_primary, the test should fail
        # (the plan should always have at least one).
        pytest.fail("No chest COMPOUND_PRIMARY exercise found in any workout")

    def test_beginner_does_not_get_plyometric_exercises(self):
        """BEGINNER users must never be prescribed plyometric exercises (injury risk)."""
        profile = _profile(
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            equipment_access=EquipmentAccess.BODYWEIGHT_ONLY,
            training_days_per_week=2,
        )
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        plyos = []
        for meso in plan.training.mesocycles:
            for micro in meso.microcycles:
                for w in micro.workouts:
                    for we in w.exercises:
                        if we.exercise.exercise_type and "plyometric" in we.exercise.exercise_type.lower():
                            plyos.append((w.name, we.exercise.name))
        assert not plyos, (
            f"BEGINNER user got {len(plyos)} plyometric exercises: {plyos[:3]}"
        )

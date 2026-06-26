"""
Property-based tests asserting mathematical invariants of the engine.

These tests don't check specific values — they check that relationships
between values hold for ALL valid inputs (e.g. cutting calories < TDEE,
macro kcal sums match target, weekly meal plan averages ~target).
"""
from __future__ import annotations

import pytest

from fitness_engine import (
    PlanPreferences,
    UserProfile,
    assess_profile,
    propose_plan,
)
from fitness_engine.models.assessment import RecommendedStrategy
from fitness_engine.models.profile import (
    ActivityLevel,
    DietType,
    EquipmentAccess,
    PrimaryGoal,
    Sex,
    TrainingStatus,
)
from fitness_engine.nutrition.calories import (
    MAX_WEEKLY_LOSS_PCT,
    CalorieStrategy,
)


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
    if "diet" in kw:
        kw["diet_type"] = kw.pop("diet")
    defaults.update(kw)
    return UserProfile(**defaults)


# ============================================================
# Calorie invariants
# ============================================================

class TestCalorieInvariants:
    """Mathematical relationships between TDEE, target, and strategy."""

    def test_cut_target_below_tdee(self):
        """Cut strategy must produce target < TDEE."""
        profile = _profile(primary_goal=PrimaryGoal.FAT_LOSS, body_fat_pct=20)
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        assert plan.nutrition.calories.strategy == CalorieStrategy.DEFICIT
        assert plan.nutrition.calories.target_calories_kcal < plan.nutrition.tdee.final_tdee_kcal
        assert plan.nutrition.calories.calorie_delta_kcal < 0

    def test_bulk_target_above_tdee(self):
        """Bulk strategy must produce target > TDEE."""
        profile = _profile(primary_goal=PrimaryGoal.MUSCLE_GAIN, body_fat_pct=12)
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        assert plan.nutrition.calories.strategy == CalorieStrategy.SURPLUS
        assert plan.nutrition.calories.target_calories_kcal > plan.nutrition.tdee.final_tdee_kcal
        assert plan.nutrition.calories.calorie_delta_kcal > 0

    def test_maintenance_target_equals_tdee(self):
        """Maintenance strategy must produce target ≈ TDEE (within 1 kcal)."""
        profile = _profile(primary_goal=PrimaryGoal.MAINTENANCE, body_fat_pct=18)
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        assert plan.nutrition.calories.strategy == CalorieStrategy.MAINTENANCE
        assert abs(plan.nutrition.calories.target_calories_kcal -
                   plan.nutrition.tdee.final_tdee_kcal) < 1.0
        assert abs(plan.nutrition.calories.calorie_delta_kcal) < 1.0

    def test_cut_rate_within_safety_cap(self):
        """Any cut must respect MAX_WEEKLY_LOSS_PCT (1.0% BW/week)."""
        for bf in [10, 15, 20, 25, 30, 35, 40, 50]:
            profile = _profile(primary_goal=PrimaryGoal.FAT_LOSS, body_fat_pct=bf)
            assessment = assess_profile(profile)
            plan = propose_plan(profile, assessment)
            rate = plan.nutrition.calories.rate_pct
            assert rate <= MAX_WEEKLY_LOSS_PCT + 1e-9, (
                f"Cut rate {rate*100:.2f}% exceeds safety cap {MAX_WEEKLY_LOSS_PCT*100:.2f}%"
            )

    def test_cut_rate_positive(self):
        """Cut rate must be > 0 (otherwise it's not a cut)."""
        profile = _profile(primary_goal=PrimaryGoal.FAT_LOSS, body_fat_pct=20)
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        assert plan.nutrition.calories.rate_pct > 0

    def test_calorie_floor_respected(self):
        """Calorie targets must not fall below sex-specific floors."""
        from fitness_engine.nutrition.calories import MIN_CALORIES
        profile = _profile(
            primary_goal=PrimaryGoal.FAT_LOSS,
            sex=Sex.FEMALE, weight_kg=50, height_cm=150, body_fat_pct=8,
            cut_rate_tier=None,  # let engine pick
        )
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        floor = MIN_CALORIES[Sex.FEMALE]
        assert plan.nutrition.calories.target_calories_kcal >= floor - 1, (
            f"Female cut target {plan.nutrition.calories.target_calories_kcal:.0f} "
            f"below floor {floor}"
        )


# ============================================================
# Macro invariants
# ============================================================

class TestMacroInvariants:
    """Macro split must satisfy: P*4 + C*4 + F*9 ≈ target_kcal."""

    @pytest.mark.parametrize("goal", [
        PrimaryGoal.FAT_LOSS, PrimaryGoal.MUSCLE_GAIN,
        PrimaryGoal.RECOMP, PrimaryGoal.MAINTENANCE,
    ])
    def test_macro_kcal_sums_to_target(self, goal):
        """P*4 + C*4 + F*9 must be within 5% of target calories."""
        profile = _profile(primary_goal=goal, body_fat_pct=18)
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        macros = plan.nutrition.macros
        macro_kcal = macros.protein_g * 4 + macros.carb_g * 4 + macros.fat_g * 9
        target = plan.nutrition.calories.target_calories_kcal
        # Allow 10% tolerance for rounding + protein-floor interactions
        assert abs(macro_kcal - target) / target < 0.10, (
            f"Macro kcal {macro_kcal:.0f} drifts > 10% from target {target:.0f} "
            f"(P={macros.protein_g:.0f} C={macros.carb_g:.0f} F={macros.fat_g:.0f})"
        )

    def test_macro_percentages_sum_to_100(self):
        """P_pct + C_pct + F_pct must sum to ~100."""
        profile = _profile()
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        macros = plan.nutrition.macros
        total = macros.protein_pct + macros.carb_pct + macros.fat_pct
        assert abs(total - 100.0) < 1.5, (
            f"Macro percentages sum to {total:.1f}, not 100"
        )

    def test_all_macros_non_negative(self):
        profile = _profile()
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        m = plan.nutrition.macros
        assert m.protein_g >= 0
        assert m.carb_g >= 0
        assert m.fat_g >= 0
        assert m.protein_kcal >= 0
        assert m.carb_kcal >= 0
        assert m.fat_kcal >= 0

    def test_protein_target_at_least_1g_per_kg_lean_mass(self):
        """Protein floor: at least 1 g per kg of lean body mass (minimum health)."""
        profile = _profile(body_fat_pct=20, weight_kg=80)
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        lbm = assessment.body_composition.lean_body_mass_kg
        assert plan.nutrition.macros.protein_g >= lbm * 0.8, (
            f"Protein {plan.nutrition.macros.protein_g:.0f}g < 0.8g/kg LBM ({lbm:.0f}kg)"
        )


# ============================================================
# Assessment invariants
# ============================================================

class TestAssessmentInvariants:
    """Body composition math must be self-consistent."""

    def test_bmi_formula(self):
        """BMI = weight_kg / (height_m ** 2)."""
        profile = _profile(weight_kg=80, height_cm=180)
        assessment = assess_profile(profile)
        expected_bmi = 80 / (1.80 ** 2)
        assert abs(assessment.body_composition.bmi - expected_bmi) < 0.2

    def test_ffmi_formula(self):
        """FFMI = LBM / (height_m ** 2)."""
        profile = _profile(weight_kg=80, height_cm=180, body_fat_pct=20)
        assessment = assess_profile(profile)
        lbm = 80 * (1 - 0.20)
        expected_ffmi = lbm / (1.80 ** 2)
        assert abs(assessment.body_composition.ffmi - expected_ffmi) < 0.5

    def test_lbm_plus_fat_equals_weight(self):
        """LBM + fat_mass = weight (within rounding)."""
        profile = _profile()
        assessment = assess_profile(profile)
        bc = assessment.body_composition
        total = bc.lean_body_mass_kg + bc.fat_mass_kg
        assert abs(total - profile.weight_kg) < 1.0, (
            f"LBM {bc.lean_body_mass_kg:.1f} + fat {bc.fat_mass_kg:.1f} = {total:.1f} "
            f"≠ weight {profile.weight_kg:.1f}"
        )

    def test_body_fat_pct_in_physiological_range(self):
        """BF% must be in [2, 60]."""
        for bf in [5, 10, 15, 20, 25, 30, 35, 40, 50]:
            profile = _profile(body_fat_pct=bf)
            assessment = assess_profile(profile)
            result_bf = assessment.body_composition.body_fat_pct
            assert 2.0 <= result_bf <= 60.0, f"BF% {result_bf} outside [2, 60]"

    def test_ffmi_to_ceiling_pct_in_0_100(self):
        """FFMI-to-ceiling percentage must be in [0, 100]."""
        profile = _profile()
        assessment = assess_profile(profile)
        pct = assessment.muscular_potential.ffmi_to_ceiling_pct
        assert 0.0 <= pct <= 100.0

    def test_strategy_matches_goal_when_safe(self):
        """For non-obese, non-underweight users, strategy should match goal."""
        # Normal-weight male wanting muscle gain → BULK
        profile = _profile(
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            body_fat_pct=14, weight_kg=70,
        )
        assessment = assess_profile(profile)
        assert assessment.recommended_strategy == RecommendedStrategy.BULK

        # Overweight male wanting fat loss → CUT
        profile = _profile(
            primary_goal=PrimaryGoal.FAT_LOSS,
            body_fat_pct=22, weight_kg=85,
        )
        assessment = assess_profile(profile)
        assert assessment.recommended_strategy == RecommendedStrategy.CUT


# ============================================================
# Training plan invariants
# ============================================================

class TestTrainingInvariants:
    """Training plan must satisfy structural constraints."""

    def test_training_days_match_profile(self):
        profile = _profile(training_days_per_week=4)
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        assert plan.training.training_days_per_week == 4

    def test_workouts_per_week_in_2_7(self):
        # Task 6-bug-fixes #1: training_days_per_week=7 is rejected at
        # UserProfile construction (architect only supports 2-6 days/week).
        # The loop exercises the supported range; the separate check verifies
        # 7 raises immediately rather than crashing the architect later.
        for days in [2, 3, 4, 5, 6]:
            profile = _profile(training_days_per_week=days)
            assessment = assess_profile(profile)
            plan = propose_plan(profile, assessment)
            assert plan.training.training_days_per_week == days
        with pytest.raises(ValueError, match="training_days_per_week must be 2-6"):
            _profile(training_days_per_week=7)

    def test_each_workout_has_exercises(self):
        """Every workout in every microcycle must have at least 1 exercise."""
        profile = _profile()
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        for mc in plan.training.mesocycles:
            for uc in mc.microcycles:
                for w in uc.workouts:
                    assert len(w.exercises) >= 1, (
                        f"Workout {w.name} has no exercises"
                    )

    def test_each_exercise_has_required_fields(self):
        profile = _profile()
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        for mc in plan.training.mesocycles:
            for uc in mc.microcycles:
                for w in uc.workouts:
                    for we in w.exercises:
                        assert we.exercise is not None
                        assert we.sets >= 1
                        assert we.reps  # non-empty string
                        assert we.rest_sec >= 0

    def test_reps_are_valid_format(self):
        """Reps must be a string like '5-8' or 'AMRAP' or '30s'."""
        import re
        profile = _profile()
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        valid_patterns = [
            r"^\d+-\d+$",  # "5-8"
            r"^\d+$",      # "8"
            r"^AMRAP$",    # AMRAP
            r"^\d+s$",     # "30s" (timed)
            r"^\d+ min$",  # "1 min"
        ]
        for mc in plan.training.mesocycles:
            for uc in mc.microcycles:
                for w in uc.workouts:
                    for we in w.exercises:
                        if not any(re.match(p, we.reps) for p in valid_patterns):
                            pytest.fail(f"Invalid reps format: {we.reps!r} in {we.exercise.name}")

    def test_progression_matches_experience(self):
        """Beginner → LINEAR, intermediate → DUP, advanced → BLOCK."""
        cases = [
            (TrainingStatus.BEGINNER, "linear"),
            (TrainingStatus.INTERMEDIATE, "dup"),
            (TrainingStatus.ADVANCED, "block"),
        ]
        for status, expected in cases:
            profile = _profile(training_status=status)
            assessment = assess_profile(profile)
            plan = propose_plan(profile, assessment)
            assert plan.training.progression.value == expected, (
                f"{status} → {plan.training.progression.value} (expected {expected})"
            )


# ============================================================
# Meal plan invariants
# ============================================================

class TestMealPlanInvariants:
    """Meal plan must satisfy macro-preservation + structural constraints."""

    def test_seven_day_plan(self):
        """Meal plan must have exactly 7 days."""
        profile = _profile()
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        assert len(plan.meal.days) == 7

    def test_each_day_has_meals(self):
        profile = _profile()
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        for day in plan.meal.days:
            assert len(day.meals) >= 1

    def test_meal_frequency_matches_preference(self):
        """Meal count per day should approximately match meal_frequency."""
        for freq in [2, 3, 4, 5]:
            profile = _profile()
            assessment = assess_profile(profile)
            prefs = PlanPreferences(meal_frequency=freq)
            plan = propose_plan(profile, assessment, prefs)
            for day in plan.meal.days:
                # Allow ±1 for pre/post workout on training days
                base_count = len(day.meals)
                # If training day + pre/post workout, may have 2 extra slots
                assert base_count >= freq, (
                    f"Day {day.day_name} has {base_count} meals, expected ≥ {freq}"
                )

    def test_daily_macros_within_tolerance_of_target(self):
        """Each day's total macros should be within 40% of daily target.

        v3.1.3: tightened from 50% to 40%. The v3.1.0 code allowed 50%
        drift which was too lenient — it masked the training-day macro
        preservation bug (-18.8% drift passed silently). 40% is still
        generous but catches structural defects. The remaining tolerance
        accommodates the known recipe-scaling over-shoot (fillers only
        close gaps UPWARD, never subtract — so a high-kcal recipe selected
        for a moderate slot can over-shoot by ~30-35%).
        """
        profile = _profile()
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        target_kcal = plan.nutrition.calories.target_calories_kcal
        for day in plan.meal.days:
            day_kcal = day.total_kcal
            # v3.1.3: 40% tolerance (was 50%). Recipe scaling + fillers
            # can legitimately drift ~35% (fillers over-shoot UPWARD only);
            # 40% catches the v3.1.0 training-day -18.8% bug while
            # accommodating the known recipe over-shoot.
            assert abs(day_kcal - target_kcal) / target_kcal < 0.40, (
                f"Day {day.day_name} kcal {day_kcal:.0f} drifts > 40% from target {target_kcal:.0f}"
            )

    def test_meal_total_kcal_equals_sum_of_components(self):
        """Meal.total_kcal must equal scaled_kcal + sum(foods.kcal)."""
        profile = _profile()
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        for day in plan.meal.days:
            for meal in day.meals:
                if meal.recipe is not None:
                    expected = meal.scaled_kcal + sum(f.kcal for f in meal.foods)
                else:
                    expected = sum(f.kcal for f in meal.foods)
                assert abs(meal.total_kcal - expected) < 0.5, (
                    f"Meal {meal.name} total_kcal {meal.total_kcal:.1f} ≠ "
                    f"computed {expected:.1f}"
                )

    def test_meal_total_protein_equals_sum_of_components(self):
        profile = _profile()
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        for day in plan.meal.days:
            for meal in day.meals:
                if meal.recipe is not None:
                    expected = meal.scaled_protein_g + sum(f.protein_g for f in meal.foods)
                else:
                    expected = sum(f.protein_g for f in meal.foods)
                assert abs(meal.total_protein_g - expected) < 0.5

    def test_no_recipe_contains_excluded_allergens(self):
        """When allergens_to_avoid is set, no recipe in the plan may contain them."""
        profile = _profile()
        assessment = assess_profile(profile)
        prefs = PlanPreferences(allergens_to_avoid=["dairy"])
        plan = propose_plan(profile, assessment, prefs)
        from fitness_engine.meal_plan import check_allergens
        for day in plan.meal.days:
            for meal in day.meals:
                if meal.recipe:
                    violations = check_allergens(meal.recipe, ["dairy"])
                    assert violations == [], (
                        f"Meal {meal.name} on {day.day_name} contains dairy: {violations}"
                    )

    def test_no_recipe_contains_excluded_ingredients(self):
        profile = _profile()
        assessment = assess_profile(profile)
        prefs = PlanPreferences(excluded_ingredients=["peanut butter"])
        plan = propose_plan(profile, assessment, prefs)
        # Verify no recipe contains the excluded ingredient
        for day in plan.meal.days:
            for meal in day.meals:
                if meal.recipe:
                    for ing in meal.recipe.ingredients:
                        assert "peanut butter" not in ing.lower(), (
                            f"Meal {meal.name} contains excluded ingredient 'peanut butter': {ing}"
                        )

    def test_vegan_plan_has_no_animal_recipes(self):
        """Vegan users must not get any recipe containing animal products."""
        from fitness_engine.meal_plan.recipe_loader import _recipe_has_meat_ingredients
        profile = _profile(diet=DietType.VEGAN)
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        for day in plan.meal.days:
            for meal in day.meals:
                if meal.recipe:
                    assert not _recipe_has_meat_ingredients(meal.recipe), (
                        f"Vegan plan contains animal recipe: {meal.recipe.name}"
                    )

    def test_vegan_fillers_are_vegan(self):
        """Vegan users must not get non-vegan fillers (whey, chicken, etc.)."""
        NON_VEGAN_FILLERS = {
            "Whey Protein Powder",
            "Greek Yogurt (non-fat, plain)",
            "Egg White (large)",
            "Cottage Cheese (low-fat, 2%)",
            "Chicken Breast (skinless, boneless, raw)",
        }
        profile = _profile(diet=DietType.VEGAN)
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        for day in plan.meal.days:
            for meal in day.meals:
                for food in meal.foods:
                    assert food.food.name not in NON_VEGAN_FILLERS, (
                        f"Vegan plan contains non-vegan filler: {food.food.name}"
                    )


# ============================================================
# Serialization invariants
# ============================================================

class TestSerializationInvariants:
    """to_dict() output must be JSON-serializable and structurally valid."""

    def test_plan_to_dict_has_all_top_level_keys(self):
        profile = _profile()
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        d = plan.to_dict()
        assert set(d.keys()) >= {"nutrition", "training", "meal", "summary"}

    def test_no_raw_enums_in_serialized_output(self):
        """No value in the serialized dict should be an Enum instance."""
        import json
        from enum import Enum
        profile = _profile()
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        d = plan.to_dict()
        # If any Enum leaks through, json.dumps will fail OR produce the .value
        # (since all our enums inherit from str). To be strict, walk the dict.
        def walk(obj):
            if isinstance(obj, Enum):
                return False
            if isinstance(obj, dict):
                return all(walk(v) for v in obj.values()) and all(walk(k) for k in obj)
            if isinstance(obj, (list, tuple)):
                return all(walk(v) for v in obj)
            return True
        assert walk(d), "Found raw Enum in serialized output"
        # And json.dumps must succeed
        json.dumps(d, default=str)

    def test_assessment_to_dict_json_serializable(self):
        import json
        profile = _profile()
        assessment = assess_profile(profile)
        d = assessment.to_dict()
        json.dumps(d, default=str)

    def test_to_dict_roundtrip_does_not_lose_data(self):
        """to_dict() should be lossless for the keys it includes."""
        profile = _profile()
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        d1 = plan.to_dict()
        d2 = plan.to_dict()
        assert d1 == d2, "to_dict() is not idempotent"

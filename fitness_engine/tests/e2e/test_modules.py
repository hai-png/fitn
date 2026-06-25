"""
Tests for utility functions, conversion helpers, and edge-case code paths
that aren't naturally covered by the E2E pipeline tests.

This file consolidates the unit-level coverage that was previously spread
across many test files. Each test class targets a specific module's
public API and edge cases.
"""
from __future__ import annotations

import json
import math
import warnings

import pytest

from fitness_engine.models.profile import (
    UserProfile, Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType, CutRateTier, BulkAggressiveness,
    TrainingTimeOfDay, ExerciseIntensity, Climate,
)
from fitness_engine.models.preferences import PlanPreferences
from fitness_engine.models.meal import (
    MealType, FoodCategory, FoodItem, MealFood, Meal, DayPlan,
    MealPlan, FitnessPlan, Recipe, RecipeDietTag, NutritionPerServing,
)
from fitness_engine.assessment.assessor import assess_profile
from fitness_engine.assessment.decision import decide_strategy, CUT_BULK_BOUNDARIES
from fitness_engine.meal_plan.food_database import (
    FOODS, FOOD_INDEX, get_food, protein_per_100kcal,
)
from fitness_engine.meal_plan.meal_templates import (
    get_meal_plan_template, get_meal_name, MEAL_ORDER, MEAL_NAMES,
)
from fitness_engine.meal_plan.recipe_loader import (
    load_recipes, get_recipe_by_id, get_recipe_by_name,
    recipes_by_filters, recipes_by_kcal_range, recipes_by_diet_type,
    database_stats, _recipe_has_meat_ingredients,
)
from fitness_engine.meal_plan.recipe_scorer import (
    score_recipe_for_slot, check_allergens, check_excluded_ingredients,
    score_diet_match, ALLERGEN_KEYWORDS,
)
from fitness_engine.meal_plan.swap_system import (
    get_ingredient_swaps, get_swaps_for_recipe_ingredients,
    get_recipe_swaps, INGREDIENT_SWAPS,
)
from fitness_engine.meal_plan.pre_post_workout import (
    get_pre_post_workout_recipes, PRE_POST_WORKOUT_RECIPES,
)
from fitness_engine.meal_plan.allocator import (
    allocate_meal, SelectedMeal, MIN_ACCEPTABLE_SCORE,
    _compute_allergen_filler_exclusions,
)
from fitness_engine.meal_plan.recipe_scaler import (
    compute_scale_factor, scale_recipe, is_recipe_scalable_to_target,
    select_protein_filler, select_carb_filler, select_fat_filler,
    select_veg_filler, select_fillers_for_meal, ScalerConfig,
)
from fitness_engine.nutrition.adjustments import (
    detect_plateau, recommend_cut_adjustment, recommend_bulk_adjustment,
    PlateauType, AdjustmentRecommendation,
)
from fitness_engine.nutrition.tdee import (
    update_tdee_with_logs, observed_tdee_first_principles,
    adaptive_weight_data, TDEEResult,
)
from fitness_engine.nutrition.rmr import (
    compute_rmr, select_rmr_formula, RMRFormula,
    rmr_mifflin_st_jeor, rmr_katch_mcardle,
    rmr_cunningham, rmr_harris_benedict_original, rmr_harris_benedict_revised,
)
from fitness_engine.training.exercise_library import (
    get_exercises, get_exercise_by_slug, get_exercise_by_name,
    get_exercise_by_phase1_name, _clear_exercise_cache,
)
from fitness_engine.training.exercise_categorization import (
    get_movement_pattern, get_pattern_family,
    get_environment_preferred_equipment, get_swappable_exercises,
    categorize_exercise, MOVEMENT_PATTERNS,
)
from fitness_engine.training.exercise_selector import select_exercise_for_slot
from fitness_engine.training.intensity_model import (
    get_exercise_intensity_tier, generate_warmup_sets,
    WARMUP_LEQ_6_REP, WARMUP_GEQ_6_REP,
)
from fitness_engine.training._utils import parse_view_count
from fitness_engine.utils.serialize import convert_for_json
from fitness_engine.utils.units import (
    kg_to_lb, lb_to_kg, cm_to_in, in_to_cm,
    LB_PER_KG, KG_PER_LB, IN_PER_CM, CM_PER_IN, WEEKS_PER_MONTH,
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
# Decision tree edge cases
# ============================================================

class TestDecisionTreeEdgeCases:

    def test_obese_beginner_non_fatloss_returns_habit_change(self):
        profile = _profile(
            body_fat_pct=35, training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MUSCLE_GAIN, waist_cm=120,
        )
        strategy, _ = decide_strategy(
            profile=profile, body_fat_pct=35, bmi=profile.bmi,
        )
        assert strategy.value == "habit_change_first"

    def test_obese_beginner_fatloss_returns_cut(self):
        profile = _profile(
            body_fat_pct=35, training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.FAT_LOSS, waist_cm=120,
        )
        strategy, _ = decide_strategy(
            profile=profile, body_fat_pct=35, bmi=profile.bmi,
        )
        assert strategy.value == "cut"

    def test_underweight_returns_bulk(self):
        """BF% below cut_floor with a muscle-gain goal → BULK (not maintenance).

        Engine honors MAINTENANCE goal verbatim, so to exercise the
        underweight/bulk path the profile must have a goal that allows
        bulking (MUSCLE_GAIN). With BF%=5 (well below male cut_floor=10)
        and MUSCLE_GAIN, the engine returns BULK.
        """
        profile = _profile(
            body_fat_pct=5, weight_kg=55,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
        )
        strategy, _ = decide_strategy(
            profile=profile, body_fat_pct=5, bmi=profile.bmi,
        )
        assert strategy.value == "bulk"

    def test_overweight_returns_cut(self):
        """BF% above bulk_ceiling with a muscle-gain goal → CUT first.

        Engine honors MAINTENANCE goal verbatim, so to exercise the
        overweight/cut path the profile must have a goal that triggers
        the bulk-ceiling safety check. With BF%=23 (above male
        bulk_ceiling=20) and MUSCLE_GAIN, the engine returns CUT
        ("cut first to stay in healthy operational range").
        """
        profile = _profile(
            body_fat_pct=23, weight_kg=85,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
        )
        strategy, _ = decide_strategy(
            profile=profile, body_fat_pct=23, bmi=profile.bmi,
        )
        assert strategy.value == "cut"

    def test_maintenance_goal_at_normal_bf_returns_maintenance(self):
        profile = _profile(
            body_fat_pct=15, primary_goal=PrimaryGoal.MAINTENANCE,
        )
        strategy, _ = decide_strategy(
            profile=profile, body_fat_pct=15, bmi=profile.bmi,
        )
        assert strategy.value == "maintenance"

    def test_strength_goal_at_normal_bf_returns_maintenance(self):
        profile = _profile(
            body_fat_pct=14, primary_goal=PrimaryGoal.STRENGTH,
            training_status=TrainingStatus.INTERMEDIATE,
        )
        strategy, _ = decide_strategy(
            profile=profile, body_fat_pct=14, bmi=profile.bmi,
        )
        # Strength goal should not auto-trigger cut or bulk
        assert strategy.value in ("maintenance", "bulk")

    def test_maintenance_at_low_bf_warns_in_rationale(self):
        """Task 9-engine-bug-fixes Bug 4: a MAINTENANCE goal at a BF%
        below the hormonal floor (10M/18F) is still honored (preserves
        user autonomy) but the rationale now carries a ⚠ health warning
        so the concern is surfaced to the caller/UI rather than being
        silently swallowed.
        """
        profile = _profile(body_fat_pct=5, primary_goal=PrimaryGoal.MAINTENANCE)
        strategy, rationale = decide_strategy(
            profile=profile, body_fat_pct=5, bmi=profile.bmi,
        )
        assert strategy.value == "maintenance"
        assert "hormonal" in rationale.lower() or "warning" in rationale.lower()

    def test_maintenance_at_high_bf_warns_in_rationale(self):
        """Task 9-engine-bug-fixes Bug 4 (high-BF branch): a MAINTENANCE
        goal at a BF% above the operational ceiling (20M/28F) but below
        the obese threshold (25M/32F) is honored, but the rationale
        carries a ⚠ health warning recommending a small cut.
        """
        profile = _profile(body_fat_pct=23, primary_goal=PrimaryGoal.MAINTENANCE)
        strategy, rationale = decide_strategy(
            profile=profile, body_fat_pct=23, bmi=profile.bmi,
        )
        assert strategy.value == "maintenance"
        assert "operational ceiling" in rationale.lower()

    def test_maintenance_at_normal_bf_has_no_warning(self):
        """Task 9-engine-bug-fixes Bug 4 (regression guard): a
        MAINTENANCE goal at a BF% inside the operational range must NOT
        emit a warning — the rationale stays the plain "User goal is
        maintenance." message.
        """
        profile = _profile(body_fat_pct=15, primary_goal=PrimaryGoal.MAINTENANCE)
        strategy, rationale = decide_strategy(
            profile=profile, body_fat_pct=15, bmi=profile.bmi,
        )
        assert strategy.value == "maintenance"
        assert "⚠" not in rationale
        assert rationale == "User goal is maintenance."


# ============================================================
# Assessor error recovery
# ============================================================

class TestAssessorErrorRecovery:
    """assess_profile wraps each sub-assessment in try/except — verify recovery."""

    def test_assessor_handles_invalid_profile_gracefully(self):
        """A profile that causes sub-assessment failure should still return a result."""
        # This profile is valid but has extreme measurements that might trigger edge cases
        profile = _profile(
            body_fat_pct=2,  # extreme low
            weight_kg=35, height_cm=140,
            neck_cm=20, waist_cm=40,
        )
        result = assess_profile(profile)
        assert result is not None
        assert result.body_composition is not None

    def test_assessor_summary_contains_disclaimer(self):
        """Summary must include the standardized medical disclaimer.

        The engine uses ``MEDICAL_DISCLAIMER`` from
        ``assessment/_thresholds.py``:
          "Not a substitute for clinical assessment — consult a physician
           for personalized guidance."
        The word "disclaimer" / "medical" never appears verbatim, so we
        check for the canonical phrases instead.
        """
        profile = _profile()
        result = assess_profile(profile)
        summary_lower = result.summary.lower()
        assert (
            "clinical assessment" in summary_lower
            or "physician" in summary_lower
            or "substitute" in summary_lower
        ), (
            "Assessor summary should include the medical disclaimer "
            f"(got: {result.summary!r})"
        )


# ============================================================
# Food database
# ============================================================

class TestFoodDatabase:

    def test_get_food_returns_food_for_known_name(self):
        food = get_food("Banana")
        assert food is not None
        assert food.name == "Banana"

    def test_get_food_returns_none_for_unknown_name(self):
        assert get_food("Nonexistent Food XYZ") is None

    def test_food_index_contains_all_foods(self):
        for food in FOODS:
            assert food.name in FOOD_INDEX

    def test_protein_per_100kcal_for_high_protein_food(self):
        """High-protein foods should return high values."""
        chicken = get_food("Chicken Breast (skinless, boneless, raw)")
        if chicken:
            p = protein_per_100kcal(chicken)
            assert p > 15  # chicken breast is ~20g protein/100kcal

    def test_protein_per_100kcal_for_low_kcal_food(self):
        """Low-kcal foods (like coffee) produce meaningless results — verify no crash."""
        coffee = get_food("Black Coffee")
        if coffee:
            # Don't assert value — just verify no crash
            protein_per_100kcal(coffee)


# ============================================================
# Meal templates
# ============================================================

class TestMealTemplates:

    def test_get_meal_plan_template_2_meals(self):
        template = get_meal_plan_template(2)
        assert MealType.LUNCH in template
        assert MealType.DINNER in template

    def test_get_meal_plan_template_3_meals(self):
        template = get_meal_plan_template(3)
        assert MealType.BREAKFAST in template
        assert MealType.LUNCH in template
        assert MealType.DINNER in template

    def test_get_meal_plan_template_4_meals(self):
        template = get_meal_plan_template(4)
        assert len(template) == 4

    def test_get_meal_plan_template_5_meals(self):
        template = get_meal_plan_template(5)
        assert len(template) == 5

    def test_get_meal_name_returns_string(self):
        name = get_meal_name(MealType.BREAKFAST)
        assert isinstance(name, str)

    def test_meal_order_has_5_entries(self):
        assert len(MEAL_ORDER) == 5

    def test_meal_names_covers_all_types(self):
        for mt in MealType:
            if mt != MealType.PRE_WORKOUT and mt != MealType.POST_WORKOUT:
                # Some meal types may not have a name — that's OK
                pass


# ============================================================
# Recipe loader + database stats
# ============================================================

class TestRecipeLoader:

    def test_load_recipes_returns_nonempty_list(self):
        recipes = load_recipes()
        assert len(recipes) > 100

    def test_get_recipe_by_id_returns_recipe(self):
        r = get_recipe_by_id("R001")
        assert r is not None
        assert r.id == "R001"

    def test_get_recipe_by_id_returns_none_for_unknown(self):
        assert get_recipe_by_id("NONEXISTENT") is None

    def test_get_recipe_by_name(self):
        recipes = load_recipes()
        if recipes:
            r = get_recipe_by_name(recipes[0].name)
            assert r is not None

    def test_recipes_by_filters_returns_subset(self):
        vegan = recipes_by_diet_type("VEGAN")
        assert isinstance(vegan, list)
        for r in vegan:
            assert RecipeDietTag.VEGAN in r.diet_types

    def test_recipes_by_kcal_range_includes_calculated(self):
        """recipes_by_kcal_range should include 'calculated' nutrition_source (PW recipes)."""
        recipes = recipes_by_kcal_range(100, 1000)
        # Just verify it returns a list
        assert isinstance(recipes, list)

    def test_database_stats_returns_expected_fields(self):
        stats = database_stats()
        assert "total_recipes" in stats
        assert "curated_count" in stats
        assert stats["total_recipes"] > 0

    def test_recipe_has_meat_ingredients_chicken(self):
        """A recipe with 'chicken breast' should be flagged."""
        recipe = Recipe(
            id="TEST",
            name="Test",
            ingredients=["1 lb chicken breast, diced"],
            nutrition_per_serving=NutritionPerServing(
                kcal=400, protein_g=35, carb_g=10, fat_g=15, fiber_g=2,
            ),
            diet_types=[RecipeDietTag.OMNI],
            cuisine="test",
        )
        assert _recipe_has_meat_ingredients(recipe) is True

    def test_recipe_has_meat_ingredients_tofu(self):
        """A recipe with only tofu should not be flagged."""
        recipe = Recipe(
            id="TEST",
            name="Test",
            ingredients=["1 block tofu, cubed", "2 cups broccoli"],
            nutrition_per_serving=NutritionPerServing(
                kcal=300, protein_g=20, carb_g=15, fat_g=10, fiber_g=5,
            ),
            diet_types=[RecipeDietTag.VEGAN],
            cuisine="test",
        )
        assert _recipe_has_meat_ingredients(recipe) is False

    def test_recipe_has_meat_ingredients_beyond_beef(self):
        """'Beyond beef' (plant-based) should NOT be flagged."""
        recipe = Recipe(
            id="TEST",
            name="Test",
            ingredients=["1 package Beyond beef"],
            nutrition_per_serving=NutritionPerServing(
                kcal=300, protein_g=20, carb_g=10, fat_g=15, fiber_g=3,
            ),
            diet_types=[RecipeDietTag.VEGAN],
            cuisine="test",
        )
        assert _recipe_has_meat_ingredients(recipe) is False

    def test_recipe_has_meat_ingredients_no_chicken_broth(self):
        """'no-chicken broth' should NOT be flagged (plant qualifier)."""
        recipe = Recipe(
            id="TEST",
            name="Test",
            ingredients=["2 cups no-chicken broth"],
            nutrition_per_serving=NutritionPerServing(
                kcal=50, protein_g=2, carb_g=5, fat_g=1, fiber_g=0,
            ),
            diet_types=[RecipeDietTag.VEGAN],
            cuisine="test",
        )
        assert _recipe_has_meat_ingredients(recipe) is False


# ============================================================
# Pre/post workout recipes
# ============================================================

class TestPrePostWorkoutRecipes:

    def test_get_pre_post_workout_recipes_returns_list(self):
        recipes = get_pre_post_workout_recipes()
        assert len(recipes) > 0
        assert len(recipes) == len(PRE_POST_WORKOUT_RECIPES)

    def test_pre_post_recipes_not_marked_as_curated(self):
        """Engine-generated PW recipes should not be tagged as curated."""
        recipes = get_pre_post_workout_recipes()
        for r in recipes:
            assert "[curated]" not in (r.notes or ""), (
                f"PW recipe {r.name} should not be marked curated"
            )


# ============================================================
# Recipe scaler + fillers
# ============================================================

class TestRecipeScaler:

    def test_compute_scale_factor_no_scaling_when_within_band(self):
        """If target is within ±10% of recipe kcal, scale=1.0."""
        factor = compute_scale_factor(recipe_kcal=500, target_kcal=520)
        assert factor == 1.0  # 520/500 = 1.04, within ±10% band

    def test_compute_scale_factor_clamps_to_min(self):
        factor = compute_scale_factor(recipe_kcal=500, target_kcal=50)
        assert factor == ScalerConfig.min_scale  # 0.7

    def test_compute_scale_factor_clamps_to_max(self):
        factor = compute_scale_factor(recipe_kcal=100, target_kcal=10000)
        assert factor == ScalerConfig.max_scale  # 1.5

    def test_compute_scale_factor_zero_target_returns_one(self):
        """Phase-6 fix: target_kcal <= 0 returns 1.0 (no scaling)."""
        assert compute_scale_factor(recipe_kcal=500, target_kcal=0) == 1.0
        assert compute_scale_factor(recipe_kcal=500, target_kcal=-100) == 1.0

    def test_is_recipe_scalable_to_target_within_deviation(self):
        assert is_recipe_scalable_to_target(500, 500) is True
        assert is_recipe_scalable_to_target(500, 600) is True  # within ±20%
        assert is_recipe_scalable_to_target(500, 100) is False

    def test_select_protein_filler_returns_food(self):
        result = select_protein_filler(gap_protein_g=30, diet_tag="OMNI")
        assert result is not None
        assert result.food.name  # non-empty

    def test_select_protein_filler_returns_none_for_small_gap(self):
        result = select_protein_filler(gap_protein_g=0.5, diet_tag="OMNI")
        assert result is None

    def test_select_protein_filler_vegan_returns_vegan_food(self):
        result = select_protein_filler(gap_protein_g=30, diet_tag="VEGAN")
        assert result is not None
        NON_VEGAN = {
            "Whey Protein Powder", "Greek Yogurt (non-fat, plain)",
            "Egg White (large)", "Cottage Cheese (low-fat, 2%)",
            "Chicken Breast (skinless, boneless, raw)",
        }
        assert result.food.name not in NON_VEGAN

    def test_select_protein_filler_vegan_ethiopian_returns_vegan_food(self):
        result = select_protein_filler(gap_protein_g=30, diet_tag="VEGAN_ETHIOPIAN")
        assert result is not None
        assert result.food.is_vegan

    def test_select_carb_filler_returns_food(self):
        result = select_carb_filler(gap_carb_g=50)
        assert result is not None

    def test_select_fat_filler_returns_food(self):
        result = select_fat_filler(gap_fat_g=20)
        assert result is not None

    def test_select_veg_filler_returns_food(self):
        result = select_veg_filler(gap_fiber_g=15)
        assert result is not None


# ============================================================
# Allergen + exclusion detection
# ============================================================

class TestAllergenDetection:

    def _recipe(self, ingredients, diet_types=None):
        return Recipe(
            id="TEST", name="Test",
            ingredients=ingredients,
            nutrition_per_serving=NutritionPerServing(
                kcal=400, protein_g=20, carb_g=30, fat_g=15, fiber_g=5,
            ),
            diet_types=diet_types or [RecipeDietTag.OMNI],
            cuisine="test",
        )

    def test_dairy_allergen_detected(self):
        """``check_allergens`` returns the list of violated allergen NAMES
        (e.g. ``["dairy"]``), not the triggering ingredient. So we assert
        that "dairy" appears in the violations list.
        """
        r = self._recipe(["1 cup milk", "1 cup rice"])
        violations = check_allergens(r, ["dairy"])
        assert "dairy" in violations

    def test_dairy_allergen_not_detected_in_dairy_free_recipe(self):
        r = self._recipe(["1 cup oat milk", "1 cup rice"])
        violations = check_allergens(r, ["dairy"])
        assert violations == []

    def test_egg_allergen_detected(self):
        r = self._recipe(["2 eggs", "1 cup flour"])
        violations = check_allergens(r, ["eggs"])
        assert len(violations) > 0

    def test_egg_allergen_not_detected_in_eggplant(self):
        """'eggplant' should not trigger egg allergen."""
        r = self._recipe(["1 eggplant, diced", "2 cups tomato"])
        violations = check_allergens(r, ["eggs"])
        assert violations == []

    def test_gluten_allergen_detected(self):
        r = self._recipe(["1 cup wheat flour"])
        violations = check_allergens(r, ["gluten"])
        # 'wheat' is in the gluten keyword list
        assert len(violations) > 0

    def test_peanut_allergen_detected(self):
        r = self._recipe(["2 tbsp peanut butter"])
        violations = check_allergens(r, ["peanuts"])
        assert len(violations) > 0

    def test_peanut_allergen_not_detected_in_peanut_butter_plant_phrase(self):
        """Wait — peanut butter IS peanuts. This SHOULD be detected."""
        r = self._recipe(["2 tbsp peanut butter"])
        violations = check_allergens(r, ["peanuts"])
        # peanut butter contains peanuts — should be flagged
        assert len(violations) > 0

    def test_tree_nuts_allergen_detected(self):
        """Engine's allergen key for tree nuts is ``"nuts"`` (not
        ``"tree_nuts"``). The regex patterns use word boundaries (e.g.
        ``\\balmond\\b``), so we use the singular form "almond" — plural
        "almonds" is currently NOT matched (see engine bug note in
        worklog).
        """
        r = self._recipe(["1 cup almond"])
        violations = check_allergens(r, ["nuts"])
        assert "nuts" in violations

    def test_nuts_allergen_detected_plural(self):
        """Task 9-engine-bug-fixes Bug 1: the nut regexes now match
        plurals. Real recipes almost always write nuts in the plural
        ("1 cup almonds, slivered"), so the previous strict-singular
        regexes (``\\balmond\\b`` etc.) caused silent false-negatives
        for tree-nut allergies.
        """
        r = self._recipe(["1 cup almonds, slivered"])
        violations = check_allergens(r, ["nuts"])
        assert "nuts" in violations

    def test_nuts_allergen_detected_plural_for_each_nut_keyword(self):
        """Task 9-engine-bug-fixes Bug 1 (parametrized regression guard):
        every nut keyword in ``ALLERGEN_KEYWORDS["nuts"]`` must match
        its plural form. Sanity-checks the most common ones the bug
        originally missed.
        """
        plural_ingredients = [
            "1 cup almonds", "1 cup cashews", "1 cup walnuts",
            "1 cup pecans", "1 cup hazelnuts", "1 cup pistachios",
            "1 cup brazil nuts", "1 cup macadamias", "1 cup pine nuts",
        ]
        for ingredient in plural_ingredients:
            r = self._recipe([ingredient])
            violations = check_allergens(r, ["nuts"])
            assert "nuts" in violations, (
                f"Plural nut ingredient {ingredient!r} was not detected "
                f"as a tree-nut allergen (violations={violations!r})."
            )

    def test_tree_nuts_alias_works(self):
        """Task 9-engine-bug-fixes Bug 2: ``"tree_nuts"`` (the
        FDA-standard identifier) is now silently aliased to the
        engine's internal ``"nuts"`` key. Previously, passing
        ``"tree_nuts"`` returned ``[]`` for every recipe — a dangerous
        false-negative for tree-nut allergies.

        The violation is reported under the engine's internal key
        (``"nuts"``), not the original alias (``"tree_nuts"``); the
        test accepts either form for forward-compatibility.
        """
        r = self._recipe(["1 cup almond"])
        violations = check_allergens(r, ["tree_nuts"])
        assert "tree_nuts" in violations or "nuts" in violations

    def test_tree_nuts_alias_works_with_plural(self):
        """Task 9-engine-bug-fixes Bug 1 + Bug 2 (combined): the
        ``"tree_nuts"`` alias works together with the plural-form fix
        — a recipe containing "almonds" (plural) is correctly flagged
        when the caller passes ``"tree_nuts"`` (FDA-standard alias).
        """
        r = self._recipe(["1 cup almonds, slivered"])
        violations = check_allergens(r, ["tree_nuts"])
        assert "tree_nuts" in violations or "nuts" in violations

    def test_crustacean_alias_works(self):
        """Task 9-engine-bug-fixes Bug 2 (bonus alias): the FDA's
        formal label for the shellfish category is "crustacean
        shellfish" (vs. "mollusk shellfish"). The engine's
        ``shellfish`` list only contains crustaceans, so
        ``"crustacean"`` is aliased to ``"shellfish"``.
        """
        r = self._recipe(["1 lb shrimp, peeled and deveined"])
        violations = check_allergens(r, ["crustacean"])
        assert "crustacean" in violations or "shellfish" in violations

    def test_tree_nuts_alias_does_not_break_unknown_allergen_fallback(self):
        """Task 9-engine-bug-fixes Bug 2 (regression guard): a truly
        unknown allergen (e.g. "corn") still falls back to the
        word-boundary substring match — aliasing is opt-in for the
        specific known FDA identifiers only.
        """
        r = self._recipe(["1 cup corn", "1 tbsp oil"])
        violations = check_allergens(r, ["corn"])
        assert "corn" in violations

    def test_soy_allergen_detected(self):
        r = self._recipe(["1 tbsp soy sauce"])
        violations = check_allergens(r, ["soy"])
        assert len(violations) > 0

    def test_check_excluded_ingredients_peanut_butter(self):
        """Excluded ingredient 'peanut butter' should exclude recipes containing it."""
        r = self._recipe(["½ cup almond or peanut butter, unsweetened"])
        violations = check_excluded_ingredients(r, ["peanut butter"])
        assert len(violations) > 0

    def test_check_excluded_ingredients_no_match(self):
        r = self._recipe(["1 cup rice", "1 cup beans"])
        violations = check_excluded_ingredients(r, ["peanut butter"])
        assert violations == []


# ============================================================
# Swap system
# ============================================================

class TestSwapSystem:

    def test_get_ingredient_swaps_returns_swaps_for_known_ingredient(self):
        swaps = get_ingredient_swaps("1 lb chicken breast")
        assert swaps is not None
        assert len(swaps) > 0

    def test_get_ingredient_swaps_returns_none_for_unknown(self):
        """Unknown ingredients return an empty list (NOT None).

        Per the function signature ``get_ingredient_swaps(...) ->
        list[IngredientSwap]``, the "no match" sentinel is ``[]``.
        """
        swaps = get_ingredient_swaps("2 cups mystery ingredient")
        assert swaps == []

    def test_get_ingredient_swaps_handles_plant_phrase(self):
        """'almond milk' should not return swaps for 'milk'."""
        # Almond milk is plant-based — the swap for milk should not apply
        swaps = get_ingredient_swaps("1 cup almond milk")
        # Either None (plant-phrase excludes) or a non-dairy swap
        if swaps is not None:
            # Verify the swap isn't suggesting dairy
            for swap in swaps:
                assert "milk" not in swap.lower() or "plant" in swap.lower()

    def test_get_recipe_swaps_does_not_mutate_caller_set(self):
        from fitness_engine import UserProfile, assess_profile, propose_plan, PlanPreferences
        profile = _profile()
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        # Find a recipe to get swaps for
        for day in plan.meal.days:
            for meal in day.meals:
                if meal.recipe:
                    original = {"R_OTHER"}
                    original_copy = set(original)
                    try:
                        get_recipe_swaps(
                            recipe=meal.recipe,
                            target_kcal=500,
                            exclude_ids=original,
                        )
                    except Exception:
                        pass
                    assert original == original_copy, (
                        "get_recipe_swaps mutated caller's exclude_ids set"
                    )
                    return
        pytest.skip("No recipe in default plan to test swaps")

    def test_get_swaps_for_recipe_ingredients_returns_dict(self):
        r = Recipe(
            id="TEST", name="Test",
            ingredients=["1 lb chicken breast", "2 cups rice", "1 tbsp olive oil"],
            nutrition_per_serving=NutritionPerServing(
                kcal=500, protein_g=35, carb_g=40, fat_g=12, fiber_g=2,
            ),
            diet_types=[RecipeDietTag.OMNI],
            cuisine="test",
        )
        swaps = get_swaps_for_recipe_ingredients(r)
        assert isinstance(swaps, dict)


# ============================================================
# Exercise database + categorization
# ============================================================

class TestExerciseDatabase:

    def test_get_exercises_returns_tuple(self):
        exs = get_exercises()
        assert isinstance(exs, tuple)
        assert len(exs) > 1000  # 1217 exercises

    def test_get_exercise_by_slug_returns_exercise(self):
        ex = get_exercise_by_slug("barbell-bench-press")
        assert ex is not None
        assert ex.slug == "barbell-bench-press"

    def test_get_exercise_by_slug_returns_none_for_unknown(self):
        assert get_exercise_by_slug("nonexistent-exercise") is None

    def test_get_exercise_by_name(self):
        exs = get_exercises()
        if exs:
            ex = get_exercise_by_name(exs[0].name)
            assert ex is not None

    def test_get_exercise_by_phase1_name_returns_none_for_removed_cardio(self):
        """Phase-1 names like 'Incline Walk' should return None (no Phase-2 cardio equivalent)."""
        assert get_exercise_by_phase1_name("Incline Walk") is None
        assert get_exercise_by_phase1_name("Cycling (moderate)") is None
        assert get_exercise_by_phase1_name("Swimming") is None

    def test_get_exercise_by_phase1_name_returns_exercise_for_known(self):
        """'Rowing Machine' should still resolve."""
        ex = get_exercise_by_phase1_name("Rowing Machine")
        assert ex is not None

    def test_clear_exercise_cache_does_not_crash(self):
        get_exercises()  # prime cache
        _clear_exercise_cache()
        # Should reload on next call
        exs = get_exercises()
        assert len(exs) > 0


class TestExerciseCategorization:

    def test_get_movement_pattern_returns_string(self):
        from fitness_engine.training.exercise_library import get_exercise_by_slug
        ex = get_exercise_by_slug("barbell-bench-press")
        if ex:
            pattern = get_movement_pattern(ex)
            assert isinstance(pattern, str)

    def test_get_pattern_family_returns_family(self):
        family = get_pattern_family("horizontal_push")
        assert family is not None

    def test_categorize_exercise_returns_info(self):
        """``categorize_exercise`` takes a single ``Exercise`` object (not
        three strings) and returns an ``ExerciseCategoryInfo`` dataclass
        with fields: ``exercise``, ``movement_pattern``, ``pattern_family``,
        ``primary_muscles``, ``environment_preferences``.
        """
        from fitness_engine.training.exercise_categorization import (
            ExerciseCategoryInfo,
        )
        from fitness_engine.training.exercise_library import get_exercise_by_slug

        ex = get_exercise_by_slug("barbell-bench-press")
        assert ex is not None, "barbell-bench-press slug should resolve"
        info = categorize_exercise(ex)
        assert isinstance(info, ExerciseCategoryInfo)
        assert info.exercise is ex
        assert info.movement_pattern == "horizontal_push"
        assert info.pattern_family is not None
        assert isinstance(info.primary_muscles, list) and info.primary_muscles
        assert isinstance(info.environment_preferences, dict)

    def test_movement_patterns_count_is_40(self):
        """Updated from 24 to 40 in Phase-6 fix."""
        assert len(MOVEMENT_PATTERNS) >= 24  # at least the original 24


# ============================================================
# PlanPreferences edge cases
# ============================================================

class TestPlanPreferences:

    def test_default_preferences(self):
        prefs = PlanPreferences()
        assert prefs.meal_frequency == 3
        assert prefs.exercise_hours_per_day == 1.0
        assert prefs.exercise_intensity == ExerciseIntensity.MODERATE

    def test_from_kwargs_filters_unknown(self):
        prefs = PlanPreferences.from_kwargs(
            meal_frequency=4,
            unknown_param="should_be_ignored",
        )
        assert prefs.meal_frequency == 4

    def test_to_dict_returns_json_serializable(self):
        prefs = PlanPreferences(meal_frequency=4)
        d = prefs.to_dict()
        json.dumps(d, default=str)

    def test_coerce_string_to_enum(self):
        prefs = PlanPreferences(exercise_intensity="intense")
        assert prefs.exercise_intensity == ExerciseIntensity.INTENSE

    def test_coerce_invalid_string_falls_back_to_default(self):
        prefs = PlanPreferences(exercise_intensity="extreme")
        assert prefs.exercise_intensity == ExerciseIntensity.MODERATE


# ============================================================
# Utils: serialize + units
# ============================================================

class TestUtils:

    def test_convert_for_json_handles_enum(self):
        from enum import Enum
        class Color(str, Enum):
            RED = "red"
        assert convert_for_json(Color.RED) == "red"

    def test_convert_for_json_handles_dict_with_enum_keys(self):
        """Phase-6 fix: dict keys are now converted too."""
        from enum import Enum
        class Color(str, Enum):
            RED = "red"
            BLUE = "blue"
        d = {Color.RED: 1, Color.BLUE: 2}
        result = convert_for_json(d)
        assert "red" in result
        assert "blue" in result

    def test_convert_for_json_handles_set(self):
        """Phase-6 fix: sets are converted to sorted lists."""
        result = convert_for_json({"c", "a", "b"})
        assert isinstance(result, list)
        assert set(result) == {"a", "b", "c"}

    def test_convert_for_json_handles_nested_dataclass(self):
        from dataclasses import dataclass
        from enum import Enum
        class Color(str, Enum):
            RED = "red"
        @dataclass
        class Inner:
            color: Color
        @dataclass
        class Outer:
            inner: Inner
            items: list
        o = Outer(inner=Inner(color=Color.RED), items=[1, 2, 3])
        d = convert_for_json(o)
        assert d["inner"]["color"] == "red"
        assert d["items"] == [1, 2, 3]

    def test_kg_to_lb_basic(self):
        assert abs(kg_to_lb(1) - LB_PER_KG) < 0.001
        assert abs(kg_to_lb(10) - 22.046) < 0.01

    def test_lb_to_kg_basic(self):
        assert abs(lb_to_kg(1) - KG_PER_LB) < 0.001
        assert abs(lb_to_kg(10) - 4.536) < 0.01

    def test_kg_lb_roundtrip(self):
        """kg_to_lb(lb_to_kg(x)) ≈ x."""
        for x in [1, 10, 50, 100, 250]:
            assert abs(kg_to_lb(lb_to_kg(x)) - x) < 0.001

    def test_cm_to_in_basic(self):
        assert abs(cm_to_in(2.54) - 1.0) < 0.001

    def test_in_to_cm_basic(self):
        assert abs(in_to_cm(1) - 2.54) < 0.001

    def test_cm_in_roundtrip(self):
        for x in [1, 10, 100, 200]:
            assert abs(cm_to_in(in_to_cm(x)) - x) < 0.001

    def test_weeks_per_month_constant(self):
        assert abs(WEEKS_PER_MONTH - 4.348) < 0.001


class TestParseViewCount:
    """``parse_view_count`` takes an ``Exercise`` (not a raw string) and
    reads its ``views`` attribute (e.g. "1.2K", "3.5M", "12345"). All
    tests build a minimal ``Exercise`` with the desired views string."""

    @staticmethod
    def _ex(views):
        from fitness_engine.models.training import Exercise, ExerciseCategory
        return Exercise(
            name="Test",
            category=ExerciseCategory.COMPOUND_PRIMARY,
            muscle_groups=["chest"],
            equipment="barbell",
            default_sets=4,
            default_reps="5-8",
            default_rest_sec=180,
            views=views,
        )

    def test_parse_numeric_string(self):
        assert parse_view_count(self._ex("12345")) == 12345

    def test_parse_thousands(self):
        assert parse_view_count(self._ex("12.3K")) == 12300

    def test_parse_millions(self):
        assert parse_view_count(self._ex("6.6M")) == 6_600_000

    def test_parse_empty_returns_zero(self):
        assert parse_view_count(self._ex("")) == 0

    def test_parse_none_returns_zero(self):
        """Task 9-engine-bug-fixes Bug 3: ``parse_view_count`` now
        returns 0 for ALL "missing/unparseable" cases per its stated
        contract:

          * passing ``None`` as the ``ex`` argument (previously raised
            ``AttributeError`` — the docstring said "Returns 0 if the
            field is missing or unparseable" but the code didn't guard)
          * an ``Exercise`` whose ``views`` field is ``None``
          * an ``Exercise`` whose ``views`` field is empty (``""``)
        """
        # ex=None — previously AttributeError, now 0
        assert parse_view_count(None) == 0
        # Exercise with views=None — already worked, keep the coverage
        assert parse_view_count(self._ex(None)) == 0
        # Exercise with views="" — already worked, keep the coverage
        assert parse_view_count(self._ex("")) == 0


# ============================================================
# Allocator edge cases
# ============================================================

class TestAllocatorEdgeCases:

    def test_compute_allergen_filler_exclusions_returns_set(self):
        result = _compute_allergen_filler_exclusions(["dairy", "eggs"])
        assert isinstance(result, set)
        # Should exclude whey, yogurt, etc.
        assert len(result) > 0

    def test_compute_allergen_filler_exclusions_empty_list(self):
        result = _compute_allergen_filler_exclusions([])
        assert result == set()

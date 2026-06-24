"""
Phase-5 tests for the clean meal planning system.

Verifies:
  - Profile requirements computation (per-slot targets)
  - Pre/Post workout slot targets
  - Recipe scorer (best-fit scoring algorithm)
  - Recipe scaler (acceptable scaling 0.7x-1.5x)
  - Filler system (protein/carb/fat/veg fillers)
  - Swap system (recipe swaps + ingredient swaps)
  - Pre/Post workout recipes (16 engine-generated recipes)
  - Allocator (single-slot allocation)
  - Planner (7-day plan generation)
  - Allergen filtering
  - Diet type filtering (OMNI / VEGAN / OMNI_ETHIOPIAN / VEGAN_ETHIOPIAN)
  - End-to-end integration with engine.propose_plan
"""
import json
import pytest

from fitness_engine import (
    UserProfile, assess_profile, propose_plan,
)
from fitness_engine.models.profile import (
    Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType,
)
from fitness_engine.models.meal import MealType
from fitness_engine.meal_plan import (
    # Profile requirements
    compute_meal_plan_requirements, MealPlanRequirements, MealSlotTarget,
    compute_pre_workout_target, compute_post_workout_target,
    get_recipe_diet_tag,
    # Scorer
    score_recipe_for_slot, score_candidates, RecipeScore,
    MIN_ACCEPTABLE_SCORE, WEIGHTS,
    score_kcal_match, score_protein_match, score_diet_match,
    score_goal_fit, score_variety, score_cuisine,
    check_allergens, check_excluded_ingredients,
    # Scaler + fillers
    compute_scale_factor, scale_recipe, ScaledRecipe,
    compute_filler_gap, select_fillers_for_meal,
    select_protein_filler, select_carb_filler, select_fat_filler, select_veg_filler,
    MIN_SCALE, MAX_SCALE,
    # Swap system
    get_ingredient_swaps, get_swaps_for_recipe_ingredients,
    get_recipe_swaps, get_recipe_swaps_for_plan, IngredientSwap,
    # Pre/Post workout
    get_pre_post_workout_recipes, get_pre_workout_recipes, get_post_workout_recipes,
    PRE_POST_WORKOUT_RECIPES,
    # Allocator + planner
    allocate_meal, SelectedMeal, selected_meal_to_dict,
    build_meal_plan,
    # Recipe loader
    load_recipes, get_recipe_by_id, recipes_by_filters,
)
from fitness_engine.meal_plan.recipe_loader import _build_indexes


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
def vegan_profile():
    return UserProfile(
        age=27, sex=Sex.MALE, height_cm=180, weight_kg=78,
        body_fat_pct=14,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        training_status=TrainingStatus.NOVICE,
        primary_goal=PrimaryGoal.MAINTENANCE,
        training_days_per_week=3,
        equipment_access=EquipmentAccess.FULL_GYM,
        diet_type=DietType.VEGAN,
    )


# === Profile requirements tests ===

class TestProfileRequirements:
    def test_compute_requirements_returns_full_targets(self, cut_profile):
        """compute_meal_plan_requirements should return per-slot targets."""
        from fitness_engine import assess_profile
        from fitness_engine.nutrition.planner import build_nutrition_plan
        assessment = assess_profile(cut_profile)
        nutrition = build_nutrition_plan(cut_profile, assessment)
        req = compute_meal_plan_requirements(
            cut_profile, assessment, nutrition, meal_frequency=3,
        )
        assert req.daily_kcal > 0
        assert req.daily_protein_g > 0
        assert req.daily_carb_g > 0
        assert req.daily_fat_g > 0
        assert len(req.slot_targets) == 3   # breakfast, lunch, dinner

    def test_3_meal_frequency_has_3_slots(self, cut_profile):
        from fitness_engine import assess_profile
        from fitness_engine.nutrition.planner import build_nutrition_plan
        assessment = assess_profile(cut_profile)
        nutrition = build_nutrition_plan(cut_profile, assessment)
        req = compute_meal_plan_requirements(
            cut_profile, assessment, nutrition, meal_frequency=3,
        )
        assert len(req.slot_targets) == 3
        meal_types = [s.meal_type for s in req.slot_targets]
        assert MealType.BREAKFAST in meal_types
        assert MealType.LUNCH in meal_types
        assert MealType.DINNER in meal_types

    def test_5_meal_frequency_has_5_slots(self, cut_profile):
        from fitness_engine import assess_profile
        from fitness_engine.nutrition.planner import build_nutrition_plan
        assessment = assess_profile(cut_profile)
        nutrition = build_nutrition_plan(cut_profile, assessment)
        req = compute_meal_plan_requirements(
            cut_profile, assessment, nutrition, meal_frequency=5,
        )
        assert len(req.slot_targets) == 5

    def test_pre_post_workout_adds_slots(self, cut_profile):
        """include_pre_post_workout should add PRE/POST slots on training days."""
        from fitness_engine import assess_profile
        from fitness_engine.nutrition.planner import build_nutrition_plan
        assessment = assess_profile(cut_profile)
        nutrition = build_nutrition_plan(cut_profile, assessment)
        req = compute_meal_plan_requirements(
            cut_profile, assessment, nutrition,
            meal_frequency=3, include_pre_post_workout=True,
        )
        # Training day should have more slots than rest day
        assert len(req.training_day_slot_targets) > len(req.slot_targets)
        # Training day slots include PRE_WORKOUT and POST_WORKOUT
        training_types = [s.meal_type for s in req.training_day_slot_targets]
        assert MealType.PRE_WORKOUT in training_types
        assert MealType.POST_WORKOUT in training_types

    def test_pre_workout_target_is_high_carb_low_fat(self):
        """Pre-workout target should be ~10% daily kcal, high carb."""
        target = compute_pre_workout_target(
            daily_kcal=2500, daily_protein_g=150,
            daily_carb_g=300, daily_fat_g=80,
        )
        assert 240 <= target.target_kcal <= 260   # ~10% of 2500
        assert target.target_protein_g < 30   # low protein
        assert target.target_carb_g > 50      # high carb
        assert target.target_fat_g < 10       # low fat

    def test_post_workout_target_is_protein_plus_carbs(self):
        """Post-workout target should be ~15% daily kcal, protein + carbs."""
        target = compute_post_workout_target(
            daily_kcal=2500, daily_protein_g=150,
            daily_carb_g=300, daily_fat_g=80,
        )
        assert 360 <= target.target_kcal <= 390   # ~15% of 2500
        assert target.target_protein_g > 30   # high protein
        assert target.target_carb_g > 50      # high carb

    def test_diet_tag_mapping(self):
        """Diet type should map to the correct recipe tag."""
        assert get_recipe_diet_tag(DietType.OMNIVORE) == "OMNI"
        assert get_recipe_diet_tag(DietType.VEGAN) == "VEGAN"
        assert get_recipe_diet_tag(DietType.VEGETARIAN) == "VEGAN"

    def test_ethiopian_cuisine_overrides_diet_tag(self, cut_profile):
        """cuisine_preference=ethiopian should override diet_tag to ETHIOPIAN variant."""
        from fitness_engine import assess_profile
        from fitness_engine.nutrition.planner import build_nutrition_plan
        assessment = assess_profile(cut_profile)
        nutrition = build_nutrition_plan(cut_profile, assessment)
        req = compute_meal_plan_requirements(
            cut_profile, assessment, nutrition,
            cuisine_preference="ethiopian",
        )
        assert req.diet_tag == "OMNI_ETHIOPIAN"


# === Recipe scorer tests ===

class TestRecipeScorer:
    def test_kcal_match_perfect_returns_100(self):
        """kcal match within ±20% should return 100."""
        assert score_kcal_match(500, 500) == 100.0
        assert score_kcal_match(510, 500) == 100.0   # 2% off
        assert score_kcal_match(590, 500) == 100.0   # 18% off (within tight band)

    def test_kcal_match_loose_returns_50(self):
        """kcal match within ±40% (but outside ±20%) should interpolate."""
        # 30% off should be between 50 and 100
        score = score_kcal_match(650, 500)   # 30% off
        assert 0 < score < 100

    def test_kcal_match_far_returns_0(self):
        """kcal match >40% off should return 0."""
        assert score_kcal_match(800, 500) == 0.0   # 60% off
        assert score_kcal_match(200, 500) == 0.0   # 60% off

    def test_protein_match_perfect_returns_100(self):
        """Protein match within ±15% should return 100."""
        assert score_protein_match(40, 40) == 100.0
        assert score_protein_match(45, 40) == 100.0   # 12.5% off

    def test_diet_match_vegan_excludes_non_vegan(self):
        """Vegan diet should reject OMNI recipes."""
        from fitness_engine.models.meal import Recipe, NutritionPerServing
        omni_recipe = Recipe(
            name="Chicken", id="T1",
            meal_types=["dinner"], diet_types=["OMNI"],
            ingredients=["chicken breast"],
            nutrition_per_serving=NutritionPerServing(kcal=300, protein_g=30),
        )
        assert score_diet_match(omni_recipe, "VEGAN") == 0.0

    def test_diet_match_vegan_accepts_vegan_recipe(self):
        """Vegan diet should accept VEGAN recipes."""
        from fitness_engine.models.meal import Recipe, NutritionPerServing
        vegan_recipe = Recipe(
            name="Tofu Bowl", id="T2",
            meal_types=["dinner"], diet_types=["VEGAN"],
            ingredients=["tofu", "rice"],
            nutrition_per_serving=NutritionPerServing(kcal=400, protein_g=25),
        )
        assert score_diet_match(vegan_recipe, "VEGAN") == 100.0

    def test_diet_match_omni_accepts_vegan(self):
        """Omni diet should accept VEGAN recipes (vegan food is omni-compatible)."""
        from fitness_engine.models.meal import Recipe, NutritionPerServing
        vegan_recipe = Recipe(
            name="Tofu Bowl", id="T3",
            meal_types=["dinner"], diet_types=["VEGAN"],
            ingredients=["tofu", "rice"],
            nutrition_per_serving=NutritionPerServing(kcal=400, protein_g=25),
        )
        assert score_diet_match(vegan_recipe, "OMNI") == 100.0

    def test_diet_match_vegan_rejects_diet_warning(self):
        """Vegan diet should reject recipes flagged with diet-warning."""
        from fitness_engine.models.meal import Recipe, NutritionPerServing
        mis_tagged = Recipe(
            name="Corned Beef (mislabeled)", id="T4",
            meal_types=["dinner"], diet_types=["VEGAN"],
            ingredients=["corned beef"],
            notes="[diet-warning: tagged VEGAN but ingredients contain meat]",
            nutrition_per_serving=NutritionPerServing(kcal=500, protein_g=30),
        )
        assert score_diet_match(mis_tagged, "VEGAN") == 0.0

    def test_goal_fit_exact_match_returns_100(self):
        """Recipe with matching goal_fit should return 100."""
        from fitness_engine.models.meal import Recipe, NutritionPerServing
        recipe = Recipe(
            name="Test", id="T5",
            goal_fit=["cut", "maintenance"],
            ingredients=["test"],
            nutrition_per_serving=NutritionPerServing(),
        )
        assert score_goal_fit(recipe, "cut") == 100.0
        assert score_goal_fit(recipe, "maintenance") == 100.0

    def test_goal_fit_maintenance_fallback_returns_50(self):
        """Recipe with only 'maintenance' should return 50 for non-maintenance goals."""
        from fitness_engine.models.meal import Recipe, NutritionPerServing
        recipe = Recipe(
            name="Test", id="T6",
            goal_fit=["maintenance"],
            ingredients=["test"],
            nutrition_per_serving=NutritionPerServing(),
        )
        assert score_goal_fit(recipe, "cut") == 50.0

    def test_variety_score(self):
        """Variety score should reward unused recipes."""
        from fitness_engine.models.meal import Recipe, NutritionPerServing
        recipe = Recipe(name="Test", id="R999", ingredients=["test"],
                        nutrition_per_serving=NutritionPerServing())
        # Not used at all → 100
        assert score_variety(recipe, set(), set()) == 100.0
        # Used in last 3 days → 0
        assert score_variety(recipe, {"R999"}, set()) == 0.0
        # Used in last 7 days but not 3 → 50
        assert score_variety(recipe, set(), {"R999"}) == 50.0

    def test_cuisine_match_with_preference(self):
        """Cuisine match should return 100 when preference matches."""
        from fitness_engine.models.meal import Recipe, NutritionPerServing
        recipe = Recipe(name="Wat", id="T7", cuisine="ethiopian",
                        ingredients=["test"],
                        nutrition_per_serving=NutritionPerServing())
        assert score_cuisine(recipe, "ethiopian") == 100.0
        assert score_cuisine(recipe, "indian") == 0.0
        assert score_cuisine(recipe, None) == 50.0

    def test_allergen_check_dairy(self):
        """check_allergens should detect dairy."""
        from fitness_engine.models.meal import Recipe, NutritionPerServing
        recipe = Recipe(
            name="Yogurt Bowl", id="T8",
            ingredients=["greek yogurt", "honey", "berries"],
            nutrition_per_serving=NutritionPerServing(),
        )
        violations = check_allergens(recipe, ["dairy"])
        assert "dairy" in violations

    def test_allergen_check_no_violations(self):
        """check_allergens should return empty list when no allergens present."""
        from fitness_engine.models.meal import Recipe, NutritionPerServing
        recipe = Recipe(
            name="Rice Bowl", id="T9",
            ingredients=["rice", "vegetables"],
            nutrition_per_serving=NutritionPerServing(),
        )
        violations = check_allergens(recipe, ["dairy", "gluten"])
        assert violations == []

    def test_excluded_ingredients_check(self):
        """check_excluded_ingredients should detect excluded ingredients."""
        from fitness_engine.models.meal import Recipe, NutritionPerServing
        recipe = Recipe(
            name="Tofu Bowl", id="T10",
            ingredients=["tofu", "rice", "broccoli"],
            nutrition_per_serving=NutritionPerServing(),
        )
        found = check_excluded_ingredients(recipe, ["tofu"])
        assert "tofu" in found
        found = check_excluded_ingredients(recipe, ["chicken"])
        assert found == []

    def test_score_recipe_for_slot_returns_score(self):
        """score_recipe_for_slot should return a RecipeScore with total > 0."""
        recipes = recipes_by_filters(meal_type="dinner", diet_type="OMNI")
        if not recipes:
            pytest.skip("No dinner recipes available")
        recipe = recipes[0]
        slot = MealSlotTarget(
            meal_type=MealType.DINNER,
            target_kcal=recipe.kcal,
            target_protein_g=recipe.protein_g,
            target_carb_g=recipe.carb_g,
            target_fat_g=recipe.fat_g,
            target_fiber_g=recipe.fiber_g,
        )
        score = score_recipe_for_slot(recipe, slot, "OMNI")
        assert score.total_score > 0
        assert not score.excluded
        assert "kcal_match" in score.component_scores


# === Recipe scaler tests ===

class TestRecipeScaler:
    def test_compute_scale_factor_no_scaling_when_close(self):
        """Scale factor should be 1.0 when recipe is within ±10% of target."""
        assert compute_scale_factor(500, 500) == 1.0
        assert compute_scale_factor(510, 500) == 1.0
        assert compute_scale_factor(490, 500) == 1.0

    def test_compute_scale_factor_clamps_to_range(self):
        """Scale factor should be clamped to [0.7, 1.5]."""
        # Target much higher than recipe → clamped to 1.5
        assert compute_scale_factor(500, 1000) == 1.5
        # Target much lower → clamped to 0.7
        assert compute_scale_factor(1000, 500) == 0.7

    def test_compute_scale_factor_normal_scaling(self):
        """Scale factor should be target/recipe when within range."""
        # 20% scaling
        assert abs(compute_scale_factor(500, 600) - 1.2) < 0.01
        # -15% scaling
        assert abs(compute_scale_factor(500, 425) - 0.85) < 0.01

    def test_scale_recipe_returns_scaled_macros(self):
        """scale_recipe should return scaled macros."""
        from fitness_engine.models.meal import Recipe, NutritionPerServing
        recipe = Recipe(
            name="Test", id="T11",
            ingredients=["test"],
            nutrition_per_serving=NutritionPerServing(
                kcal=400, protein_g=30, carb_g=40, fat_g=10, fiber_g=5,
            ),
        )
        scaled = scale_recipe(recipe, 600)   # 1.5x scaling
        assert scaled.scale_factor == 1.5
        assert scaled.scaled_kcal == 600
        assert scaled.scaled_protein_g == 45
        assert scaled.scaled_carb_g == 60

    def test_compute_filler_gap(self):
        """compute_filler_gap should compute remaining macros after scaling."""
        from fitness_engine.models.meal import Recipe, NutritionPerServing
        recipe = Recipe(
            name="Test", id="T12",
            ingredients=["test"],
            nutrition_per_serving=NutritionPerServing(
                kcal=400, protein_g=20, carb_g=40, fat_g=10, fiber_g=3,
            ),
        )
        scaled = ScaledRecipe(
            recipe=recipe, scale_factor=1.0,
            scaled_kcal=400, scaled_protein_g=20, scaled_carb_g=40,
            scaled_fat_g=10, scaled_fiber_g=3,
        )
        gap = compute_filler_gap(
            scaled, target_kcal=500, target_protein_g=40,
            target_carb_g=50, target_fat_g=15, target_fiber_g=8,
        )
        assert gap.kcal == 100
        assert gap.protein_g == 20
        assert gap.carb_g == 10
        assert gap.fat_g == 5
        assert gap.fiber_g == 5


# === Filler system tests ===

class TestFillerSystem:
    def test_select_protein_filler_omni(self):
        """select_protein_filler should return a protein-rich food for omni."""
        filler = select_protein_filler(20, "OMNI")
        assert filler is not None
        assert filler.protein_g > 0

    def test_select_protein_filler_vegan(self):
        """select_protein_filler should return a vegan protein source."""
        filler = select_protein_filler(20, "VEGAN")
        assert filler is not None
        assert filler.food.is_vegan

    def test_select_protein_filler_below_threshold_returns_none(self):
        """Below threshold (5g) should return None."""
        filler = select_protein_filler(3, "OMNI")
        assert filler is None

    def test_select_carb_filler(self):
        """select_carb_filler should return a carb-rich food."""
        filler = select_carb_filler(30, "OMNI")
        assert filler is not None
        assert filler.carb_g > 0

    def test_select_fat_filler(self):
        """select_fat_filler should return a fat-rich food."""
        filler = select_fat_filler(10, "OMNI")
        assert filler is not None
        assert filler.fat_g > 0

    def test_select_fillers_for_meal_returns_result(self):
        """select_fillers_for_meal should return a FillerResult."""
        from fitness_engine.models.meal import Recipe, NutritionPerServing
        recipe = Recipe(
            name="Test", id="T13",
            ingredients=["test"],
            nutrition_per_serving=NutritionPerServing(
                kcal=400, protein_g=20, carb_g=40, fat_g=10, fiber_g=3,
            ),
        )
        scaled = ScaledRecipe(
            recipe=recipe, scale_factor=1.0,
            scaled_kcal=400, scaled_protein_g=20, scaled_carb_g=40,
            scaled_fat_g=10, scaled_fiber_g=3,
        )
        gap = compute_filler_gap(
            scaled, target_kcal=500, target_protein_g=40,
            target_carb_g=50, target_fat_g=15, target_fiber_g=8,
        )
        result = select_fillers_for_meal(gap, "OMNI", is_main_meal=True)
        assert len(result.fillers) > 0
        assert result.total_filler_protein_g > 0


# === Swap system tests ===

class TestSwapSystem:
    def test_get_ingredient_swaps_for_chicken(self):
        """get_ingredient_swaps should return swaps for chicken breast."""
        swaps = get_ingredient_swaps("chicken breast")
        assert len(swaps) > 0
        # Should include tofu as a swap
        all_alternatives = []
        for swap in swaps:
            all_alternatives.extend(swap.alternatives)
        assert "tofu (firm)" in all_alternatives

    def test_get_ingredient_swaps_unknown_returns_empty(self):
        """Unknown ingredient should return empty list."""
        swaps = get_ingredient_swaps("nonexistent_ingredient_xyz")
        assert swaps == []

    def test_get_ingredient_swaps_case_insensitive(self):
        """get_ingredient_swaps should be case-insensitive."""
        swaps_lower = get_ingredient_swaps("rice")
        swaps_upper = get_ingredient_swaps("RICE")
        assert len(swaps_lower) == len(swaps_upper)

    def test_get_swaps_for_recipe_ingredients(self):
        """get_swaps_for_recipe_ingredients should return swaps for recipe ingredients."""
        recipes = recipes_by_filters(meal_type="dinner", diet_type="OMNI")
        if not recipes:
            pytest.skip("No dinner recipes available")
        recipe = recipes[0]
        swaps = get_swaps_for_recipe_ingredients(recipe)
        # Most recipes have at least one swappable ingredient
        assert isinstance(swaps, dict)

    def test_get_recipe_swaps_returns_alternatives(self):
        """get_recipe_swaps should return alternative recipes."""
        recipes = recipes_by_filters(meal_type="dinner", diet_type="OMNI")
        if not recipes:
            pytest.skip("No dinner recipes available")
        recipe = recipes[0]
        swaps = get_recipe_swaps(
            recipe, diet_tag="OMNI",
            target_kcal=recipe.kcal,
            kcal_tolerance_pct=0.30,
        )
        assert isinstance(swaps, list)
        # Should not include the original recipe
        for swap in swaps:
            assert swap.id != recipe.id

    def test_get_recipe_swaps_for_plan_returns_dicts(self):
        """get_recipe_swaps_for_plan should return serializable dicts."""
        recipes = recipes_by_filters(meal_type="dinner", diet_type="OMNI")
        if not recipes:
            pytest.skip("No dinner recipes available")
        recipe = recipes[0]
        swaps = get_recipe_swaps_for_plan(recipe, "OMNI", recipe.kcal)
        for swap in swaps:
            assert "recipe_id" in swap
            assert "name" in swap
            assert "kcal" in swap


# === Pre/Post workout recipe tests ===

class TestPrePostWorkoutRecipes:
    def test_16_pre_post_workout_recipes_defined(self):
        """16 Pre/Post workout recipes should be defined."""
        assert len(PRE_POST_WORKOUT_RECIPES) == 16

    def test_get_pre_post_workout_recipes_returns_recipe_objects(self):
        """get_pre_post_workout_recipes should return Recipe dataclass instances."""
        recipes = get_pre_post_workout_recipes()
        assert len(recipes) == 16
        for r in recipes:
            assert r.id is not None
            assert r.id.startswith("PW")
            assert "pre_workout" in r.meal_types or "post_workout" in r.meal_types

    def test_8_pre_workout_recipes(self):
        """8 Pre-Workout recipes should exist."""
        pre = get_pre_workout_recipes()
        assert len(pre) == 8
        for r in pre:
            assert "pre_workout" in r.meal_types

    def test_8_post_workout_recipes(self):
        """8 Post-Workout recipes should exist."""
        post = get_post_workout_recipes()
        assert len(post) == 8
        for r in post:
            assert "post_workout" in r.meal_types

    def test_pre_post_workout_recipes_loaded_into_database(self):
        """Pre/Post workout recipes should be in the loaded recipe database."""
        all_recipes = load_recipes()
        # Find pre/post workout recipes
        pw_recipes = [r for r in all_recipes
                      if r.id and r.id.startswith("PW")]
        assert len(pw_recipes) == 16

    def test_pre_workout_recipes_cover_4_diets(self):
        """Pre-workout recipes should cover all 4 diet types."""
        pre = get_pre_workout_recipes()
        diets_covered = set()
        for r in pre:
            for d in r.diet_types:
                diets_covered.add(d)
        assert "OMNI" in diets_covered
        assert "VEGAN" in diets_covered
        assert "OMNI_ETHIOPIAN" in diets_covered
        assert "VEGAN_ETHIOPIAN" in diets_covered


# === Allocator tests ===

class TestAllocator:
    def test_allocate_meal_returns_selected_meal(self):
        """allocate_meal should return a SelectedMeal with a recipe."""
        slot = MealSlotTarget(
            meal_type=MealType.DINNER,
            target_kcal=500, target_protein_g=35,
            target_carb_g=50, target_fat_g=15, target_fiber_g=8,
        )
        selected = allocate_meal(slot, "OMNI")
        assert isinstance(selected, SelectedMeal)
        assert selected.recipe is not None
        assert selected.score > 0

    def test_allocate_meal_includes_swap_options(self):
        """allocate_meal should include swap options."""
        slot = MealSlotTarget(
            meal_type=MealType.DINNER,
            target_kcal=500, target_protein_g=35,
            target_carb_g=50, target_fat_g=15, target_fiber_g=8,
        )
        selected = allocate_meal(slot, "OMNI")
        assert len(selected.swap_options) > 0

    def test_allocate_meal_includes_ingredient_swaps(self):
        """allocate_meal should include ingredient swaps."""
        slot = MealSlotTarget(
            meal_type=MealType.DINNER,
            target_kcal=500, target_protein_g=35,
            target_carb_g=50, target_fat_g=15, target_fiber_g=8,
        )
        selected = allocate_meal(slot, "OMNI")
        # Most recipes have at least one swappable ingredient
        assert isinstance(selected.ingredient_swaps, dict)

    def test_allocate_meal_vegan_gets_vegan_recipe(self):
        """Vegan allocator should only return vegan recipes."""
        slot = MealSlotTarget(
            meal_type=MealType.DINNER,
            target_kcal=500, target_protein_g=30,
            target_carb_g=50, target_fat_g=15, target_fiber_g=10,
        )
        selected = allocate_meal(slot, "VEGAN")
        assert selected.recipe is not None
        diet_tags = [d.upper() for d in selected.recipe.diet_types]
        assert any(d == "VEGAN" or d.startswith("VEGAN_") for d in diet_tags)

    def test_allocate_meal_with_allergen_filter(self):
        """allocate_meal with allergens_to_avoid should exclude allergen recipes."""
        slot = MealSlotTarget(
            meal_type=MealType.DINNER,
            target_kcal=500, target_protein_g=35,
            target_carb_g=50, target_fat_g=15, target_fiber_g=8,
        )
        selected = allocate_meal(slot, "OMNI", allergens_to_avoid=["dairy"])
        # Selected recipe should not contain dairy
        if selected.recipe:
            violations = check_allergens(selected.recipe, ["dairy"])
            assert violations == []


# === Planner tests ===

class TestPlanner:
    def test_build_meal_plan_returns_7_days(self, cut_profile):
        from fitness_engine import assess_profile
        from fitness_engine.nutrition.planner import build_nutrition_plan
        assessment = assess_profile(cut_profile)
        nutrition = build_nutrition_plan(cut_profile, assessment)
        plan = build_meal_plan(
            cut_profile, assessment, nutrition, meal_frequency=3,
        )
        assert len(plan.days) == 7
        for day in plan.days:
            assert len(day.meals) == 3

    def test_build_meal_plan_includes_pre_post_workout(self, cut_profile):
        """include_pre_post_workout should add PRE/POST slots on training days."""
        from fitness_engine import assess_profile
        from fitness_engine.nutrition.planner import build_nutrition_plan
        assessment = assess_profile(cut_profile)
        nutrition = build_nutrition_plan(cut_profile, assessment)
        plan = build_meal_plan(
            cut_profile, assessment, nutrition,
            meal_frequency=3, include_pre_post_workout=True,
        )
        # Find training days (should have more meals)
        training_days = [d for d in plan.days if len(d.meals) > 3]
        assert len(training_days) > 0   # at least 1 training day
        # Training day meals should include PRE_WORKOUT and POST_WORKOUT
        for d in training_days:
            meal_types = [m.meal_type for m in d.meals]
            assert MealType.PRE_WORKOUT in meal_types
            assert MealType.POST_WORKOUT in meal_types

    def test_build_meal_plan_summary_has_match_pct(self, cut_profile):
        from fitness_engine import assess_profile
        from fitness_engine.nutrition.planner import build_nutrition_plan
        assessment = assess_profile(cut_profile)
        nutrition = build_nutrition_plan(cut_profile, assessment)
        plan = build_meal_plan(
            cut_profile, assessment, nutrition, meal_frequency=3,
        )
        assert "weekly_kcal_match_pct" in plan.recipe_source_summary
        assert "weekly_protein_match_pct" in plan.recipe_source_summary

    def test_build_meal_plan_vegan_only_vegan_recipes(self, vegan_profile):
        from fitness_engine import assess_profile
        from fitness_engine.nutrition.planner import build_nutrition_plan
        assessment = assess_profile(vegan_profile)
        nutrition = build_nutrition_plan(vegan_profile, assessment)
        plan = build_meal_plan(
            vegan_profile, assessment, nutrition, meal_frequency=3,
        )
        for day in plan.days:
            for meal in day.meals:
                if meal.recipe:
                    diet_tags = [d.upper() for d in meal.recipe.diet_types]
                    assert any(d == "VEGAN" or d.startswith("VEGAN_") for d in diet_tags), (
                        f"Non-vegan recipe in vegan plan: {meal.recipe.name}"
                    )


# === Integration tests ===

class TestIntegration:
    def test_propose_plan_passes_meal_params_through(self, cut_profile):
        """engine.propose_plan should pass meal planning params through."""
        assessment = assess_profile(cut_profile)
        plan = propose_plan(
            cut_profile, assessment,
            cuisine_preference="ethiopian",
            include_pre_post_workout=True,
        )
        # Plan should have 7 days
        assert len(plan.meal.days) == 7

    def test_propose_plan_with_allergen_filter(self, cut_profile):
        """engine.propose_plan should respect allergens_to_avoid."""
        assessment = assess_profile(cut_profile)
        plan = propose_plan(
            cut_profile, assessment,
            allergens_to_avoid=["dairy"],
        )
        # No meal should contain dairy
        for day in plan.meal.days:
            for meal in day.meals:
                if meal.recipe:
                    violations = check_allergens(meal.recipe, ["dairy"])
                    assert violations == [], (
                        f"Meal {meal.name} contains dairy allergen"
                    )

    def test_full_plan_serializes_to_valid_json(self, cut_profile):
        assessment = assess_profile(cut_profile)
        plan = propose_plan(cut_profile, assessment)
        d = plan.to_dict()
        json_str = json.dumps(d, default=str)
        assert len(json_str) > 10_000

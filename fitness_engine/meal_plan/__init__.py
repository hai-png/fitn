"""
Meal plan module — Phase-5 clean implementation.

Public API:
  - build_meal_plan(profile, assessment, nutrition, meal_frequency?, ...)
  - compute_meal_plan_requirements(profile, assessment, nutrition, ...)
  - allocate_meal(slot, diet_tag, ...) → SelectedMeal
  - score_recipe_for_slot(recipe, slot, diet_tag, ...) → RecipeScore
  - get_recipe_swaps(recipe, diet_tag, target_kcal) → list[Recipe]
  - get_ingredient_swaps(ingredient) → list[IngredientSwap]

Phase-5 modules:
  - profile_requirements: computes per-slot nutritional targets
  - recipe_scorer: best-fit scoring algorithm (0-100 scale)
  - recipe_scaler: acceptable scaling (0.7x-1.5x) + filler system
  - swap_system: recipe swaps + ingredient swaps
  - pre_post_workout: 16 engine-generated Pre/Post workout recipes
  - allocator_v2: clean slot allocator (replaces legacy allocator)
  - planner_v2: clean 7-day orchestrator (replaces legacy planner)
"""
from .food_database import (
    FOODS, FOOD_INDEX,
    get_food, foods_by_category, high_protein_foods, protein_per_100kcal,
)
from .recipe_loader import (
    load_recipes, get_recipe_by_id, get_recipe_by_name,
    swap_groups, recipes_in_swap_group,
    recipes_by_meal_type, recipes_by_diet_type, recipes_by_cuisine,
    recipes_by_goal_fit, recipes_by_kcal_range, recipes_by_filters,
    database_stats,
)
from .meal_templates import (
    MEAL_ALLOCATIONS, MEAL_ORDER, MEAL_NAMES,
    get_meal_allocation, get_meal_plan_template, get_meal_name,
)
# Phase-5: legacy allocator kept for backward compat
from .allocator import (
    DEFAULT_MEAL_FREQUENCY, KCAL_TOLERANCE_PCT,
    allocate_macros_per_meal, select_recipe_for_meal, select_foods_for_meal,
)
# Phase-5: new clean allocator + planner
from .allocator_v2 import (
    SelectedMeal, allocate_meal, selected_meal_to_dict,
)
from .planner_v2 import build_meal_plan as build_meal_plan_v2
from .planner import build_meal_plan
# Phase-5: new modules
from .profile_requirements import (
    MealSlotTarget, MealPlanRequirements,
    compute_meal_plan_requirements,
    compute_pre_workout_target, compute_post_workout_target,
    get_meal_allocation as get_meal_allocation_v2,
    get_recipe_diet_tag,
    STANDARD_ALLOCATIONS,
)
from .recipe_scorer import (
    RecipeScore, score_recipe_for_slot, score_candidates,
    WEIGHTS, MIN_ACCEPTABLE_SCORE,
    score_kcal_match, score_protein_match, score_carb_match,
    score_fat_match, score_fiber_match, score_diet_match,
    score_goal_fit, score_variety, score_cuisine,
    check_allergens, check_excluded_ingredients,
    ALLERGEN_KEYWORDS,
)
from .recipe_scaler import (
    ScaledRecipe, FillerGap, FillerResult,
    compute_scale_factor, scale_recipe,
    compute_filler_gap, select_fillers_for_meal,
    select_protein_filler, select_carb_filler,
    select_fat_filler, select_veg_filler,
    MIN_SCALE, MAX_SCALE, FILLER_THRESHOLDS,
    PROTEIN_FILLERS, CARB_FILLERS, FAT_FILLERS, VEG_FILLERS,
)
from .swap_system import (
    IngredientSwap, INGREDIENT_SWAPS,
    get_ingredient_swaps, get_swaps_for_recipe_ingredients,
    get_recipe_swaps, get_recipe_swaps_for_plan,
)
from .pre_post_workout import (
    PRE_POST_WORKOUT_RECIPES,
    get_pre_post_workout_recipes,
    get_pre_workout_recipes,
    get_post_workout_recipes,
)

__all__ = [
    # Food database (Phase-1 fallback for fillers)
    "FOODS", "FOOD_INDEX",
    "get_food", "foods_by_category", "high_protein_foods", "protein_per_100kcal",
    # Recipe loader
    "load_recipes", "get_recipe_by_id", "get_recipe_by_name",
    "swap_groups", "recipes_in_swap_group",
    "recipes_by_meal_type", "recipes_by_diet_type", "recipes_by_cuisine",
    "recipes_by_goal_fit", "recipes_by_kcal_range", "recipes_by_filters",
    "database_stats",
    # Templates (legacy)
    "MEAL_ALLOCATIONS", "MEAL_ORDER", "MEAL_NAMES",
    "get_meal_allocation", "get_meal_plan_template", "get_meal_name",
    # Legacy allocator (backward compat)
    "DEFAULT_MEAL_FREQUENCY", "KCAL_TOLERANCE_PCT",
    "allocate_macros_per_meal", "select_recipe_for_meal", "select_foods_for_meal",
    # Phase-5: new allocator + planner
    "SelectedMeal", "allocate_meal", "selected_meal_to_dict",
    "build_meal_plan_v2",
    "build_meal_plan",
    # Phase-5: profile requirements
    "MealSlotTarget", "MealPlanRequirements",
    "compute_meal_plan_requirements",
    "compute_pre_workout_target", "compute_post_workout_target",
    "get_recipe_diet_tag",
    "STANDARD_ALLOCATIONS",
    # Phase-5: recipe scorer
    "RecipeScore", "score_recipe_for_slot", "score_candidates",
    "WEIGHTS", "MIN_ACCEPTABLE_SCORE",
    "score_kcal_match", "score_protein_match", "score_carb_match",
    "score_fat_match", "score_fiber_match", "score_diet_match",
    "score_goal_fit", "score_variety", "score_cuisine",
    "check_allergens", "check_excluded_ingredients",
    "ALLERGEN_KEYWORDS",
    # Phase-5: recipe scaler + fillers
    "ScaledRecipe", "FillerGap", "FillerResult",
    "compute_scale_factor", "scale_recipe",
    "compute_filler_gap", "select_fillers_for_meal",
    "select_protein_filler", "select_carb_filler",
    "select_fat_filler", "select_veg_filler",
    "MIN_SCALE", "MAX_SCALE", "FILLER_THRESHOLDS",
    "PROTEIN_FILLERS", "CARB_FILLERS", "FAT_FILLERS", "VEG_FILLERS",
    # Phase-5: swap system
    "IngredientSwap", "INGREDIENT_SWAPS",
    "get_ingredient_swaps", "get_swaps_for_recipe_ingredients",
    "get_recipe_swaps", "get_recipe_swaps_for_plan",
    # Phase-5: Pre/Post workout
    "PRE_POST_WORKOUT_RECIPES",
    "get_pre_post_workout_recipes",
    "get_pre_workout_recipes",
    "get_post_workout_recipes",
]

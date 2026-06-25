"""
Meal plan module — clean implementation.

Public API:
  - build_meal_plan(profile, assessment, nutrition, ...) → MealPlan
  - compute_meal_plan_requirements(profile, assessment, nutrition, ...) → MealPlanRequirements
  - allocate_meal(slot, diet_tag, ...) → SelectedMeal
  - score_recipe_for_slot(recipe, slot, diet_tag, ...) → RecipeScore
  - get_recipe_swaps(recipe, diet_tag, target_kcal) → list[Recipe]
  - get_ingredient_swaps(ingredient) → list[IngredientSwap]

Modules:
  - profile_requirements: computes per-slot nutritional targets
  - recipe_scorer: best-fit scoring (10 components, 0-100 scale)
  - recipe_scaler: acceptable scaling (0.7x-1.5x) + filler system
  - swap_system: recipe swaps + ingredient swaps
  - pre_post_workout: 16 engine-generated Pre/Post workout recipes
  - allocator: single-slot allocator (recipe + scaling + fillers)
  - planner: 7-day orchestrator
  - recipe_loader: loads curated + uncurated + Pre/Post workout recipes
  - food_database: raw foods (used for fillers)
  - meal_templates: meal frequency templates + macro allocations
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
    # Tier 3.41 fix: removed `get_meal_allocation` from this import — it was
    # imported from BOTH meal_templates AND profile_requirements, with the
    # profile_requirements version (which has the richer signature) winning.
    # Phase-6 cleanup: the meal_templates version has now been deleted entirely
    # (Batch 6). Only the profile_requirements version is exported.
    get_meal_plan_template, get_meal_name,
)
# Allocator + planner (clean implementation)
from .allocator import (
    SelectedMeal, allocate_meal, selected_meal_to_dict,
)
from .planner import build_meal_plan
# Profile requirements
from .profile_requirements import (
    MealSlotTarget, MealPlanRequirements,
    compute_meal_plan_requirements,
    compute_pre_workout_target, compute_post_workout_target,
    get_recipe_diet_tag,
    STANDARD_ALLOCATIONS,
)
# Recipe scorer
from .recipe_scorer import (
    RecipeScore, score_recipe_for_slot, score_candidates,
    WEIGHTS, MIN_ACCEPTABLE_SCORE,
    score_kcal_match, score_protein_match, score_carb_match,
    score_fat_match, score_fiber_match, score_diet_match,
    score_goal_fit, score_variety, score_cuisine,
    check_allergens, check_excluded_ingredients,
    ALLERGEN_KEYWORDS,
)
# Recipe scaler + fillers
from .recipe_scaler import (
    ScaledRecipe, FillerGap, FillerResult,
    compute_scale_factor, scale_recipe,
    compute_filler_gap, select_fillers_for_meal,
    select_protein_filler, select_carb_filler,
    select_fat_filler, select_veg_filler,
    MIN_SCALE, MAX_SCALE, FILLER_THRESHOLDS,
    PROTEIN_FILLERS, CARB_FILLERS, FAT_FILLERS, VEG_FILLERS,
)
# Swap system
from .swap_system import (
    IngredientSwap, INGREDIENT_SWAPS,
    get_ingredient_swaps, get_swaps_for_recipe_ingredients,
    get_recipe_swaps, get_recipe_swaps_for_plan,
)
# Pre/Post workout recipes
from .pre_post_workout import (
    PRE_POST_WORKOUT_RECIPES,
    get_pre_post_workout_recipes,
    get_pre_workout_recipes,
    get_post_workout_recipes,
)

__all__ = [
    # Food database (for fillers)
    "FOODS", "FOOD_INDEX",
    "get_food", "foods_by_category", "high_protein_foods", "protein_per_100kcal",
    # Recipe loader
    "load_recipes", "get_recipe_by_id", "get_recipe_by_name",
    "swap_groups", "recipes_in_swap_group",
    "recipes_by_meal_type", "recipes_by_diet_type", "recipes_by_cuisine",
    "recipes_by_goal_fit", "recipes_by_kcal_range", "recipes_by_filters",
    "database_stats",
    # Templates
    "MEAL_ALLOCATIONS", "MEAL_ORDER", "MEAL_NAMES",
    # Phase-6 cleanup: removed ``get_meal_allocation`` from __all__ — the
    # meal_templates version was deleted; the canonical version is exported
    # under the "Profile requirements" section below.
    "get_meal_plan_template", "get_meal_name",
    # Allocator + planner
    "SelectedMeal", "allocate_meal", "selected_meal_to_dict",
    "build_meal_plan",
    # Profile requirements
    "MealSlotTarget", "MealPlanRequirements",
    "compute_meal_plan_requirements",
    "compute_pre_workout_target", "compute_post_workout_target",
    "get_recipe_diet_tag",
    "STANDARD_ALLOCATIONS",
    # Recipe scorer
    "RecipeScore", "score_recipe_for_slot", "score_candidates",
    "WEIGHTS", "MIN_ACCEPTABLE_SCORE",
    "score_kcal_match", "score_protein_match", "score_carb_match",
    "score_fat_match", "score_fiber_match", "score_diet_match",
    "score_goal_fit", "score_variety", "score_cuisine",
    "check_allergens", "check_excluded_ingredients",
    "ALLERGEN_KEYWORDS",
    # Recipe scaler + fillers
    "ScaledRecipe", "FillerGap", "FillerResult",
    "compute_scale_factor", "scale_recipe",
    "compute_filler_gap", "select_fillers_for_meal",
    "select_protein_filler", "select_carb_filler",
    "select_fat_filler", "select_veg_filler",
    "MIN_SCALE", "MAX_SCALE", "FILLER_THRESHOLDS",
    "PROTEIN_FILLERS", "CARB_FILLERS", "FAT_FILLERS", "VEG_FILLERS",
    # Swap system
    "IngredientSwap", "INGREDIENT_SWAPS",
    "get_ingredient_swaps", "get_swaps_for_recipe_ingredients",
    "get_recipe_swaps", "get_recipe_swaps_for_plan",
    # Pre/Post workout
    "PRE_POST_WORKOUT_RECIPES",
    "get_pre_post_workout_recipes",
    "get_pre_workout_recipes",
    "get_post_workout_recipes",
]

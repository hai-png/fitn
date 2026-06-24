"""Meal plan module — recipe loader, food database, meal templates, allocator, planner."""
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
from .allocator import (
    DEFAULT_MEAL_FREQUENCY, KCAL_TOLERANCE_PCT,
    allocate_macros_per_meal, select_recipe_for_meal, select_foods_for_meal,
)
from .planner import build_meal_plan

__all__ = [
    # Food database (Phase-1 fallback)
    "FOODS", "FOOD_INDEX",
    "get_food", "foods_by_category", "high_protein_foods", "protein_per_100kcal",
    # Recipe loader (Phase-2)
    "load_recipes", "get_recipe_by_id", "get_recipe_by_name",
    "swap_groups", "recipes_in_swap_group",
    "recipes_by_meal_type", "recipes_by_diet_type", "recipes_by_cuisine",
    "recipes_by_goal_fit", "recipes_by_kcal_range", "recipes_by_filters",
    "database_stats",
    # Templates
    "MEAL_ALLOCATIONS", "MEAL_ORDER", "MEAL_NAMES",
    "get_meal_allocation", "get_meal_plan_template", "get_meal_name",
    # Allocator
    "DEFAULT_MEAL_FREQUENCY", "KCAL_TOLERANCE_PCT",
    "allocate_macros_per_meal", "select_recipe_for_meal", "select_foods_for_meal",
    # Planner
    "build_meal_plan",
]

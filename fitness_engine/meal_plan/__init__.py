"""Meal plan module — food database, meal templates, allocator, planner."""
from .food_database import (
    FOODS, FOOD_INDEX,
    get_food, foods_by_category, high_protein_foods, protein_per_100kcal,
)
from .meal_templates import (
    MEAL_ALLOCATIONS, MEAL_ORDER, MEAL_NAMES,
    get_meal_allocation, get_meal_plan_template, get_meal_name,
)
from .allocator import (
    DEFAULT_MEAL_FREQUENCY,
    allocate_macros_per_meal, select_foods_for_meal,
)
from .planner import build_meal_plan

__all__ = [
    # Food database
    "FOODS", "FOOD_INDEX",
    "get_food", "foods_by_category", "high_protein_foods", "protein_per_100kcal",
    # Templates
    "MEAL_ALLOCATIONS", "MEAL_ORDER", "MEAL_NAMES",
    "get_meal_allocation", "get_meal_plan_template", "get_meal_name",
    # Allocator
    "DEFAULT_MEAL_FREQUENCY",
    "allocate_macros_per_meal", "select_foods_for_meal",
    # Planner
    "build_meal_plan",
]

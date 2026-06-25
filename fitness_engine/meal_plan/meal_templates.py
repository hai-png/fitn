"""
Meal templates and macro allocation per meal.

Phase-1 framework: ships with default meal-frequency templates and macro
allocation percentages. The user will supply detailed meal resources later.
"""
from __future__ import annotations

from ..models.meal import MealType
# Phase-6 cleanup: ``MEAL_ALLOCATIONS`` was byte-identical to
# ``STANDARD_ALLOCATIONS`` in ``profile_requirements``. Deduplicated to a
# single source of truth; this alias preserves the legacy public name.
from .profile_requirements import STANDARD_ALLOCATIONS as MEAL_ALLOCATIONS


# === Macro allocation per meal (% of daily calories per meal) ===
# (formerly defined inline here — see STANDARD_ALLOCATIONS in
# profile_requirements for the canonical definition.)

# For 5 meals, we add a second snack labeled as SNACK too — we'll handle
# this in the allocator by splitting the snack allocation evenly.
MEAL_ORDER = [
    MealType.BREAKFAST, MealType.SNACK, MealType.LUNCH,
    MealType.SNACK, MealType.DINNER,
]


# Phase-6 cleanup: removed the local ``get_meal_allocation(meal_frequency)``
# function — it was superseded by the richer-signature
# ``profile_requirements.get_meal_allocation(meal_frequency,
# include_pre_post_workout=False, is_training_day=False)``. The 1-arg form
# is no longer needed (callers should use the canonical version).


def get_meal_plan_template(meal_frequency: int) -> list[MealType]:
    """
    Get the ordered list of meal types for a day based on frequency.
    """
    if meal_frequency == 2:
        return [MealType.LUNCH, MealType.DINNER]
    elif meal_frequency == 3:
        return [MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER]
    elif meal_frequency == 4:
        return [MealType.BREAKFAST, MealType.LUNCH, MealType.SNACK, MealType.DINNER]
    elif meal_frequency == 5:
        return [MealType.BREAKFAST, MealType.SNACK, MealType.LUNCH,
                MealType.SNACK, MealType.DINNER]
    else:
        return [MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER]


# === Default meal name templates ===
MEAL_NAMES = {
    MealType.BREAKFAST: {
        "default": "Breakfast",
        "options": ["Greek Yogurt Parfait", "Oatmeal Power Bowl",
                    "Egg & Avocado Toast", "Protein Smoothie",
                    "Veggie Omelette", "Banana & PB Oats",
                    "Cottage Cheese Bowl"],
    },
    MealType.LUNCH: {
        "default": "Lunch",
        "options": ["Grilled Chicken Salad", "Turkey & Rice Bowl",
                    "Tuna Salad Wrap", "Salmon & Quinoa",
                    "Chicken Burrito Bowl", "Steak & Sweet Potato",
                    "Lentil Power Bowl"],
    },
    MealType.DINNER: {
        "default": "Dinner",
        "options": ["Salmon & Asparagus", "Steak & Veggies",
                    "Chicken & Broccoli", "Shrimp Stir-Fry",
                    "Cod & Sweet Potato", "Pork & Green Beans",
                    "Turkey Meatballs & Pasta"],
    },
    MealType.SNACK: {
        "default": "Snack",
        "options": ["Whey Shake & Banana", "Greek Yogurt & Berries",
                    "Apple & Almonds", "Cottage Cheese & Pear",
                    "Protein Bar & Apple", "Edamame Bowl",
                    "Boiled Eggs & Carrots"],
    },
    MealType.PRE_WORKOUT: {
        "default": "Pre-Workout",
        "options": ["Banana & Whey", "Oats & Whey", "Rice Cake & PB"],
    },
    MealType.POST_WORKOUT: {
        "default": "Post-Workout",
        "options": ["Whey & Banana", "Chicken & Rice", "Greek Yogurt & Berries"],
    },
}


def get_meal_name(meal_type: MealType, day: int = 1) -> str:
    """Get a meal name from the template, varying by day for 7-day rotation."""
    options = MEAL_NAMES.get(meal_type, {}).get("options", [meal_type.value])
    return options[(day - 1) % len(options)]


__all__ = [
    "MEAL_ALLOCATIONS", "MEAL_ORDER", "MEAL_NAMES",
    # Phase-6 cleanup: removed ``get_meal_allocation`` from __all__ — callers
    # should import the canonical version from profile_requirements.
    "get_meal_plan_template", "get_meal_name",
]

"""
Meal plan allocator — distributes daily macros across meals and selects
foods to hit per-meal targets.

Phase-1: simple greedy allocator that hits protein first, then carbs,
then fat. Future versions will use more sophisticated optimization
(LP / constraint solving) once detailed food database is loaded.
"""
from __future__ import annotations

from ..models.nutrition import MacroSplit
from ..models.meal import (
    Meal, MealFood, MealType, DayPlan, FoodItem, FoodCategory,
)
from .food_database import FOODS, get_food, foods_by_category, high_protein_foods
from .meal_templates import (
    get_meal_allocation, get_meal_plan_template, get_meal_name,
)


# Default meal frequency if user doesn't specify
DEFAULT_MEAL_FREQUENCY = 3


def allocate_macros_per_meal(
    macros: MacroSplit,
    meal_frequency: int,
) -> dict[MealType, dict[str, float]]:
    """
    Split daily macros into per-meal targets based on meal frequency.

    Returns dict: {meal_type: {kcal, protein_g, carb_g, fat_g}}
    """
    allocation = get_meal_allocation(meal_frequency)
    # Handle 5-meal case where SNACK appears twice
    if meal_frequency == 5:
        # Two snacks each get half the snack allocation
        snack_pct = allocation[MealType.SNACK] / 2
        # First call: BREAKFAST + SNACK(1) + LUNCH + SNACK(2) + DINNER
        meal_plan = get_meal_plan_template(5)
        result = {}
        snack_count = 0
        for mt in meal_plan:
            if mt == MealType.SNACK:
                snack_count += 1
                pct = snack_pct
                result[f"{mt.value}_{snack_count}"] = _alloc(macros, pct)
            else:
                pct = allocation[mt]
                result[mt.value] = _alloc(macros, pct)
        return result

    # Standard case
    return {
        mt.value: _alloc(macros, pct)
        for mt, pct in allocation.items()
    }


def _alloc(macros: MacroSplit, pct: float) -> dict[str, float]:
    """Allocate a fraction of daily macros."""
    return {
        "kcal": macros.protein_kcal * pct + macros.fat_kcal * pct + macros.carb_kcal * pct,
        "protein_g": macros.protein_g * pct,
        "carb_g": macros.carb_g * pct,
        "fat_g": macros.fat_g * pct,
    }


# === Food selection for a single meal ===

def select_foods_for_meal(
    meal_type: MealType,
    protein_target_g: float,
    carb_target_g: float,
    fat_target_g: float,
    kcal_target: float,
    day: int = 1,
) -> list[MealFood]:
    """
    Select foods to approximately hit per-meal macro targets.

    Strategy (greedy):
      1. Pick a primary protein source (~80% of protein target)
      2. Pick a primary carb source (~60% of carb target)
      3. Pick a primary fat source (~50% of fat target)
      4. Add a vegetable (free — low calorie, fills volume)
      5. If still under protein, add whey/egg whites
      6. If still under carb, add fruit

    This is a simple framework — Phase-2 will replace with optimization.
    """
    meal_foods: list[MealFood] = []

    # Protein rotation by day
    protein_options_by_meal = {
        MealType.BREAKFAST: [
            "Greek Yogurt (non-fat, plain)",
            "Egg White (large)", "Whole Egg (large)",
            "Cottage Cheese (low-fat, 2%)",
            "Whey Protein Powder",
        ],
        MealType.LUNCH: [
            "Chicken Breast (skinless, boneless, raw)",
            "Tuna (light, water-packed, drained)",
            "Turkey Breast (skinless, raw)",
            "Salmon (Atlantic, raw)",
        ],
        MealType.DINNER: [
            "Chicken Breast (skinless, boneless, raw)",
            "Salmon (Atlantic, raw)",
            "Steak (Sirloin, raw)",
            "Cod (raw)",
            "Shrimp (raw)",
            "Pork Loin (raw)",
        ],
        MealType.SNACK: [
            "Whey Protein Powder",
            "Greek Yogurt (non-fat, plain)",
            "Cottage Cheese (low-fat, 2%)",
        ],
    }
    carb_options_by_meal = {
        MealType.BREAKFAST: [
            "Oats (rolled, dry)", "Banana", "Whole Wheat Bread",
        ],
        MealType.LUNCH: [
            "White Rice (cooked)", "Brown Rice (cooked)",
            "Quinoa (cooked)", "Sweet Potato (raw)",
        ],
        MealType.DINNER: [
            "White Rice (cooked)", "Brown Rice (cooked)",
            "Sweet Potato (raw)", "Potato (white, raw)",
            "Quinoa (cooked)", "Pasta (cooked)",
        ],
        MealType.SNACK: [
            "Banana", "Apple", "Blueberries", "Whole Wheat Bread",
        ],
    }
    fat_options_by_meal = {
        MealType.BREAKFAST: [
            "Avocado (raw)", "Almonds (raw)", "Peanut Butter (natural)",
        ],
        MealType.LUNCH: [
            "Olive Oil", "Avocado (raw)", "Almonds (raw)",
        ],
        MealType.DINNER: [
            "Olive Oil", "Avocado (raw)", "Walnuts (raw)",
        ],
        MealType.SNACK: [
            "Almonds (raw)", "Peanut Butter (natural)", "Walnuts (raw)",
        ],
    }
    veg_options = [
        "Broccoli (raw)", "Spinach (raw)", "Mixed Salad Greens",
        "Bell Pepper (raw)", "Asparagus (raw)", "Green Beans (raw)",
        "Carrots (raw)", "Mushrooms (raw)",
    ]

    # Pick protein
    protein_options = protein_options_by_meal.get(meal_type, ["Chicken Breast (skinless, boneless, raw)"])
    protein_name = protein_options[(day - 1) % len(protein_options)]
    protein_food = get_food(protein_name)
    if protein_food:
        # Compute grams needed to hit ~80% of protein target
        grams = _grams_to_hit(protein_food, "protein", protein_target_g * 0.80)
        grams = max(grams, protein_food.serving_size_g * 0.7)  # at least 70% of a serving
        meal_foods.append(MealFood(food=protein_food, grams=round(grams, 0)))

    # Pick carb
    carb_options = carb_options_by_meal.get(meal_type, ["White Rice (cooked)"])
    carb_name = carb_options[(day - 1) % len(carb_options)]
    carb_food = get_food(carb_name)
    if carb_food:
        grams = _grams_to_hit(carb_food, "carb", carb_target_g * 0.60)
        grams = max(grams, carb_food.serving_size_g * 0.7)
        meal_foods.append(MealFood(food=carb_food, grams=round(grams, 0)))

    # Pick fat
    fat_options = fat_options_by_meal.get(meal_type, ["Olive Oil"])
    fat_name = fat_options[(day - 1) % len(fat_options)]
    fat_food = get_food(fat_name)
    if fat_food:
        grams = _grams_to_hit(fat_food, "fat", fat_target_g * 0.50)
        grams = max(grams, fat_food.serving_size_g * 0.5)
        meal_foods.append(MealFood(food=fat_food, grams=round(grams, 0)))

    # Add vegetable (free — don't count toward macro budget)
    veg_name = veg_options[(day - 1) % len(veg_options)]
    veg_food = get_food(veg_name)
    if veg_food and meal_type in (MealType.LUNCH, MealType.DINNER):
        meal_foods.append(MealFood(food=veg_food, grams=100))

    # If still under protein, add whey
    current_protein = sum(mf.protein_g for mf in meal_foods)
    if current_protein < protein_target_g * 0.90:
        deficit = protein_target_g - current_protein
        whey = get_food("Whey Protein Powder")
        if whey:
            grams = deficit / whey.protein_g_per_100g * 100
            grams = max(grams, 20)   # at least 20g whey
            meal_foods.append(MealFood(food=whey, grams=round(grams, 0)))

    return meal_foods


def _grams_to_hit(food: FoodItem, macro: str, target_g: float) -> float:
    """Compute grams of food needed to hit a macro target."""
    if macro == "protein":
        per_100g = food.protein_g_per_100g
    elif macro == "carb":
        per_100g = food.carb_g_per_100g
    elif macro == "fat":
        per_100g = food.fat_g_per_100g
    else:
        return 0

    if per_100g <= 0:
        return 0
    return target_g / per_100g * 100


__all__ = [
    "DEFAULT_MEAL_FREQUENCY",
    "allocate_macros_per_meal", "select_foods_for_meal", "_grams_to_hit",
]

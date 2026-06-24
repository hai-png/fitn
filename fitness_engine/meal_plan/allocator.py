"""
Meal plan allocator — Phase-2 recipe-based allocator.

Distributes daily macros across meals AND selects a real recipe for each
meal slot that approximately hits the per-meal macro targets.

Selection strategy:
  1. Compute per-meal macro targets (Phase-1 logic, unchanged).
  2. For each meal slot:
     a. Query curated recipes by meal_type + diet_type + kcal range.
     b. If curated has matches, pick by day-index rotation (variety).
     c. If no curated match, fall back to uncurated DB.
     d. If still no match, fall back to Phase-1 raw-foods allocator.
  3. Honor swap_groups when available (e.g. breakfast_vegan_266-316kcal
     returns [R011, R008] — rotate between them across days).
"""
from __future__ import annotations

from ..models.nutrition import MacroSplit
from ..models.meal import (
    Meal, MealFood, MealType, DayPlan, FoodItem, FoodCategory, Recipe,
)
from .food_database import FOODS, get_food, foods_by_category, high_protein_foods
from .meal_templates import (
    get_meal_allocation, get_meal_plan_template, get_meal_name,
)
from .recipe_loader import (
    load_recipes, get_recipe_by_id, recipes_by_filters, swap_groups,
)


# Default meal frequency if user doesn't specify
DEFAULT_MEAL_FREQUENCY = 3

# Kcal tolerance band — recipe kcal within ±this % of target is acceptable
KCAL_TOLERANCE_PCT = 0.40  # 40 % wide band (recipes are discrete)


def allocate_macros_per_meal(
    macros: MacroSplit,
    meal_frequency: int,
) -> dict[str, dict[str, float]]:
    """
    Split daily macros into per-meal targets based on meal frequency.

    Returns dict: {meal_key: {kcal, protein_g, carb_g, fat_g}}
    where meal_key is the MealType value (e.g. "breakfast") or
    "snack_1" / "snack_2" for the 5-meal case.
    """
    allocation = get_meal_allocation(meal_frequency)
    # Handle 5-meal case where SNACK appears twice
    if meal_frequency == 5:
        # Two snacks each get half the snack allocation
        snack_pct = allocation[MealType.SNACK] / 2
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


# === Recipe selection for a single meal ===

def _find_matching_swap_group(
    meal_type: MealType,
    target_kcal: float,
    diet_type: str = "OMNI",
) -> list[str] | None:
    """
    Find a swap_group whose key matches this meal slot.

    Swap group key format (examples from the DB):
      breakfast_vegan_266-316kcal
      breakfast_omni_ethiopian_200-210kcal
      dinner_vegan_500-530kcal
      lunch_vegan_ethiopian_135-136kcal
      breakfast_variety
      dinner_variety

    Matching priority:
      1. Exact meal_type + diet + kcal band
      2. meal_type + diet + "variety"
      3. meal_type + "variety" (ONLY for OMNI diet — never for VEGAN)

    For non-OMNI diets (vegan, vegetarian), we never fall back to a
    plain "meal_type_variety" group because it may contain non-vegan
    recipes. The caller's recipe filter (recipes_by_filters) handles
    diet_type filtering properly.
    """
    mt = meal_type.value.lower()
    diet = diet_type.lower()
    target_lo = target_kcal * (1 - KCAL_TOLERANCE_PCT)
    target_hi = target_kcal * (1 + KCAL_TOLERANCE_PCT)

    all_groups = swap_groups()

    # 1. Try kcal-banded groups first
    for key, recipe_ids in all_groups.items():
        if not key.startswith(mt):
            continue
        # Parse kcal range from key
        if "_kcal" in key or any(c.isdigit() for c in key.split("_")[-1]):
            # Extract kcal range like "266-316kcal"
            import re
            m = re.search(r"(\d+)-(\d+)kcal", key)
            if m:
                lo, hi = int(m.group(1)), int(m.group(2))
                # Check diet match (vegan matches both "vegan" and "vegan_ethiopian")
                if diet != "omni":
                    # For vegan, key must contain "vegan"
                    if diet not in key:
                        continue
                # Check kcal band overlaps target
                if lo <= target_hi and hi >= target_lo:
                    return list(recipe_ids)

    # 2. Try meal_type + diet + "variety"
    if diet == "vegan":
        # Vegan matches "breakfast_vegan_variety"
        for key, recipe_ids in all_groups.items():
            if key == f"{mt}_vegan_variety":
                return list(recipe_ids)
    elif diet == "omni":
        # Omni matches "breakfast_omni_variety" or "breakfast_variety"
        for candidate in (f"{mt}_omni_variety", f"{mt}_variety"):
            if candidate in all_groups:
                return list(all_groups[candidate])

    # 3. For OMNI only: try just meal_type + "variety"
    # (non-omni diets do NOT fall back here — the recipe filter handles it)
    if diet == "omni":
        plain_variety = f"{mt}_variety"
        if plain_variety in all_groups:
            return list(all_groups[plain_variety])

    return None


def _recipe_matches_diet(recipe: Recipe, diet_type: str) -> bool:
    """
    Check if a recipe is compatible with the given diet_type.

    For VEGAN/VEGETARIAN diets, also reject recipes flagged with
    [diet-warning] (curation errors where VEGAN-tagged recipes
    actually contain meat/dairy/egg).
    """
    dt = diet_type.upper()
    recipe_diets = [d.upper() for d in recipe.diet_types]
    if dt == "VEGAN":
        if not any(d == "VEGAN" or d.startswith("VEGAN_") for d in recipe_diets):
            return False
        # Reject recipes flagged with diet-warning
        if "[diet-warning" in (recipe.notes or ""):
            return False
        return True
    if dt == "OMNI":
        return any(
            d == "OMNI" or d.startswith("OMNI_")
            or d == "VEGAN" or d.startswith("VEGAN_")
            for d in recipe_diets
        )
    return dt in recipe_diets


def select_recipe_for_meal(
    meal_type: MealType,
    target_kcal: float,
    target_protein_g: float,
    target_carb_g: float,
    target_fat_g: float,
    day: int = 1,
    diet_type: str = "OMNI",
    goal_fit: str | None = None,
    cuisine: str | None = None,
    exclude_ids: set[str] | None = None,
    prefer_curated: bool = True,
) -> Recipe | None:
    """
    Select a recipe for a single meal slot.

    Tries (in order):
      1. Matching swap_group (rotated by day for variety)
      2. Curated recipes matching meal_type + diet + kcal range
      3. Uncurated recipes matching same filters
      4. Any recipe matching meal_type (kcal-agnostic)

    Returns None if no recipe found (caller should fall back to raw foods).
    """
    if exclude_ids is None:
        exclude_ids = set()

    # Compute kcal band
    kcal_lo = target_kcal * (1 - KCAL_TOLERANCE_PCT)
    kcal_hi = target_kcal * (1 + KCAL_TOLERANCE_PCT)

    # 1. Try swap_group
    swap_ids = _find_matching_swap_group(meal_type, target_kcal, diet_type)
    if swap_ids:
        # Filter out excluded IDs and verify diet match for each recipe
        valid_ids = []
        for rid in swap_ids:
            if rid in exclude_ids:
                continue
            r = get_recipe_by_id(rid)
            if r and _recipe_matches_diet(r, diet_type):
                valid_ids.append(rid)
        if valid_ids:
            # Rotate by day
            chosen_id = valid_ids[(day - 1) % len(valid_ids)]
            recipe = get_recipe_by_id(chosen_id)
            if recipe:
                return recipe

    # 2. Try curated recipes with full filter
    curated_candidates = recipes_by_filters(
        meal_type=meal_type.value,
        diet_type=diet_type,
        goal_fit=goal_fit,
        cuisine=cuisine,
        kcal_lo=kcal_lo,
        kcal_hi=kcal_hi,
        is_curated_only=prefer_curated,
        exclude_ids=exclude_ids,
    )
    if curated_candidates:
        # Sort by closeness to target kcal
        curated_candidates.sort(key=lambda r: abs(r.kcal - target_kcal))
        # Rotate by day among top 5
        top = curated_candidates[:5]
        return top[(day - 1) % len(top)]

    # 3. Fall back to uncurated
    uncurated_candidates = recipes_by_filters(
        meal_type=meal_type.value,
        diet_type=diet_type,
        goal_fit=goal_fit,
        cuisine=cuisine,
        kcal_lo=kcal_lo,
        kcal_hi=kcal_hi,
        exclude_ids=exclude_ids,
    )
    if uncurated_candidates:
        uncurated_candidates.sort(key=lambda r: abs(r.kcal - target_kcal))
        top = uncurated_candidates[:5]
        return top[(day - 1) % len(top)]

    # 4. Last resort: any recipe of this meal_type (ignore kcal)
    any_candidates = recipes_by_filters(
        meal_type=meal_type.value,
        diet_type=diet_type,
        exclude_ids=exclude_ids,
    )
    if any_candidates:
        any_candidates.sort(key=lambda r: abs(r.kcal - target_kcal))
        return any_candidates[(day - 1) % min(len(any_candidates), 7)]

    return None


# === Phase-1 raw-foods allocator (kept as fallback) ===

def select_foods_for_meal(
    meal_type: MealType,
    protein_target_g: float,
    carb_target_g: float,
    fat_target_g: float,
    kcal_target: float,
    day: int = 1,
) -> list[MealFood]:
    """
    Phase-1 fallback: select raw foods to hit per-meal macro targets.

    Used only when no recipe matches the meal slot.
    """
    meal_foods: list[MealFood] = []

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
        grams = _grams_to_hit(protein_food, "protein", protein_target_g * 0.80)
        grams = max(grams, protein_food.serving_size_g * 0.7)
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

    # Add vegetable (free)
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
            grams = max(grams, 20)
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
    "KCAL_TOLERANCE_PCT",
    "allocate_macros_per_meal",
    "select_recipe_for_meal",
    "select_foods_for_meal",
    "_grams_to_hit",
]

"""
Recipe scaler + filler system — Phase-5.

When a recipe is selected but doesn't perfectly hit the slot's macros,
this module:
  1. Scales the recipe to a serving multiplier (0.7x – 1.5x) to get closer
  2. Adds "fillers" (side dishes / supplements) to cover the remaining gap

Scaling rules:
  - Compute scaling factor = target_kcal / recipe_kcal
  - If factor in [0.7, 1.5], scale the recipe
  - If factor outside, skip scaling (recipe stays at 1.0x)
  - All macros scale linearly with the factor

Filler rules:
  - After scaling, compute remaining macro gap (target - scaled_recipe)
  - Add fillers to close the gap:
    * Protein filler (whey, greek yogurt, tofu, etc.)
    * Carb filler (rice, oats, banana, bread)
    * Fat filler (olive oil, nuts, avocado)
    * Veg filler (free — broccoli, spinach, etc.)
  - Each filler is a MealFood entry with computed grams
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..models.meal import (
    Recipe, MealFood, FoodItem, FoodCategory,
)
from .food_database import get_food


# === Scaling limits ===

MIN_SCALE = 0.7
MAX_SCALE = 1.5
# Phase-6: if the scaled kcal deviates from target by more than this fraction,
# the recipe is a poor fit and the caller should fall back to fillers-only.
# 40% allows MIN_SCALE=0.7 (30% under) and MAX_SCALE=1.5 (50% over) but flags
# extreme cases where the clamp is the only thing keeping the recipe in range.
SCALE_DEVIATION_LIMIT = 0.40


@dataclass
class ScaledRecipe:
    """A recipe with an applied serving multiplier."""
    recipe: Recipe
    scale_factor: float
    scaled_kcal: float
    scaled_protein_g: float
    scaled_carb_g: float
    scaled_fat_g: float
    scaled_fiber_g: float

    @property
    def servings_display(self) -> str:
        """Human-readable servings, e.g. '1.3 servings' or '0.8 serving'."""
        if self.scale_factor == 1.0:
            return "1 serving"
        return f"{self.scale_factor:.2f} servings"


def compute_scale_factor(recipe_kcal: float, target_kcal: float) -> float:
    """
    Compute the optimal scaling factor for a recipe to hit a target kcal.

    Returns a value in [MIN_SCALE, MAX_SCALE]. If the unscaled recipe is
    already close (within ±10%), returns 1.0 (no scaling).
    """
    if recipe_kcal <= 0:
        return 1.0

    raw_factor = target_kcal / recipe_kcal

    # If within ±10%, no need to scale
    if 0.9 <= raw_factor <= 1.1:
        return 1.0

    # Clamp to [MIN_SCALE, MAX_SCALE]
    return max(MIN_SCALE, min(MAX_SCALE, raw_factor))


def is_recipe_scalable_to_target(recipe_kcal: float, target_kcal: float) -> bool:
    """
    Phase-6: check whether a recipe can be scaled to within
    SCALE_DEVIATION_LIMIT of the target kcal.

    Used by the allocator to decide whether to skip a recipe and fall back
    to fillers-only (e.g. a 500-kcal recipe cannot satisfy a 100-kcal slot
    even at MIN_SCALE=0.7, which would produce 350 kcal — 250% over target).
    """
    if recipe_kcal <= 0 or target_kcal <= 0:
        return False
    factor = compute_scale_factor(recipe_kcal, target_kcal)
    scaled_kcal = recipe_kcal * factor
    deviation = abs(scaled_kcal - target_kcal) / target_kcal
    return deviation <= SCALE_DEVIATION_LIMIT


def scale_recipe(recipe: Recipe, target_kcal: float) -> ScaledRecipe:
    """
    Scale a recipe to better hit a target kcal.

    Returns ScaledRecipe with the applied factor + scaled macros.
    """
    factor = compute_scale_factor(recipe.kcal, target_kcal)

    return ScaledRecipe(
        recipe=recipe,
        scale_factor=round(factor, 3),
        scaled_kcal=recipe.kcal * factor,
        scaled_protein_g=recipe.protein_g * factor,
        scaled_carb_g=recipe.carb_g * factor,
        scaled_fat_g=recipe.fat_g * factor,
        scaled_fiber_g=recipe.fiber_g * factor,
    )


# === Filler system ===

@dataclass
class FillerGap:
    """Remaining macro gap after scaling a recipe."""
    kcal: float
    protein_g: float
    carb_g: float
    fat_g: float
    fiber_g: float


def compute_filler_gap(
    scaled: ScaledRecipe,
    target_kcal: float,
    target_protein_g: float,
    target_carb_g: float,
    target_fat_g: float,
    target_fiber_g: float,
) -> FillerGap:
    """Compute the remaining macro gap after scaling a recipe."""
    return FillerGap(
        kcal=max(0, target_kcal - scaled.scaled_kcal),
        protein_g=max(0, target_protein_g - scaled.scaled_protein_g),
        carb_g=max(0, target_carb_g - scaled.scaled_carb_g),
        fat_g=max(0, target_fat_g - scaled.scaled_fat_g),
        fiber_g=max(0, target_fiber_g - scaled.scaled_fiber_g),
    )


# === Filler thresholds ===
# Only add fillers if the gap exceeds these thresholds (avoid micro-fillers)

FILLER_THRESHOLDS = {
    "kcal": 50,        # don't add fillers for <50 kcal gap
    "protein_g": 5,    # don't add fillers for <5g protein gap
    "carb_g": 5,
    "fat_g": 3,
    "fiber_g": 3,
}


# === Filler food options ===
# Maps filler type → list of food names from food_database

PROTEIN_FILLERS = {
    "OMNI": [
        ("Whey Protein Powder", 1.0),       # (name, vegan_compatible_flag)
        ("Greek Yogurt (non-fat, plain)", 1.0),
        ("Egg White (large)", 1.0),
        ("Cottage Cheese (low-fat, 2%)", 1.0),
        ("Chicken Breast (skinless, boneless, raw)", 1.0),
    ],
    "VEGAN": [
        ("Tofu (firm)", 1.0),
        ("Tempeh", 1.0),
        ("Pea Protein Powder", 1.0),
        ("Soy Protein Powder", 1.0),
        ("Lentils (cooked)", 1.0),
    ],
}

CARB_FILLERS = [
    ("White Rice (cooked)", 1.0),
    ("Brown Rice (cooked)", 1.0),
    ("Oats (rolled, dry)", 1.0),
    ("Banana", 1.0),
    ("Whole Wheat Bread", 1.0),
    ("Quinoa (cooked)", 1.0),
    ("Sweet Potato (raw)", 1.0),
]

FAT_FILLERS = [
    ("Olive Oil", 1.0),
    ("Almonds (raw)", 1.0),
    ("Peanut Butter (natural)", 1.0),
    ("Walnuts (raw)", 1.0),
    ("Avocado (raw)", 1.0),
]

VEG_FILLERS = [
    ("Broccoli (raw)", 1.0),
    ("Spinach (raw)", 1.0),
    ("Mixed Salad Greens", 1.0),
    ("Bell Pepper (raw)", 1.0),
    ("Asparagus (raw)", 1.0),
    ("Green Beans (raw)", 1.0),
    ("Carrots (raw)", 1.0),
]


def _grams_to_hit_macro(food: FoodItem, macro: str, target_g: float) -> float:
    """Compute grams of food needed to hit a macro target."""
    if macro == "protein":
        per_100g = food.protein_g_per_100g
    elif macro == "carb":
        per_100g = food.carb_g_per_100g
    elif macro == "fat":
        per_100g = food.fat_g_per_100g
    elif macro == "fiber":
        per_100g = food.fiber_g_per_100g
    else:
        return 0
    if per_100g <= 0:
        return 0
    return target_g / per_100g * 100


def select_protein_filler(
    gap_protein_g: float,
    diet_tag: str,
    exclude_foods: set[str] | None = None,
) -> Optional[MealFood]:
    """
    Select a protein filler to close the protein gap.

    Picks the highest-protein-density food available for the diet.
    """
    if gap_protein_g < FILLER_THRESHOLDS["protein_g"]:
        return None

    exclude_foods = exclude_foods or set()
    options = PROTEIN_FILLERS.get(diet_tag, PROTEIN_FILLERS["OMNI"])

    for food_name, _ in options:
        if food_name in exclude_foods:
            continue
        food = get_food(food_name)
        if food is None:
            continue
        grams = _grams_to_hit_macro(food, "protein", gap_protein_g)
        if grams > 0:
            # Cap at reasonable serving (e.g. max 60g whey, max 400g chicken)
            max_grams = food.serving_size_g * 4
            grams = min(grams, max_grams)
            grams = max(grams, food.serving_size_g * 0.5)  # at least half a serving
            return MealFood(food=food, grams=round(grams, 0))

    return None


def select_carb_filler(
    gap_carb_g: float,
    exclude_foods: set[str] | None = None,
) -> Optional[MealFood]:
    """Select a carb filler to close the carb gap."""
    if gap_carb_g < FILLER_THRESHOLDS["carb_g"]:
        return None

    exclude_foods = exclude_foods or set()

    for food_name, _ in CARB_FILLERS:
        if food_name in exclude_foods:
            continue
        food = get_food(food_name)
        if food is None:
            continue
        grams = _grams_to_hit_macro(food, "carb", gap_carb_g)
        if grams > 0:
            max_grams = food.serving_size_g * 3
            grams = min(grams, max_grams)
            grams = max(grams, food.serving_size_g * 0.5)
            return MealFood(food=food, grams=round(grams, 0))

    return None


def select_fat_filler(
    gap_fat_g: float,
    exclude_foods: set[str] | None = None,
) -> Optional[MealFood]:
    """Select a fat filler to close the fat gap."""
    if gap_fat_g < FILLER_THRESHOLDS["fat_g"]:
        return None

    exclude_foods = exclude_foods or set()

    for food_name, _ in FAT_FILLERS:
        if food_name in exclude_foods:
            continue
        food = get_food(food_name)
        if food is None:
            continue
        grams = _grams_to_hit_macro(food, "fat", gap_fat_g)
        if grams > 0:
            max_grams = food.serving_size_g * 3
            grams = min(grams, max_grams)
            grams = max(grams, food.serving_size_g * 0.5)
            return MealFood(food=food, grams=round(grams, 0))

    return None


def select_veg_filler(
    gap_fiber_g: float,
    exclude_foods: set[str] | None = None,
) -> Optional[MealFood]:
    """
    Select a vegetable filler to close the fiber gap.

    Vegetables are 'free' (low kcal, high volume) — added liberally.
    """
    if gap_fiber_g < FILLER_THRESHOLDS["fiber_g"]:
        return None

    exclude_foods = exclude_foods or set()

    for food_name, _ in VEG_FILLERS:
        if food_name in exclude_foods:
            continue
        food = get_food(food_name)
        if food is None:
            continue
        grams = _grams_to_hit_macro(food, "fiber", gap_fiber_g)
        if grams > 0:
            # Veg is free — cap at 200g
            grams = min(grams, 200)
            grams = max(grams, 80)  # at least 80g
            return MealFood(food=food, grams=round(grams, 0))

    return None


# === Main filler orchestrator ===

@dataclass
class FillerResult:
    """Result of filler selection for a meal."""
    fillers: list[MealFood] = field(default_factory=list)
    total_filler_kcal: float = 0.0
    total_filler_protein_g: float = 0.0
    total_filler_carb_g: float = 0.0
    total_filler_fat_g: float = 0.0
    total_filler_fiber_g: float = 0.0
    notes: list[str] = field(default_factory=list)


def select_fillers_for_meal(
    gap: FillerGap,
    diet_tag: str,
    is_main_meal: bool = True,
    exclude_foods: set[str] | None = None,
) -> FillerResult:
    """
    Select fillers to close the macro gap for a meal.

    Args:
      gap: FillerGap with remaining macros needed
      diet_tag: "OMNI" / "VEGAN" / etc.
      is_main_meal: True for lunch/dinner (adds veg filler); False for snacks
      exclude_foods: set of food names to exclude

    Returns FillerResult with selected fillers + their totals.
    """
    result = FillerResult()
    used_food_names: set[str] = set()
    exclude_foods = exclude_foods or set()

    # Protein filler (priority 1)
    protein_filler = select_protein_filler(gap.protein_g, diet_tag, exclude_foods | used_food_names)
    if protein_filler:
        result.fillers.append(protein_filler)
        used_food_names.add(protein_filler.food.name)
        result.total_filler_kcal += protein_filler.kcal
        result.total_filler_protein_g += protein_filler.protein_g
        result.total_filler_carb_g += protein_filler.carb_g
        result.total_filler_fat_g += protein_filler.fat_g
        result.total_filler_fiber_g += protein_filler.fiber_g
        result.notes.append(
            f"+ {protein_filler.grams:.0f}g {protein_filler.food.name} "
            f"(protein filler: +{protein_filler.protein_g:.0f}g P)"
        )

    # Recompute remaining gap after protein filler
    remaining_carb = gap.carb_g - result.total_filler_carb_g
    remaining_fat = gap.fat_g - result.total_filler_fat_g

    # Carb filler (priority 2)
    carb_filler = select_carb_filler(remaining_carb, exclude_foods | used_food_names)
    if carb_filler:
        result.fillers.append(carb_filler)
        used_food_names.add(carb_filler.food.name)
        result.total_filler_kcal += carb_filler.kcal
        result.total_filler_protein_g += carb_filler.protein_g
        result.total_filler_carb_g += carb_filler.carb_g
        result.total_filler_fat_g += carb_filler.fat_g
        result.total_filler_fiber_g += carb_filler.fiber_g
        result.notes.append(
            f"+ {carb_filler.grams:.0f}g {carb_filler.food.name} "
            f"(carb filler: +{carb_filler.carb_g:.0f}g C)"
        )

    # Fat filler (priority 3)
    remaining_fat = gap.fat_g - result.total_filler_fat_g
    fat_filler = select_fat_filler(remaining_fat, exclude_foods | used_food_names)
    if fat_filler:
        result.fillers.append(fat_filler)
        used_food_names.add(fat_filler.food.name)
        result.total_filler_kcal += fat_filler.kcal
        result.total_filler_protein_g += fat_filler.protein_g
        result.total_filler_carb_g += fat_filler.carb_g
        result.total_filler_fat_g += fat_filler.fat_g
        result.total_filler_fiber_g += fat_filler.fiber_g
        result.notes.append(
            f"+ {fat_filler.grams:.0f}g {fat_filler.food.name} "
            f"(fat filler: +{fat_filler.fat_g:.0f}g F)"
        )

    # Veg filler (priority 4 — only for main meals)
    if is_main_meal:
        remaining_fiber = gap.fiber_g - result.total_filler_fiber_g
        veg_filler = select_veg_filler(remaining_fiber, exclude_foods | used_food_names)
        if veg_filler:
            result.fillers.append(veg_filler)
            used_food_names.add(veg_filler.food.name)
            result.total_filler_kcal += veg_filler.kcal
            result.total_filler_protein_g += veg_filler.protein_g
            result.total_filler_carb_g += veg_filler.carb_g
            result.total_filler_fat_g += veg_filler.fat_g
            result.total_filler_fiber_g += veg_filler.fiber_g
            result.notes.append(
                f"+ {veg_filler.grams:.0f}g {veg_filler.food.name} "
                f"(veg filler: +{veg_filler.fiber_g:.1f}g fiber)"
            )

    return result


__all__ = [
    "MIN_SCALE", "MAX_SCALE",
    "ScaledRecipe",
    "compute_scale_factor",
    "scale_recipe",
    "FillerGap",
    "compute_filler_gap",
    "FillerResult",
    "select_fillers_for_meal",
    "select_protein_filler",
    "select_carb_filler",
    "select_fat_filler",
    "select_veg_filler",
    "FILLER_THRESHOLDS",
    "PROTEIN_FILLERS", "CARB_FILLERS", "FAT_FILLERS", "VEG_FILLERS",
]

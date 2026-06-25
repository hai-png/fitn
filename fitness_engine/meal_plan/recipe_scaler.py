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

# ScalerConfig centralizes the scaler + filler tuning knobs (scale clamps,
# no-scale band, deviation limit, filler thresholds, serving-cap multipliers,
# veg-gram range) so they can be inspected / overridden in one place.
@dataclass(frozen=True)
class ScalerConfig:
    """Tunable knobs for the recipe scaler + filler system.

    Defaults match the original hardcoded values; expose them as a dataclass
    so they can be reasoned about as a unit (and overridden in tests).
    """
    # Scale clamps
    min_scale: float = 0.7
    max_scale: float = 1.5
    # ±this fraction → no scaling needed (recipe already close enough)
    no_scale_band: float = 0.10
    # Allow scaled-kcal deviation up to this fraction before declaring the
    # recipe a poor fit (40% lets 0.7-1.5x clamp through but flags extremes)
    scale_deviation_limit: float = 0.40

    # Filler thresholds (don't add fillers for gaps below these)
    filler_kcal_threshold: float = 50.0
    filler_protein_g_threshold: float = 5.0
    filler_carb_g_threshold: float = 5.0
    filler_fat_g_threshold: float = 3.0
    filler_fiber_g_threshold: float = 3.0

    # Serving-cap multipliers (max grams = serving_size_g × this)
    protein_serving_cap_multiplier: float = 4.0    # e.g. max 4× whey scoop
    carb_serving_cap_multiplier: float = 3.0
    fat_serving_cap_multiplier: float = 3.0
    # Minimum fraction of a serving (so we don't add 1g of oats)
    filler_min_serving_fraction: float = 0.5

    # Veg filler (vegetables are 'free' — high volume, low kcal)
    veg_max_grams: float = 200.0
    veg_min_grams: float = 80.0


# Default singleton used everywhere in this module.
SCALER_CONFIG = ScalerConfig()

# Back-compat module-level aliases (existing callers may reference these).
MIN_SCALE = SCALER_CONFIG.min_scale
MAX_SCALE = SCALER_CONFIG.max_scale
SCALE_DEVIATION_LIMIT = SCALER_CONFIG.scale_deviation_limit


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

    Phase-6 fix: also guard target_kcal <= 0 — previously a 0-kcal target
    produced raw_factor = 0, which failed the band check and then was
    clamped to MIN_SCALE (0.7), yielding 70% of the recipe's kcal instead
    of 0. Now returns 1.0 (no scaling) when target is non-positive, since
    the allocator's `is_recipe_scalable_to_target` will reject the recipe
    anyway and fall back to fillers.
    """
    if recipe_kcal <= 0:
        return 1.0
    if target_kcal <= 0:
        return 1.0

    raw_factor = target_kcal / recipe_kcal

    # If within ±no_scale_band, no need to scale
    band = SCALER_CONFIG.no_scale_band
    if (1.0 - band) <= raw_factor <= (1.0 + band):
        return 1.0

    # Clamp to [min_scale, max_scale]
    return max(SCALER_CONFIG.min_scale, min(SCALER_CONFIG.max_scale, raw_factor))


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
# previously a dict with hardcoded values; now sourced from
# ScalerConfig (single source of truth). Kept as a dict for back-compat with
# callers that index by string key (e.g. FILLER_THRESHOLDS["protein_g"]).
FILLER_THRESHOLDS = {
    "kcal":     SCALER_CONFIG.filler_kcal_threshold,
    "protein_g": SCALER_CONFIG.filler_protein_g_threshold,
    "carb_g":   SCALER_CONFIG.filler_carb_g_threshold,
    "fat_g":    SCALER_CONFIG.filler_fat_g_threshold,
    "fiber_g":  SCALER_CONFIG.filler_fiber_g_threshold,
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


def _select_filler(
    gap_g: float,
    options: list[tuple[str, float]],
    threshold_key: str,
    cap_multiplier: float | None = None,
    min_grams: float | None = None,
    max_grams: float | None = None,
    exclude_foods: set[str] | None = None,
) -> Optional[MealFood]:
    """Internal helper shared by all four `select_*_filler` wrappers.

    Picks the first filler in `options` whose `_grams_to_hit_macro` for the
    macro named by `threshold_key` (strip the `_g` suffix) closes `gap_g`.

    Two cap modes:
      * `cap_multiplier` set (protein/carb/fat): cap grams at
        `serving_size_g * cap_multiplier`; skip the food if the min serving
        (`serving_size_g * filler_min_serving_fraction`) would overshoot the
        gap (Phase-6 fix — was previously clamped UP, doubling the gap).
      * `cap_multiplier` is None (veg): clamp grams to
        `[min_grams, max_grams]` (vegetables are 'free' — high volume, low
        kcal, so we add them liberally without skipping).
    """
    if gap_g < FILLER_THRESHOLDS[threshold_key]:
        return None

    exclude_foods = exclude_foods or set()
    macro = threshold_key[:-2] if threshold_key.endswith("_g") else threshold_key

    for food_name, _ in options:
        if food_name in exclude_foods:
            continue
        food = get_food(food_name)
        if food is None:
            continue
        grams = _grams_to_hit_macro(food, macro, gap_g)
        if grams <= 0:
            continue
        if cap_multiplier is not None:
            # Protein/carb/fat mode: cap + skip-if-overshoot.
            cap = food.serving_size_g * cap_multiplier
            grams = min(grams, cap)
            min_serving = food.serving_size_g * SCALER_CONFIG.filler_min_serving_fraction
            if grams < min_serving:
                # Min serving would overshoot the gap — try the next food.
                continue
        else:
            # Veg mode: fixed min/max grams, no skip.
            grams = min(grams, max_grams)
            grams = max(grams, min_grams)
        return MealFood(food=food, grams=round(grams, 0))

    return None


def select_protein_filler(
    gap_protein_g: float,
    diet_tag: str,
    exclude_foods: set[str] | None = None,
) -> Optional[MealFood]:
    """
    Select a protein filler to close the protein gap.

    Picks the highest-protein-density food available for the diet.

    Phase-6 fix: previously `PROTEIN_FILLERS.get(diet_tag, PROTEIN_FILLERS["OMNI"])`
    silently fell back to the OMNI list (which contains whey, chicken, etc.)
    for any diet_tag not in the dict — including "VEGAN_ETHIOPIAN" and
    "VEGAN_VEGETARIAN", which are produced by `profile_requirements.get_recipe_diet_tag`.
    Vegan users got non-vegan fillers. Now we check the diet_tag prefix:
    any tag starting with "VEGAN" uses the VEGAN list.
    """
    # match by prefix so VEGAN_ETHIOPIAN / VEGAN_* tags
    # resolve to the vegan list rather than silently falling back to OMNI.
    if diet_tag.startswith("VEGAN"):
        options = PROTEIN_FILLERS["VEGAN"]
    else:
        options = PROTEIN_FILLERS["OMNI"]
    return _select_filler(
        gap_protein_g,
        options,
        threshold_key="protein_g",
        cap_multiplier=SCALER_CONFIG.protein_serving_cap_multiplier,
        exclude_foods=exclude_foods,
    )


def select_carb_filler(
    gap_carb_g: float,
    exclude_foods: set[str] | None = None,
) -> Optional[MealFood]:
    """Select a carb filler to close the carb gap."""
    return _select_filler(
        gap_carb_g,
        CARB_FILLERS,
        threshold_key="carb_g",
        cap_multiplier=SCALER_CONFIG.carb_serving_cap_multiplier,
        exclude_foods=exclude_foods,
    )


def select_fat_filler(
    gap_fat_g: float,
    exclude_foods: set[str] | None = None,
) -> Optional[MealFood]:
    """Select a fat filler to close the fat gap."""
    return _select_filler(
        gap_fat_g,
        FAT_FILLERS,
        threshold_key="fat_g",
        cap_multiplier=SCALER_CONFIG.fat_serving_cap_multiplier,
        exclude_foods=exclude_foods,
    )


def select_veg_filler(
    gap_fiber_g: float,
    exclude_foods: set[str] | None = None,
) -> Optional[MealFood]:
    """
    Select a vegetable filler to close the fiber gap.

    Vegetables are 'free' (low kcal, high volume) — added liberally.
    """
    return _select_filler(
        gap_fiber_g,
        VEG_FILLERS,
        threshold_key="fiber_g",
        cap_multiplier=None,
        min_grams=SCALER_CONFIG.veg_min_grams,
        max_grams=SCALER_CONFIG.veg_max_grams,
        exclude_foods=exclude_foods,
    )


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
    "ScalerConfig", "SCALER_CONFIG",
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

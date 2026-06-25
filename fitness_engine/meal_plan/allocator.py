"""
Meal allocator — Phase-5 clean implementation.

This module REPLACES the legacy Phase-2 allocator with a clean, comprehensive
recipe selection + scaling + filler system.

Algorithm per meal slot:
  1. Get the slot target (MealSlotTarget from profile_requirements)
  2. Get candidate recipes (filtered by meal_type + diet)
  3. Score each candidate (recipe_scorer.score_recipe_for_slot)
  4. Pick the highest-scoring recipe
  5. If score < MIN_ACCEPTABLE_SCORE, try scaling (recipe_scaler.scale_recipe)
  6. After scaling, compute remaining gap (recipe_scaler.compute_filler_gap)
  7. Add fillers to close the gap (recipe_scaler.select_fillers_for_meal)
  8. Return a SelectedMeal with recipe + scale_factor + fillers + swap options

This is a SINGLE PASS per slot — no backtracking. The 7-day planner handles
weekly balancing separately.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..models.meal import (
    Meal, MealFood, MealType, Recipe,
)
from .profile_requirements import MealSlotTarget
from .recipe_scorer import (
    score_candidates, RecipeScore, MIN_ACCEPTABLE_SCORE,
)
from .recipe_scaler import (
    scale_recipe, compute_filler_gap, select_fillers_for_meal,
    ScaledRecipe, FillerResult,
)
from .swap_system import get_recipe_swaps_for_plan, get_swaps_for_recipe_ingredients
from .recipe_loader import recipes_by_filters


@dataclass
class SelectedMeal:
    """Result of selecting a recipe + fillers for a meal slot."""
    meal_type: MealType
    recipe: Optional[Recipe]
    scale_factor: float = 1.0
    scaled_kcal: float = 0.0
    scaled_protein_g: float = 0.0
    scaled_carb_g: float = 0.0
    scaled_fat_g: float = 0.0
    scaled_fiber_g: float = 0.0
    fillers: list[MealFood] = field(default_factory=list)
    filler_kcal: float = 0.0
    filler_protein_g: float = 0.0
    filler_carb_g: float = 0.0
    filler_fat_g: float = 0.0
    filler_fiber_g: float = 0.0
    score: float = 0.0
    target_kcal: float = 0.0
    target_protein_g: float = 0.0
    target_carb_g: float = 0.0
    target_fat_g: float = 0.0
    swap_options: list[dict] = field(default_factory=list)
    ingredient_swaps: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def total_kcal(self) -> float:
        return self.scaled_kcal + self.filler_kcal

    @property
    def total_protein_g(self) -> float:
        return self.scaled_protein_g + self.filler_protein_g

    @property
    def total_carb_g(self) -> float:
        return self.scaled_carb_g + self.filler_carb_g

    @property
    def total_fat_g(self) -> float:
        return self.scaled_fat_g + self.filler_fat_g

    @property
    def total_fiber_g(self) -> float:
        return self.scaled_fiber_g + self.filler_fiber_g

    @property
    def kcal_match_pct(self) -> float:
        """How close total kcal is to target (100 = perfect)."""
        if self.target_kcal <= 0:
            return 100.0
        delta_pct = abs(self.total_kcal - self.target_kcal) / self.target_kcal
        return max(0.0, 100.0 * (1 - delta_pct))

    @property
    def protein_match_pct(self) -> float:
        if self.target_protein_g <= 0:
            return 100.0
        delta_pct = abs(self.total_protein_g - self.target_protein_g) / self.target_protein_g
        return max(0.0, 100.0 * (1 - delta_pct))


def _compute_allergen_filler_exclusions(
    allergens_to_avoid: Optional[list[str]],
) -> set[str]:
    """
    Tier 3.37 fix: map allergen categories to filler food names that should be excluded.

    Previously, allergens were checked against recipes but NOT against fillers, so a
    dairy-allergic user would get whey/yogurt/cottage-cheese fillers. Now we return
    a set of food names to exclude based on the user's allergen list.
    """
    if not allergens_to_avoid:
        return set()

    # Map allergen category → set of filler food names (from PROTEIN_FILLERS,
    # CARB_FILLERS, FAT_FILLERS, VEG_FILLERS in recipe_scaler.py) that contain
    # that allergen.
    ALLERGEN_FILLER_MAP: dict[str, set[str]] = {
        "dairy": {
            "Whey Protein Powder",
            "Greek Yogurt (non-fat, plain)",
            "Cottage Cheese (low-fat, 2%)",
            "Milk (skim)",
            "Cheddar Cheese",
        },
        "eggs": {
            "Egg White (large)",
            "Eggs (large)",
        },
        "gluten": {
            "Whole Wheat Bread",
            "Oats (rolled, dry)",
        },
        "nuts": {
            "Almonds (raw)",
            "Walnuts (raw)",
        },
        "peanuts": {
            "Peanut Butter (natural)",
        },
        "soy": {
            "Tofu (firm)",
            "Tempeh",
            "Soy Protein Powder",
            "Edamame (cooked)",
        },
        "shellfish": set(),
        "fish": set(),
        "sesame": set(),
    }

    exclusions: set[str] = set()
    for allergen in allergens_to_avoid:
        allergen_lower = allergen.lower().strip()
        exclusions |= ALLERGEN_FILLER_MAP.get(allergen_lower, set())
    return exclusions


def allocate_meal(
    slot: MealSlotTarget,
    diet_tag: str,
    user_goal: str = "maintenance",
    cuisine_preference: Optional[str] = None,
    allergens_to_avoid: Optional[list[str]] = None,
    excluded_ingredients: Optional[list[str]] = None,
    used_recipe_ids_last_3_days: Optional[set[str]] = None,
    used_recipe_ids_last_7_days: Optional[set[str]] = None,
    used_today: Optional[set[str]] = None,
    is_main_meal: bool = True,
) -> SelectedMeal:
    """
    Allocate a single meal slot.

    Steps:
      1. Query candidate recipes by meal_type + diet
      2. Score each candidate
      3. Pick highest score; if < MIN_ACCEPTABLE, scale the recipe
      4. Compute filler gap; add fillers
      5. Attach swap options + ingredient swaps
      6. Return SelectedMeal

    Args:
      slot: MealSlotTarget with per-slot macro targets
      diet_tag: user's diet tag ("OMNI", "VEGAN", etc.)
      user_goal: "cut" / "bulk" / "recomp" / "maintenance"
      cuisine_preference: optional cuisine filter
      allergens_to_avoid: list of allergens to exclude
      excluded_ingredients: list of ingredients to exclude
      used_recipe_ids_last_3_days: set of recipe IDs used in last 3 days
      used_recipe_ids_last_7_days: set of recipe IDs used in last 7 days
      used_today: set of recipe IDs already used today (avoid repeats)
      is_main_meal: True for breakfast/lunch/dinner (adds veg filler)

    Returns SelectedMeal.
    """
    used_3d = used_recipe_ids_last_3_days or set()
    used_7d = used_recipe_ids_last_7_days or set()
    used_today = used_today or set()

    # Combine "used" sets for exclusion
    exclude_ids = used_today | used_3d

    # 1. Get candidates by meal_type + diet
    candidates = recipes_by_filters(
        meal_type=slot.meal_type.value,
        diet_type=diet_tag,
        exclude_ids=exclude_ids,
    )

    # 2. Score each candidate
    scores = score_candidates(
        candidates=candidates,
        slot=slot,
        diet_tag=diet_tag,
        user_goal=user_goal,
        cuisine_preference=cuisine_preference,
        allergens_to_avoid=allergens_to_avoid,
        excluded_ingredients=excluded_ingredients,
        used_recipe_ids_last_3_days=used_3d,
        used_recipe_ids_last_7_days=used_7d,
    )

    # 3. Pick highest score
    if not scores:
        # No recipe found — return empty SelectedMeal (planner handles fallback)
        return SelectedMeal(
            meal_type=slot.meal_type,
            recipe=None,
            target_kcal=slot.target_kcal,
            target_protein_g=slot.target_protein_g,
            target_carb_g=slot.target_carb_g,
            target_fat_g=slot.target_fat_g,
            notes=["No recipe found for this slot — planner should fall back to raw foods"],
        )

    best = scores[0]

    # Tier 3.36 fix: enforce MIN_ACCEPTABLE_SCORE. If the best candidate scores
    # below the threshold, log a warning and try the next candidate. If no
    # candidate meets the threshold, fall back to the best available (so the
    # meal isn't empty) but add a note so the user knows the fit is poor.
    # Phase-6: removed redundant local import (MIN_ACCEPTABLE_SCORE is already
    # imported at module top).
    low_score_warning: str | None = None
    if best.total_score < MIN_ACCEPTABLE_SCORE:
        # Try to find a better-scoring candidate among the rest
        better = next((s for s in scores[1:] if s.total_score >= MIN_ACCEPTABLE_SCORE), None)
        if better is not None:
            best = better
        else:
            # No candidate meets threshold — use best available but note it
            low_score_warning = (
                f"⚠ Best recipe score {best.total_score:.1f} < MIN_ACCEPTABLE_SCORE "
                f"({MIN_ACCEPTABLE_SCORE}). Recipe fit is poor — consider raw-foods fallback."
            )

    # Phase-6: if the best recipe cannot be scaled to within
    # SCALE_DEVIATION_LIMIT of the slot target, fall back to fillers-only
    # (returns SelectedMeal with recipe=None). This prevents the previous
    # behavior where a 500-kcal recipe was clamped to MIN_SCALE=0.7 → 350 kcal
    # for a 100-kcal slot, leaving the user 250% over target with no fillers
    # to compensate.
    from .recipe_scaler import is_recipe_scalable_to_target
    if not is_recipe_scalable_to_target(best.recipe.kcal, slot.target_kcal):
        return SelectedMeal(
            meal_type=slot.meal_type,
            recipe=None,
            target_kcal=slot.target_kcal,
            target_protein_g=slot.target_protein_g,
            target_carb_g=slot.target_carb_g,
            target_fat_g=slot.target_fat_g,
            notes=[
                f"Recipe '{best.recipe.name}' ({best.recipe.kcal:.0f} kcal) cannot be "
                f"scaled to slot target ({slot.target_kcal:.0f} kcal) within ±40% — "
                f"falling back to fillers-only meal."
            ],
        )

    # 4. Scale the recipe
    scaled = scale_recipe(best.recipe, slot.target_kcal)

    # 5. Compute filler gap
    gap = compute_filler_gap(
        scaled=scaled,
        target_kcal=slot.target_kcal,
        target_protein_g=slot.target_protein_g,
        target_carb_g=slot.target_carb_g,
        target_fat_g=slot.target_fat_g,
        target_fiber_g=slot.target_fiber_g,
    )

    # 6. Select fillers
    # Tier 3.37 fix: pass allergens_to_avoid through to filler selection so
    # dairy-allergic users don't get whey/yogurt/cottage-cheese fillers.
    # Map allergen categories to filler food names that should be excluded.
    allergen_filler_exclusions = _compute_allergen_filler_exclusions(allergens_to_avoid)
    filler_result = select_fillers_for_meal(
        gap=gap,
        diet_tag=diet_tag,
        is_main_meal=is_main_meal,
        exclude_foods=allergen_filler_exclusions,
    )

    # 7. Get swap options (Phase-6: forward allergens/excluded/cuisine so
    # swap suggestions respect the same constraints as the primary allocation)
    swap_options = get_recipe_swaps_for_plan(
        recipe=best.recipe,
        diet_tag=diet_tag,
        target_kcal=slot.target_kcal,
        allergens_to_avoid=allergens_to_avoid,
        excluded_ingredients=excluded_ingredients,
        cuisine_preference=cuisine_preference,
    )

    # 8. Get ingredient swaps
    ingredient_swaps_raw = get_swaps_for_recipe_ingredients(best.recipe)
    # Convert to serializable format
    ingredient_swaps = {
        ing: [
            {
                "alternatives": swap.alternatives,
                "ratio": swap.ratio,
                "notes": swap.notes,
            }
            for swap in swaps
        ]
        for ing, swaps in ingredient_swaps_raw.items()
    }

    # 9. Build notes
    notes: list[str] = []
    notes.append(f"Score: {best.total_score:.1f}/100")
    if low_score_warning:
        notes.append(low_score_warning)
    if scaled.scale_factor != 1.0:
        notes.append(f"Scaled to {scaled.servings_display} ({scaled.scale_factor:.2f}x)")
    if filler_result.fillers:
        notes.extend(filler_result.notes)
    if slot.timing_note:
        notes.append(f"Timing: {slot.timing_note}")

    return SelectedMeal(
        meal_type=slot.meal_type,
        recipe=best.recipe,
        scale_factor=scaled.scale_factor,
        scaled_kcal=scaled.scaled_kcal,
        scaled_protein_g=scaled.scaled_protein_g,
        scaled_carb_g=scaled.scaled_carb_g,
        scaled_fat_g=scaled.scaled_fat_g,
        scaled_fiber_g=scaled.scaled_fiber_g,
        fillers=filler_result.fillers,
        filler_kcal=filler_result.total_filler_kcal,
        filler_protein_g=filler_result.total_filler_protein_g,
        filler_carb_g=filler_result.total_filler_carb_g,
        filler_fat_g=filler_result.total_filler_fat_g,
        filler_fiber_g=filler_result.total_filler_fiber_g,
        score=best.total_score,
        target_kcal=slot.target_kcal,
        target_protein_g=slot.target_protein_g,
        target_carb_g=slot.target_carb_g,
        target_fat_g=slot.target_fat_g,
        swap_options=swap_options,
        ingredient_swaps=ingredient_swaps,
        notes=notes,
    )


def selected_meal_to_dict(selected: SelectedMeal) -> dict:
    """Convert SelectedMeal to a serializable dict."""
    return {
        "meal_type": selected.meal_type.value,
        "recipe": selected.recipe.to_dict() if selected.recipe else None,
        "scale_factor": selected.scale_factor,
        "scaled_nutrition": {
            "kcal": round(selected.scaled_kcal, 1),
            "protein_g": round(selected.scaled_protein_g, 1),
            "carb_g": round(selected.scaled_carb_g, 1),
            "fat_g": round(selected.scaled_fat_g, 1),
            "fiber_g": round(selected.scaled_fiber_g, 1),
        },
        "fillers": [
            {
                "food": {
                    "name": mf.food.name,
                    "category": mf.food.category.value if hasattr(mf.food.category, 'value') else str(mf.food.category),
                    "kcal_per_100g": mf.food.kcal_per_100g,
                    "protein_g_per_100g": mf.food.protein_g_per_100g,
                    "carb_g_per_100g": mf.food.carb_g_per_100g,
                    "fat_g_per_100g": mf.food.fat_g_per_100g,
                    "fiber_g_per_100g": mf.food.fiber_g_per_100g,
                    "serving_size_g": mf.food.serving_size_g,
                    "serving_description": mf.food.serving_description,
                    "is_vegan": mf.food.is_vegan,
                },
                "grams": mf.grams,
                "kcal": round(mf.kcal, 1),
                "protein_g": round(mf.protein_g, 1),
                "carb_g": round(mf.carb_g, 1),
                "fat_g": round(mf.fat_g, 1),
            }
            for mf in selected.fillers
        ],
        "filler_nutrition": {
            "kcal": round(selected.filler_kcal, 1),
            "protein_g": round(selected.filler_protein_g, 1),
            "carb_g": round(selected.filler_carb_g, 1),
            "fat_g": round(selected.filler_fat_g, 1),
            "fiber_g": round(selected.filler_fiber_g, 1),
        },
        "total_nutrition": {
            "kcal": round(selected.total_kcal, 1),
            "protein_g": round(selected.total_protein_g, 1),
            "carb_g": round(selected.total_carb_g, 1),
            "fat_g": round(selected.total_fat_g, 1),
            "fiber_g": round(selected.total_fiber_g, 1),
        },
        "target_nutrition": {
            "kcal": round(selected.target_kcal, 1),
            "protein_g": round(selected.target_protein_g, 1),
            "carb_g": round(selected.target_carb_g, 1),
            "fat_g": round(selected.target_fat_g, 1),
        },
        "match_pct": {
            "kcal": round(selected.kcal_match_pct, 1),
            "protein": round(selected.protein_match_pct, 1),
        },
        "score": selected.score,
        "swap_options": selected.swap_options,
        "ingredient_swaps": selected.ingredient_swaps,
        "notes": selected.notes,
    }


__all__ = [
    "SelectedMeal",
    "allocate_meal",
    "selected_meal_to_dict",
]

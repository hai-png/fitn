"""
Swap system — Phase-5.

Provides two kinds of swaps:

  1. **Recipe swaps**: alternative recipes in the same (diet, meal_type,
     kcal_bin) cell. The user can swap a recipe for another without
     breaking the macro budget.

  2. **Ingredient swaps**: per-ingredient substitutions for when a specific
     ingredient is unavailable. E.g. "chicken breast" → "tofu / turkey /
     tempeh".

The swap system is queried:
  - At plan-generation time: alternative_recipe_ids attached to each Meal
  - At runtime: user can request swaps for a specific recipe or ingredient
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..models.meal import Recipe
from ._allergen_constants import PLANT_NAMED_PHRASES as _PLANT_NAMED_PHRASES
from .recipe_loader import load_recipes
from .recipe_scorer import (
    check_allergens,
    check_excluded_ingredients,
    score_diet_match,
)

# === Ingredient swap database ===

@dataclass
class IngredientSwap:
    """A substitution for a specific ingredient."""
    original: str
    alternatives: list[str]
    ratio: float = 1.0   # scaling factor (e.g. 1.0 for 1:1, 0.75 for tofu vs chicken)
    notes: str = ""

    def adjusted_grams(self, original_grams: float) -> float:
        """
        Tier 4.52 fix: apply the ratio to compute the adjusted gram amount
        for the substitute. E.g. if original=100g chicken, ratio=0.75 for tofu,
        the adjusted amount is 75g tofu.

        This was previously the "never applied" field — now consumers can
        call this method to get the correct substitute quantity.
        """
        return original_grams * self.ratio


# Common ingredient swaps (covering proteins, carbs, fats, dairy, etc.)
INGREDIENT_SWAPS: dict[str, list[IngredientSwap]] = {
    # === Proteins ===
    "chicken breast": [
        IngredientSwap("chicken breast", ["turkey breast", "tofu (firm)", "tempeh", "seitan"], 1.0,
                       "1:1 for turkey; 1:1 for tofu/tempeh (drain well); 1:1 for seitan"),
        IngredientSwap("chicken breast", ["chicken thigh (skinless)"], 0.9,
                       "Slightly higher fat; reduce added fat by 1 tsp"),
    ],
    "chicken thigh": [
        IngredientSwap("chicken thigh", ["chicken breast", "turkey thigh", "tofu (firm)"], 1.0),
    ],
    "turkey breast": [
        IngredientSwap("turkey breast", ["chicken breast", "tofu (firm)"], 1.0),
    ],
    "beef": [
        IngredientSwap("beef", ["beyond beef", "impossible beef", "lentils (cooked)"], 1.0,
                       "Plant-based alternatives are 1:1; lentils need 1.5x volume"),
        IngredientSwap("beef", ["lamb", "venison"], 1.0),
    ],
    "ground beef": [
        IngredientSwap("ground beef", ["ground turkey", "beyond beef", "lentils (cooked)"], 1.0),
    ],
    "salmon": [
        IngredientSwap("salmon", ["trout", "mackerel", "arctic char"], 1.0),
        IngredientSwap("salmon", ["tofu (firm) + nori"], 1.0, "Add umami (soy sauce, mushrooms)"),
    ],
    "tuna": [
        IngredientSwap("tuna", ["salmon (canned)", "sardines", "chickpeas"], 1.0),
    ],
    "shrimp": [
        IngredientSwap("shrimp", ["scallops", "tofu (firm, cubed)"], 1.0),
    ],
    "pork": [
        IngredientSwap("pork", ["chicken breast", "tofu (firm)", "tempeh"], 1.0),
    ],
    "tofu": [
        IngredientSwap("tofu", ["tempeh", "seitan", "chicken breast (if omni)"], 1.0),
    ],
    "tempeh": [
        IngredientSwap("tempeh", ["tofu (firm)", "seitan"], 1.0),
    ],
    "eggs": [
        IngredientSwap("eggs", ["flax egg (1 tbsp flax + 3 tbsp water)", "chia egg", "JUST egg"], 1.0,
                       "1 egg = 1 flax egg; baking only"),
    ],
    "egg": [
        IngredientSwap("egg", ["flax egg", "chia egg", "JUST egg"], 1.0),
    ],
    "whey protein": [
        IngredientSwap("whey protein", ["pea protein", "soy protein", "rice protein"], 1.0),
    ],
    "greek yogurt": [
        IngredientSwap("greek yogurt", ["coconut yogurt", "soy yogurt", "almond yogurt"], 1.0,
                       "Plant-based yogurts are lower protein; add protein powder"),
    ],

    # === Carbs ===
    "rice": [
        IngredientSwap("rice", ["quinoa", "cauliflower rice", "couscous", "millet"], 1.0),
    ],
    "white rice": [
        IngredientSwap("white rice", ["brown rice", "jasmine rice", "basmati rice", "quinoa"], 1.0),
    ],
    "brown rice": [
        IngredientSwap("brown rice", ["white rice", "wild rice", "quinoa"], 1.0),
    ],
    "quinoa": [
        IngredientSwap("quinoa", ["rice", "couscous", "bulgur", "millet"], 1.0),
    ],
    "pasta": [
        IngredientSwap("pasta", ["rice noodles", "zucchini noodles", "lentil pasta", "chickpea pasta"], 1.0),
    ],
    "bread": [
        IngredientSwap("bread", ["gluten-free bread", "rice cakes", "corn tortilla", "lettuce wrap"], 1.0),
    ],
    "oats": [
        IngredientSwap("oats", ["quinoa flakes", "rice flakes", "buckwheat groats"], 1.0),
    ],
    "potato": [
        IngredientSwap("potato", ["sweet potato", "cauliflower", "turnip", "rutabaga"], 1.0),
    ],
    "sweet potato": [
        IngredientSwap("sweet potato", ["butternut squash", "pumpkin", "carrot", "potato"], 1.0),
    ],

    # === Ethiopian ingredients ===
    "injera": [
        IngredientSwap("injera", ["teff injera (gluten-free)", "rice crepe", "dosa"], 1.0,
                       "Traditional injera is teff-only (GF); restaurant injera often has wheat"),
    ],
    "teff": [
        IngredientSwap("teff", ["millet flour", "sorghum flour", "rice flour"], 1.0),
    ],
    "berbere": [
        IngredientSwap("berbere", ["ras el hanout", "garam masala", "chili powder + paprika mix"], 0.8,
                       "Use ~80% volume; berbere is spicier"),
    ],
    "niter kibbeh": [
        IngredientSwap("niter kibbeh", ["ghee", "butter", "coconut oil (vegan)"], 1.0),
    ],
    "mitmita": [
        IngredientSwap("mitmita", ["cayenne + cardamom mix", "berbere"], 0.7),
    ],

    # === Fats ===
    "olive oil": [
        IngredientSwap("olive oil", ["avocado oil", "coconut oil", "grapeseed oil"], 1.0),
    ],
    "butter": [
        IngredientSwap("butter", ["ghee", "coconut oil (vegan)", "olive oil (for cooking)"], 1.0),
    ],
    "coconut oil": [
        IngredientSwap("coconut oil", ["olive oil", "avocado oil", "butter (if omni)"], 1.0),
    ],
    "almonds": [
        IngredientSwap("almonds", ["cashews", "sunflower seeds", "peanuts"], 1.0),
    ],
    "peanut butter": [
        IngredientSwap("peanut butter", ["almond butter", "sunflower seed butter", "cashew butter"], 1.0),
    ],

    # === Dairy alternatives ===
    "milk": [
        IngredientSwap("milk", ["oat milk", "soy milk", "almond milk", "coconut milk"], 1.0,
                       "Soy milk is closest nutritionally (protein)"),
    ],
    "cheese": [
        IngredientSwap("cheese", ["nutritional yeast + cashew", "vegan cheese", "tofu (crumbled)"], 1.0),
    ],
    "cream": [
        IngredientSwap("cream", ["coconut cream", "cashew cream", "oat cream"], 1.0),
    ],

    # === Vegetables ===
    "broccoli": [
        IngredientSwap("broccoli", ["cauliflower", "brussels sprouts", "asparagus"], 1.0),
    ],
    "spinach": [
        IngredientSwap("spinach", ["kale", "swiss chard", "collard greens"], 1.0),
    ],
    "kale": [
        IngredientSwap("kale", ["spinach", "collard greens", "swiss chard"], 1.0),
    ],
    "tomato": [
        IngredientSwap("tomato", ["canned tomato", "passata", "red bell pepper"], 1.0),
    ],
    "onion": [
        IngredientSwap("onion", ["shallot", "leek", "scallion", "onion powder"], 1.0),
    ],
    "garlic": [
        IngredientSwap("garlic", ["garlic powder (0.25 tsp per clove)", "shallot", "chives"], 1.0),
    ],
}


# pre-compile the per-key word-boundary regex once at module load so
# get_ingredient_swaps() doesn't re-compile the same pattern on every call
# inside its `for key in INGREDIENT_SWAPS` loop.
_INGREDIENT_SWAP_REGEXES: dict[str, re.Pattern] = {
    key: re.compile(r"\b" + re.escape(key) + r"\b", re.IGNORECASE)
    for key in INGREDIENT_SWAPS
}


def get_ingredient_swaps(ingredient: str) -> list[IngredientSwap]:
    """
    Get swap options for a specific ingredient.

    Case-insensitive match. Phase-6 fix: matching now uses word boundaries
    (regex `\\b<key>\\b`) instead of raw substring test, so "eggplant" no
    longer matches the "egg" swap key. Plant-named phrases like
    "butter lettuce", "milk thistle", "cream of tartar" are also blocked
    so the dairy/egg swap keys don't fire on them.
    Exact match still takes precedence.
    """
    ing_lower = ingredient.lower().strip()

    # Exact match
    if ing_lower in INGREDIENT_SWAPS:
        return INGREDIENT_SWAPS[ing_lower]

    # Block plant-named phrases: if the ingredient IS a plant-named phrase,
    # don't try to match its dairy/egg keyword substring.
    for phrase in _PLANT_NAMED_PHRASES:
        if ing_lower == phrase:
            return []

    # Word-boundary partial match (e.g. "boneless chicken breast" → "chicken
    # breast"). Also skip matching if the ingredient contains a plant-named
    # phrase that subsumes the key (e.g. "butter lettuce" contains "butter"
    # but "butter lettuce" is a plant).
    #
    # v3.1.4 MEDIUM-3 fix: iterate keys sorted by length DESCENDING so the
    # most-specific key wins. Previously "beef" (4 chars) matched before
    # "ground beef" (11 chars), so "ground beef sirloin" returned the generic
    # "beef" swaps and lost the "ground turkey" option specific to ground beef.
    for key in sorted(INGREDIENT_SWAPS.keys(), key=len, reverse=True):
        swaps = INGREDIENT_SWAPS[key]
        # If any plant-named phrase containing this key is present in the
        # ingredient, skip this key (the dairy/egg keyword is part of a
        # plant name, not the actual ingredient).
        if any(phrase in ing_lower for phrase in _PLANT_NAMED_PHRASES if key in phrase):
            continue
        pat = _INGREDIENT_SWAP_REGEXES[key]
        if pat.search(ing_lower):
            return swaps

    return []


def get_swaps_for_recipe_ingredients(
    recipe: Recipe,
    allergens_to_avoid: list[str] | None = None,
    excluded_ingredients: list[str] | None = None,
) -> dict[str, list[IngredientSwap]]:
    """
    Get ingredient swap options for every ingredient in a recipe.

    Returns dict: {ingredient_string: list[IngredientSwap]}.
    Ingredients with no swaps are omitted from the dict.

    MEDIUM-severity fix: now accepts ``allergens_to_avoid`` and
    ``excluded_ingredients`` parameters. Each swap's ``alternatives`` list
    is filtered to drop alternatives that contain an allergen or excluded
    ingredient (using the same word-boundary regex as ``check_allergens``).
    A swap with all alternatives filtered out is dropped entirely.
    """
    # Build a regex-based allergen/excluded scanner.
    import re

    from .recipe_scorer import _ALLERGEN_REGEXES, _PLANT_QUALIFIERS_FOR_ALLERGENS
    bad_patterns: list[tuple[re.Pattern, str]] = []
    if allergens_to_avoid:
        for ag in allergens_to_avoid:
            ag_lower = ag.lower().strip()
            patterns = _ALLERGEN_REGEXES.get(ag_lower)
            if patterns is None:
                # Unknown allergen — fall back to plain word-boundary substring match.
                patterns = [(re.compile(r"\b" + re.escape(ag_lower) + r"\b", re.IGNORECASE), ag_lower)]
            for pat, _kw in patterns:
                bad_patterns.append((pat, f"allergen:{ag_lower}"))
    if excluded_ingredients:
        for ing in excluded_ingredients:
            # v3.1.4 HIGH-2 fix: add word boundaries so excluding "nut"
            # doesn't match the "nut" inside "nutritional yeast". Previously
            # the bare `re.escape(ing.lower())` (no \b) was inconsistent with
            # check_excluded_ingredients in recipe_scorer.py which uses \b...\b.
            ing_lower = ing.lower().strip()
            bad_patterns.append((
                re.compile(r"\b" + re.escape(ing_lower) + r"\b", re.IGNORECASE),
                f"excluded:{ing}",
            ))

    def _is_safe(alt_name: str) -> bool:
        """Return True if the alternative name contains no allergen/excluded ingredient."""
        name_lower = alt_name.lower()
        # Check plant-qualifier suppression for allergens (but NOT for excluded
        # ingredients — if the user said "no soy", they don't want soy sauce
        # even if it's "coconut soy sauce").
        for pat, _label in bad_patterns:
            m = pat.search(name_lower)
            if m:
                # Check plant-qualifier suppression (allergen-only).
                if _label.startswith("allergen:"):
                    context = name_lower[max(0, m.start() - 25):m.start()]
                    if any(pq in context for pq in _PLANT_QUALIFIERS_FOR_ALLERGENS):
                        continue
                return False
        return True

    swaps: dict[str, list[IngredientSwap]] = {}
    for ing in recipe.ingredients:
        # Extract the main ingredient name (strip quantities/units).
        words = ing.split()
        if len(words) <= 2:
            main = ing
            swap_list = get_ingredient_swaps(main)
        else:
            main_3 = " ".join(words[:3])
            swap_list = get_ingredient_swaps(main_3)
            if swap_list:
                main = main_3
            else:
                main_2 = " ".join(words[:2])
                swap_list = get_ingredient_swaps(main_2)
                if swap_list:
                    main = main_2
                else:
                    main = ing
                    swap_list = get_ingredient_swaps(ing)
        if swap_list:
            # Filter alternatives by allergens/excluded ingredients.
            if bad_patterns:
                filtered_swap_list = []
                for swp in swap_list:
                    safe_alts = [a for a in swp.alternatives if _is_safe(a)]
                    if safe_alts:
                        # Return a copy with filtered alternatives.
                        from dataclasses import replace
                        filtered_swap_list.append(replace(swp, alternatives=safe_alts))
                if filtered_swap_list:
                    swaps[ing] = filtered_swap_list
            else:
                swaps[ing] = swap_list

    return swaps


# === Recipe swap system ===

def get_recipe_swaps(
    recipe: Recipe,
    diet_tag: str,
    target_kcal: float,
    kcal_tolerance_pct: float = 0.20,
    exclude_ids: set[str] | None = None,
    limit: int = 5,
    allergens_to_avoid: list[str] | None = None,
    excluded_ingredients: list[str] | None = None,
    cuisine_preference: str | None = None,
) -> list[Recipe]:
    """
    Get alternative recipes that can substitute for the given recipe.

    Two recipes are swappable if they:
      1. Share at least one meal_type
      2. Are diet-compatible (recipe's diet_types match user's diet_tag)
      3. Have kcal within ±kcal_tolerance_pct of the target_kcal
      4. Are not in exclude_ids
      5. Do not contain any allergens the user wants to avoid (Phase-6 fix)
      6. Do not contain any explicitly excluded ingredients (Phase-6 fix)
      7. Match cuisine_preference if specified (Phase-6 fix)

    Args:
      recipe: the reference recipe
      diet_tag: user's diet tag ("OMNI", "VEGAN", etc.)
      target_kcal: the kcal target the swap should hit
      kcal_tolerance_pct: acceptable kcal deviation (default ±20%)
      exclude_ids: recipe IDs to exclude (e.g. already used today)
      limit: max number of swaps to return
      allergens_to_avoid: list of allergens (e.g. ["dairy", "eggs"]) — Phase-6
      excluded_ingredients: list of ingredients to exclude — Phase-6
      cuisine_preference: optional cuisine filter (substring match) — Phase-6

    Returns list of Recipes sorted by kcal closeness to target.
    """
    # copy the caller's set so we don't mutate it.
    exclude_ids = set(exclude_ids) if exclude_ids else set()
    if recipe.id:
        exclude_ids.add(recipe.id)

    target_lo = target_kcal * (1 - kcal_tolerance_pct)
    target_hi = target_kcal * (1 + kcal_tolerance_pct)

    candidates: list[Recipe] = []
    for r in load_recipes():
        if r.id and r.id in exclude_ids:
            continue
        # Must share at least one meal_type
        if not (set(r.meal_types) & set(recipe.meal_types)):
            continue
        # Must be diet-compatible
        if score_diet_match(r, diet_tag) == 0:
            continue
        # Must be in kcal range
        if not (target_lo <= r.kcal <= target_hi):
            continue
        # Skip recipes with diet warnings
        if "[diet-warning" in (r.notes or ""):
            continue
        # must not contain allergens
        if allergens_to_avoid and check_allergens(r, allergens_to_avoid):
            continue
        # must not contain excluded ingredients
        if excluded_ingredients and check_excluded_ingredients(r, excluded_ingredients):
            continue
        # must match cuisine preference if specified
        if cuisine_preference:
            recipe_cuisine = (r.cuisine or "").lower()
            pref_lower = cuisine_preference.lower()
            if pref_lower not in recipe_cuisine:
                continue
        candidates.append(r)

    # Sort by kcal closeness to target
    # MEDIUM-severity fix: add secondary sort keys for explicit determinism.
    candidates.sort(key=lambda r: (
        abs(r.kcal - target_kcal),
        r.id or "",
        r.name.lower(),
    ))
    return candidates[:limit]


def get_recipe_swaps_for_plan(
    recipe: Recipe,
    diet_tag: str,
    target_kcal: float,
    allergens_to_avoid: list[str] | None = None,
    excluded_ingredients: list[str] | None = None,
    cuisine_preference: str | None = None,
) -> list[dict]:
    """
    Get recipe swaps formatted for plan output (with reason + kcal match).

    Phase-6 fix: now accepts and forwards allergens_to_avoid,
    excluded_ingredients, and cuisine_preference so that swap suggestions
    respect the same constraints as the primary allocation.

    Returns list of dicts:
      {"recipe_id": str, "name": str, "kcal": float, "kcal_diff": float}
    """
    swaps = get_recipe_swaps(
        recipe, diet_tag, target_kcal, limit=5,
        allergens_to_avoid=allergens_to_avoid,
        excluded_ingredients=excluded_ingredients,
        cuisine_preference=cuisine_preference,
    )
    return [
        {
            "recipe_id": s.id,
            "name": s.name,
            "kcal": s.kcal,
            "kcal_diff": round(s.kcal - target_kcal, 0),
            "cuisine": s.cuisine,
        }
        for s in swaps
    ]


__all__ = [
    "IngredientSwap",
    "INGREDIENT_SWAPS",
    "get_ingredient_swaps",
    "get_swaps_for_recipe_ingredients",
    "get_recipe_swaps",
    "get_recipe_swaps_for_plan",
]

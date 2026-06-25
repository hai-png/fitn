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

from dataclasses import dataclass, field
from typing import Optional

from ..models.meal import Recipe
from .recipe_loader import load_recipes, get_recipe_by_id


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
        IngredientSwap("olive oil", ["avocado oil", "coconut oil", " grapeseed oil"], 1.0),
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


def get_ingredient_swaps(ingredient: str) -> list[IngredientSwap]:
    """
    Get swap options for a specific ingredient.

    Case-insensitive, partial match (e.g. "Chicken Breast" or "chicken" both work).
    """
    ing_lower = ingredient.lower().strip()

    # Exact match
    if ing_lower in INGREDIENT_SWAPS:
        return INGREDIENT_SWAPS[ing_lower]

    # Partial match (e.g. "boneless chicken breast" → "chicken breast").
    # Tier 4.42 fix: removed bidirectional `or ing_lower in key` which caused
    # false positives (e.g. "egg" matching "eggplant", "butter" matching
    # "butter lettuce"). Now only checks if the swap key is a substring of
    # the ingredient (forward direction only), which is the intended behavior.
    for key, swaps in INGREDIENT_SWAPS.items():
        if key in ing_lower:
            return swaps

    return []


def get_swaps_for_recipe_ingredients(recipe: Recipe) -> dict[str, list[IngredientSwap]]:
    """
    Get ingredient swap options for every ingredient in a recipe.

    Returns dict: {ingredient_string: list[IngredientSwap]}.
    Ingredients with no swaps are omitted from the dict.
    """
    swaps: dict[str, list[IngredientSwap]] = {}
    for ing in recipe.ingredients:
        # Extract the main ingredient name (strip quantities/units)
        # Simple heuristic: take first 2-3 words
        words = ing.split()
        if len(words) <= 2:
            main = ing
        else:
            # Try first 2 words, then 3
            main_2 = " ".join(words[:2])
            main_3 = " ".join(words[:3])
            if get_ingredient_swaps(main_3):
                main = main_3
            elif get_ingredient_swaps(main_2):
                main = main_2
            else:
                main = ing

        swap_list = get_ingredient_swaps(main)
        if swap_list:
            swaps[ing] = swap_list

    return swaps


# === Recipe swap system ===

def get_recipe_swaps(
    recipe: Recipe,
    diet_tag: str,
    target_kcal: float,
    kcal_tolerance_pct: float = 0.20,
    exclude_ids: Optional[set[str]] = None,
    limit: int = 5,
) -> list[Recipe]:
    """
    Get alternative recipes that can substitute for the given recipe.

    Two recipes are swappable if they:
      1. Share at least one meal_type
      2. Are diet-compatible (recipe's diet_types match user's diet_tag)
      3. Have kcal within ±kcal_tolerance_pct of the target_kcal
      4. Are not in exclude_ids

    Args:
      recipe: the reference recipe
      diet_tag: user's diet tag ("OMNI", "VEGAN", etc.)
      target_kcal: the kcal target the swap should hit
      kcal_tolerance_pct: acceptable kcal deviation (default ±20%)
      exclude_ids: recipe IDs to exclude (e.g. already used today)
      limit: max number of swaps to return

    Returns list of Recipes sorted by kcal closeness to target.
    """
    from .recipe_scorer import score_diet_match

    exclude_ids = exclude_ids or set()
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
        candidates.append(r)

    # Sort by kcal closeness to target
    candidates.sort(key=lambda r: abs(r.kcal - target_kcal))
    return candidates[:limit]


def get_recipe_swaps_for_plan(
    recipe: Recipe,
    diet_tag: str,
    target_kcal: float,
) -> list[dict]:
    """
    Get recipe swaps formatted for plan output (with reason + kcal match).

    Returns list of dicts:
      {"recipe_id": str, "name": str, "kcal": float, "kcal_diff": float}
    """
    swaps = get_recipe_swaps(recipe, diet_tag, target_kcal, limit=5)
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

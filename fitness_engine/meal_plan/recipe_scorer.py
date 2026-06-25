"""
Recipe scorer — Phase-5 best-fit scoring algorithm.

Scores every candidate recipe against a meal slot target on a 0-100 scale.
The score is a weighted sum of component scores (kcal match, protein match,
diet match, goal fit, fiber match, variety bonus, cuisine match, allergen
penalty).

The scorer is the SINGLE SOURCE OF TRUTH for "how good a fit is this recipe
for this slot?". The allocator calls it for every candidate and picks the
highest-scoring one.

Score component weights (Section 5.1 of design doc):

| Component        | Weight | Description                                   |
|------------------|--------|-----------------------------------------------|
| kcal_match       | 30     | Within ±20% = 100, ±40% = 50, >40% = 0        |
| protein_match    | 25     | Within ±15% = 100, ±30% = 50, >30% = 0        |
| carb_match       | 15     | Within ±20% = 100, ±40% = 50, >40% = 0        |
| fat_match        | 10     | Within ±25% = 100, ±50% = 50, >50% = 0        |
| diet_match       | 15     | 100 if diet matches, 0 if not (hard filter)   |
| goal_fit         | 5      | 100 if matches, 50 if "maintenance", 0 other  |
| fiber_match      | 5      | Within ±50% = 100, else linear                |
| variety_bonus    | 5      | 100 if not used in last 3 days, 50 if 7 days  |
| cuisine_match    | 5      | 100 if matches preference, 50 if no pref      |
| allergen_penalty | -100   | Hard exclude if allergen present              |

Min acceptable score = 60 (else allocator tries scaling or fillers).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from ..models.meal import Recipe
from .profile_requirements import MealSlotTarget


# === Score component weights ===
# Tier 3.39 fix: previously summed to 115 (not 100 as documented), causing
# scores to exceed 100. Normalized to sum to exactly 100 by scaling each
# weight by 100/115. MIN_ACCEPTABLE_SCORE (60) now correctly means 60%.
WEIGHTS = {
    "kcal_match": 26,      # was 30 → 30*100/115 ≈ 26.1 → 26
    "protein_match": 22,   # was 25 → 21.7 → 22
    "carb_match": 13,      # was 15 → 13.0 → 13
    "fat_match": 9,        # was 10 → 8.7 → 9
    "diet_match": 13,      # was 15 → 13.0 → 13
    "goal_fit": 4,         # was 5 → 4.3 → 4
    "fiber_match": 4,      # was 5 → 4.3 → 4
    "variety_bonus": 4,    # was 5 → 4.3 → 4
    "cuisine_match": 5,    # was 5 → 4.3 → 5 (rounded up to make sum=100)
    # allergen_penalty is applied as -100 (hard exclude)
}
# Verify sum is 100
assert sum(WEIGHTS.values()) == 100, f"WEIGHTS must sum to 100; got {sum(WEIGHTS.values())}"

MIN_ACCEPTABLE_SCORE = 60


@dataclass
class RecipeScore:
    """Detailed breakdown of a recipe's score for a slot."""
    recipe: Recipe
    total_score: float
    component_scores: dict[str, float] = field(default_factory=dict)
    allergen_violations: list[str] = field(default_factory=list)
    excluded: bool = False   # True if hard-excluded (allergen / diet mismatch)
    exclusion_reason: str = ""


# === Component scorers ===

def _band_score(actual: float, target: float, tight_pct: float, loose_pct: float) -> float:
    """
    Score based on how close `actual` is to `target`.

    Returns:
      100 if within tight_pct (e.g. ±20%)
      50 if within loose_pct (e.g. ±40%)
      0 if outside loose_pct
      Linear interpolation between tight and loose.

    If target is 0, returns 100 if actual is also 0, else 50.
    """
    if target <= 0:
        return 100.0 if actual <= 0 else 50.0
    delta_pct = abs(actual - target) / target
    tight = tight_pct
    loose = loose_pct
    if delta_pct <= tight:
        return 100.0
    elif delta_pct >= loose:
        return 0.0
    else:
        # Linear interpolation: 100 at tight, 0 at loose
        return 100.0 * (1 - (delta_pct - tight) / (loose - tight))


def score_kcal_match(recipe_kcal: float, target_kcal: float) -> float:
    """kcal match: ±20% = 100, ±40% = 50, >40% = 0."""
    return _band_score(recipe_kcal, target_kcal, tight_pct=0.20, loose_pct=0.40)


def score_protein_match(recipe_protein: float, target_protein: float) -> float:
    """Protein match: ±15% = 100, ±30% = 50, >30% = 0."""
    return _band_score(recipe_protein, target_protein, tight_pct=0.15, loose_pct=0.30)


def score_carb_match(recipe_carb: float, target_carb: float) -> float:
    """Carb match: ±20% = 100, ±40% = 50, >40% = 0."""
    return _band_score(recipe_carb, target_carb, tight_pct=0.20, loose_pct=0.40)


def score_fat_match(recipe_fat: float, target_fat: float) -> float:
    """Fat match: ±25% = 100, ±50% = 50, >50% = 0."""
    return _band_score(recipe_fat, target_fat, tight_pct=0.25, loose_pct=0.50)


def score_fiber_match(recipe_fiber: float, target_fiber: float) -> float:
    """Fiber match: ±50% = 100, else linear to 0 at 100% off."""
    return _band_score(recipe_fiber, target_fiber, tight_pct=0.50, loose_pct=1.00)


# === Diet matching ===

def score_diet_match(recipe: Recipe, diet_tag: str) -> float:
    """
    Diet match: 100 if recipe's diet_types include the user's diet_tag
    (or a superset), 0 otherwise.

    Diet hierarchy (superset → subset):
      OMNI ⊇ OMNI_ETHIOPIAN
      VEGAN ⊇ VEGAN_ETHIOPIAN
      OMNI can eat VEGAN food (but not vice versa)

    For vegan users: recipe must be VEGAN or VEGAN_*
    For omni users: recipe can be OMNI, OMNI_*, VEGAN, or VEGAN_*
    For vegan_ethiopian users: recipe must be VEGAN_ETHIOPIAN (strict)
    For omni_ethiopian users: recipe must be OMNI_ETHIOPIAN (strict)
    """
    recipe_diets = [d.upper() for d in recipe.diet_types]

    # Reject recipes flagged with diet-warning for vegan users
    if diet_tag in ("VEGAN", "VEGAN_ETHIOPIAN", "VEGETARIAN"):
        if "[diet-warning" in (recipe.notes or ""):
            return 0.0

    if diet_tag == "VEGAN":
        # Vegan can eat VEGAN or VEGAN_* (including VEGAN_ETHIOPIAN)
        if any(d == "VEGAN" or d.startswith("VEGAN_") for d in recipe_diets):
            return 100.0
        return 0.0

    if diet_tag == "VEGAN_ETHIOPIAN":
        # Strict: must be VEGAN_ETHIOPIAN (or VEGAN with ethiopian cuisine)
        if "VEGAN_ETHIOPIAN" in recipe_diets:
            return 100.0
        if any(d == "VEGAN" or d.startswith("VEGAN_") for d in recipe_diets):
            if "ethiopian" in (recipe.cuisine or "").lower():
                return 90.0   # close match but not strict
            return 0.0
        return 0.0

    if diet_tag == "OMNI":
        # Omni can eat anything omnivore- or vegan-compatible
        if any(d == "OMNI" or d.startswith("OMNI_")
               or d == "VEGAN" or d.startswith("VEGAN_")
               for d in recipe_diets):
            return 100.0
        return 0.0

    if diet_tag == "OMNI_ETHIOPIAN":
        # Strict: must be OMNI_ETHIOPIAN (or VEGAN_ETHIOPIAN with ethiopian cuisine)
        if "OMNI_ETHIOPIAN" in recipe_diets:
            return 100.0
        if "VEGAN_ETHIOPIAN" in recipe_diets:
            return 90.0
        if any(d == "OMNI" or d.startswith("OMNI_") for d in recipe_diets):
            if "ethiopian" in (recipe.cuisine or "").lower():
                return 80.0
        return 0.0

    return 0.0


# === Goal fit ===

def score_goal_fit(recipe: Recipe, user_goal: str) -> float:
    """
    Goal fit: 100 if recipe's goal_fit includes user_goal,
    50 if includes "maintenance", 0 otherwise.
    """
    if not user_goal:
        return 50.0
    goal_lower = user_goal.lower()
    recipe_goals = [g.lower() for g in recipe.goal_fit]

    if goal_lower in recipe_goals:
        return 100.0
    if "maintenance" in recipe_goals:
        return 50.0
    return 0.0


# === Variety bonus ===

def score_variety(recipe: Recipe, used_recipe_ids_last_3_days: set[str],
                  used_recipe_ids_last_7_days: set[str]) -> float:
    """
    Variety: 100 if not used in last 3 days, 50 if used in last 7 days, 0 if used in last 3 days.
    """
    if not recipe.id:
        return 100.0
    if recipe.id in used_recipe_ids_last_3_days:
        return 0.0
    if recipe.id in used_recipe_ids_last_7_days:
        return 50.0
    return 100.0


# === Cuisine match ===

def score_cuisine(recipe: Recipe, cuisine_preference: Optional[str]) -> float:
    """
    Cuisine: 100 if matches preference, 50 if no preference, 0 if explicitly different.

    If user has no preference, return 50 (neutral).
    If recipe cuisine matches preference (substring), return 100.
    Otherwise, return 0.
    """
    if not cuisine_preference:
        return 50.0
    pref_lower = cuisine_preference.lower()
    recipe_cuisine = (recipe.cuisine or "").lower()
    if pref_lower in recipe_cuisine:
        return 100.0
    return 0.0


# === Allergen check ===

# Allergen keyword map (maps allergen category → ingredient keywords).
# Tier 1.4 fix: matching is now done with word boundaries (regex \b) on BOTH
# sides to prevent false positives like "eggplant" matching "egg", "butter
# lettuce" matching "butter", "cream of tartar" matching "cream", "coconut
# milk" matching "milk" for dairy-allergic users (coconut milk is dairy-free).
# Plant qualifiers (almond, soy, oat, coconut, etc.) cause a keyword match to
# be ignored for dairy/eggs, since the ingredient is plant-based.
ALLERGEN_KEYWORDS: dict[str, list[str]] = {
    "dairy": ["milk", "cheese", "butter", "cream", "yogurt", "whey", "lactose",
              "ghee", "kibbeh", "niter kibbeh"],
    "gluten": ["wheat", "flour", "bread", "pasta", "couscous", "barley", "rye",
               "seitan", "bulgur", "farro", "spelt", "injera"],  # injera has gluten unless teff-only
    "soy": ["soy", "tofu", "tempeh", "edamame", "tamari", "soy sauce", "miso"],
    "nuts": ["almond", "cashew", "walnut", "pecan", "hazelnut", "pistachio",
             "brazil nut", "macadamia", "pine nut"],
    "peanuts": ["peanut", "groundnut"],
    "eggs": ["egg", "eggs", "mayonnaise", "meringue"],  # Tier 1.4: added plural
    "shellfish": ["shrimp", "prawn", "crab", "lobster", "crawfish", "langoustine"],
    "fish": ["salmon", "tuna", "cod", "tilapia", "sardine", "anchovy", "mackerel",
             "trout", "halibut", "fish"],
    "sesame": ["sesame", "tahini", "sesame oil"],
}

# Plant-based qualifiers that, when preceding a dairy/egg keyword, indicate
# the ingredient is dairy-free/egg-free (e.g. "almond milk", "vegan butter",
# "just egg", "flax egg"). For these allergens, a qualifier match suppresses
# the violation.
_PLANT_QUALIFIERS_FOR_ALLERGENS = (
    "almond", "soy", "oat", "rice", "coconut", "cashew", "hemp", "flax",
    "macadamia", "pea", "vegan", "plant", "dairy-free", "dairy free",
    "non-dairy", "nondairy", "peanut", "cocoa", "shea", "sunflower",
    "avocado", "apple", "agave", "maple", "date", "molasses",
    "vegenaise", "just egg", "egg replacer", "flax egg", "chia egg",
    "beyond", "impossible", "gardein", "tofu", "tempeh", "seitan",
    "vegetable", "veggie", "mushroom", "no-chicken", "no chicken",
    "chicken-style", "chicken style",
    "vegan beef", "vegan chicken", "vegan pork", "vegan fish",
)

# Plant-named phrases that contain a dairy/egg keyword as a substring but
# are themselves plant-based and safe for dairy/egg-allergic users.
# Tier 1.4 fix: includes "just egg", "flax egg", "chia egg", "egg replacer"
# as full phrases so the word-boundary egg match doesn't fire on them
# (the 25-char context check can't see "just egg" because "egg" is the
# matched word itself).
_PLANT_NAMED_PHRASES_FOR_ALLERGENS = (
    "eggplant", "eggsplant",
    "butter lettuce", "butterleaf", "buttercup squash",
    "cocoa butter", "shea butter",
    "cream of tartar", "creamed corn", "coconut cream",
    "almond butter", "peanut butter", "cashew butter", "sunflower butter",
    "apple butter", "pumpkin butter",
    "milk thistle", "milkweed",
    "honeydew", "honeycrisp",
    # Egg substitutes (plant-based):
    "just egg", "just eggs", "flax egg", "flax eggs", "chia egg", "chia eggs",
    "egg replacer", "egg substitute", "vegan egg", "vegan eggs",
)

# Pre-compile a word-boundary regex per allergen category for fast matching.
_ALLERGEN_REGEXES: dict[str, list[tuple[re.Pattern, str]]] = {
    allergen: [
        (re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE), kw)
        for kw in keywords
    ]
    for allergen, keywords in ALLERGEN_KEYWORDS.items()
}


def check_allergens(recipe: Recipe, allergens_to_avoid: list[str]) -> list[str]:
    """
    Check if recipe contains any allergens the user wants to avoid.

    Tier 1.4 fix: matching now uses word boundaries on both sides (so
    "eggplant" no longer matches "egg", "butter lettuce" no longer matches
    "butter"). For dairy and eggs specifically, plant-based qualifiers
    (almond, soy, oat, coconut, vegan, just-egg, flax-egg, etc.) and
    known plant-named phrases (eggplant, butter lettuce, cream of tartar,
    cocoa butter, etc.) suppress the violation, since those ingredients
    are dairy-free / egg-free.

    Returns list of violated allergens (empty if none).
    """
    if not allergens_to_avoid or not recipe.ingredients:
        return []

    violations = []
    combined_ingredients = " ".join(recipe.ingredients).lower()

    # Build a sanitized string with plant-named phrases blanked out, used
    # only for the dairy/egg allergen scans.
    sanitized = combined_ingredients
    for phrase in _PLANT_NAMED_PHRASES_FOR_ALLERGENS:
        sanitized = sanitized.replace(phrase, " " * len(phrase))

    for allergen in allergens_to_avoid:
        allergen_lower = allergen.lower().strip()
        patterns = _ALLERGEN_REGEXES.get(allergen_lower)
        if patterns is None:
            # Unknown allergen — fall back to plain word-boundary substring match.
            patterns = [(re.compile(r"\b" + re.escape(allergen_lower) + r"\b", re.IGNORECASE), allergen_lower)]
        # For dairy/eggs, scan the sanitized string (plant-named phrases removed).
        scan_target = sanitized if allergen_lower in ("dairy", "eggs") else combined_ingredients
        for pat, kw in patterns:
            found = False
            for m in pat.finditer(scan_target):
                # For dairy/eggs, check for a plant qualifier in the 25 chars
                # before the match. If present, this is a plant-based alternative
                # (almond milk, just egg, etc.) — not a violation.
                if allergen_lower in ("dairy", "eggs"):
                    context = scan_target[max(0, m.start() - 25):m.start()]
                    if any(pq in context for pq in _PLANT_QUALIFIERS_FOR_ALLERGENS):
                        continue
                found = True
                break
            if found:
                violations.append(allergen)
                break

    return violations


# === Excluded ingredients check ===

def check_excluded_ingredients(recipe: Recipe, excluded_ingredients: list[str]) -> list[str]:
    """
    Check if recipe contains any explicitly excluded ingredients.

    Returns list of found excluded ingredients.
    """
    if not excluded_ingredients or not recipe.ingredients:
        return []

    found = []
    combined = " ".join(recipe.ingredients).lower()

    for ing in excluded_ingredients:
        if ing.lower().strip() in combined:
            found.append(ing)

    return found


# === Main scorer ===

def score_recipe_for_slot(
    recipe: Recipe,
    slot: MealSlotTarget,
    diet_tag: str,
    user_goal: str = "maintenance",
    cuisine_preference: Optional[str] = None,
    allergens_to_avoid: Optional[list[str]] = None,
    excluded_ingredients: Optional[list[str]] = None,
    used_recipe_ids_last_3_days: Optional[set[str]] = None,
    used_recipe_ids_last_7_days: Optional[set[str]] = None,
) -> RecipeScore:
    """
    Score a single recipe against a meal slot target.

    Returns RecipeScore with total_score, component breakdown, and any
    allergen violations or exclusion reasons.
    """
    allergens_to_avoid = allergens_to_avoid or []
    excluded_ingredients = excluded_ingredients or []
    used_3d = used_recipe_ids_last_3_days or set()
    used_7d = used_recipe_ids_last_7_days or set()

    components: dict[str, float] = {}

    # === Hard exclusions (return score 0 immediately) ===

    # Allergen check
    allergen_violations = check_allergens(recipe, allergens_to_avoid)
    if allergen_violations:
        return RecipeScore(
            recipe=recipe,
            total_score=0.0,
            component_scores={},
            allergen_violations=allergen_violations,
            excluded=True,
            exclusion_reason=f"Contains allergens: {', '.join(allergen_violations)}",
        )

    # Excluded ingredients check
    excluded_found = check_excluded_ingredients(recipe, excluded_ingredients)
    if excluded_found:
        return RecipeScore(
            recipe=recipe,
            total_score=0.0,
            component_scores={},
            allergen_violations=[],
            excluded=True,
            exclusion_reason=f"Contains excluded ingredients: {', '.join(excluded_found)}",
        )

    # Diet match (hard filter — if 0, exclude)
    diet_score = score_diet_match(recipe, diet_tag)
    if diet_score == 0.0:
        return RecipeScore(
            recipe=recipe,
            total_score=0.0,
            component_scores={"diet_match": 0.0},
            excluded=True,
            exclusion_reason=f"Diet mismatch: recipe={recipe.diet_types}, user={diet_tag}",
        )

    # === Soft scores ===

    components["kcal_match"] = score_kcal_match(recipe.kcal, slot.target_kcal)
    components["protein_match"] = score_protein_match(recipe.protein_g, slot.target_protein_g)
    components["carb_match"] = score_carb_match(recipe.carb_g, slot.target_carb_g)
    components["fat_match"] = score_fat_match(recipe.fat_g, slot.target_fat_g)
    components["diet_match"] = diet_score
    components["goal_fit"] = score_goal_fit(recipe, user_goal)
    components["fiber_match"] = score_fiber_match(recipe.fiber_g, slot.target_fiber_g)
    components["variety_bonus"] = score_variety(recipe, used_3d, used_7d)
    components["cuisine_match"] = score_cuisine(recipe, cuisine_preference)

    # Weighted sum
    total = sum(components.get(k, 0.0) * w / 100.0 for k, w in WEIGHTS.items())

    return RecipeScore(
        recipe=recipe,
        total_score=round(total, 2),
        component_scores=components,
        allergen_violations=[],
        excluded=False,
    )


def score_candidates(
    candidates: list[Recipe],
    slot: MealSlotTarget,
    diet_tag: str,
    user_goal: str = "maintenance",
    cuisine_preference: Optional[str] = None,
    allergens_to_avoid: Optional[list[str]] = None,
    excluded_ingredients: Optional[list[str]] = None,
    used_recipe_ids_last_3_days: Optional[set[str]] = None,
    used_recipe_ids_last_7_days: Optional[set[str]] = None,
) -> list[RecipeScore]:
    """
    Score a list of candidate recipes for a slot.

    Returns list of RecipeScore sorted by total_score descending.
    Excluded recipes (allergen/diet violations) are filtered out.
    """
    scores = []
    for recipe in candidates:
        score = score_recipe_for_slot(
            recipe=recipe,
            slot=slot,
            diet_tag=diet_tag,
            user_goal=user_goal,
            cuisine_preference=cuisine_preference,
            allergens_to_avoid=allergens_to_avoid,
            excluded_ingredients=excluded_ingredients,
            used_recipe_ids_last_3_days=used_recipe_ids_last_3_days,
            used_recipe_ids_last_7_days=used_recipe_ids_last_7_days,
        )
        if not score.excluded:
            scores.append(score)

    scores.sort(key=lambda s: s.total_score, reverse=True)
    return scores


__all__ = [
    "WEIGHTS",
    "MIN_ACCEPTABLE_SCORE",
    "RecipeScore",
    "score_recipe_for_slot",
    "score_candidates",
    "score_kcal_match",
    "score_protein_match",
    "score_carb_match",
    "score_fat_match",
    "score_fiber_match",
    "score_diet_match",
    "score_goal_fit",
    "score_variety",
    "score_cuisine",
    "check_allergens",
    "check_excluded_ingredients",
    "ALLERGEN_KEYWORDS",
]

"""
Recipe loader — loads both curated and uncurated recipe databases and
merges them into a single recipe index.

Files:
  - fitness_engine/meal_plan/recipe_database.json          (107 curated)
  - fitness_engine/meal_plan/recipe_database_uncurated.json (370 uncurated)

Merge rules:
  - Both DBs use the same recipe ID space (R001, R002, ...) starting
    from R001. Curated IDs take precedence on collision (the curation
    layer is a quality filter on the uncurated pool).
  - Both DBs are loaded; curated recipes are tagged with `is_curated=True`
    (stored in notes) so the planner can prefer them.
  - The merged index preserves swap_groups from both DBs (curated wins
    on key collision).

Public API:
  - load_recipes() → list[Recipe]
  - get_recipe_by_id(id) → Recipe | None
  - recipes_by_meal_type(meal_type) → list[Recipe]
  - recipes_by_diet_type(diet_type) → list[Recipe]
  - recipes_by_cuisine(cuisine) → list[Recipe]
  - recipes_by_goal_fit(goal) → list[Recipe]
  - recipes_by_kcal_range(lo, hi) → list[Recipe]
  - recipes_in_swap_group(group_key) → list[str]  (returns recipe IDs)
  - swap_groups() → dict[str, list[str]]
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from ..models.meal import (
    Recipe,
    NutritionPerServing,
)


# === Path resolution ===
_MEAL_PLAN_DIR = Path(__file__).resolve().parent
_CURATED_DB_PATH = _MEAL_PLAN_DIR / "recipe_database.json"
_UNCURATED_DB_PATH = _MEAL_PLAN_DIR / "recipe_database_uncurated.json"


# === JSON → Recipe ===

def _parse_nutrition(raw: dict) -> NutritionPerServing:
    """Parse the nutrition_per_serving sub-dict."""
    if not raw:
        return NutritionPerServing()
    return NutritionPerServing(
        kcal=float(raw.get("kcal") or 0),
        protein_g=float(raw.get("protein_g") or 0),
        carb_g=float(raw.get("carb_g") or 0),
        fat_g=float(raw.get("fat_g") or 0),
        fiber_g=float(raw.get("fiber_g") or 0),
        sugar_g=float(raw.get("sugar_g") or 0),
    )


# === Diet sanity check ===
# The recipe DB has a few mis-tagged recipes (e.g. "Easy Baked Corned Beef
# and Cabbage" is tagged VEGAN despite containing corned beef). We flag
# suspicious recipes so consumers can choose to filter them out.
#
# Heuristic: scan ingredients for animal-product keywords. To avoid false
# positives:
#   - Use word-boundary matching (so "lard" doesn't match "collards")
#   - Exclude plant-based substitutes (e.g. "almond milk", "peanut butter",
#     "cocoa butter", "vegan butter", "Beyond Beef", "Just Egg")

import re

# Strict animal-product keywords (always non-vegan) — matched as whole words
_STRICT_MEAT_KEYWORDS = (
    "beef", "pork", "chicken", "turkey", "duck", "lamb", "veal", "venison",
    "goose", "rabbit", "bacon", "sausage", "ham", "steak", "brisket",
    "salami", "pepperoni", "salmon", "tuna", "cod", "shrimp", "tilapia",
    "trout", "mackerel", "sardine", "anchovy", "halibut", "lobster",
    "crab", "clam", "mussel", "oyster", "scallop", "squid", "octopus",
    "gelatin", "rennet", "lard", "tallow", "suet", "worcestershire",
)

# Multi-word strict phrases (substring match is fine since they're specific)
_STRICT_MEAT_PHRASES = (
    "corned beef", "ground beef", "ground turkey", "ground pork",
    "pork loin", "pork chop", "fish sauce", "fish stock",
    "anchovy paste", "shrimp paste", "oyster sauce", "bone broth",
    "sea bass", "seafood",
)

# Conditional keywords — only flag if NOT preceded by a plant qualifier
# (e.g. "almond milk", "soy milk", "oat milk", "coconut milk", "vegan butter")
_CONDITIONAL_KEYWORDS = ("milk", "butter", "cream", "cheese", "yogurt", "whey", "egg", "honey", "broth")

_PLANT_QUALIFIERS = (
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

# Tier 1.4 fix: plant-named items that contain a conditional keyword as a
# SUBSTRING but are themselves plant-based. These are matched as whole-word
# phrases so they short-circuit the conditional keyword check.
_PLANT_NAMED_PHRASES = (
    "eggplant", "eggsplant",          # contains "egg"
    "butter lettuce", "butterleaf",   # contains "butter"
    "buttercup squash",               # contains "butter"
    "cocoa butter", "shea butter",    # already covered by qualifiers, listed for clarity
    "cream of tartar",                # contains "cream"
    "creamed corn",                   # contains "cream" — vegetarian
    "coconut cream",                  # already covered by qualifiers
    "almond butter", "peanut butter", "cashew butter", "sunflower butter",
    "apple butter", "pumpkin butter",
    "milk thistle", "milkweed",       # plants containing "milk"
    "honeydew", "honeycrisp",         # fruits containing "honey"
    "broth of",  # generic; vegetable broth is covered by "vegetable" qualifier
)

# Compile strict-word regex (word-boundary match)
_STRICT_WORD_RE = re.compile(
    r"\b(" + "|".join(_STRICT_MEAT_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

# Tier 1.4 fix: compile conditional keywords with word boundaries on BOTH sides.
# This prevents "egg" from matching inside "eggplant", "butter" inside
# "butter lettuce", "cream" inside "cream of tartar", etc.
_CONDITIONAL_WORD_RE = re.compile(
    r"\b(" + "|".join(_CONDITIONAL_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


def _recipe_has_meat_ingredients(recipe: Recipe) -> bool:
    """
    Heuristic: scan ingredients for animal-product keywords.

    Strict keywords (beef, chicken, salmon, etc.) are matched with word
    boundaries (so "lard" doesn't match "collards").
    Conditional keywords (milk, butter, egg, honey, broth) only flag if
    NOT preceded by a plant-based qualifier (almond, soy, oat, coconut,
    Beyond, Impossible, etc.) AND not part of a known plant-named phrase
    (eggplant, butter lettuce, cream of tartar, etc.).

    Tier 1.4 fix: previously the conditional-keyword loop only checked the
    character BEFORE the keyword (so "eggplant" matched "egg" at pos=0 and
    skipped the boundary check) and never checked the character AFTER. Now
    we use a proper word-boundary regex on both sides, plus an explicit
    plant-named-phrase blocklist.
    """
    if not recipe.ingredients:
        return False
    combined = " ".join(recipe.ingredients).lower()

    # 0. Tier 1.4 fix: short-circuit on plant-named phrases that contain a
    # conditional keyword as a substring. If the ONLY occurrence of a
    # conditional keyword is inside one of these phrases, we should not flag.
    # We handle this by removing these phrases from the combined string
    # before the conditional-keyword scan. Strict keywords (meat) are not
    # affected.
    sanitized = combined
    for phrase in _PLANT_NAMED_PHRASES:
        sanitized = sanitized.replace(phrase, " " * len(phrase))

    # 1. Strict multi-word phrases — always flag (substring is fine here)
    for phrase in _STRICT_MEAT_PHRASES:
        if phrase in combined:
            # But check for "beyond beef" / "impossible beef" / "no-chicken broth" qualifier
            pos = combined.find(phrase)
            context = combined[max(0, pos - 25):pos]
            # Tier 1.4 fix: use the full _PLANT_QUALIFIERS list (was only 3 entries).
            # This catches "no-chicken broth", "vegan beef", "beyond beef", etc.
            if not any(pq in context for pq in _PLANT_QUALIFIERS):
                return True

    # 2. Strict single-word keywords with word boundaries
    for m in _STRICT_WORD_RE.finditer(combined):
        kw = m.group(1)
        # Check for plant qualifier in 25 chars before
        context = combined[max(0, m.start() - 25):m.start()]
        # Tier 1.4 fix: use the full _PLANT_QUALIFIERS list (was only 3 entries).
        if not any(pq in context for pq in _PLANT_QUALIFIERS):
            # Tier 1.4 fix: also check for "no-" or "no " immediately before the
            # keyword (e.g. "no-chicken broth", "no beef stock"). The qualifier
            # list includes "no-chicken" / "no chicken" but those phrases include
            # the keyword itself, so they can't appear in the BEFORE context.
            # We check the 4 chars immediately before the match for "no-" or "no ".
            immediate_prefix = combined[max(0, m.start() - 4):m.start()]
            if not (immediate_prefix.endswith("no-") or immediate_prefix.endswith("no ")):
                return True

    # 3. Conditional keywords with word boundaries on BOTH sides (Tier 1.4 fix).
    # Uses the sanitized string so plant-named phrases (eggplant, butter lettuce,
    # cream of tartar) don't false-positive.
    for m in _CONDITIONAL_WORD_RE.finditer(sanitized):
        # Check the 25 chars before the keyword for a plant qualifier
        context = sanitized[max(0, m.start() - 25):m.start()]
        has_plant_qualifier = any(pq in context for pq in _PLANT_QUALIFIERS)
        if not has_plant_qualifier:
            return True

    return False


def _check_kcal_macro_consistency(recipe: Recipe) -> str | None:
    """
    Tier 3.40 fix: verify that the stated kcal matches the macro-derived kcal
    (P*4 + C*4 + F*9) within 10%. Returns a warning string if inconsistent,
    None if OK.

    This catches curation errors like R001 (324 kcal stated but ingredients
    imply ~1900 kcal) and R003 (210 kcal stated but ~770 kcal expected).
    """
    n = recipe.nutrition_per_serving
    if n is None or n.kcal <= 0:
        return None
    macro_kcal = (n.protein_g * 4) + (n.carb_g * 4) + (n.fat_g * 9)
    if macro_kcal <= 0:
        return None
    delta_pct = abs(n.kcal - macro_kcal) / n.kcal
    if delta_pct > 0.10:  # >10% off
        return (
            f"[kcal-warning: stated {n.kcal:.0f} kcal vs macro-derived "
            f"{macro_kcal:.0f} kcal ({delta_pct*100:.0f}% off) — likely a "
            f"curation error in servings or per-serving values]"
        )
    return None


def _sanitize_recipe(recipe: Recipe) -> Recipe:
    """
    Flag suspicious diet_type tags and kcal/macro inconsistencies.

    If a recipe is tagged VEGAN but its ingredients contain meat/dairy/eggs,
    add a `[diet-warning]` tag to notes so callers can filter it out.

    Tier 3.40 fix: also checks kcal-vs-macro consistency and adds a
    `[kcal-warning]` tag if the stated kcal is >10% off from P*4+C*4+F*9.
    """
    recipe_diets = [d.upper() for d in recipe.diet_types]
    is_tagged_vegan = any(
        d == "VEGAN" or d.startswith("VEGAN_") for d in recipe_diets
    )
    if is_tagged_vegan and _recipe_has_meat_ingredients(recipe):
        warning = (
            "[diet-warning: tagged VEGAN but ingredients contain "
            "meat/dairy/egg — likely a curation error]"
        )
        if warning not in (recipe.notes or ""):
            recipe.notes = (
                f"{recipe.notes or ''} {warning}".strip()
            )

    # Tier 3.40 fix: kcal-vs-macro consistency check
    kcal_warning = _check_kcal_macro_consistency(recipe)
    if kcal_warning and kcal_warning not in (recipe.notes or ""):
        recipe.notes = f"{recipe.notes or ''} {kcal_warning}".strip()

    return recipe


def _parse_recipe(raw: dict, is_curated: bool) -> Recipe:
    """Convert a raw JSON recipe dict into a Recipe dataclass."""
    notes = raw.get("notes") or ""
    if is_curated and "curated" not in notes.lower():
        notes = (notes + " [curated]").strip()

    recipe = Recipe(
        name=raw.get("name") or "Untitled",
        id=raw.get("id"),
        source=raw.get("source"),
        source_file=raw.get("source_file"),
        legacy_id=raw.get("legacy_id"),
        cuisine=raw.get("cuisine") or "american",
        category=raw.get("category") or "",
        recipe_kind=raw.get("recipe_kind") or "meal",
        meal_types=list(raw.get("meal_types") or []),
        diet_types=list(raw.get("diet_types") or []),
        goal_fit=list(raw.get("goal_fit") or []),
        servings=int(raw.get("servings") or 1),
        prep_time_min=raw.get("prep_time_min"),
        cook_time_min=raw.get("cook_time_min"),
        ingredients=list(raw.get("ingredients") or []),
        instructions=list(raw.get("instructions") or []),
        nutrition_per_serving=_parse_nutrition(raw.get("nutrition_per_serving")),
        nutrition_source=raw.get("nutrition_source") or "published",
        serving_size_g=raw.get("serving_size_g"),
        protein_density=raw.get("protein_density"),
        calorie_density=raw.get("calorie_density"),
        allergens=list(raw.get("allergens") or []),
        alternative_recipe_ids=list(raw.get("alternative_recipe_ids") or []),
        fasting_yetsom=bool(raw.get("fasting_yetsom")),
        injera_accompaniment=bool(raw.get("injera_accompaniment")),
        image_url=raw.get("image_url"),
        notes=notes,
        _extraction_method=raw.get("_extraction_method"),
    )
    return _sanitize_recipe(recipe)


# === Loader ===

@lru_cache(maxsize=1)
def _load_raw_dbs() -> tuple[dict, dict]:
    """Load and cache the raw JSON databases."""
    if not _CURATED_DB_PATH.exists():
        raise FileNotFoundError(
            f"Curated recipe database not found at {_CURATED_DB_PATH}"
        )
    if not _UNCURATED_DB_PATH.exists():
        raise FileNotFoundError(
            f"Uncurated recipe database not found at {_UNCURATED_DB_PATH}"
        )
    with open(_CURATED_DB_PATH, encoding="utf-8") as f:
        curated = json.load(f)
    with open(_UNCURATED_DB_PATH, encoding="utf-8") as f:
        uncurated = json.load(f)
    return curated, uncurated


# Tier 3.35 fix: module-level cache for parsed recipes. load_recipes() is called
# per meal slot (7 days × 3-5 slots = 21-35 calls per plan), and each call
# re-parses 460+ recipes with regex sanitization. The cache stores the parsed
# list so subsequent calls are O(1).
_RECIPES_CACHE: list[Recipe] | None = None


def load_recipes() -> list[Recipe]:
    """
    Load all recipes from both databases + Pre/Post Workout recipes.

    Returns a list of Recipe dataclasses. Curated recipes appear first
    (and override uncurated on ID collision). Pre/Post Workout recipes
    are appended last (Phase-5).

    Tier 3.35 fix: results are cached at module level. The first call pays
    the parse cost; subsequent calls return the cached list. Use
    `clear_recipes_cache()` to force a re-parse (e.g. in tests).
    """
    global _RECIPES_CACHE
    if _RECIPES_CACHE is not None:
        return _RECIPES_CACHE

    curated_db, uncurated_db = _load_raw_dbs()

    seen_ids: set[str] = set()
    out: list[Recipe] = []

    # Curated first
    for raw in curated_db.get("recipes", []):
        r = _parse_recipe(raw, is_curated=True)
        if r.id and r.id in seen_ids:
            continue
        if r.id:
            seen_ids.add(r.id)
        out.append(r)

    # Uncurated second (skip IDs already in curated)
    for raw in uncurated_db.get("recipes", []):
        r = _parse_recipe(raw, is_curated=False)
        if r.id and r.id in seen_ids:
            continue
        if r.id:
            seen_ids.add(r.id)
        out.append(r)

    # Phase-5: Pre/Post Workout recipes (engine-generated)
    try:
        from .pre_post_workout import get_pre_post_workout_recipes
        for r in get_pre_post_workout_recipes():
            if r.id and r.id in seen_ids:
                continue
            if r.id:
                seen_ids.add(r.id)
            out.append(r)
    except ImportError:
        pass  # pre_post_workout module not available

    _RECIPES_CACHE = out
    return out


def clear_recipes_cache() -> None:
    """Clear the recipes cache (for tests)."""
    global _RECIPES_CACHE
    _RECIPES_CACHE = None


# === Convenience indexes (built lazily) ===

@lru_cache(maxsize=1)
def _build_indexes() -> tuple[dict, dict, dict]:
    """Build id→Recipe, name→Recipe, and swap_groups indexes."""
    recipes = load_recipes()
    by_id = {r.id: r for r in recipes if r.id}
    by_name = {}
    for r in recipes:
        # last-write-wins on name collision (rare)
        by_name[r.name] = r

    curated_db, uncurated_db = _load_raw_dbs()
    # Merge swap_groups — curated wins on collision
    swap_groups: dict[str, list[str]] = {}
    # Uncurated first (so curated overrides)
    swap_groups.update(uncurated_db.get("swap_groups") or {})
    swap_groups.update(curated_db.get("swap_groups") or {})

    return by_id, by_name, swap_groups


def get_recipe_by_id(recipe_id: str) -> Optional[Recipe]:
    """Look up a recipe by its ID (e.g. 'R001')."""
    by_id, _, _ = _build_indexes()
    return by_id.get(recipe_id)


def get_recipe_by_name(name: str) -> Optional[Recipe]:
    """Look up a recipe by its display name."""
    _, by_name, _ = _build_indexes()
    return by_name.get(name)


def swap_groups() -> dict[str, list[str]]:
    """Return the merged swap_groups dict."""
    _, _, sg = _build_indexes()
    return sg


def recipes_in_swap_group(group_key: str) -> list[str]:
    """Return the list of recipe IDs in a given swap_group."""
    _, _, sg = _build_indexes()
    return list(sg.get(group_key, []))


# === Query functions ===

def recipes_by_meal_type(meal_type: str) -> list[Recipe]:
    """Return all recipes tagged with a given meal_type."""
    target = meal_type.lower()
    return [r for r in load_recipes() if target in [m.lower() for m in r.meal_types]]


def recipes_by_diet_type(diet_type: str) -> list[Recipe]:
    """Return all recipes tagged with a given diet_type."""
    target = diet_type.upper()
    return [r for r in load_recipes() if target in [d.upper() for d in r.diet_types]]


def recipes_by_cuisine(cuisine: str) -> list[Recipe]:
    """Return all recipes matching a cuisine (case-insensitive substring)."""
    target = cuisine.lower()
    return [r for r in load_recipes() if target in r.cuisine.lower()]


def recipes_by_goal_fit(goal: str) -> list[Recipe]:
    """Return all recipes whose goal_fit list contains `goal`."""
    target = goal.lower()
    return [r for r in load_recipes() if target in [g.lower() for g in r.goal_fit]]


def recipes_by_kcal_range(lo: float, hi: float) -> list[Recipe]:
    """Return all recipes whose per-serving kcal is in [lo, hi]."""
    return [
        r for r in load_recipes()
        if lo <= r.kcal <= hi and r.nutrition_source in ("published", "estimated")
    ]


def recipes_by_filters(
    meal_type: Optional[str] = None,
    diet_type: Optional[str] = None,
    cuisine: Optional[str] = None,
    goal_fit: Optional[str] = None,
    kcal_lo: Optional[float] = None,
    kcal_hi: Optional[float] = None,
    is_curated_only: bool = False,
    exclude_ids: Optional[set[str]] = None,
    exclude_diet_warnings: bool = False,
) -> list[Recipe]:
    """
    Multi-filter recipe query. All filters are AND-combined.

    Args:
      meal_type: "breakfast" / "lunch" / "dinner" / "snack" / "side"
      diet_type: "OMNI" / "VEGAN" / "VEGAN_ETHIOPIAN" / ...
        Special handling: VEGAN matches both VEGAN and VEGAN_ETHIOPIAN
        (the latter is a stricter subset of vegan).
      cuisine: substring match (e.g. "ethiopian", "indian", "american")
      goal_fit: "cut" / "bulk" / "recomp" / "maintenance"
      kcal_lo, kcal_hi: per-serving kcal range
      is_curated_only: only return curated recipes
      exclude_ids: set of recipe IDs to exclude (e.g. already used today)
      exclude_diet_warnings: if True, exclude recipes flagged with
        [diet-warning] (set automatically for VEGAN diet_type)
    """
    out = load_recipes()
    if meal_type:
        mt = meal_type.lower()
        out = [r for r in out if mt in [m.lower() for m in r.meal_types]]
    if diet_type:
        dt = diet_type.upper()
        if dt == "VEGAN":
            # Vegan users can eat anything tagged VEGAN or VEGAN_*
            out = [r for r in out if any(
                d.upper() == "VEGAN" or d.upper().startswith("VEGAN_")
                for d in r.diet_types
            )]
        elif dt == "OMNI":
            # Omni users can eat anything tagged OMNI or OMNI_* or VEGAN*
            # (vegan food is omni-compatible)
            out = [r for r in out if any(
                d.upper() == "OMNI" or d.upper().startswith("OMNI_")
                or d.upper() == "VEGAN" or d.upper().startswith("VEGAN_")
                for d in r.diet_types
            )]
        else:
            # Exact match for other diet types
            out = [r for r in out if dt in [d.upper() for d in r.diet_types]]
        # Phase-6 fix: filter diet-warnings universally (was VEGAN-only).
        # A "VEGAN" recipe whose ingredient scan flagged meat/dairy/eggs is a
        # curation error and should not be served to OMNI users either —
        # otherwise the same mislabeled recipe appears differently depending
        # on the user's diet tag, breaking cuisine_mix and is_vegan checks.
        out = [r for r in out if "[diet-warning" not in (r.notes or "")]
    if exclude_diet_warnings:
        out = [r for r in out if "[diet-warning" not in (r.notes or "")]
    if cuisine:
        c = cuisine.lower()
        out = [r for r in out if c in r.cuisine.lower()]
    if goal_fit:
        g = goal_fit.lower()
        out = [r for r in out if g in [gf.lower() for gf in r.goal_fit]]
    if kcal_lo is not None:
        out = [r for r in out if r.kcal >= kcal_lo]
    if kcal_hi is not None:
        out = [r for r in out if r.kcal <= kcal_hi]
    if is_curated_only:
        out = [r for r in out if "[curated]" in (r.notes or "")]
    if exclude_ids:
        out = [r for r in out if r.id not in exclude_ids]
    return out


# === Stats ===

def database_stats() -> dict:
    """Return summary stats about the loaded recipe databases."""
    curated_db, uncurated_db = _load_raw_dbs()
    recipes = load_recipes()
    curated_count = sum(1 for r in recipes if "[curated]" in (r.notes or ""))
    uncurated_count = len(recipes) - curated_count

    from collections import Counter
    meal_dist = Counter()
    diet_dist = Counter()
    cuisine_dist = Counter()
    goal_dist = Counter()
    for r in recipes:
        for m in r.meal_types:
            meal_dist[m] += 1
        for d in r.diet_types:
            diet_dist[d] += 1
        cuisine_dist[r.cuisine] += 1
        for g in r.goal_fit:
            goal_dist[g] += 1

    return {
        "total_recipes": len(recipes),
        "curated_count": curated_count,
        "uncurated_count": uncurated_count,
        "raw_curated_total": curated_db.get("total_recipes", curated_count),
        "raw_uncurated_total": uncurated_db.get("total_recipes", uncurated_count),
        "swap_group_count": len(swap_groups()),
        "meal_type_distribution": dict(meal_dist),
        "diet_type_distribution": dict(diet_dist),
        "cuisine_distribution": dict(cuisine_dist.most_common(20)),
        "goal_fit_distribution": dict(goal_dist),
    }


__all__ = [
    "load_recipes",
    "get_recipe_by_id",
    "get_recipe_by_name",
    "swap_groups",
    "recipes_in_swap_group",
    "recipes_by_meal_type",
    "recipes_by_diet_type",
    "recipes_by_cuisine",
    "recipes_by_goal_fit",
    "recipes_by_kcal_range",
    "recipes_by_filters",
    "database_stats",
]

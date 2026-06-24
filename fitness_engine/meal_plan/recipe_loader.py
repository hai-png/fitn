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

# Compile strict-word regex (word-boundary match)
_STRICT_WORD_RE = re.compile(
    r"\b(" + "|".join(_STRICT_MEAT_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


def _recipe_has_meat_ingredients(recipe: Recipe) -> bool:
    """
    Heuristic: scan ingredients for animal-product keywords.

    Strict keywords (beef, chicken, salmon, etc.) are matched with word
    boundaries (so "lard" doesn't match "collards").
    Conditional keywords (milk, butter, egg, honey, broth) only flag if
    NOT preceded by a plant-based qualifier (almond, soy, oat, coconut,
    Beyond, Impossible, etc.).
    """
    if not recipe.ingredients:
        return False
    combined = " ".join(recipe.ingredients).lower()

    # 1. Strict multi-word phrases — always flag (substring is fine here)
    for phrase in _STRICT_MEAT_PHRASES:
        if phrase in combined:
            # But check for "beyond beef" / "impossible beef" qualifier
            pos = combined.find(phrase)
            context = combined[max(0, pos - 25):pos]
            if not any(pq in context for pq in ("beyond", "impossible", "vegan")):
                return True

    # 2. Strict single-word keywords with word boundaries
    for m in _STRICT_WORD_RE.finditer(combined):
        kw = m.group(1)
        # Check for plant qualifier in 25 chars before
        context = combined[max(0, m.start() - 25):m.start()]
        if not any(pq in context for pq in _PLANT_QUALIFIERS):
            return True

    # 3. Conditional keywords — check for plant qualifier in 20 chars before
    for kw in _CONDITIONAL_KEYWORDS:
        idx = 0
        while True:
            pos = combined.find(kw, idx)
            if pos == -1:
                break
            # Use word boundary: char before must be space or start
            if pos > 0 and combined[pos - 1].isalpha():
                idx = pos + len(kw)
                continue
            # Check the 20 chars before the keyword for a plant qualifier
            context = combined[max(0, pos - 20):pos]
            has_plant_qualifier = any(pq in context for pq in _PLANT_QUALIFIERS)
            if not has_plant_qualifier:
                return True
            idx = pos + len(kw)

    return False


def _sanitize_recipe(recipe: Recipe) -> Recipe:
    """
    Flag suspicious diet_type tags.

    If a recipe is tagged VEGAN but its ingredients contain meat/dairy/eggs,
    add a `[diet-warning]` tag to notes so callers can filter it out.
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


def load_recipes() -> list[Recipe]:
    """
    Load all recipes from both databases.

    Returns a list of Recipe dataclasses. Curated recipes appear first
    (and override uncurated on ID collision).
    """
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

    return out


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
            # Always exclude diet-warnings for vegan queries
            out = [r for r in out if "[diet-warning" not in (r.notes or "")]
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

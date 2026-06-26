#!/usr/bin/env python3
"""
Recipe database curation pipeline (v3.1.4).

Builds the engine-compatible ``recipe_database.json`` from the raw uploaded
``recipe_database.json`` (schema A: flat fields, lowercase tags) by:

  1. Cleaning + validating each raw recipe (null fiber → 0, missing servings → 1).
  2. Selecting a curated subset via a 6-phase pipeline:
       Phase 1: Nutritional set cover (greedy)
       Phase 2: Variety per (cuisine_cat × meal_type)
       Phase 3: Cuisine diversity floor (every cuisine ≥ 1 recipe)
       Phase 4: Ethiopian/non-Ethiopian balance (~30%)
       Phase 5: Graph deduplication (title similarity + cal/protein proximity)
       Phase 6: Size boundary enforcement (target_min ≤ count ≤ target_max)
  3. Transforming each selected recipe from schema A → schema B (the engine's
     ``Recipe`` dataclass format):
       - Rename: title→name, image→image_url, meal_type→meal_types, url→source
       - Nest nutrition: flat calories/protein_g/carbs_g/fat_g/fiber_g/sugar_g
         → nutrition_per_serving.{kcal,protein_g,carb_g,fat_g,fiber_g,sugar_g}
         (note: carb_g not carbs_g, kcal not calories)
       - Normalize diet_tags: lowercase ["vegan","gluten-free"] → UPPERCASE
         engine tags ["VEGAN"] (only 5 valid: OMNI/OMNI_ETHIOPIAN/VEGAN/
         VEGAN_ETHIOPIAN/VEGETARIAN)
       - Lowercase cuisine: "American" → "american"
       - Derive allergens from ingredients (dairy/eggs/gluten/nuts/peanuts/
         soy/shellfish/fish/sesame)
       - Derive goal_fit from calorie/protein profile (cut/bulk/recomp/
         maintenance)
       - Compute protein_density + calorie_density (low/medium/high)
       - Set Ethiopian cultural flags (fasting_yetsom, injera_accompaniment)
       - Assign recipe IDs (R001, R002, …)
       - Compute total_time_min = prep_time_min + cook_time_min
       - Validate nutritional consistency (kcal ≈ P*4 + C*4 + F*9 ± 10%)
  4. Writing the curated DB + a human-readable audit log + machine-readable
     JSON audit.

Usage:
  python scripts/curate_recipe_db.py [--input PATH] [--output PATH]
          [--audit-txt PATH] [--audit-json PATH]
          [--target-min N] [--target-max N] [--eth-target RATIO]

Defaults:
  --input      fitness_engine/meal_plan/recipe_database_uncurated.json
  --output     fitness_engine/meal_plan/recipe_database.json
  --audit-txt  download/curation_audit.txt
  --audit-json download/curation_audit.json
  --target-min 80
  --target-max 120
  --eth-target 0.30

Idempotent: re-running on the same input produces identical output.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

# ══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════

# Variety targets per (cuisine_category × meal_type).
# Below these → recipe allocator runs out of candidates and produces
# filler-only meals. Tuned for a 7-day plan with 4 meals/day.
DEFAULT_VARIETY = {
    ("ethiopian", "breakfast"): 3,
    ("ethiopian", "lunch"): 5,
    ("ethiopian", "dinner"): 5,
    ("ethiopian", "snack"): 3,
    ("ethiopian", "dessert"): 2,
    ("ethiopian", "shake"): 1,
    ("non_ethiopian", "breakfast"): 5,
    ("non_ethiopian", "lunch"): 6,
    ("non_ethiopian", "dinner"): 6,
    ("non_ethiopian", "snack"): 5,
    ("non_ethiopian", "dessert"): 3,
    ("non_ethiopian", "shake"): 4,
}

# Engine-compatible diet tags (must match models/meal.py::RecipeDietTag).
VALID_DIET_TAGS = {"OMNI", "OMNI_ETHIOPIAN", "VEGAN", "VEGAN_ETHIOPIAN", "VEGETARIAN"}

# Allergen categories → ingredient keywords (word-boundary regex).
# Used to derive the engine's `allergens` list from raw ingredients.
ALLERGEN_KEYWORDS = {
    "dairy": {"milk", "cream", "butter", "cheese", "yogurt", "whey", "lactose",
              "ghee", "paneer", "ricotta", "mozzarella", "parmesan", "feta",
              "buttermilk", "sour cream", "cream cheese"},
    "eggs": {"egg", "eggs", "yolk", "egg white", "egg yolk", "meringue",
             "mayonnaise"},
    "gluten": {"wheat", "flour", "bread", "pasta", "couscous", "bulgur", "spelt",
               "barley", "rye", "seitan", "soy sauce"},
    "nuts": {"almond", "walnut", "cashew", "pecan", "hazelnut", "pistachio",
             "brazil nut", "macadamia"},
    "peanuts": {"peanut", "peanut butter"},
    "soy": {"soy", "tofu", "tempeh", "edamame", "tamari", "miso"},
    "shellfish": {"shrimp", "prawn", "crab", "lobster", "crawfish"},
    "fish": {"salmon", "tuna", "cod", "tilapia", "sardine", "mackerel",
             "trout", "anchovy", "halibut"},
    "sesame": {"sesame", "tahini"},
}

# Plant-qualifier phrases that suppress an allergen match (e.g. "coconut milk"
# is NOT dairy). Mirrors the existing curate_recipes.py logic.
PLANT_QUALIFIERS = (
    "coconut", "almond", "soy", "oat", "rice", "hemp", "cashew",
    "macadamia", "pea", "flax", "vegan", "plant-based", "non-dairy",
    "dairy-free", "egg-free", "eggless", "egg replacer", "nutritional yeast",
)

# False-positive compounds (e.g. "butternut" contains "butter" but is a squash).
FALSE_POSITIVE_WORDS = {
    "butternut", "eggplant", "peanut butter",  # peanut butter is in peanuts, not nuts
    "coconut butter", "cocoa butter", "shea butter", "mango butter",
    "apple butter", "pumpkin butter", "cashew butter", "almond butter",
    "sunflower butter",
}

# Meat/animal keywords for VEGAN/VEGETARIAN re-tagging.
STRICT_MEAT_KEYWORDS = {
    "chicken", "beef", "pork", "turkey", "lamb", "veal", "venison", "bison",
    "duck", "goose", "rabbit", "salmon", "tuna", "cod", "tilapia", "shrimp",
    "prawn", "crab", "lobster", "sardine", "mackerel", "trout", "anchovy",
    "bacon", "ham", "sausage", "pepperoni", "salami", "prosciutto", "pancetta",
    "steak", "minced", "ground beef", "ground turkey",
    "brisket", "flank", "sirloin", "ribeye", "tenderloin",
    "fish sauce", "oyster sauce", "worcestershire",
    "chicken stock", "beef stock", "fish stock",
    "gelatin", "rennet",
    "honey",
}
EGG_KEYWORDS = {"egg", "eggs", "yolk", "egg white", "meringue"}
DAIRY_KEYWORDS = ALLERGEN_KEYWORDS["dairy"]


# ══════════════════════════════════════════════════════════════════
# PHASE 0: CLEANING + VALIDATION
# ══════════════════════════════════════════════════════════════════

def clean_recipe(raw: dict) -> dict:
    """Clean + validate a single raw recipe (schema A in, schema A out).

    - Coerces null numeric fields to 0 (fiber_g, sugar_g) or 1 (servings).
    - Strips whitespace from title, cuisine, description.
    - Lowercases meal_type entries.
    - Drops recipes missing required fields (title, ingredients, calories).
    """
    r = dict(raw)
    # Required fields
    title = (r.get("title") or "").strip()
    if not title:
        return None  # type: ignore[return-value]
    ingredients = r.get("ingredients") or []
    if not isinstance(ingredients, list) or not ingredients:
        return None  # type: ignore[return-value]
    calories = r.get("calories")
    if calories is None or not isinstance(calories, (int, float)):
        return None  # type: ignore[return-value]
    r["title"] = title
    r["ingredients"] = [str(i).strip() for i in ingredients if i]
    r["calories"] = float(calories)
    # Nullable numeric fields → 0 (engine expects numeric)
    for f in ("protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g"):
        v = r.get(f)
        r[f] = float(v) if isinstance(v, (int, float)) else 0.0
    # Servings → 1 if missing
    s = r.get("servings")
    r["servings"] = int(s) if isinstance(s, (int, float)) and s > 0 else 1
    # Cuisine → strip + lowercase (engine wants lowercase)
    c = (r.get("cuisine") or "american").strip()
    r["cuisine"] = c.lower() if c else "american"
    # meal_type → lowercase list
    mt = r.get("meal_type") or []
    r["meal_type"] = [str(m).strip().lower() for m in mt if m]
    # diet_tags → lowercase list (will be normalized to UPPERCASE later)
    dt = r.get("diet_tags") or []
    r["diet_tags"] = [str(d).strip().lower() for d in dt if d]
    # Description → strip
    r["description"] = (r.get("description") or "").strip()
    # Instructions → list of strings
    inst = r.get("instructions") or []
    if isinstance(inst, list):
        r["instructions"] = [str(i).strip() for i in inst if i]
    else:
        r["instructions"] = [str(inst).strip()]
    # Prep/cook time → int or None
    for f in ("prep_time_min", "cook_time_min"):
        v = r.get(f)
        r[f] = int(v) if isinstance(v, (int, float)) and v >= 0 else None
    # Compute total_time_min (engine uses this as a property)
    if r["prep_time_min"] is not None and r["cook_time_min"] is not None:
        r["total_time_min"] = r["prep_time_min"] + r["cook_time_min"]
    else:
        r["total_time_min"] = None
    return r


def reclassify_diet_tags(
    ingredients: list[str], current_tags: list[str], cuisine: str = "",
) -> tuple[list[str], str]:
    """Re-classify diet tags based on actual ingredients.

    Returns (new_tags, change_reason). The new tags are in the engine's
    UPPERCASE format: OMNI / OMNI_ETHIOPIAN / VEGAN / VEGAN_ETHIOPIAN / VEGETARIAN.

    Logic:
      1. If any ingredient contains a strict meat keyword → OMNI (or OMNI_ETHIOPIAN
         if cuisine is ethiopian).
      2. Else if any ingredient contains an egg keyword → VEGETARIAN.
      3. Else if any ingredient contains a dairy keyword → VEGETARIAN.
      4. Else → VEGAN (or VEGAN_ETHIOPIAN if cuisine is ethiopian).

    Plant-qualifier phrases (coconut milk, almond milk) suppress dairy matches.

    v3.1.4 fix: the Ethiopian check now uses the ``cuisine`` field (not just
    the current tags, which in the raw DB don't contain "ethiopian" even for
    Ethiopian recipes).
    """
    has_meat, _kw = _has_keyword(ingredients, STRICT_MEAT_KEYWORDS)
    has_egg, _ = _has_keyword(ingredients, EGG_KEYWORDS)
    has_dairy, _ = _has_keyword(ingredients, DAIRY_KEYWORDS)

    # Check if recipe is Ethiopian: by cuisine OR by existing ETHIOPIAN tag.
    is_ethiopian = (
        "ethiopian" in (cuisine or "").lower()
        or any("ethiopian" in t for t in current_tags)
    )

    if has_meat:
        return (["OMNI_ETHIOPIAN"] if is_ethiopian else ["OMNI"]), "contains meat/fish"
    if has_egg or has_dairy:
        # Vegetarian isn't a valid engine tag for non-Ethiopian — use OMNI.
        # (VEGETARIAN is in the enum but not in the loader's filter logic
        # for OMNI/VEGAN; we err on the side of OMNI for safety.)
        return (["OMNI_ETHIOPIAN"] if is_ethiopian else ["OMNI"]), "contains eggs/dairy"
    return (["VEGAN_ETHIOPIAN"] if is_ethiopian else ["VEGAN"]), "plant-based"


def _has_keyword(ingredients: list[str], keywords: set[str]) -> tuple[bool, str]:
    """Word-boundary regex match for any keyword, with plant-qualifier + false-positive suppression."""
    for ing in ingredients:
        ing_lower = ing.lower()
        # Skip if any plant-qualifier is present in this ingredient.
        if any(pq in ing_lower for pq in PLANT_QUALIFIERS):
            continue
        # Skip false-positive compounds.
        if any(fp in ing_lower for fp in FALSE_POSITIVE_WORDS):
            continue
        for kw in keywords:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, ing_lower):
                return True, kw
    return False, ""


def extract_allergens(ingredients: list[str]) -> list[str]:
    """Extract the engine's `allergens` list from ingredients.

    Returns a sorted list of allergen categories present: e.g.
    ["dairy", "eggs", "gluten"]. Uses plant-qualifier suppression so
    "coconut milk" doesn't trigger "dairy".
    """
    found = set()
    for allergen, keywords in ALLERGEN_KEYWORDS.items():
        has, _ = _has_keyword(ingredients, keywords)
        if has:
            found.add(allergen)
    return sorted(found)


def compute_goal_fit(calories: float, protein_g: float, carbs_g: float, fat_g: float) -> list[str]:
    """Derive the engine's `goal_fit` list from the recipe's macro profile.

    Returns a subset of ["cut","bulk","recomp","maintenance"].
    Logic:
      - cut: ≤400 kcal AND ≥25g protein (low-cal high-protein)
      - bulk: ≥500 kcal AND ≥30g protein (high-calorie mass builder)
      - recomp: 300-500 kcal AND ≥25g protein (balanced)
      - maintenance: 300-600 kcal AND ≥15g protein (general)
    """
    fits = []
    if calories <= 400 and protein_g >= 25:
        fits.append("cut")
    if calories >= 500 and protein_g >= 30:
        fits.append("bulk")
    if 300 <= calories <= 500 and protein_g >= 25:
        fits.append("recomp")
    if 300 <= calories <= 600 and protein_g >= 15:
        fits.append("maintenance")
    # Always include at least one
    if not fits:
        fits.append("maintenance")
    return fits


def compute_density(value: float, low_threshold: float, high_threshold: float) -> str:
    """Classify a density value as low/medium/high."""
    if value >= high_threshold:
        return "high"
    if value >= low_threshold:
        return "medium"
    return "low"


def compute_protein_density(calories: float, protein_g: float) -> str:
    """Protein density classification based on g protein per 100 kcal."""
    if calories <= 0:
        return "low"
    ratio = protein_g / calories * 100  # g per 100 kcal
    return compute_density(ratio, 7.0, 12.0)  # <7 low, 7-12 medium, ≥12 high


def compute_calorie_density(calories: float, servings: int) -> str:
    """Calorie density classification based on kcal per serving."""
    if servings <= 0:
        return "medium"
    return compute_density(calories, 300.0, 600.0)


def is_ethiopian_recipe(r: dict) -> bool:
    """True if the recipe is from EthiopianFood.org or has Ethiopian cuisine."""
    return (
        r.get("source") == "EthiopianFood.org"
        or "ethiopian" in (r.get("cuisine") or "").lower()
    )


def derive_ethiopian_flags(r: dict) -> tuple[bool, bool]:
    """Derive fasting_yetsom and injera_accompaniment flags.

    - fasting_yetsom: True if the recipe is vegan AND Ethiopian (Ethiopian
      Orthodox fasting diet is essentially vegan).
    - injera_accompaniment: True if the recipe is Ethiopian AND appears to be
      a stew/wat (served on injera). Heuristic: title contains "wat", "wot",
      "tibs", "shiro", "kitfo", "gomen", "misir", "kik", "yekik", "alecha".
    """
    is_eth = is_ethiopian_recipe(r)
    if not is_eth:
        return False, False
    diet_tags = [d.upper() for d in r.get("diet_tags", [])]
    is_vegan = any(d.startswith("VEGAN") for d in diet_tags)
    fasting_yetsom = is_vegan
    title_lower = r.get("title", "").lower()
    injera_keywords = ("wat", "wot", "tibs", "shiro", "kitfo", "gomen",
                       "misir", "kik", "yekik", "alecha", "firfir", "kitir")
    injera_accompaniment = any(kw in title_lower for kw in injera_keywords)
    return fasting_yetsom, injera_accompaniment


# ══════════════════════════════════════════════════════════════════
# PHASE 1-6: SELECTION PIPELINE (adapted from uploaded curate_database.py)
# ══════════════════════════════════════════════════════════════════

def _nut_dims(r: dict) -> set:
    """Nutritional dimensions for set-cover (calorie bucket, protein bucket,
    meal types, diet tags)."""
    d = set()
    cal = r.get("calories", 0)
    prot = r.get("protein_g", 0)
    # Calorie buckets
    if cal < 200: d.add("cal_<200")
    elif cal < 400: d.add("cal_200-400")
    elif cal < 600: d.add("cal_400-600")
    else: d.add("cal_600+")
    # Protein buckets
    if prot < 10: d.add("prot_<10g")
    elif prot < 20: d.add("prot_10-20g")
    elif prot < 30: d.add("prot_20-30g")
    elif prot < 40: d.add("prot_30-40g")
    else: d.add("prot_40g+")
    # Meal types + diet tags + cuisine
    for mt in r.get("meal_type", []): d.add(f"meal_{mt}")
    for dt in r.get("diet_tags", []): d.add(f"diet_{dt}")
    c = r.get("cuisine", "")
    if c: d.add(f"cuisine_{c}")
    return d


def _protein_density_score(r: dict) -> float:
    """Protein density score (g protein per kcal) — higher is better."""
    c, p = r.get("calories", 0), r.get("protein_g", 0)
    return p / c if (c and c > 0) else p / 500.0


def _title_similarity(t1: str, t2: str) -> float:
    """Jaccard similarity of stopword-stripped title tokens."""
    stop = {"recipe", "the", "a", "an", "with", "and", "in", "of", "for",
            "to", "on", "is", "how", "make", "best", "easy", "simple",
            "quick", "delicious", "healthy", "perfect", "homemade",
            "classic", "fresh", "creamy", "spicy", "savory", "sweet",
            "ultimate", "authentic", "amazing"}
    def norm(t):
        t = re.sub(r"[^\w\s]", "", t.lower().strip())
        t = re.sub(r"\s+", " ", t)
        return " ".join(w for w in t.split() if w not in stop)
    n1, n2 = norm(t1), norm(t2)
    if not n1 or not n2:
        return 0
    s1, s2 = set(n1.split()), set(n2.split())
    return len(s1 & s2) / len(s1 | s2)


def _is_essential(r: dict, selected: list, all_dims: set) -> bool:
    """True if removing r would leave any required nutritional dimension
    completely uncovered."""
    other_dims = set()
    for x in selected:
        if x["url"] != r["url"]:
            other_dims |= _nut_dims(x)
    r_dims = _nut_dims(r) & all_dims
    return len(r_dims - other_dims) > 0


def select_recipes(
    recipes: list[dict],
    target_min: int = 80,
    target_max: int = 120,
    eth_target: float = 0.30,
    eth_min: float = 0.20,
    eth_max: float = 0.50,
    variety: dict | None = None,
) -> tuple[list[dict], dict]:
    """Run the 6-phase selection pipeline. Returns (selected, audit_metadata)."""
    variety = variety or DEFAULT_VARIETY
    audit = {"phases": []}
    all_nut = set()
    for r in recipes:
        all_nut |= _nut_dims(r)

    # Phase 1: Nutritional set cover (greedy)
    remaining = set(all_nut)
    core = []
    pool = list(recipes)
    while remaining and pool:
        best_i = max(
            range(len(pool)),
            key=lambda i: (
                len(_nut_dims(pool[i]) & remaining),
                _protein_density_score(pool[i]),
                pool[i]["url"],
            ),
        )
        nd = _nut_dims(pool[best_i]) & remaining
        if not nd:
            break
        core.append(pool.pop(best_i))
        remaining -= nd
    selected = list(core)
    selected_urls = {r["url"] for r in selected}
    remaining_pool = [r for r in recipes if r["url"] not in selected_urls]
    audit["phases"].append({
        "phase": 1, "name": "nutritional_set_cover",
        "selected": len(selected), "dims_covered": len(all_nut) - len(remaining),
        "dims_total": len(all_nut),
    })

    # Phase 2: Variety per (cuisine_cat × meal_type)
    def _cc(r):
        return "ethiopian" if is_ethiopian_recipe(r) else "non_ethiopian"
    for ccat in ["ethiopian", "non_ethiopian"]:
        for mt in ["breakfast", "lunch", "dinner", "snack", "dessert", "shake"]:
            have = sum(1 for r in selected if _cc(r) == ccat and mt in r.get("meal_type", []))
            need = variety.get((ccat, mt), 1)
            add = max(0, need - have)
            if add <= 0:
                continue
            candidates = [r for r in remaining_pool
                         if _cc(r) == ccat and mt in r.get("meal_type", [])]
            candidates.sort(
                key=lambda r: (
                    len(_nut_dims(r) & remaining) if remaining else 0,
                    len(r.get("diet_tags", [])),
                    _protein_density_score(r),
                    r["url"],
                ),
                reverse=True,
            )
            for r in candidates[:add]:
                selected.append(r)
                selected_urls.add(r["url"])
                remaining = remaining - _nut_dims(r)
                remaining_pool = [x for x in remaining_pool if x["url"] != r["url"]]
    audit["phases"].append({
        "phase": 2, "name": "variety_per_cat_meal", "selected": len(selected),
        "ethiopian": sum(1 for r in selected if is_ethiopian_recipe(r)),
    })

    # Phase 3: Cuisine diversity floor (every cuisine ≥ 1)
    selected_cuisines = Counter(r.get("cuisine", "unknown") for r in selected)
    all_cuisines = sorted({r.get("cuisine") for r in recipes if r.get("cuisine")})
    missing = [c for c in all_cuisines
               if c != "ethiopian" and selected_cuisines.get(c, 0) == 0]
    for cuisine in missing:
        candidates = [r for r in remaining_pool if r.get("cuisine") == cuisine]
        if not candidates:
            continue
        candidates.sort(
            key=lambda r: (
                len(_nut_dims(r) & remaining) if remaining else 0,
                _protein_density_score(r),
                r["url"],
            ),
            reverse=True,
        )
        best = candidates[0]
        selected.append(best)
        selected_urls.add(best["url"])
        remaining_pool = [r for r in remaining_pool if r["url"] != best["url"]]
        remaining = remaining - _nut_dims(best)
    audit["phases"].append({
        "phase": 3, "name": "cuisine_diversity_floor", "selected": len(selected),
        "cuisines_covered": len({r.get("cuisine") for r in selected}),
    })

    # Phase 4: Ethiopian/non-Ethiopian balance
    def _adjust_balance(recipes_list, pool):
        eth = [r for r in recipes_list if is_ethiopian_recipe(r)]
        total = len(recipes_list)
        if total == 0:
            return recipes_list, pool
        ratio = len(eth) / total
        target_eth = max(int(total * eth_target), int(total * eth_min))
        target_eth = min(target_eth, int(total * eth_max))
        if len(eth) > target_eth:
            excess = len(eth) - target_eth
            eth_sorted = []
            for r in eth:
                if _is_essential(r, recipes_list, all_nut):
                    eth_sorted.append((999, r["url"], r))
                else:
                    other_dims = set.union(*[ _nut_dims(x) for x in recipes_list
                                              if x["url"] != r["url"]])
                    uniq = len(_nut_dims(r) - other_dims)
                    eth_sorted.append((uniq, r["url"], r))
            eth_sorted.sort(key=lambda x: (x[0], x[1]))
            to_remove = set()
            for uniq, url, r in eth_sorted:
                if len(to_remove) >= excess:
                    break
                if uniq == 999:
                    continue
                to_remove.add(url)
            recipes_list = [r for r in recipes_list if r["url"] not in to_remove]
        elif len(eth) < target_eth:
            need = target_eth - len(eth)
            candidates = [r for r in pool if is_ethiopian_recipe(r)]
            candidates.sort(
                key=lambda r: (
                    len(_nut_dims(r) & remaining) if remaining else 0,
                    _protein_density_score(r),
                    r["url"],
                ),
                reverse=True,
            )
            for r in candidates[:need]:
                recipes_list.append(r)
                pool = [x for x in pool if x["url"] != r["url"]]
        return recipes_list, pool
    selected, remaining_pool = _adjust_balance(selected, remaining_pool)
    audit["phases"].append({
        "phase": 4, "name": "ethiopian_balance", "selected": len(selected),
        "ethiopian": sum(1 for r in selected if is_ethiopian_recipe(r)),
    })

    # Phase 5: Size expansion (toward target_min) with Ethiopian bias
    while len(selected) < target_min and remaining_pool:
        cur_eth = sum(1 for r in selected if is_ethiopian_recipe(r))
        cur_ratio = cur_eth / len(selected) if selected else 0
        bias_eth = cur_ratio < eth_target
        candidates = []
        for r in remaining_pool:
            r_cc = _cc(r)
            # If below Ethiopian target, penalize non-Ethiopian candidates
            if bias_eth and r_cc == "non_ethiopian":
                score = -100
            elif not bias_eth and r_cc == "ethiopian":
                score = -100
            else:
                gap_fill = sum(
                    max(0, variety.get((r_cc, mt), 1) - sum(
                        1 for x in selected
                        if _cc(x) == r_cc and mt in x.get("meal_type", [])
                    ))
                    for mt in r.get("meal_type", [])
                )
                nut_gain = len(_nut_dims(r) & remaining) if remaining else 0
                diversity = 1 if r.get("cuisine", "") not in {
                    x.get("cuisine") for x in selected
                } else 0
                score = (gap_fill * 8 + nut_gain * 3 + diversity * 15 +
                         _protein_density_score(r) * 2)
            candidates.append((score, r["url"], r))
        candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        if not candidates or candidates[0][0] <= 0:
            break
        best = candidates[0][2]
        selected.append(best)
        selected_urls.add(best["url"])
        remaining = remaining - _nut_dims(best)
        remaining_pool = [r for r in remaining_pool if r["url"] != best["url"]]
    # v3.1.4: final balance pass after expansion
    selected, remaining_pool = _adjust_balance(selected, remaining_pool)
    audit["phases"].append({
        "phase": 5, "name": "size_expansion", "selected": len(selected),
        "ethiopian": sum(1 for r in selected if is_ethiopian_recipe(r)),
    })

    # Phase 6: Graph deduplication
    seen = {}
    deduped = []
    for r in selected:
        key = (r.get("source"), r.get("title", "").strip().lower())
        if key in seen:
            if _protein_density_score(r) > _protein_density_score(seen[key]):
                deduped = [x for x in deduped if x["url"] != seen[key]["url"]]
                deduped.append(r)
                seen[key] = r
        else:
            seen[key] = r
            deduped.append(r)
    # Connected-components dedup on title similarity
    adj = defaultdict(list)
    for i, j in combinations(range(len(deduped)), 2):
        r1, r2 = deduped[i], deduped[j]
        if r1.get("source") != r2.get("source"):
            continue
        sim = _title_similarity(r1.get("title", ""), r2.get("title", ""))
        if sim < 0.65:
            continue
        mt1, mt2 = set(r1.get("meal_type", [])), set(r2.get("meal_type", []))
        if mt1 and mt2 and not (mt1 & mt2):
            continue
        c1, c2 = r1.get("calories", 0), r2.get("calories", 0)
        if max(c1, c2) > 0 and min(c1, c2) / max(c1, c2) < 0.4:
            continue
        adj[i].append(j)
        adj[j].append(i)
    visited = set()
    to_remove = set()
    for i in range(len(deduped)):
        if i in visited:
            continue
        comp = []
        queue = [i]
        visited.add(i)
        while queue:
            curr = queue.pop(0)
            comp.append(curr)
            for nbr in adj[curr]:
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)
        if len(comp) > 1:
            comp_recipes = [deduped[idx] for idx in comp]
            comp_recipes.sort(
                key=lambda x: (
                    _is_essential(x, deduped, all_nut),
                    _protein_density_score(x),
                    x["url"],
                ),
                reverse=True,
            )
            for loser in comp_recipes[1:]:
                to_remove.add(loser["url"])
    selected = [r for r in deduped if r["url"] not in to_remove]
    audit["phases"].append({
        "phase": 6, "name": "graph_dedup", "selected": len(selected),
        "duplicates_removed": len(to_remove),
    })

    # Final boundary enforcement (trim if over target_max)
    while len(selected) > target_max:
        trim_candidates = []
        for r in selected:
            if _is_essential(r, selected, all_nut):
                continue
            score = _protein_density_score(r) * 10 + len(r.get("diet_tags", []))
            trim_candidates.append((score, r["url"], r))
        if not trim_candidates:
            break
        trim_candidates.sort(key=lambda x: (x[0], x[1]))
        removed = trim_candidates[0][2]
        selected = [x for x in selected if x["url"] != removed["url"]]

    audit["final_count"] = len(selected)
    audit["final_ethiopian"] = sum(1 for r in selected if is_ethiopian_recipe(r))
    audit["final_ethiopian_ratio"] = audit["final_ethiopian"] / max(1, len(selected))
    return selected, audit


# ══════════════════════════════════════════════════════════════════
# PHASE 7: SCHEMA-A → SCHEMA-B TRANSFORMATION
# ══════════════════════════════════════════════════════════════════

def compute_selection_reason(r: dict, goal_fit: list[str], all_recipes: list[dict]) -> str:
    """Compute a human-readable selection reason for a recipe.

    v3.1.5 Task 3: tags each recipe with WHY it was chosen, combining:
      - Cuisine (Ethiopian vs other)
      - Macro profile (high-protein, low-cal, high-cal, balanced)
      - Goal fit (cut/bulk/recomp/maintenance)
      - Meal-type coverage (breakfast/lunch/dinner/snack/dessert/shake)
      - Diet tag (vegan/omni)
    """
    parts = []
    is_eth = is_ethiopian_recipe(r)
    if is_eth:
        parts.append("Ethiopian cuisine")

    cal = r.get("calories", 0)
    prot = r.get("protein_g", 0)
    # Macro profile
    if prot >= 50 and cal >= 500:
        parts.append("High-protein high-calorie")
    elif prot >= 40:
        parts.append("High-protein")
    elif cal <= 200 and prot >= 20:
        parts.append("Protein-dense low-calorie")
    elif cal >= 600:
        parts.append("High-calorie option")
    elif cal <= 250:
        parts.append("Low-calorie")

    # Goal fit
    if goal_fit:
        if "cut" in goal_fit and "bulk" not in goal_fit:
            parts.append("for cutting")
        elif "bulk" in goal_fit and "cut" not in goal_fit:
            parts.append("for bulking")
        elif "recomp" in goal_fit:
            parts.append("for recomp")
        elif "maintenance" in goal_fit and len(goal_fit) == 1:
            parts.append("for maintenance")

    # Meal type
    meal_types = r.get("meal_type", [])
    if "breakfast" in meal_types:
        parts.append("breakfast option")
    elif "shake" in meal_types:
        parts.append("protein shake")
    elif "snack" in meal_types:
        parts.append("snack option")
    elif "dessert" in meal_types:
        parts.append("dessert option")

    # Diet
    diet_tags = [d.upper() for d in r.get("diet_tags", [])]
    if any(d.startswith("VEGAN") for d in diet_tags):
        parts.append("(vegan)")

    return "; ".join(parts) if parts else "General recipe"


def compute_top_alternatives(
    r: dict, all_recipes: list[dict], top_n: int = 5,
) -> list[dict]:
    """Compute top-N alternative recipes for a given recipe.

    v3.1.5 Task 3: finds the most similar recipes by:
      - Meal type overlap (30% weight)
      - Calorie similarity (25% weight)
      - Protein similarity (25% weight)
      - Cuisine match (20% weight)

    Returns a list of dicts: {"id", "name", "kcal", "protein_g", "cuisine",
    "similarity"} sorted by similarity descending.
    """
    r_mt = set(r.get("meal_type", []))
    r_cal = r.get("calories", 0)
    r_prot = r.get("protein_g", 0)
    r_cuisine = r.get("cuisine", "")
    r_id = r.get("_recipe_id", "")  # set by caller before this function

    scored = []
    for other in all_recipes:
        if other.get("title") == r.get("title"):
            continue  # skip self
        other_mt = set(other.get("meal_type", []))
        # Must share at least one meal type
        if not (r_mt & other_mt):
            continue
        # Similarity scores (0-1)
        other_cal = other.get("calories", 0)
        other_prot = other.get("protein_g", 0)
        # Calorie similarity: 1.0 when equal, 0.0 when 2× apart
        cal_sim = max(0, 1 - abs(r_cal - other_cal) / max(r_cal, other_cal, 1))
        # Protein similarity
        prot_sim = max(0, 1 - abs(r_prot - other_prot) / max(r_prot, other_prot, 1))
        # Meal type overlap (Jaccard)
        mt_sim = len(r_mt & other_mt) / max(len(r_mt | other_mt), 1)
        # Cuisine match
        cuisine_sim = 1.0 if r_cuisine == other.get("cuisine", "") else 0.0
        # Weighted total
        total = (mt_sim * 0.30 + cal_sim * 0.25 + prot_sim * 0.25 +
                 cuisine_sim * 0.20)
        scored.append((total, other))

    scored.sort(key=lambda x: x[0], reverse=True)
    alternatives = []
    for sim, other in scored[:top_n]:
        alternatives.append({
            "id": other.get("_recipe_id", ""),
            "name": other.get("title", ""),
            "kcal": round(other.get("calories", 0), 0),
            "protein_g": round(other.get("protein_g", 0), 0),
            "cuisine": other.get("cuisine", ""),
            "similarity": round(sim, 3),
        })
    return alternatives


def transform_to_engine_schema(
    selected: list[dict], start_id: int = 1,
) -> tuple[list[dict], list[str]]:
    """Transform selected recipes from schema A → schema B (engine format).

    Returns (transformed_recipes, audit_warnings).
    Assigns recipe IDs R001, R002, … in sorted order (by source then title).

    v3.1.5 Task 3: also computes ``selection_reason`` and ``top_alternatives``
    for each recipe and attaches them to the output.
    """
    warnings: list[str] = []
    # Sort for deterministic ID assignment
    selected_sorted = sorted(selected, key=lambda r: (r.get("source", ""), r.get("title", "")))

    # v3.1.5 Task 3: pre-assign recipe IDs so we can compute alternatives
    # that reference them.
    for i, r in enumerate(selected_sorted, start=start_id):
        r["_recipe_id"] = f"R{i:03d}"

    transformed = []
    for r in selected_sorted:
        recipe_id = r["_recipe_id"]
        # Re-classify diet tags based on actual ingredients + cuisine
        new_diet_tags, reason = reclassify_diet_tags(
            r["ingredients"], r.get("diet_tags", []), r.get("cuisine", ""),
        )
        original_tags = [d.upper() for d in r.get("diet_tags", [])]
        if set(new_diet_tags) != set(original_tags) and "VEGAN" in original_tags:
            warnings.append(
                f"{recipe_id} {r['title']!r}: re-tagged {original_tags} → {new_diet_tags} "
                f"({reason})"
            )
        # Extract allergens
        allergens = extract_allergens(r["ingredients"])
        # Derive goal_fit
        goal_fit = compute_goal_fit(
            r["calories"], r["protein_g"], r["carbs_g"], r["fat_g"],
        )
        # Compute density tags
        p_density = compute_protein_density(r["calories"], r["protein_g"])
        c_density = compute_calorie_density(r["calories"], r["servings"])
        # Ethiopian cultural flags
        fasting_yetsom, injera_accompaniment = derive_ethiopian_flags(r)
        # Nutritional consistency check (engine uses [kcal-warning] tag)
        macro_kcal = (r["protein_g"] * 4 + r["carbs_g"] * 4 + r["fat_g"] * 9)
        delta_pct = abs(r["calories"] - macro_kcal) / max(r["calories"], 1)
        kcal_warning = delta_pct > 0.10
        if kcal_warning:
            warnings.append(
                f"{recipe_id} {r['title']!r}: kcal mismatch — stated {r['calories']:.0f} vs "
                f"macro-derived {macro_kcal:.0f} ({delta_pct*100:.0f}% off)"
            )
        # v3.1.5 Task 3: compute selection reason + top alternatives
        selection_reason = compute_selection_reason(r, goal_fit, selected_sorted)
        top_alternatives = compute_top_alternatives(r, selected_sorted, top_n=5)

        # Build the engine-schema recipe
        notes_parts = []
        if r.get("fiber_g", 0) == 0:
            notes_parts.append("[curation-note: fiber_g unknown — backfilled to 0]")
        if kcal_warning:
            notes_parts.append(
                f"[kcal-warning: stated {r['calories']:.0f} kcal vs macro-derived "
                f"{macro_kcal:.0f} kcal ({delta_pct*100:.0f}% off)]"
            )
        if reason != "plant-based":
            notes_parts.append(f"[curation-note: diet re-tagged — {reason}]")
        notes_parts.append("[curated]")  # mark as curated for the engine's counter

        engine_recipe = {
            "name": r["title"],
            "id": recipe_id,
            "source": r.get("url", ""),
            "source_file": f"{r.get('source', 'unknown').lower().replace('.', '')}__recipe.json",
            "cuisine": r["cuisine"],
            "category": "",
            "recipe_kind": "meal",
            "meal_types": r["meal_type"],
            "diet_types": new_diet_tags,
            "goal_fit": goal_fit,
            "servings": r["servings"],
            "prep_time_min": r["prep_time_min"],
            "cook_time_min": r["cook_time_min"],
            "ingredients": r["ingredients"],
            "instructions": r["instructions"],
            "nutrition_per_serving": {
                "kcal": round(r["calories"], 1),
                "protein_g": round(r["protein_g"], 1),
                "carb_g": round(r["carbs_g"], 1),
                "fat_g": round(r["fat_g"], 1),
                "fiber_g": round(r["fiber_g"], 1),
                "sugar_g": round(r["sugar_g"], 1),
            },
            "nutrition_source": "published",
            "serving_size_g": None,
            "protein_density": p_density,
            "calorie_density": c_density,
            "allergens": allergens,
            "alternative_recipe_ids": [],
            "fasting_yetsom": fasting_yetsom,
            "injera_accompaniment": injera_accompaniment,
            "image_url": r.get("image", ""),
            # v3.1.5 Task 3: selection reason + top alternatives
            "selection_reason": selection_reason,
            "top_alternatives": top_alternatives,
            "notes": " ".join(notes_parts),
            "_extraction_method": "curate_recipe_db.py",
        }
        transformed.append(engine_recipe)

    return transformed, warnings


# ══════════════════════════════════════════════════════════════════
# PHASE 8: AUDIT LOG GENERATION
# ══════════════════════════════════════════════════════════════════

def write_audit_txt(
    path: Path, raw_count: int, selected: list[dict],
    transformed: list[dict], audit: dict, warnings: list[str],
) -> None:
    """Write a human-readable audit log."""
    lines = [
        "RECIPE DATABASE CURATION AUDIT LOG (v3.1.4)",
        "=" * 70,
        f"Raw input recipes:     {raw_count}",
        f"Selected for curation: {len(selected)}",
        f"Final curated recipes: {len(transformed)}",
        f"Ethiopian count:       {audit.get('final_ethiopian', 0)} "
        f"({audit.get('final_ethiopian_ratio', 0)*100:.1f}%)",
        "",
        "Phase Summary:",
    ]
    for p in audit.get("phases", []):
        lines.append(f"  Phase {p['phase']} ({p['name']}): {p.get('selected', '?')} selected")
    lines.append("")
    lines.append("Composition Breakdown:")
    # By meal type
    mt_counts = Counter()
    for r in transformed:
        for mt in r.get("meal_types", []):
            mt_counts[mt] += 1
    lines.append("  By meal type:")
    for mt in ["breakfast", "lunch", "dinner", "snack", "dessert", "shake"]:
        lines.append(f"    {mt:10}: {mt_counts.get(mt, 0)}")
    # By diet type
    dt_counts = Counter()
    for r in transformed:
        for dt in r.get("diet_types", []):
            dt_counts[dt] += 1
    lines.append("  By diet type:")
    for dt in ["VEGAN", "VEGAN_ETHIOPIAN", "OMNI", "OMNI_ETHIOPIAN", "VEGETARIAN"]:
        lines.append(f"    {dt:18}: {dt_counts.get(dt, 0)}")
    # By cuisine
    c_counts = Counter(r.get("cuisine", "unknown") for r in transformed)
    lines.append("  By cuisine:")
    for c, n in c_counts.most_common():
        lines.append(f"    {c:20}: {n}")
    # By goal_fit
    gf_counts = Counter()
    for r in transformed:
        for gf in r.get("goal_fit", []):
            gf_counts[gf] += 1
    lines.append("  By goal_fit:")
    for gf in ["cut", "bulk", "recomp", "maintenance"]:
        lines.append(f"    {gf:12}: {gf_counts.get(gf, 0)}")
    # Allergen coverage
    a_counts = Counter()
    for r in transformed:
        for a in r.get("allergens", []):
            a_counts[a] += 1
    lines.append("  Allergens present in N recipes:")
    for a, n in sorted(a_counts.items()):
        lines.append(f"    {a:12}: {n}")
    # Warnings
    lines.append("")
    lines.append(f"Curation Warnings ({len(warnings)}):")
    for w in warnings[:50]:
        lines.append(f"  ⚠ {w}")
    if len(warnings) > 50:
        lines.append(f"  ... and {len(warnings) - 50} more")
    # Full recipe inventory
    lines.append("")
    lines.append("Recipe Inventory:")
    for r in transformed:
        n = r["nutrition_per_serving"]
        mt = ",".join(r.get("meal_types", []))
        dt = ",".join(r.get("diet_types", []))
        gf = ",".join(r.get("goal_fit", []))
        lines.append(
            f"  [{r['id']}] {r['name'][:55]:<55} "
            f"({n['kcal']:.0f}cal, {n['protein_g']:.0f}g) "
            f"[{r['cuisine']}] {mt} {{{dt}}} <{gf}>"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_audit_json(
    path: Path, raw_count: int, selected: list[dict],
    transformed: list[dict], audit: dict, warnings: list[str],
) -> None:
    """Write a machine-readable audit log."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "3.1.4",
        "raw_count": raw_count,
        "selected_count": len(selected),
        "final_count": len(transformed),
        "ethiopian_count": audit.get("final_ethiopian", 0),
        "ethiopian_ratio": round(audit.get("final_ethiopian_ratio", 0), 4),
        "phases": audit.get("phases", []),
        "warnings": warnings,
        "by_meal_type": dict(Counter(
            mt for r in transformed for mt in r.get("meal_types", [])
        )),
        "by_diet_type": dict(Counter(
            dt for r in transformed for dt in r.get("diet_types", [])
        )),
        "by_cuisine": dict(Counter(r.get("cuisine", "unknown") for r in transformed)),
        "by_goal_fit": dict(Counter(
            gf for r in transformed for gf in r.get("goal_fit", [])
        )),
        "by_allergen": dict(Counter(
            a for r in transformed for a in r.get("allergens", [])
        )),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recipe database curation pipeline (v3.1.4)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input", default="/home/z/my-project/upload/recipe_database.json",
        help="Path to raw input database (schema A: title/ingredients/calories/...). "
             "Default is the uploaded raw file location.",
    )
    parser.add_argument(
        "--output", default="fitness_engine/meal_plan/recipe_database.json",
        help="Path to write curated database (schema B: engine-compatible)",
    )
    parser.add_argument(
        "--uncurated-output", default="fitness_engine/meal_plan/recipe_database_uncurated.json",
        help="Path to write uncurated database (all cleaned recipes, schema B)",
    )
    parser.add_argument(
        "--audit-txt", default="download/curation_audit.txt",
        help="Path to write human-readable audit log",
    )
    parser.add_argument(
        "--audit-json", default="download/curation_audit.json",
        help="Path to write machine-readable audit log",
    )
    parser.add_argument("--target-min", type=int, default=80)
    parser.add_argument("--target-max", type=int, default=120)
    parser.add_argument("--eth-target", type=float, default=0.30)
    parser.add_argument("--eth-min", type=float, default=0.20)
    parser.add_argument("--eth-max", type=float, default=0.50)
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    audit_txt_path = Path(args.audit_txt).resolve()
    audit_json_path = Path(args.audit_json).resolve()

    if not input_path.is_file():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading raw recipes from {input_path}")
    with open(input_path, encoding="utf-8") as f:
        raw_data = json.load(f)
    # Raw DB may be a list (schema A) or a dict with 'recipes' (schema B-ish)
    if isinstance(raw_data, list):
        raw_recipes = raw_data
    elif isinstance(raw_data, dict) and "recipes" in raw_data:
        raw_recipes = raw_data["recipes"]
    else:
        print("Error: input must be a list of recipes or {recipes: [...]}", file=sys.stderr)
        sys.exit(1)
    print(f"  Loaded {len(raw_recipes)} raw recipes")

    # Phase 0: Clean + validate
    print(f"\nPhase 0: Cleaning + validation")
    cleaned = []
    dropped = 0
    for r in raw_recipes:
        c = clean_recipe(r)
        if c is None:
            dropped += 1
        else:
            cleaned.append(c)
    print(f"  Cleaned: {len(cleaned)} recipes ({dropped} dropped for missing required fields)")

    # Phase 1-6: Selection pipeline
    print(f"\nPhases 1-6: Selection pipeline (target {args.target_min}-{args.target_max}, "
          f"eth target {args.eth_target*100:.0f}%)")
    selected, audit = select_recipes(
        cleaned,
        target_min=args.target_min,
        target_max=args.target_max,
        eth_target=args.eth_target,
        eth_min=args.eth_min,
        eth_max=args.eth_max,
    )
    print(f"  Selected: {len(selected)} recipes "
          f"({audit['final_ethiopian']} Ethiopian, {audit['final_ethiopian_ratio']*100:.1f}%)")
    for p in audit["phases"]:
        print(f"    Phase {p['phase']} ({p['name']}): {p.get('selected', '?')}")

    # Phase 7: Schema transformation (curated subset)
    print(f"\nPhase 7: Schema-A → Schema-B transformation (curated)")
    transformed, warnings = transform_to_engine_schema(selected)
    print(f"  Transformed: {len(transformed)} recipes")
    print(f"  Warnings: {len(warnings)}")
    for w in warnings[:10]:
        print(f"    ⚠ {w}")
    if len(warnings) > 10:
        print(f"    ... and {len(warnings) - 10} more")

    # Phase 7b: Also transform ALL cleaned recipes → uncurated DB (schema B)
    # This gives the engine a broader pool for variety without selection bias.
    print(f"\nPhase 7b: Schema-A → Schema-B transformation (uncurated, all {len(cleaned)} recipes)")
    uncurated_transformed, uncurated_warnings = transform_to_engine_schema(
        cleaned, start_id=len(transformed) + 1,
    )
    print(f"  Transformed: {len(uncurated_transformed)} recipes")
    print(f"  Warnings: {len(uncurated_warnings)}")

    # Build the final curated DB (engine format)
    final_db = {
        "version": "3.1.4",
        "total_recipes": len(transformed),
        "curation_notes": (
            "Curated by scripts/curate_recipe_db.py (v3.1.4) from "
            f"{input_path.name}. Selection: 6-phase pipeline "
            "(set cover → variety → cuisine diversity → ethiopian balance → "
            "size expansion → graph dedup). Transformation: schema-A → schema-B "
            "with allergen extraction, goal_fit derivation, density tags, "
            "Ethiopian cultural flags, nutritional consistency check. "
            f"See {audit_txt_path.name} for the full audit log."
        ),
        "recipes": transformed,
        "swap_groups": [],  # populated by the engine at load time
    }

    # Build the uncurated DB (all cleaned recipes, schema B)
    uncurated_db = {
        "version": "3.1.4-uncurated",
        "total_recipes": len(uncurated_transformed),
        "curation_notes": (
            f"Uncurated pool (all {len(cleaned)} cleaned recipes from "
            f"{input_path.name}) transformed to schema B by "
            "scripts/curate_recipe_db.py (v3.1.4). No selection applied — "
            "this is the broad pool the engine loads alongside the curated DB."
        ),
        "recipes": uncurated_transformed,
        "swap_groups": [],
    }

    # Write outputs
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_db, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Wrote curated DB: {output_path} ({len(transformed)} recipes)")

    uncurated_output_path = Path(args.uncurated_output).resolve()
    uncurated_output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(uncurated_output_path, "w", encoding="utf-8") as f:
        json.dump(uncurated_db, f, indent=2, ensure_ascii=False)
    print(f"✓ Wrote uncurated DB: {uncurated_output_path} ({len(uncurated_transformed)} recipes)")

    # Write audit logs (curated only — uncurated is the superset)
    write_audit_txt(audit_txt_path, len(raw_recipes), selected, transformed, audit, warnings)
    print(f"✓ Wrote audit log (txt): {audit_txt_path}")
    write_audit_json(audit_json_path, len(raw_recipes), selected, transformed, audit, warnings)
    print(f"✓ Wrote audit log (json): {audit_json_path}")

    print(f"\n{'='*65}")
    print(f"  DONE: {len(transformed)} curated + {len(uncurated_transformed)} uncurated recipes")
    print(f"  Curated:  {output_path.name}")
    print(f"  Uncurated: {uncurated_output_path.name}")
    print(f"  Audit:    {audit_txt_path.name} + {audit_json_path.name}")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()

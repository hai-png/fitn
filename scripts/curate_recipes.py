"""
Recipe database curation script.

Fixes three classes of data-quality issues identified in ANALYSIS.md:
  1. Mis-tagged VEGAN recipes that contain meat/dairy/eggs (84 recipes).
     Re-tags them as OMNI based on ingredient scan.
  2. Missing `fiber_g` field (103 recipes) — backfilled to 0 with a
     `[curation-note]` flag so consumers know the value is unknown.
  3. Missing `instructions` (44 recipes) — backfilled with a placeholder
     "[curation-note: instructions not provided — see source URL]" entry
     so the recipe is at least actionable (cook can consult the source).

Run:  python scripts/curate_recipes.py
Reads:  fitness_engine/meal_plan/recipe_database.json
        fitness_engine/meal_plan/recipe_database_uncurated.json
Writes: same files in-place (after backing up to .bak).

Idempotent: re-running on already-curated files is a no-op.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CURATED = REPO_ROOT / "fitness_engine" / "meal_plan" / "recipe_database.json"
UNCURATED = REPO_ROOT / "fitness_engine" / "meal_plan" / "recipe_database_uncurated.json"

# Meat/dairy/egg keywords that disqualify a recipe from VEGAN/VEGETARIAN tags.
# Substring match is fine here — we re-check with word boundaries below for
# ambiguous cases.
STRICT_MEAT_KEYWORDS = {
    "chicken", "beef", "pork", "turkey", "lamb", "veal", "venison", "bison",
    "duck", "goose", "rabbit", "salmon", "tuna", "cod", "tilapia", "shrimp",
    "prawn", "crab", "lobster", "sardine", "mackerel", "trout", "anchovy",
    "bacon", "ham", "sausage", "pepperoni", "salami", "prosciutto", "pancetta",
    "meat", "mince", "steak", "minced", "ground beef", "ground turkey",
    "brisket", "flank", "sirloin", "ribeye", "tenderloin",
    "fish sauce", "oyster sauce", "worcestershire",
    "anchovy paste", "fish stock", "chicken stock", "beef stock",
    "gelatin", "rennet", "carmine", "cochineal",
    "honey",  # bee-derived
    "egg", "eggs",  # for VEGAN (not VEGETARIAN)
    "yolk", "white of egg", "meringue",
    "milk", "cream", "butter", "cheese", "yogurt", "whey", "lactose",
    "ghee", "paneer", "ricotta", "mozzarella", "parmesan", "feta",
    "buttermilk", "sour cream", "cream cheese",
}

# Plant-qualifier phrases that suppress a meat/dairy keyword match.
# E.g. "coconut milk" should NOT disqualify a recipe from VEGAN.
PLANT_QUALIFIERS = (
    "coconut", "almond", "soy", "oat", "rice", "hemp", "cashew",
    "macadamia", "pea", "flax", "vegan", "plant-based", "non-dairy",
    "dairy-free", "egg-free", "eggless", "egg replacer",
    "nutritional yeast",  # often called "vegan cheese" substitute
)

# Words that contain a meat keyword as a substring but are NOT meat.
# E.g. "butternut" contains "butter", "eggplant" contains "egg".
FALSE_POSITIVE_WORDS = {
    "butternut", "eggplant", "eggnut", "butterleaf", "butterhead",
    "buttercrunch", "butterleaf lettuce", "peanut butter",  # peanut butter is vegan
    "coconut butter", "cocoa butter", "shea butter", "mango butter",
    "apple butter", "pumpkin butter", "cashew butter", "almond butter",
    "sunflower butter", "peanut", "peanuts",
}


def _has_strict_animal_ingredient(ingredients: list[str]) -> tuple[bool, str]:
    """Return (True, matched_keyword) if any ingredient contains an animal product.

    Uses word-boundary matching and suppresses plant-qualified phrases
    (e.g. "coconut milk" is NOT an animal product).
    """
    import re
    for ing in ingredients:
        ing_lower = ing.lower()
        # Skip if any plant-qualifier is present.
        if any(pq in ing_lower for pq in PLANT_QUALIFIERS):
            continue
        # Skip false-positive compounds.
        if any(fp in ing_lower for fp in FALSE_POSITIVE_WORDS):
            continue
        # Word-boundary check for each strict keyword.
        for kw in STRICT_MEAT_KEYWORDS:
            # "egg" should match "egg" but not "eggplant" — word boundary handles this.
            # Multi-word keywords need their own boundary check.
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, ing_lower):
                return True, kw
    return False, ""


def curate_recipe(recipe: dict) -> tuple[dict, list[str]]:
    """Apply curation fixes to a single recipe dict.

    Returns (curated_recipe, list_of_changes_made).
    Idempotent: re-applying produces no further changes.
    """
    changes: list[str] = []
    ingredients = recipe.get("ingredients", [])
    diet_types = recipe.get("diet_types", [])
    notes = recipe.get("notes", "") or ""

    # Fix 1: mis-tagged VEGAN recipes with animal ingredients.
    if any(dt.upper().startswith("VEGAN") for dt in diet_types):
        has_animal, kw = _has_strict_animal_ingredient(ingredients)
        if has_animal:
            # Re-tag: remove all VEGAN* tags, add OMNI.
            new_diet_types = [
                dt for dt in diet_types if not dt.upper().startswith("VEGAN")
            ]
            # Preserve OMNI_ETHIOPIAN if the recipe was VEGAN_ETHIOPIAN.
            if any(dt.upper() == "VEGAN_ETHIOPIAN" for dt in diet_types):
                if "OMNI_ETHIOPIAN" not in new_diet_types:
                    new_diet_types.append("OMNI_ETHIOPIAN")
            elif "OMNI" not in new_diet_types:
                new_diet_types.append("OMNI")
            recipe["diet_types"] = new_diet_types
            changes.append(
                f"re-tagged {diet_types} → {new_diet_types} "
                f"(ingredient '{kw}' is animal-derived)"
            )

    # Fix 2: missing fiber_g.
    nutrition = recipe.get("nutrition_per_serving", {}) or {}
    if "fiber_g" not in nutrition or nutrition.get("fiber_g") is None:
        nutrition["fiber_g"] = 0.0
        recipe["nutrition_per_serving"] = nutrition
        changes.append("backfilled missing fiber_g=0.0")
    # Fix 3: missing instructions.
    instructions = recipe.get("instructions", [])
    if not instructions or instructions == []:
        recipe["instructions"] = [
            "[curation-note: instructions not provided — see source URL if available]"
        ]
        changes.append("backfilled missing instructions placeholder")

    return recipe, changes


def curate_db(path: Path) -> int:
    """Curate a recipe DB file in-place. Returns count of recipes changed."""
    if not path.is_file():
        print(f"  SKIP: {path} does not exist")
        return 0
    # Back up to .bak (only first time).
    backup = path.with_suffix(path.suffix + ".bak")
    if not backup.exists():
        shutil.copy2(path, backup)
        print(f"  Backed up to {backup.name}")

    with open(path, encoding="utf-8") as f:
        db = json.load(f)
    recipes = db.get("recipes", [])
    print(f"  Loaded {len(recipes)} recipes from {path.name}")

    changed_count = 0
    for r in recipes:
        r, changes = curate_recipe(r)
        if changes:
            changed_count += 1
            # Append a curation note.
            existing_notes = r.get("notes", "") or ""
            curation_note = "[curation-v3.1.1: " + "; ".join(changes) + "]"
            if "[curation-v3.1.1:" not in existing_notes:
                r["notes"] = (existing_notes + " " + curation_note).strip()

    if changed_count > 0:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Curated {changed_count}/{len(recipes)} recipes; wrote {path.name}")
    else:
        print(f"  ✓ No changes needed (already curated)")
    return changed_count


def main() -> None:
    print("=== Recipe database curation (v3.1.1) ===\n")
    print("Curated DB:")
    n1 = curate_db(CURATED)
    print("\nUncurated DB:")
    n2 = curate_db(UNCURATED)
    print(f"\n=== Done. Total recipes curated: {n1 + n2} ===")


if __name__ == "__main__":
    main()

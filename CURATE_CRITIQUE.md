# Recipe Curation Script Critique

> Comparative review of two candidate curation scripts for the `fitn` recipe database.

## Inputs reviewed

1. **Existing script** — `scripts/curate_recipes.py` (190 lines, v3.1.1)
2. **Uploaded script** — `curate_database.py` (755 lines, "UNIFIED CURATION")
3. **Raw input DB** — uploaded `recipe_database.json` (315 recipes, schema A)
4. **Engine schema** — `fitness_engine/models/meal.py::Recipe` dataclass (schema B)

## Schema mismatch (the fundamental problem)

The uploaded raw DB and the engine's expected DB use **incompatible schemas**:

| Field | Raw (schema A) | Engine (schema B) |
|---|---|---|
| Title | `title` (str) | `name` (str) |
| Recipe URL | `url` (str) | `source` (str) + `source_file` (str) |
| Recipe ID | none (URL used as key) | `id` ("R001"…"R370") |
| Meal types | `meal_type` (list, lowercase: `["breakfast","lunch"]`) | `meal_types` (list, lowercase) |
| Diet tags | `diet_tags` (list, lowercase: `["vegan","gluten-free"]`) | `diet_types` (list, UPPERCASE: `["VEGAN","VEGAN_ETHIOPIAN"]`) |
| Nutrition | flat fields: `calories`, `protein_g`, `carbs_g`, `fat_g`, `fiber_g`, `sugar_g` | nested `nutrition_per_serving: {kcal, protein_g, carb_g, fat_g, fiber_g, sugar_g}` (note: `carb_g` not `carbs_g`, `kcal` not `calories`) |
| Cuisine | `cuisine` (Capitalized: "American", "Ethiopian") | `cuisine` (lowercase: "american", "ethiopian") |
| Tags for goal-fit | none | `goal_fit: ["cut","bulk","recomp","maintenance"]` (list) |
| Density tags | none | `protein_density` / `calorie_density` ("low"/"medium"/"high") |
| Allergens | none | `allergens: ["dairy","eggs","gluten",...]` |
| Cultural flags | none | `fasting_yetsom`, `injera_accompaniment` (booleans, Ethiopian-specific) |
| Servings | `servings` (int) | `servings` (int, but stored as string in current DB) |
| Description | `description` (str) | not used by engine (dropped) |
| Image URL | `image` (str) | `image_url` (str) |
| Prep/cook time | `prep_time_min`, `cook_time_min` | same |
| Total time | `total_time_min` (always null in raw) | computed property (`prep + cook`) |
| Source category | `source_category` (str) | not used (dropped) |
| Source site | `source` (str: "Trifecta", "MuscleAndStrength", "EthiopianFood.org") | not directly used (URL is in `source`) |

**Critique**: **NEITHER script performs the schema-A → schema-B transformation.** Both assume the input is already in their own native schema:

- `scripts/curate_recipes.py` assumes the input is already in schema B (it just patches missing `fiber_g`, `instructions`, and re-tags VEGAN→OMNI on mislabeled recipes). Running it on the uploaded raw DB would crash on `recipe.get("nutrition_per_serving", {})` returning `{}` and then `nutrition["fiber_g"] = 0` would work but every other field would be missing.

- `curate_database.py` (uploaded) assumes the input is in schema A. It successfully selects 50-65 recipes, deduplicates, balances Ethiopian/non-Ethiopian, and adds rich `metadata` (selection_reason, profile_fit, alternatives). But its OUTPUT is also schema A (with `metadata` added) — NOT schema B. Running it then loading the result into the engine's `Recipe` dataclass would fail because the loader expects `name`, `nutrition_per_serving.kcal`, `meal_types`, `diet_types` (uppercase), etc.

**Verdict**: The uploaded script is far more sophisticated (10 phases, graph dedup, profile-fit scoring) but produces the wrong output schema. The existing script is simpler but operates only on already-curated data. Neither is fit for purpose as-is.

## Detailed critique of `scripts/curate_recipes.py` (existing)

**Strengths**:
1. ✅ Idempotent — re-running produces no further changes (curation notes are tagged `[curation-v3.1.1:` so they're detectable).
2. ✅ Plant-qualifier suppression for allergen detection (`coconut milk` doesn't disqualify VEGAN). Good keyword hygiene.
3. ✅ False-positive word list (`butternut` contains `butter`, `eggplant` contains `egg`).
4. ✅ Word-boundary regex for meat keywords (avoids `minced` matching `mince`).
5. ✅ Backs up to `.bak` before mutating.

**Weaknesses**:
1. ❌ **No schema transformation** — only patches 3 specific issues (fiber, instructions, vegan-tagging) on already-schema-B data.
2. ❌ **No selection logic** — operates on every recipe in the DB. Can't reduce 370 → 107 or 315 → ~80.
3. ❌ **No deduplication** — doesn't detect near-duplicate recipes (e.g. "Easy Chicken Breast" vs "Simple Chicken Breast").
4. ❌ **No Ethiopian/non-Ethiopian balance** — the engine needs ~30% Ethiopian recipes for the cuisine_preference feature; this script doesn't enforce that.
5. ❌ **No macro-gap analysis** — doesn't check whether the DB covers high-protein breakfasts, low-cal snacks, etc.
6. ❌ **No quality scoring** — doesn't rank recipes by protein density, instruction completeness, etc.
7. ❌ **Hardcoded paths** — `REPO_ROOT / "fitness_engine" / "meal_plan" / "recipe_database.json"` can't be overridden.
8. ❌ **No CLI** — must edit the script to change input/output paths.
9. ❌ **No audit log** — changes are baked into the JSON `notes` field but no separate human-readable audit report is produced.
10. ❌ **Silent fiber backfill to 0** — `fiber_g = 0.0` is misleading; should be `null` or flagged `[curation-note: fiber unknown]` so consumers can prefer recipes with real fiber data.

## Detailed critique of `curate_database.py` (uploaded)

**Strengths**:
1. ✅ **10-phase pipeline** with clear separation: set cover → variety → cuisine diversity → balance → size expansion → dedup → gap supplementation → fillers → boundary enforcement → tagging.
2. ✅ **Graph-based deduplication** using connected components + title similarity (Jaccard on stopword-stripped tokens). Better than the existing script's no-dedup.
3. ✅ **Coverage protection** — `is_essential_for_coverage` prevents deletion of recipes that uniquely provide a nutritional dimension (calorie/protein bucket).
4. ✅ **Profile-fit scoring** — computes a fit score for each of 5 goal profiles (recomp/weight_loss/muscle_gain/strength/general_health) based on diet overlap + meal-type overlap + calorie/protein match. Useful metadata.
5. ✅ **Alternative-recipe computation** — for each selected recipe, finds top-3 similar recipes (by cal/protein/meal-type/cuisine similarity). Useful for the swap system.
6. ✅ **Strict boundary enforcement** — final count guaranteed to be in `[target_min, target_max]` with Ethiopian ratio in `[eth_min, eth_max]`.
7. ✅ **CLI via argparse** — `--db-path`, `--out-path`, `--audit-path`, `--target-min`, `--target-max`, `--eth-target`, etc.
8. ✅ **Detailed audit log** — writes a separate `.txt` with composition breakdown, dimension coverage, meal-type variety, cuisine representation, and a full recipe inventory.
9. ✅ **Fallback logic** — when the ideal Ethiopian count for a category can't be met, falls back to non-Ethiopian candidates (avoids hard failures).

**Weaknesses**:
1. ❌ **CRITICAL: No schema transformation.** Output is in schema A (with `metadata` added). The engine's `Recipe` loader expects schema B. Running this script then loading the result would crash.
2. ❌ **Field name mismatches**: outputs `title` (engine wants `name`), `meal_type` (engine wants `meal_types`), `diet_tags` (engine wants `diet_types` UPPERCASE), `calories`/`protein_g`/`carbs_g`/`fat_g` flat (engine wants `nutrition_per_serving.{kcal,protein_g,carb_g,fat_g,fiber_g,sugar_g}` nested — note `carb_g` not `carbs_g`, `kcal` not `calories`).
3. ❌ **No allergen extraction** — the engine needs an `allergens` list per recipe (e.g. `["dairy","eggs","gluten"]`). The uploaded script doesn't extract these from ingredients.
4. ❌ **No goal_fit derivation** — the engine uses `goal_fit: ["cut","bulk",...]` to filter recipes by user goal. The script computes `profile_scores` but doesn't translate them into the engine's `goal_fit` list format.
5. ❌ **No density tags** — the engine uses `protein_density` and `calorie_density` ("low"/"medium"/"high") for swap selection. The script doesn't compute these.
6. ❌ **No Ethiopian cultural flags** — `fasting_yetsom` (Ethiopian Orthodox fasting-friendly) and `injera_accompaniment` are not derived. These matter for the Ethiopian cuisine feature.
7. ❌ **Diet-tag normalization is incomplete** — raw DB has `["vegan","gluten-free","soy-free","nut-free"]` etc. Engine wants `["VEGAN","VEGAN_ETHIOPIAN","OMNI","OMNI_ETHIOPIAN","VEGETARIAN"]` (5 specific tags). The script doesn't do this normalization.
8. ❌ **Cuisine casing** — raw DB has `"American"`, `"Ethiopian"`, `"Mexican"`. Engine wants lowercase `"american"`, `"ethiopian"`. The script preserves the capitalized form.
9. ❌ **No recipe ID assignment** — engine expects `id` field like `"R001"`. Script uses `url` as the key. The loader's collision handler would assign IDs, but it's cleaner to assign them in the curate script.
10. ❌ **`total_time_min` always null in raw** — the script doesn't compute it from `prep_time_min + cook_time_min`.
11. ❌ **`fiber_g` null in 283/315 recipes** — the script doesn't backfill or flag this. Engine needs a numeric value (0 is acceptable but should be flagged).
12. ❌ **`sugar_g` null in 164/315 recipes** — same issue.
13. ❌ **Hardcoded PROFILES dict** — the 5 goal profiles (recomp/weight_loss/muscle_gain/strength/general_health) don't match the engine's `RecommendedStrategy` enum (CUT/BULK/RECOMP/MAINTENANCE/HABIT_CHANGE_FIRST/REVERSE_DIET). Should map to the engine's enum values.
14. ❌ **VARIETY targets are hardcoded** — e.g. `('ethiopian','breakfast'): 3`. These should be configurable.
15. ❌ **No nutritional consistency check** — the engine's loader flags recipes where stated kcal differs from `P*4 + C*4 + F*9` by >10% (the `[kcal-warning]` tag). The script doesn't perform this check.
16. ❌ **`source` field is overwritten** — the script uses `source` to mean "Trifecta"/"MuscleAndStrength"/"EthiopianFood.org" (site name). The engine uses `source` to mean the recipe URL. This collision would lose information.
17. ❌ **No `description` truncation** — some descriptions are very long; engine doesn't use them but they bloat the JSON.
18. ❌ **`image` field is preserved as `image`** — engine wants `image_url`.
19. ❌ **No `_extraction_method` or `recipe_kind`** — engine uses these for routing (e.g. `recipe_kind: "meal"` vs `"pantry"`).
20. ❌ **Lambdas in FILLER_CATEGORIES** — `criteria: lambda r: ...` makes the config non-serializable and non-reusable. Should be declarative.

## Summary verdict

| Criterion | Existing `curate_recipes.py` | Uploaded `curate_database.py` |
|---|---|---|
| Schema transformation | ❌ No | ❌ No |
| Selection logic | ❌ None | ✅ 10-phase pipeline |
| Deduplication | ❌ None | ✅ Graph-based |
| Coverage protection | ❌ None | ✅ Essential-recipe guard |
| Profile-fit scoring | ❌ None | ✅ 5 profiles |
| Alternative-recipe links | ❌ None | ✅ Top-3 |
| CLI | ❌ Hardcoded paths | ✅ argparse |
| Audit log | ❌ In-JSON notes only | ✅ Separate .txt |
| Schema-A input support | ❌ No | ✅ Yes |
| Schema-B output | ❌ No (already B) | ❌ No (still A) |
| Allergen extraction | ❌ No | ❌ No |
| goal_fit derivation | ❌ No | ❌ No (has profile_scores but wrong format) |
| Density tags | ❌ No | ❌ No |
| Ethiopian cultural flags | ❌ No | ❌ No |
| Diet-tag normalization | ❌ No | ❌ No |
| Nutritional consistency check | ❌ No | ❌ No |

**Conclusion**: The uploaded script has the right *architecture* (selection pipeline, dedup, coverage protection, profile scoring) but the wrong *output contract* (schema A instead of schema B). The existing script has the right *output contract* (schema B) but no *selection logic*.

The improved script needs to:
1. **Adopt the uploaded script's 10-phase pipeline** (set cover, variety, dedup, gap supplementation, fillers, boundary enforcement).
2. **Add a schema-A → schema-B transformer** as the final phase (renames fields, normalizes diet tags to UPPERCASE, derives allergens from ingredients, computes goal_fit from profile scores, computes density tags, sets Ethiopian cultural flags, assigns recipe IDs, computes total_time_min, flags null fiber/sugar).
3. **Add a nutritional consistency check** (the `[kcal-warning]` tag the engine expects).
4. **Map the 5 hardcoded profiles to the engine's `RecommendedStrategy` enum**.
5. **Make VARIETY targets configurable** via CLI.
6. **Replace lambdas in FILLER_CATEGORIES with declarative criteria**.
7. **Preserve the existing script's plant-qualifier suppression** for allergen detection (the uploaded script has no allergen logic at all).
8. **Produce a clean audit log** in both `.txt` (human-readable) and `.json` (machine-readable) formats.

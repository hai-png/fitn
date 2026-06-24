# Critical Analysis — `hai-png/fitn` Fitness Engine

Repository: https://github.com/hai-png/fitn
Analysis date: 2026-06-24
Analyst: Super Z (post-clone review)

---

## 1. Repository overview

`fitn` is a pure-Python (3.11+) **fitness engine library** that takes a
`UserProfile` and returns an assessment + a complete plan (nutrition +
training + meal). It is Phase-1 of a two-phase build; Phase-2 was always
intended to plug in richer user-supplied food / exercise resources.

```
fitness_engine/
├── __init__.py                  public API surface
├── engine.py                    top-level orchestrator (propose_plan)
├── models/                      dataclasses (profile, assessment, nutrition, training, meal)
├── assessment/                  body composition, health risk, muscular potential, decision tree
├── nutrition/                   RMR, TDEE, calories, macros, hydration, micronutrients, planner
├── training/                    exercise_library, splits, progression, planner
├── meal_plan/                   food_database, meal_templates, allocator, planner
└── tests/                       81 unit tests (all currently passing)
```

The repo also ships **three rich JSON databases** that are NOT yet wired to the
engine:

| File | Records | Purpose |
|------|---------|---------|
| `content_files/all_exercises.json` | 1,217 | Full exercise library (slug, equipment, mechanics, force type, target/secondary muscles, instructions, tips, video URL, experience level) |
| `fitness_engine/meal_plan/recipe_database.json` | 107 | Curated recipes (kcal/P/C/F/fiber/sugar, ingredients, instructions, meal_types, diet_types, cuisine, goal_fit, swap_groups) |
| `fitness_engine/meal_plan/recipe_database_uncurated.json` | 370 | Broader recipe pool incl. 33 pantry items (same schema as curated) |

---

## 2. Architecture strengths

1. **Clean separation of concerns** — assessment / nutrition / training /
   meal_plan / engine are independent packages with no circular imports
   (one intentional forward-import in `models/meal.py`).
2. **Pure-function design** — every formula is a pure function; trivially
   unit-testable. 81 tests run in ~0.3 s.
3. **Decision tree is robust** — `assessment/decision.py` handles
   cut/bulk/recomp/maintenance/habit-change-first/skinny-fat correctly
   with safety overrides (obese → cut regardless of goal; cut-floor
   protection; bulk-ceiling protection).
4. **Adaptive TDEE** is implemented (Bayesian blend of observed-TDEE
   identity + Mifflin-St Jeor prior) even though Phase-1 doesn't expose
   the intake/weight log inputs yet.
5. **Models are JSON-serializable** via `to_dict()` everywhere, with enum
   coercion in `__post_init__` so the engine accepts string-or-enum input.
6. **Source citations** — every formula is tagged with `[source-file.txt]`
   in the analysis reports under `reports/` and `resources/analysis/`.

---

## 3. Critical issues (BLOCKERS)

### Issue 1 — Training library is hardcoded and tiny (1.7 % of available data)

`fitness_engine/training/exercise_library.py` defines **41 exercises
inline** as Python literals. The repo simultaneously ships
`content_files/all_exercises.json` with **1,217 exercises** — only 3.4 %
of which are reachable from the engine. The hardcoded library omits
every rich field the new DB provides:

| Field in new DB | Used by engine? |
|-----------------|-----------------|
| `instructions` (step-by-step) | ❌ |
| `tips` (form cues) | ❌ |
| `video_url` + `video_id` + `video_thumbnail` | ❌ |
| `secondary_muscles` | ❌ |
| `experience_level` (Beginner/Intermediate/Advanced) | ❌ |
| `force_type` (Push/Pull/Hinge/Isometric…) | ❌ |
| `mechanics` (Compound/Isolation) | ❌ |
| `overview` (long-form exercise description) | ❌ |
| `views` (popularity) | ❌ |
| `url` (canonical muscleandstrength.com page) | ❌ |

**Impact:** the training planner cannot filter by experience level, cannot
show the user how to actually perform an exercise, and cannot embed video
guides. The Phase-2 promise ("user-supplied detailed exercise resources")
is unfulfilled despite the resources already being in the repo.

### Issue 2 — Meal database is raw ingredients, not recipes

`fitness_engine/meal_plan/food_database.py` defines **50 raw staple foods**
(chicken breast, oats, olive oil, etc.). The allocator then composes a
"meal" by picking 3-4 raw foods and computing grams to hit macro targets.

The repo simultaneously ships **477 recipes** (107 curated + 370
uncurated) with full ingredients, instructions, cuisine, diet_types,
goal_fit, swap_groups — none of which are reachable from the engine.

**Impact:** sample output for "Day 1 Breakfast — Greek Yogurt Parfait"
actually consists of:
- 398 g plain non-fat Greek yogurt
- 73 g dry rolled oats
- 75 g raw avocado

That is not a parfait. The meal name is a decorative lie — the user
cannot cook or eat the plan as described.

### Issue 3 — Meal allocator ignores `kcal_target` parameter

`meal_plan/allocator.py:select_foods_for_meal` accepts `kcal_target` as
a parameter but never reads it. Grams are computed only from
protein/carb/fat targets at fixed fractions (80 % / 60 % / 50 %). This
regularly produces meals whose actual kcal is 30-50 % off target.

### Issue 4 — Equipment filter strips exercises *after* building workouts

`training/planner.py:build_training_plan` builds the workouts using the
full hardcoded library, **then** does:

```python
if profile.equipment_access != EquipmentAccess.FULL_GYM:
    for w in workouts:
        w.exercises = [we for we in w.exercises if ... equipment in allowed]
```

For `BODYWEIGHT_ONLY` users this can leave a workout with zero exercises
and no warning. Should filter at library level **before** building
workouts, with substitution fallbacks.

### Issue 5 — `_pplul_workouts` references "Leg Press" which doesn't exist

```python
("Leg Press" if get_exercise("Leg Press") else "Bulgarian Split Squat", 3, "8-12", 120, 6),
```

`Leg Press` is not in the hardcoded library. The fallback always fires
silently. This is a bug-by-design — the user's "Legs" workout always
contains Bulgarian Split Squat twice (once as Legs-day primary, once as
substitution), with no log entry.

---

## 4. High-severity issues

### Issue 6 — Equipment naming mismatch (will break after Issue 1 fix)

| Engine expects (lowercase) | New DB provides (capitalized) |
|----------------------------|-------------------------------|
| `barbell` | `Barbell` |
| `dumbbell` | `Dumbbell` |
| `kettlebell` | `Kettle Bells` (note space + plural) |
| `bodyweight` | `Bodyweight` |
| `cable` | `Cable` |
| `machine` | `Machine` |
| — | `Bands`, `Exercise Ball`, `EZ Bar`, `Landmine`, `Trap Bar`, `Foam Roll`, `Medicine Ball`, `Rope`, `Sled`, `Box`, `Lacrosse Ball`, `Jump Rope`, `Chains`, `Other` |

The engine's `filter_exercises_by_equipment` will silently match nothing
if the new DB is wired without normalization.

### Issue 7 — Muscle naming mismatch (will break after Issue 1 fix)

| Engine expects (lowercase, snake) | New DB provides (Title Case) |
|------------------------------------|------------------------------|
| `quads` | `Quads` |
| `shoulders` | `Shoulders` |
| `chest` | `Chest` |
| `triceps` | `Triceps` |
| `biceps` | `Biceps` |
| `hamstrings` | `Hamstrings` |
| `glutes` | `Glutes` |
| `calves` | `Calves` |
| `back` | (split into `Upper Back`, `Lats`, `Lower Back`, `Traps`) |
| `core` | (split into `Abs`, `Obliques`, `Hip Flexors`) |
| `rear_delts` | (not in target_muscle_group; appears in `secondary_muscles` only) |
| `chest_upper` | (no equivalent; Incline DB Press is just `Chest` in new DB) |

The split between "back" → {Upper Back, Lats, Lower Back, Traps} and
"core" → {Abs, Obliques, Hip Flexors} is actually *better* than the
engine's monolithic tags, but a normalization layer is required.

### Issue 8 — `ExerciseCategory` enum doesn't map to new DB schema

Engine's enum: `COMPOUND_PRIMARY`, `COMPOUND_SECONDARY`, `ACCESSORY`,
`ISOLATION`, `CARDIO`, `MOBILITY`.

New DB provides: `mechanics ∈ {Compound, Isolation}` ×
`force_type ∈ {Push, Pull, Hinge, Isometric, Compression, …}` ×
`exercise_type ∈ {Strength, Cardio, Mobility, Stretching, …}`.

There is no clean 1:1 mapping. The engine should derive a *category*
from the new DB fields rather than require it.

### Issue 9 — `DietType` enum is locked to OMNIVORE

`models/profile.py:__post_init__` raises `ValueError` if diet_type ≠
OMNIVORE. But the recipe DB has 78 VEGAN, 21 VEGAN_ETHIOPIAN, 9
OMNI_ETHIOPIAN recipes that the engine cannot use even after the meal
planner is rewired. The Phase-1 lock should be relaxed for the meal
planner at minimum (vegan recipes are still omnivore-compatible).

### Issue 10 — Meal planner ignores cuisine / goal_fit / swap_groups

The curated DB ships `swap_groups` like
`breakfast_vegan_266-316kcal: [R011, R008]` — exactly the
macro-and-meal-type bucketing a meal planner needs. The engine
completely ignores this curation layer.

### Issue 11 — Training planner silently drops unknown exercises

`_build_workout` does `if ex is None: continue` — no warning, no log.
If a workout template references 6 exercises and 2 are missing, the
user gets a 4-exercise workout with no indication anything went wrong.

---

## 5. Medium-severity issues

### Issue 12 — Volume check counts every muscle group equally

`_compute_weekly_volume` adds `we.sets` to every entry in
`exercise.muscle_groups`. A bench press (`["chest", "triceps",
"shoulders"]`) credits 4 sets to all three. This inflates volume for
muscles that are only secondary movers. Should weight primary vs
secondary differently.

### Issue 13 — Deload week rebuilds every workout deep-copy

`_build_mesocycle` deep-copies every workout for every week, then
strips one set in deload week. For a 6-week advanced block with 6
workouts × 6 exercises, this creates 216 `WorkoutExercise` objects in
memory where 36 would suffice. A `is_deload: bool` flag on Microcycle
would be cleaner.

### Issue 14 — `linear_progression_next` requires ≥3 sets

```python
if all_at_target and len(last_reps_achieved) >= 3:
    next_weight = current_weight_kg + increment_kg
```

Accessories done for 2 sets never progress. Should be `>= 2` or
configurable per exercise.

### Issue 15 — `_compute_rest_days` ignores actual workout frequency

Returns hardcoded rest-day positions (e.g., `[2, 4, 6, 7]` for 3-day
splits) without checking the user's actual weekly schedule. If the user
trains Tue/Thu/Sat, the rest days should be Mon/Wed/Fri/Sun, not
Tue/Thu/Sat/Sun.

### Issue 16 — Meal plan summary says "7-day rotation" but food choices only rotate by 7 indices

The protein/carb/fat option lists each have 3-5 entries. Day 8 of a
14-day plan would be identical to Day 1. The "rotation" claim is only
true for ≤7-day plans.

### Issue 17 — `protein_per_100kcal` defined but never used

`food_database.py` exports `protein_per_100kcal` for ranking protein
density, but the allocator hardcodes protein options per meal type
instead of using the ranking function. Dead code.

### Issue 18 — `Exercise.notes` field exists but is never populated

Every `Exercise` in the hardcoded library leaves `notes=""`. The new DB
has `tips` (list of form cues) and `overview` (long-form description)
that should populate this field.

### Issue 19 — `ProgressionState` enum is unused

Defined in `progression.py` but never set on any `ProgressionEntry` in
the codebase. Dead code.

### Issue 20 — No persistence layer

Everything is in-memory. The recipe DBs are loaded but the engine has
no caching, no schema versioning, no migration path.

---

## 6. Low-severity issues

### Issue 21 — `MealType.PRE_WORKOUT` and `POST_WORKOUT` are defined but never used

`meal_templates.py:MEAL_NAMES` has entries for them, but
`get_meal_plan_template` never returns them. Dead UI.

### Issue 22 — `FoodCategory.CONDIMENT` defined but no food uses it

### Issue 23 — `FoodItem` has `notes` field, never populated

### Issue 24 — Tests don't validate meal content

`test_engine.py:TestMealFrequency` only checks meal count, not whether
the foods are sensible (e.g., no avocado in a parfait).

### Issue 25 — No CLI

`scripts/sample_runner.py` is the only entry point. Library-only is a
Phase-1 design choice, but a `python -m fitness_engine` CLI would help.

### Issue 26 — `recipe_database.json` curation_notes contains literal `$(date)`

```json
"curation_notes": "Curated from 355 recipes on $(date). Hard filters: ..."
```

Bash variable expansion leaked into the JSON. Should be a real date.

### Issue 27 — `download/README.md` and `download/fitness_engine_reference_guide.md` are stale

They describe the Phase-1 hardcoded library, not the new databases.

---

## 7. Wiring plan (post-analysis)

The user requested: *"use the new exercise database in contents folder,
recipe_uncurated database json and recipe_curated database json replacing
original meal and training database properly wiring to meal planning and
training planning system (adapt the systems as necessary)"*.

### 7.1 Training side

1. Add `Exercise` model fields: `slug`, `instructions`, `tips`,
   `secondary_muscles`, `experience_level`, `force_type`, `mechanics`,
   `overview`, `video_url`, `video_thumbnail`, `source_url`, `views`.
2. Build `exercise_loader.py` that:
   - Loads `content_files/all_exercises.json`
   - Normalizes equipment names to lowercase snake_case
   - Normalizes muscle names to lowercase snake_case + maps
     `Upper Back/Lats/Lower Back/Traps` to a `back_*` taxonomy
   - Derives `ExerciseCategory` from `mechanics` + `force_type` +
     `exercise_type`
   - Maps experience level to the engine's `TrainingStatus`
3. Replace `exercise_library.py:EXERCISES` with loader output.
4. Refactor `build_training_plan` to:
   - Filter at library level by equipment + experience **before** building
   - Pick compound primary exercises per movement pattern (squat / hinge
     / horizontal push / vertical push / horizontal pull / vertical pull)
   - Substitute accessories dynamically from filtered library
5. Add a per-exercise `instructions`, `tips`, `video_url` to the
   serialized `WorkoutExercise` output so the user can actually perform
   the workout.

### 7.2 Meal side

1. Add `Recipe` dataclass matching the JSON schema (name, source,
   cuisine, meal_types, diet_types, servings, prep/cook time,
   ingredients, instructions, nutrition_per_serving, goal_fit,
   protein_density, calorie_density, allergens, swap_groups, image_url,
   id).
2. Build `recipe_loader.py` that:
   - Loads both curated (`recipe_database.json`) and uncurated
     (`recipe_database_uncurated.json`) DBs
   - Merges into a single recipe index by `id` (curated wins on conflict)
   - Exposes queries: `by_meal_type`, `by_diet_type`, `by_cuisine`,
     `by_goal_fit`, `by_kcal_range`, `by_swap_group`
3. Refactor `meal_plan/planner.py:build_meal_plan` to:
   - Allocate daily macros per meal (unchanged logic)
   - For each meal slot, query recipes by (meal_type, diet_type,
     kcal_range) and pick from the matching `swap_group` for variety
   - Fall back to uncurated DB when curated has no match
   - Emit `Meal` with a `recipe` field instead of (or in addition to)
     raw `foods`
4. Relax `DietType` validation: still warn on non-omnivore for
   nutrition calculations, but allow vegan/vegetarian recipes to be
   selected from the meal DB.
5. Add a `MealPlan.cuisine_mix` summary so the user can see the
   distribution of cuisines in their week.

### 7.3 Cross-cutting

- Fix all 27 issues listed above where applicable.
- Update tests to assert that meal plans contain recipe references,
  not just raw foods.
- Update tests to assert that training plans include exercise
  instructions + video URLs.
- Regenerate the four sample plans in `download/` so the user can
  diff before/after.
- Bump `__version__` to `2.0.0` (breaking change to data shape).

---

## 8. Acceptance criteria for the rewire

- [ ] `python -m pytest fitness_engine/tests/` passes 100 % (existing 81 +
      new tests).
- [ ] `python scripts/sample_runner.py` produces 4 sample plans with:
  - Meal plans that reference real recipe IDs from the curated /
    uncurated DBs
  - Training plans where every exercise has `instructions`, `tips`,
    and `video_url` populated
- [ ] A `BODYWEIGHT_ONLY` user gets a training plan with >0 exercises
      per workout (Issue 4 regression test).
- [ ] A user querying for "Leg Press" no longer silently falls back —
      the new DB has `leg-press` and `leg-press-machine` slugs.
- [ ] The `MealPlan.to_dict()` output includes `recipe_id`,
      `recipe_name`, `cuisine`, `instructions`, `ingredients` per meal.

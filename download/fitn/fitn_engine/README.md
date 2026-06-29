# fitn_engine

Pure-Dart physiology-grounded fitness engine. The deterministic core of the
Fitn mobile fitness companion app.

**Deterministic** (same inputs → byte-identical output). **Grounded in
published physiology** — Mifflin-St Jeor, Katch-McArdle, Kouri FFMI,
Hodgdon-Beckett Navy, CUN-BAE, ABSI, RippedBody volume landmarks, Lyle
McDonald muscle-gain rates. Produces a coherent cut/bulk/recomp/maintenance/
reverse-diet recommendation with a defensible rationale.

No Flutter deps. Safe to run in `Isolate.run()`.

## Public API

```dart
import 'package:fitn_engine/fitn_engine.dart';

void main() async {
  // Load engine data (JSON assets).
  final data = await loadEngineData();
  final engine = FitnEngine(data: data);

  // Build inputs.
  final profile = UserProfile(
    age: 30,
    sex: Sex.male,
    heightCm: 180,
    weightKg: 80,
    activityLevel: ActivityLevel.lightlyActive,
    trainingStatus: TrainingStatus.novice,
    primaryGoal: PrimaryGoal.muscleGain,
    trainingDaysPerWeek: 4,
    equipmentAccess: EquipmentAccess.fullGym,
    bodyFatPct: 16,
  );
  final prefs = PlanPreferences(mealFrequency: 4);

  // Generate (assess + propose in one call).
  final response = engine.generatePlan(profile, prefs);
  print(response.plan.summary);

  // Or step-by-step:
  //   final assessment = engine.assessProfile(profile);
  //   if (assessment.isPartial) { /* show regenerate CTA */ }
  //   final plan = engine.proposePlan(profile, assessment, prefs);
}
```

## Engine data files

Loaded from `assets/` at construction. All are JSON.

| File | Purpose | Count |
| ---- | ------- | ----- |
| `all_exercises.json` | Exercise library (slug, name, equipment, mechanics, force_type, experience_level, exercise_type, muscle_groups, secondary_muscles, views, overview, instructions, tips, video_url, video_id, video_thumbnail, url) | 1,217 |
| `split_designs.json` | 8 workout split designs (full-body, upper/lower, PPL, body-part, etc.) | 8 |
| `movement_patterns.json` | 40 movement-pattern specs (family, primary muscles, detection keywords, equipment preferences) | 40 |
| `food_database.json` | ~30 food items for macro-gap fillers (per-100g macros, serving size, category) | ~30 |
| `recipe_database.json` | Curated recipes (`is_curated=true`, `[curated]` tag) | variable |
| `recipe_database_uncurated.json` | Uncurated recipes (IDs renamed to `U<id>` on collision with curated) | ~197 |
| `pre_post_workout_recipes.json` | 16 pre/post-workout recipes (4 diets × 2 meal types × 2 kcal bins) | 16 |

If `recipe_database.json` is missing, the engine tolerates it (loads empty
curated list). The other files are required.

## Sub-engines

### Assessment (`src/assessment/`)
Orchestrates 4 sub-assessments in order, never short-circuiting on failure:

1. `assessBodyComposition(profile)` — root of the dependency tree.
   - Body fat % priority order: user-provided → Navy circumference (Hodgdon-
     Beckett 1984) → CUN-BAE (always computable).
   - FFMI + normalized FFMI (Kouri 1995).
   - Target weights at 4 named BF% landmarks (athletic/fitness/acceptable/
     hormonal_floor).
2. `assessHealthRisk(profile)` — independent of body comp.
   - WHR, WHtR, ABSI (with NHANES 10-year age-band z-scores), IBW (4 formulas:
     Devine/Robinson/Miller/Hamwi).
   - Weighted overall risk heuristic (ABSI 0.5, WHR 0.3, WHtR 0.2).
3. `assessMuscularPotential(profile, bodyFatPct)` — skipped if bodyComp == null.
   - FFMI ceiling %, headroom, Berkhan stage max (men only), expected monthly
     muscle gain (Lyle McDonald; ×0.5 for women).
4. `decideStrategy(profile, bodyFatPct)` — skipped if bodyComp == null,
   defaults to maintenance.
   - First-match-wins decision tree using sex-specific boundaries.

If any sub-assessment throws, records `"sub_name: ArgumentError: <msg>"` in
`errors` and sets the sub-result to null. `is_partial = errors.isNotEmpty`.
`proposePlan()` throws `PartialAssessmentError` if `assessment.isPartial ==
true`.

### Nutrition (`src/nutrition/`)
1. **RMR** — KATCH_MCARDLE if `bodyFatPct != null`, else MIFFLIN_ST_JEOR.
   Adjustments: ×0.95 active deficit, ×0.97 weight-reduced (>10%).
2. **TDEE** — RippedBody activity factors (1.25 / 1.45 / 1.65 / 1.85 / 2.05).
   Adaptive TDEE: requires equal-length logs ≥8 entries, sanity range [800,
   7000], ramp weight `w = clamp((nDays − 7) / 53, 0, 1)`.
3. **Calories** — by strategy, with floor 1200 (F) / 1500 (M). Cut rate
   priority: explicit tier → BF% threshold table → default 0.75% with hard cap
   1.0%.
4. **Macros** — Obese override (1g × heightCm). BF%-known paths use LBM. Vegan
   ×1.20 / vegetarian ×1.10 boost (ceil). Fat floor `max(40, weight_lb ×
   0.25)`. Carbs = remainder.
5. **Hydration** — FatCalc multi-step (base + sex + exercise × climate +
   pregnancy/breastfeeding, soft ceiling 5.0 L).
6. **Micronutrients** — Fiber `14g × kcal/1000`. Fruit/veg cups by kcal bands.
7. **Timeline** — Cut: `max(4, floor(kgToLose / weeklyRateKg) + 4)`. Bulk:
   `max(12, floor((targetGainKg / monthlyRateKg) × 4.348) + 4)`. Recomp:
   12 weeks. Maintenance: 12. Habit-change: 8. Reverse-diet: 8.

### Training (`src/training/`)
1. Derive training goal from `(primaryGoal, recommendedStrategy)`.
2. Pick split from 8 designs (filter by days → experience+goal → experience →
   goal → all, tie-break by experience preference order).
3. Pick progression (BLOCK if strength + intermediate/advanced; else LINEAR
   beginner/novice, DUP intermediate, BLOCK advanced).
4. Apply muscle focus (append 1-2 accessory slots per focus muscle).
5. Build workouts from templates via the **7-tier exercise selector**.
6. Build mesocycles (4w beginner/novice, 5w intermediate, 6w advanced; program
   duration 4/8/10/12w by experience).
7. Apply periodization (5 layers: goal preset → DUP → block → deload → RIR
   clamp).
8. Compute weekly volume (fractional set counting: primary 1.0, secondary 0.5).
9. Validate against landmarks (MEV/MAV/MRV/ML for 22 muscles + fallback).

### Meal plan (`src/meal_plan/`)
1. Compute slot targets from daily macros × meal allocation (2/3/4/5 meals).
2. Determine training days for the 7-day week.
3. For each of 7 days × N slots: allocate meal via `scoreRecipeForSlot` → pick
   top → scale → fill gap. Track recipe usage for variety scoring.

**Recipe scoring** (9 weighted components): kcal_match (26), protein_match
(22), carb_match (13), fat_match (9), diet_match (13), goal_fit (4),
fiber_match (4), variety_bonus (4), cuisine_match (5). Hard exclusions:
allergen, excluded ingredient, diet mismatch.

**Allergen scanning** (best-in-class — plant-qualifier suppression):
`coconut milk` must NOT match `dairy`. Implemented via:
- `PLANT_QUALIFIERS` (substring match in 25-char context before allergen
  keyword).
- `PLANT_NAMED_PHRASES` (blank out with equal-length spaces before scanning).
- Alias normalization (`tree_nuts` → `nuts`, `crustacean` → `shellfish`).

**Recipe scaling**: `scaleFactor = clamp(targetKcal / recipeKcal, 0.7, 1.5)`
(1.0 if within ±10%).

**Filler system**: closes macro gap after scaling (protein/carb/fat/veg
priority; vegan variants; allergen exclusion map).

## Critical implementation rules (spec §11)

1. **Banker's rounding** everywhere except rep-range math (round-half-up).
2. **Vegetarian → vegan recipe mapping** (no separate vegetarian tag in DB).
3. **Plant-qualifier suppression** for allergens (`coconut milk` ≠ dairy).
4. **`proposePlan` throws `PartialAssessmentError`** if `isPartial == true`.
5. **Diet-type protein boosts before rounding**: vegan ×1.20, vegetarian ×1.10,
   then `ceil()`.
6. **`exercise.experience_level` is capitalized** ("Beginner"/"Intermediate"/
   "Advanced"); enum preserves this.
7. **2-meal plans skip breakfast** (LUNCH + DINNER 50/50). Intentional.
8. **5-meal plans interleave snacks** (BREAKFAST, SNACK, LUNCH, SNACK, DINNER).
9. **Adaptive TDEE requires equal-length logs** — skip otherwise.
10. **`HABIT_CHANGE_FIRST` only for obese beginners** (safety override).
11. **Engine version stamp `3.2.0`** on every `FitnessPlan`.
12. **`WEEKS_PER_MONTH = 4.348`** (not 4.345).
13. **CUN-BAE coefficient is `1.0689`** (not the published 1.39 typo).
14. **Navy BF clamped to `[2, 60]`**.
15. **Katch-McArdle throws if `bfPct ∉ [2, 60]`** — caller falls back to Mifflin.
16. **Cut rate cap = 1.0% BW/week** (even "very_aggressive").
17. **Calorie floor 1200 (F) / 1500 (M)**, applied after deficit computation.
18. **Reverse-diet detection requires 30+ days of intake logs**, only in
    maintenance goal path.

## Running tests

```bash
cd fitn_engine
dart pub get
dart test
```

## Engine version

`3.2.0` — stamped on every `FitnessPlan.engineVersion`. Bump on any engine
logic change. The app can detect stale plans by comparing stored
`engineVersion` to current and offer to regenerate.

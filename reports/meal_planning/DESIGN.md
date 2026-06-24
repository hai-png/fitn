# Phase-5: Clean Meal Planning System — Design Document

**Goal**: Replace the legacy Phase-2 meal planner with a clean, comprehensive,
accurate meal planning system that:

1. Takes a **profile** (age, sex, height, weight, goal, activity, diet, training schedule, allergies, cuisine preference, meal frequency, workout timing)
2. Computes **nutritional requirements** (TDEE, target kcal, macros, fiber, hydration, micronutrient targets)
3. Selects from a **curated recipe database** with maximum coverage and minimum recipes
4. Uses a **best-fit scoring algorithm** to assign recipes to meal slots across a 7-day plan
5. Supports **acceptable scaling** (serve 1.2 portions to hit targets)
6. Supports **fillers** (side dishes / supplements to hit remaining macros)
7. Supports **swap alternatives** for missing ingredients
8. Supports **Pre/Post Workout meals**

---

## 1. Profile Taxonomy

Every profile is parameterized by the following inputs. Each is a *dimension*
that affects either the nutritional requirements or the recipe filtering.

### 1.1 Identity & Anthropometry (drives RMR/TDEE)

| Field | Type | Range | Notes |
|---|---|---|---|
| `age` | int | 18–100 | Used in Mifflin-St Jeor |
| `sex` | enum | male / female | BMR formula differs |
| `height_cm` | float | 140–230 | |
| `weight_kg` | float | 35–300 | |
| `body_fat_pct` | float? | 3–60 | Optional; enables Katch-McArdle |

### 1.2 Activity & Training (drives TDEE activity factor)

| Field | Type | Range | Notes |
|---|---|---|---|
| `activity_level` | enum | sedentary / mostly_sedentary / lightly_active / active / highly_active | 5-tier RippedBody scale |
| `training_days_per_week` | int | 2–7 | Drives per-workout nutrition |
| `training_time_of_day` | enum | morning / midday / evening / none | Drives Pre/Post workout meal placement |
| `training_intensity` | enum | light / moderate / intense | Affects post-workout carb need |

### 1.3 Goal (drives calorie delta + macro split)

| Field | Type | Range | Notes |
|---|---|---|---|
| `primary_goal` | enum | fat_loss / muscle_gain / recomp / maintenance | From PrimaryGoal |
| `cut_rate_tier` | enum? | very_conservative … very_aggressive | Optional override |
| `bulk_aggressiveness` | enum? | conservative … very_aggressive | Optional override |

### 1.4 Diet (drives recipe filtering)

| Field | Type | Options | Notes |
|---|---|---|---|
| `diet_type` | enum | `OMNI` / `VEGAN` / `OMNI_ETHIOPIAN` / `VEGAN_ETHIOPIAN` / `VEGETARIAN` | **The 4 user-requested types** are OMNI, VEGAN, OMNI_ETHIOPIAN, VEGAN_ETHIOPIAN. VEGETARIAN is mapped to VEGAN (closest available). |
| `cuisine_preference` | str? | "ethiopian" / "indian" / "american" / "mexican" / "mediterranean" / None | Optional filter |
| `allergens_to_avoid` | list[str]? | dairy, gluten, soy, nuts, peanuts, eggs, shellfish, fish | Excludes recipes containing these |
| `excluded_ingredients` | list[str]? | free text | Recipes with these ingredients are excluded |

### 1.5 Meal Pattern (drives meal slot count + Pre/Post placement)

| Field | Type | Range | Notes |
|---|---|---|---|
| `meal_frequency` | int | 2–5 | 2 = IF; 3 = standard; 4 = 3+snack; 5 = 3+2snacks |
| `include_pre_post_workout` | bool | True/False | If True, adds 2 extra slots (PRE_WORKOUT + POST_WORKOUT) on training days |
| `intermittent_fasting_window` | str? | "16:8" / "18:6" / None | If set, shifts first meal later |

### 1.6 Lifestyle & Health (drives micronutrient + hydration targets)

| Field | Type | Range | Notes |
|---|---|---|---|
| `climate` | enum | cold / temperate / hot / hot_humid | Hydration multiplier |
| `in_active_deficit` | bool | True/False | Metabolic adaptation factor |
| `weight_reduced_pct` | float | 0–1 | <0.1 = no adaptation; >0.1 = 0.97 multiplier |
| `pregnant` | bool | True/False | +300 kcal, +25g protein |
| `breastfeeding` | bool | True/False | +500 kcal, +25g protein |
| `age_over_65` | bool | True/False (derived from age) | +0.2 g/kg protein |

---

## 2. Reference Profiles (Test Coverage)

To ensure the curated DB + algorithm cover all realistic users, we define
**12 reference profiles** spanning the dimensions above. The curation step
must guarantee every profile gets a high-quality 7-day plan.

| # | Profile | Age/Sex | H/W | BF% | Goal | Diet | Days | Equipment | Notes |
|---|---|---|---|---|---|---|---|---|---|
| P1 | Novice cut, omnivore | 30 M | 178/82 | 18 | fat_loss | OMNI | 4 | full_gym | Standard cut |
| P2 | Beginner bulk, omnivore | 25 M | 183/75 | 12 | muscle_gain | OMNI | 3 | full_gym | Beginner bulk |
| P3 | Female recomp, home gym | 28 F | 165/68 | 28 | recomp | OMNI | 3 | home_gym | Home-gym user |
| P4 | Female maintenance, 5d | 32 F | 170/62 | 22 | maintenance | OMNI | 5 | full_gym | High frequency |
| P5 | Vegan maintenance | 27 M | 180/78 | 14 | maintenance | VEGAN | 3 | full_gym | Vegan diet |
| P6 | Vegan+Ethiopian bulk | 26 M | 175/70 | 11 | muscle_gain | VEGAN_ETHIOPIAN | 4 | full_gym | Cultural preference |
| P7 | Omni+Ethiopian cut | 35 F | 162/75 | 30 | fat_loss | OMNI_ETHIOPIAN | 3 | home_gym | Ethiopian cuisine |
| P8 | Bodyweight-only recomp | 30 M | 178/80 | 16 | recomp | OMNI | 3 | bodyweight | No gym access |
| P9 | Beginner female vegan | 22 F | 168/58 | 24 | muscle_gain | VEGAN | 4 | full_gym | Young vegan |
| P10 | Senior maintenance | 60 M | 175/80 | 22 | maintenance | OMNI | 3 | full_gym | Age>65 protein bump |
| P11 | Cutting w/ pre/post workout | 28 M | 180/85 | 16 | fat_loss | OMNI | 5 | full_gym | Includes PRE/POST workout |
| P12 | Maintenance IF 16:8 | 35 F | 168/65 | 25 | maintenance | VEGAN_ETHIOPIAN | 3 | full_gym | Intermittent fasting |

---

## 3. Nutritional Requirements Matrix

For each profile, the engine computes:

### 3.1 Calorie targets

```
RMR = Mifflin-St Jeor (or Katch-McArdle if BF% known)
TDEE = RMR × activity_factor × metabolic_adaptation × weight_reduced_factor
target_kcal = TDEE + calorie_delta  (negative for cut, positive for bulk)
```

### 3.2 Macro targets

| Goal | Protein | Fat | Carbs |
|---|---|---|---|
| Cut (BF known) | 1.14 g/lb LBM | 0.3 g/lb | remainder |
| Cut (BF unknown) | 1.0 g/lb BW | 0.3 g/lb | remainder |
| Bulk | 1.0 g/lb BW | 0.3 g/lb | remainder |
| Recomp | 1.0 g/lb BW | 0.3 g/lb | remainder |
| Maintenance | 0.8 g/lb BW | 0.3 g/lb | remainder |

### 3.3 Per-meal allocation (% of daily)

| Meal freq | Breakfast | Lunch | Dinner | Snack |
|---|---|---|---|---|
| 2 (IF) | — | 45% | 55% | — |
| 3 | 30% | 35% | 35% | — |
| 4 | 25% | 30% | 30% | 15% |
| 5 | 20% | 25% | 25% | 15%+15% (2 snacks) |

### 3.4 Pre/Post Workout (additional slots, training days only)

| Slot | kcal | Protein | Carbs | Fat | Timing |
|---|---|---|---|---|---|
| Pre-workout | 0.10 × TDEE | 0.25 × meal-P | 0.65 × meal-C | 0.10 × meal-F | 60-90 min before |
| Post-workout | 0.15 × TDEE | 0.30 × meal-P | 0.60 × meal-C | 0.10 × meal-F | 30-60 min after |

### 3.5 Fiber & Hydration

- Fiber: 14 g / 1000 kcal
- Water: 30 mL/kg + 300 mL (male) + sweat_rate × climate_factor

---

## 4. Recipe Curation Strategy

The current DB has 477 recipes (107 curated + 370 uncurated). Many overlap.
Goal: produce a single `recipe_database_curated.json` with **maximum coverage**
and **minimum recipes**.

### 4.1 Coverage Matrix

We need to cover, for EACH of the 4 diet types (OMNI, VEGAN, OMNI_ETHIOPIAN, VEGAN_ETHIOPIAN):

| Meal type | kcal bins needed | Min recipes per bin | Total per diet |
|---|---|---|---|
| breakfast | <300, 300-500, 500-700, 700+ | 2 each | 8 |
| lunch | <400, 400-600, 600-800, 800+ | 2 each | 8 |
| dinner | <400, 400-600, 600-800, 800+ | 2 each | 8 |
| snack | <200, 200-400 | 2 each | 4 |
| side | <200, 200-400 | 2 each | 4 |
| pre_workout | <200, 200-400 | 2 each | 4 |
| post_workout | <300, 300-500 | 2 each | 4 |
| **Total per diet** | | | **40** |

4 diets × 40 = **160 recipes minimum** to cover all (diet × meal_type × kcal_bin) combinations with at least 2 alternatives per slot for 7-day variety.

### 4.2 Curation Algorithm

1. Start with the 107 curated recipes (already high-quality).
2. For each (diet, meal_type, kcal_bin) cell, check if ≥2 recipes are available.
3. If a cell is under-covered, pull from the uncurated DB using these filters:
   - Must have complete nutrition (kcal + P + C + F + fiber)
   - Must have ≥3 ingredients
   - Must have ≥3 instructions
   - Must not be flagged with `[diet-warning]`
   - Prefer `nutrition_source: "published"` over `"estimated"`
4. For each recipe added, also tag it with `alternative_recipe_ids` listing
   other recipes in the same cell (for swap alternatives).
5. Add Pre/Post workout recipes (currently ZERO in the DB — need to create).

### 4.3 Pre/Post Workout Recipes

These are small, fast-digesting, moderate-protein meals. We'll add **16 new
recipes** (4 diets × 2 meal_types × 2 kcal_bins):

**Pre-workout** (high carb, low fat, low fiber for fast digestion):
- Banana + oats + honey (vegan)
- Rice cake + peanut butter + banana (vegan)
- Toast + jam + coffee (omni)
- Injera + honey (vegan_ethiopian)
- ... (16 total)

**Post-workout** (protein + carbs for recovery):
- Whey + banana + oats (omni)
- Plant protein + banana + oats (vegan)
- Chicken + rice + veg (omni)
- Tofu + rice + veg (vegan)
- Lentils + rice (vegan_ethiopian)
- ... (16 total)

---

## 5. Best-Fit Scoring Algorithm

For each meal slot, score every candidate recipe on a 0-100 scale:

### 5.1 Score Components

| Component | Weight | Description |
|---|---|---|
| kcal_match | 30 | How close recipe kcal is to target (within ±20% = 100, ±40% = 50, >40% = 0) |
| protein_match | 25 | How close recipe protein is to target |
| carb_match | 15 | How close recipe carbs are to target |
| fat_match | 10 | How close recipe fat is to target |
| diet_match | 15 | 100 if diet matches, 0 if not (hard filter, scored for transparency) |
| goal_fit | 5 | 100 if goal_fit matches user goal, 50 if "maintenance", 0 otherwise |
| fiber_match | 5 | How close fiber is to (14g/1000kcal × meal_share) |
| variety_bonus | 5 | 100 if recipe not used in last 3 days, 50 if used in last 7 days, 0 if used today |
| cuisine_match | 5 | 100 if cuisine matches preference, 50 if no preference, 0 if explicitly different |
| allergen_penalty | -100 | Hard exclude if allergen present |

Total = weighted sum. **Min acceptable score = 60** (else use filler strategy).

### 5.2 Acceptable Scaling

If no recipe scores ≥60, we scale the closest recipe:

- Recipe can be scaled to **0.7x – 1.5x** servings to better hit macros.
- Scaling factor computed as `target_kcal / recipe_kcal`.
- If scaling factor is outside [0.7, 1.5], skip the recipe.
- When scaling, all macros scale linearly.

### 5.3 Filler Strategy

If a recipe is selected but doesn't fully hit the macros (e.g. recipe is
short on protein by 15g), add **fillers**:

**Filler types** (added as `MealFood` entries alongside the recipe):

| Filler | Purpose | Examples |
|---|---|---|
| Protein filler | Boost protein | Whey scoop, Greek yogurt, tofu, egg whites |
| Carb filler | Boost carbs | Rice, oats, banana, bread |
| Fat filler | Boost fat | Olive oil, nuts, avocado |
| Veg filler | Boost volume + micros | Broccoli, spinach, mixed greens (free — don't count toward macro budget) |

Fillers are computed as the **delta between target and recipe** (after scaling).

### 5.4 Daily + Weekly Balancing

After all 7 days are filled:
- Compute weekly average kcal + macros.
- If weekly average is off from target by >5%, rebalance by swapping
  higher-kcal recipes for lower-kcal ones (or vice versa).
- Ensure ≥14 unique recipes used across the week (variety).

---

## 6. Swap Alternatives

Each recipe in the curated DB will have:

```json
{
  "alternative_recipe_ids": ["R045", "R082"],
  "ingredient_swaps": [
    {"original": "chicken breast", "alternatives": ["tofu", "turkey breast", "tempeh"]},
    {"original": "rice", "alternatives": ["quinoa", "couscous", "cauliflower rice"]},
    {"original": "olive oil", "alternatives": ["avocado oil", "coconut oil"]}
  ]
}
```

- `alternative_recipe_ids`: other recipes in the same (diet, meal_type, kcal_bin) cell.
- `ingredient_swaps`: per-ingredient substitutions (e.g. chicken ↔ tofu).

---

## 7. Module Structure (Clean Implementation)

```
fitness_engine/meal_plan/
├── __init__.py
├── recipe_loader.py          # unchanged — loads curated + uncurated
├── recipe_curator.py         # NEW — curation algorithm (one-time run)
├── profile_requirements.py   # NEW — computes nutritional requirements from profile
├── recipe_scorer.py          # NEW — best-fit scoring (Section 5.1)
├── recipe_scaler.py          # NEW — acceptable scaling (Section 5.2)
├── filler_system.py          # NEW — filler selection (Section 5.3)
├── swap_system.py            # NEW — swap alternatives (Section 6)
├── pre_post_workout.py       # NEW — Pre/Post workout recipe generation
├── allocator.py              # REPLACED — clean implementation
├── planner.py                # REPLACED — clean 7-day orchestrator
├── food_database.py          # unchanged — raw foods for fillers
├── meal_templates.py         # updated — adds pre/post workout slots
├── recipe_database.json              # existing curated (107)
├── recipe_database_uncurated.json    # existing uncurated (370)
└── recipe_database_v2.json           # NEW — the new curated DB (160+ recipes)
```

---

## 8. Acceptance Criteria

- [ ] All 12 reference profiles produce a 7-day plan with ≥1 recipe per slot
- [ ] No profile requires the raw-foods fallback
- [ ] Each meal slot's actual macros are within ±15% of target (after scaling + fillers)
- [ ] Weekly average macros are within ±5% of target
- [ ] ≥14 unique recipes used across the 7-day plan
- [ ] Pre/Post workout meals included on training days when `include_pre_post_workout=True`
- [ ] Swap alternatives available for every recipe in the plan
- [ ] Allergen-free recipes selected when allergens_to_avoid is set
- [ ] Vegan users never get non-vegan recipes
- [ ] Ethiopian-preferring users get ≥3 Ethiopian recipes/week

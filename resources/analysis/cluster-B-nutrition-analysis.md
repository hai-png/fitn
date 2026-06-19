# Cluster B — Nutrition & Macros Source Analysis (Task 2-B)

**Agent:** cluster-B-analyzer
**Scope:** Nutrition pyramid, calorie math, macro calculation, micros, hydration, RMR/TDEE, protein, keto, vegan adjustments
**Sources analyzed:** 16 files (11 RippedBody, 5 FatCalc)
**Purpose:** Exhaustive extraction of every formula, threshold, decision rule, and methodology for codification into the Python fitness engine.

---

## 1. RMR / BMR Formulas

### 1.1 Mifflin-St Jeor Equation (1990) — DEFAULT for general population
**Source:** `[fatcalc.com__rmr-calculator.txt]`

```
Men:   RMR = (9.99 × weight_kg) + (6.25 × height_cm) − (4.92 × age) + 5
Women: RMR = (9.99 × weight_kg) + (6.25 × height_cm) − (4.92 × age) − 161
```
- Recommended default for general population per Frankenfield systematic review.
- Does NOT account for body composition — overestimates in high-BF individuals, underestimates in highly muscular.
- Technically measures RMR (subjects awake, normal lighting, 10–12 h fasted), not true BMR.

### 1.2 Harris-Benedict Equation — Original (1919) + Imperial version used by RippedBody
**Source:** `[rippedbody.com__calories.txt]` — RippedBody's preferred equation ("just as effective, yet simpler to do").

**Metric (kg/cm):**
```
Men:   BMR = 66 + (13.7 × weight_kg) + (5 × height_cm) − (6.8 × age)
Women: BMR = 655 + (9.6 × weight_kg) + (1.8 × height_cm) − (4.7 × age)
```
**Imperial (lb/in):**
```
Men:   BMR = 66 + (6.2 × weight_lb) + (12.7 × height_in) − (6.8 × age)
Women: BMR = 655 + (4.4 × weight_lb) + (4.6 × height_in) − (4.7 × age)
```
- Note: These are the *original* 1919 coefficients (not the 1984 Roza-Shizgal revision below).

### 1.3 Harris-Benedict Revised (1984, Roza & Shizgal)
**Source:** `[fatcalc.com__rmr-calculator.txt]`

```
Men:   RMR = (13.397 × weight_kg) + (4.799 × height_cm) − (5.677 × age) + 88.362
Women: RMR = (9.247 × weight_kg) + (3.098 × height_cm) − (4.330 × age) + 447.593
```
- Tends to overestimate RMR by 5–15% in many populations.

### 1.4 Cunningham Equation (1991) — a.k.a. "Katch-McArdle"
**Source:** `[fatcalc.com__rmr-calculator.txt]`

```
All sexes: RMR = 370 + (21.6 × LBM_kg)
where  LBM_kg = weight_kg × (1 − body_fat% ÷ 100)
```
- Sex-neutral (body composition inherently accounts for sex differences).
- Most accurate for athletes & individuals with above-average muscle mass.
- Less accurate for sedentary individuals or those over 60.
- Requires accurate body-fat % input.
- The "Katch-McArdle" name is a textbook popularization; the actual equation is Cunningham (1980, 1991).
- RippedBody's `[rippedbody.com__calories.txt]` author dismisses Cunningham because "all the methods we have available of assessing body-fat percentage have accuracy issues" — chooses Harris-Benedict instead.

### 1.5 RippedBody Macro Calculator BMR — uses Greg Nuckols' MacroFactor BMR formulas
**Source:** `[rippedbody.com__macro-calculator.txt]`
- If user is in an energy deficit: **reduce calculated BMR by 5%** (metabolic adaptation).
- If user is >10% below all-time highest body weight: **reduce calculated BMR by 3%** (weight-reduced state).
- If body-fat % is entered, calculator switches to a different equation set (better for those significantly above/below average — i.e., presumably LBM-based like Cunningham).
- Author also notes BMR formulas derived from group averages; **individuals can vary up to 15% either side**.

### 1.6 BMI-based Body Fat Estimation (Jackson et al. 2002 / HERITAGE Family Study)
**Source:** `[fatcalc.com__rmr-calculator.txt]` — used when BF% unknown but BMI is.

```
Men:   Body Fat % = 0.14 × age + 37.31 × ln(BMI) − 103.94
Women: Body Fat % = 0.14 × age + 39.96 × ln(BMI) − 102.01
```
- African American adjustment: −2.0 (men), −3.0 (women).
- Explains ~75% of variance; standard error 4–5%.

### 1.7 Population RMR Reference Values (McMurray 2014 meta-analysis, ~12,000 adults)
**Source:** `[fatcalc.com__rmr-calculator.txt]` — expressed as kcal/kg/hr.

**Men (kcal/kg/hr)**
| Age | Normal (BMI<25) | Overwt (BMI 25–29.9) | Obese (BMI≥30) |
|---|---|---|---|
| 20–39 | 1.01 | 0.92 | 0.82 |
| 40–54 | 0.92 | 0.87 | 0.69 |
| 55–74 | 0.85 | 0.79 | — |

**Women (kcal/kg/hr)**
| Age | Normal | Overwt | Obese |
|---|---|---|---|
| 20–39 | 0.95 | 0.80 | 0.73 |
| 40–54 | 0.87 | 0.80 | 0.70 |
| 55–74 | 0.85 | 0.76 | 0.73 |

### 1.8 BMR vs RMR Distinction
**Source:** `[fatcalc.com__rmr-calculator.txt]`
- True BMR requires: 12–14 h fasted, slept overnight in testing facility, motionless, measured immediately upon waking, thermoneutral (22–26 °C), dim lighting, no stress.
- Most online "BMR calculators" actually estimate RMR/REE.
- Difference between BMR and RMR is typically **3–10%**.

---

## 2. TDEE & Activity Factors

### 2.1 RippedBody simplified activity multipliers (4 categories)
**Source:** `[rippedbody.com__calories.txt]`

| Category | Multiplier | Definition |
|---|---|---|
| Sedentary | BMR × 1.15 | Little or no exercise |
| Mostly sedentary + 3–6 d/wk lifting | BMR × 1.35 | Office work + lifting |
| Lightly active + 3–6 d/wk lifting | BMR × 1.55 | On feet more, plus lifting |
| Highly active + 3–6 d/wk lifting | BMR × 1.75 | Active day + lifting |

### 2.2 RippedBody Macro Calculator activity multipliers (5 categories)
**Source:** `[rippedbody.com__macro-calculator.txt]`
- Each activity bump = +0.2 to multiplier.
- Calculator assumes everyone trains 3–6 days/week (number of workouts doesn't change TDEE meaningfully — extra training day adds only ~43 kcal/day).

| Category | Steps/day | Multiplier | Definition |
|---|---|---|---|
| Sedentary | <5,000 | ×1.25 | Desk job, drive everywhere, sit most of day |
| Mostly Sedentary + lifting | <5,000 | ×1.45 | As above + lift 3–6 d/wk |
| Lightly Active + lifting | 5,000–10,000 | ×1.65 | Light walking/movement + lift 3–6 d/wk |
| Active + lifting | 10,000–15,000 | ×1.85 | Physically active most of day or multiple other exercise days + lift |
| Highly Active + lifting | 15,000+ | ×2.05 | Very physical job or intense exercise most days + lift |

### 2.3 FatCalc TDEE Approach — Institute of Medicine Doubly Labeled Water (DLW) formulas
**Source:** `[fatcalc.com__tdee-calculator.txt]`
- Uses DLW formulas from IOM Dietary Reference Intakes (2005), NOT BMR-based equations.
- DLW considered the benchmark — measures real-world energy expenditure over 1–3 weeks.
- For healthy BMI (18.5–25) adults, computes **Estimated Energy Requirement (EER)** rather than TDEE.
- General daily burn ranges:
  - Sedentary adults: 1,600–2,000 kcal/day
  - Moderately active (exercise 3–5 d/wk): 2,000–2,500 kcal/day
  - Very active (intense training/physical job): 2,500–3,500+ kcal/day
- BMR accounts for ~60–70% (or 60–75% per RMR calculator) of TDEE.
- TDEE components: BMR + Thermic Effect of Food (TEF) + NEAT + Exercise.

### 2.4 General TDEE = RMR × Activity Factor
**Source:** `[fatcalc.com__rmr-calculator.txt]`, `[rippedbody.com__calories.txt]`
```
TDEE = RMR (or BMR) × activity_multiplier
```

---

## 3. Calorie Targets for Cut / Bulk / Maintenance / Recomp

### 3.1 Cut (Fat Loss) Math
**Source:** `[rippedbody.com__calories.txt]`, `[rippedbody.com__macro-calculator.txt]`

**Energy equivalence:**
- 1 lb fat ≈ 3,500 kcal
- 1 kg fat ≈ 7,700 kcal
- 1 lb fat/week → 500 kcal/day deficit
- 1 kg fat/week → 1,100 kcal/day deficit

**Target Daily Calorie Intake (TDCI) — Cut:**
```
TDCI_cut = TDEE − (bodyweight_lb × weekly_loss_rate × 500)
TDCI_cut = TDEE − (bodyweight_kg × weekly_loss_rate × 1100)   [metric]
```

**Recommended weekly loss rates:**
- Sweet spot: **0.5% of body weight per week**
- Sustainable range: **0.5–0.75% per week**
- Acceptable for high body fat: up to **1% per week** (most find unsustainable)
- Above 1%: muscle loss likely
- Leaner individuals (approaching single-digit BF%): stay at or slightly under 0.5%
- RippedBody calculator default: **0.75%** (accounts for metabolic adaptation)

**Worked examples (RippedBody):**
- Fat Freddie: 2499 − (180 × 0.0075 × 500) = 2499 − 675 = **1,824 kcal**
- Thicc Thelma: 2109 − (190 × 0.0075 × 500) = 2109 − 712.5 = **1,397 kcal**

### 3.2 Bulk (Muscle Gain) Math
**Source:** `[rippedbody.com__calories.txt]`, `[rippedbody.com__macro-calculator.txt]`

**Energy equivalence:**
- ~2,500 kcal to build 1 lb muscle
- ~3,500 kcal to store 1 lb fat
- Fat:muscle gain typically 1:1 in a bulk → 6,000 kcal/lb weight gain / 30 days = 200 kcal/day for 1 lb/month (or ~100 kcal/day per 1 lb/month)
- RippedBody adds 50% upward adjustment to compensate for NEAT increase: **150 kcal/lb/month (330 kcal/kg/month)**

**Target Daily Calorie Intake — Bulk:**
```
TDCI_bulk = TDEE + (bodyweight_lb × monthly_gain_rate × 150)
TDCI_bulk = TDEE + (bodyweight_kg × monthly_gain_rate × 330)   [metric]
```

**Recommended monthly gain rates by training advancement:**

| Tier | Monthly Gain Rate | Definition |
|---|---|---|
| Beginner | 1.5–2% (RippedBody calories.txt says 2%) | Totally new to training |
| Novice | 1–1.5% (RippedBody calories.txt says 1.5%) | Can add load/reps weekly |
| Intermediate | 0.5–1% (RippedBody calories.txt says 1%) | Can add load/reps monthly |
| Advanced | ≤0.5% | Progress only visible over multiple months/year |

**Worked example (RippedBody):**
- Shredded Sam (intermediate, 1%): 2844 + (175 × 0.01 × 150) = 2844 + 263 = **3,107 kcal**

### 3.3 Maintenance
**Source:** `[rippedbody.com__calories.txt]`, `[rippedbody.com__macro-calculator.txt]`
- TDCI_maintenance = TDEE (no adjustment)
- RippedBody strongly recommends NOT using a calculator when transitioning between cut/bulk/maintenance — use real tracking data instead.

### 3.4 Recomp (Simultaneous fat loss + muscle gain)
**Source:** `[rippedbody.com__calories.txt]`, `[rippedbody.com__macro-calculator.txt]`
- TDCI_recomp = TDEE (eat at maintenance)
- Suitable for: beginners, those returning from training layoff, overweight individuals new to lifting.
- Not effective for advanced trainees.

### 3.5 MacroFactor / RippedBody Calorie Adjustment Math (for tracking-based corrections)
**Source:** `[rippedbody.com__macro-calculator.txt]`

**Cut adjustments (when weekly loss rate is off-target):**
```
calorie_adjustment = delta_lb_off_target × 500     [lbs]
calorie_adjustment = delta_kg_off_target × 1100    [kg]
```
- Positive delta (losing too slowly) → **decrease** intake by adjustment.
- Negative delta (losing too fast) → **increase** intake by adjustment.
- Example: lose 0.5 lb/week slower than target → reduce by 250 kcal/day.
- Example: lose 0.3 lb/week faster than target → increase by 150 kcal/day.

**Bulk adjustments (when monthly gain rate is off-target):**
```
calorie_adjustment = delta_lb_off_target × 150     [lbs]
calorie_adjustment = delta_kg_off_target × 330     [kg]
```
- Example: 1.5 lb/month slower than target → increase by 225 kcal/day.
- Example: 0.5 kg/month faster than target → decrease by 165 kcal/day.

### 3.6 FatCalc General Calorie Deficit Recommendation
**Source:** `[fatcalc.com__tdee-calculator.txt]`
- Starting point for weight loss: eat **200–500 fewer kcal/day than TDEE**.
- 200 kcal/day deficit as initial conservative starting point.
- "200–500 kcal below TDEE" — moderate, safe, sustainable.

---

## 4. Protein Guidelines

### 4.1 RippedBody Macro Calculator Protein Rules
**Source:** `[rippedbody.com__macro-calculator.txt]`

**When body fat % is KNOWN (use lean body mass):**
- Bulking or Recomp: **1 g per pound of lean mass (2.2 g/kg LBM)**
- Cutting: **1.14 g per pound of lean mass (2.5 g/kg LBM)**

**When body fat % is UNKNOWN (use body/target weight):**
- Bulking or Recomp: **0.73 g per pound (1.6 g/kg) of body weight**
- Cutting: **1 g per pound (2.2 g/kg) of target body weight**

**Obesity override:** If 20 lb of loss is targeted but 50 lb could be lost, set target body weight at the realistic long-term goal (e.g., 210 lb) rather than current weight — avoids excessive protein.

**Height-based alternative for obese individuals:** Set protein at **1 g per cm of height**.

### 4.2 General RippedBody Protein Recommendation
**Source:** `[rippedbody.com__how-to-count-macros.txt]`, `[rippedbody.com__how-to-adjust-macros.txt]`, `[rippedbody.com__best-macro-ratio.txt]`
- **1 g per pound of body weight** — good default for most.
- When cutting, optimal range is **1.0–1.2 g/lb body weight** (per research meta-analyses cited).
- Obese individuals: 1 g per cm of height (avoids excess).
- Protein should remain CONSTANT when making calorie adjustments (unless significant body fat to lose).

### 4.3 Vegan Protein Recommendations
**Source:** `[rippedbody.com__advice-for-vegans.txt]`
- General lifting, NOT dieting: **0.7–1.0 g/lb (1.5–2.2 g/kg) body weight** (omnivore research).
- General lifting, NOT dieting — **vegan-adjusted**: **1.0 g/lb (2.2 g/kg) body weight** (higher end to compensate for lower EAA bioavailability).
- Dieting: **1.0–1.2 g/lb (2.2–2.6 g/kg) body weight** (omnivore research).
- Dieting — **vegan-adjusted**: **1.2 g/lb (2.6 g/kg) body weight**.
- If training fasted: **40 g protein powder 30–60 min pre-workout** (or ~30 g if using 70:30 pea:rice blend — the higher dose compensates for lower quality).
- Recommended vegan protein powder: 70:30 pea:rice blend (mimics whey amino acid profile).

### 4.4 FatCalc Protein Calculator
**Source:** `[fatcalc.com__protein-calculator.txt]`

**Activity-based baseline (g/kg body weight):**

| Activity Level | g/kg Range | Definition |
|---|---|---|
| Sedentary | 0.8–1.0 | Minimal physical activity |
| Lightly Active | 1.0–1.2 | Light exercise 1–3 d/wk |
| Moderately Active | 1.2–1.4 | Moderate exercise 3–5 d/wk |
| Active | 1.4–1.6 | Hard exercise 6–7 d/wk |
| Very Active | 1.6–1.8 | Very hard exercise, physical job |
| Athlete | 1.8–2.2 | Professional/competitive training |

**Goal modifiers (added to baseline):**
- Maintain Weight: +0 g/kg
- Build Muscle: **+0.2 g/kg**
- Lose Weight: **+0.3 g/kg**
- Endurance Training: **+0.1 g/kg**

**Age adjustment:** Adults >65 → minimum **1.0–1.2 g/kg** regardless of activity (anabolic resistance).

**Pregnancy / Breastfeeding:** +**25 g/day** each.

**RDA caveat:** RDA = 0.8 g/kg is the MINIMUM to prevent deficiency in sedentary individuals — NOT optimal for active people. ISSN/ACSM support **1.4–2.0 g/kg** for exercising individuals.

**Per-meal target:** **20–40 g high-quality protein per meal**, divided across 3 main meals (3–5 meals/day).

### 4.5 Protein Per 100 Calorie Sources (MacroFactor table)
**Source:** `[rippedbody.com__how-to-count-macros.txt]`

Top protein sources by g protein per 100 kcal:
| Food | Protein (g) per 100 kcal | Vegan |
|---|---|---|
| Tuna (light, water pack) | 22.6 | |
| Whey Protein | 22.0 | |
| Cod | 21.7 | |
| Egg Whites | 21.0 | |
| Soy Protein | 20.0 | V |
| Chicken Breast | 19.9 | |
| Shrimp | 19.1 | |
| Scallops | 18.5 | |
| Non-fat Greek Yogurt | 18.2 | |
| Pork Loin | 17.6 | |
| Seitan | 16.0 | V |
| Spirulina | 15.0 | V |
| Low Fat Cottage Cheese | 14.4 | |
| Nutritional Yeast | 14.0 | V |
| Lean Ground Beef | 13.6 | |
| Turkey Breast | 13.4 | |
| Mushrooms | 13.0 | V |
| Spinach | 12.9 | V |
| Tofu | 12.0 | V |
| Peanut Butter Powder | 11.1 | V |
| Tempeh | 10.6 | V |
| Edamame | 10.3 | V |
| Lentils | 7.9 | V |
| Kidney Beans | 6.8 | V |
| Black Beans | 6.7 | V |
| Chickpeas | 5.4 | V |

### 4.6 Simplified Protein Food Rules
**Source:** `[rippedbody.com__how-to-count-macros.txt]`
- 1 g protein = ~4 kcal
- Uncooked beef/chicken/pork/lamb/fish: ~25 g protein per 100 g
- One large egg = ~8 g protein + 5 g fat
- Egg whites = ~4 g protein each
- Leanest sources: skinless chicken breast, lean red meats, white fish, lean tuna, protein shakes, skim milk/low-fat dairy

### 4.7 Protein Tracking Accuracy Tolerance
**Source:** `[rippedbody.com__how-to-count-macros.txt]`
- Aim within **±10% of each macro target, 90% of the time**.
- Sub-10% body fat (stage-bound): tighten to **±5%**.

---

## 5. Fat Guidelines

### 5.1 RippedBody General Fat Rules
**Source:** `[rippedbody.com__best-macro-ratio.txt]`, `[rippedbody.com__how-to-adjust-macros.txt]`, `[rippedbody.com__macro-calculator.txt]`

- **15–30% of total calories from fat**, depending on goal:
  - Cutting: **15–25%**
  - Maintenance or Bulking: **20–30%**
- After protein, the remaining calories should be split roughly **2/3 carbs, 1/3 fats** (default), adjustable per preference.
- Fat maximum when cutting: **25%**; when at maintenance/bulking: **30%**.
- Fat minimum (absolute): **40–60 g/day**.
  - May drop lower briefly in advanced bodybuilding contest prep.
  - Also expressed as: **0.25 g/lb (0.5 g/kg) minimum**.
- If 20% of calorie intake calculates below 40 g/day floor, the 40 g floor takes precedence — extra calories come from carbs.

### 5.2 Vegan Fat Rules
**Source:** `[rippedbody.com__advice-for-vegans.txt]`
- **15–25% of daily calories from fats** (slightly tighter top end vs. omnivore).
- Absolute minimum: **0.25 g/lb (0.5 g/kg)**.
- Vegan diets naturally trend lower in fat — emphasize oils, nuts, seeds, half an avocado/day to support testosterone.

### 5.3 Saturated Fat Constraint
**Source:** `[rippedbody.com__how-to-adjust-macros.txt]` (comment reply)
- Saturated fat intake **>10% of total calories** impacts blood lipids and increases CVD/CHD risk — recommended ceiling.

### 5.4 FatCalc IOM AMDR & Diet Preset Fat %
**Source:** `[fatcalc.com__macro.txt]`
- IOM Acceptable Macronutrient Distribution Range: **20–35% of calories from fat**.
- 2,000 kcal diet: 44–78 g fat/day.
- 1 g fat = 9 kcal.

**Diet preset fat percentages:**
| Diet | Fat % | Protein % | Carb % |
|---|---|---|---|
| Balanced | 25 | 18 | 57 |
| Low Fat | 18 | 17 | 65 |
| Low Carb | 45 | 28 | 27 |
| High Protein | 25 | 35 | 40 |
| Standard Keto | 70 | 22 | 8 |
| High Protein Keto | 60 | 33 | 7 |
| Mediterranean | 38 | 17 | 45 |
| Paleo | 40 | 30 | 30 |
| Vegetarian | 30 | 17 | 53 |
| Vegan | 25 | 15 | 60 |
| Gluten-Free | 30 | 18 | 52 |

### 5.5 Simplified Fat Counting
**Source:** `[rippedbody.com__how-to-count-macros.txt]`
- 1 g fat = ~9 kcal
- Highest energy density macro — count fat in everything.
- For fatty cuts of meat (e.g., 15% fat beef): use ~10 g fat per 100 g rule.

---

## 6. Carb Guidelines

### 6.1 Fill-the-Remainder Rule
**Source:** `[rippedbody.com__best-macro-ratio.txt]`, `[rippedbody.com__how-to-adjust-macros.txt]`, `[rippedbody.com__macro-calculator.txt]`
- After setting protein (by body weight/LBM) and fat (by % preference, 15–30% range), **carbs fill the remainder**:
```
carb_calories = total_calories − protein_calories − fat_calories
carb_grams = carb_calories / 4
```
- Default remainder split (after protein): **2/3 carbs, 1/3 fat**.
- Carbs are the "prime energy balance manipulator" — once protein & fat are fixed, all calorie adjustments come from carbs (and fat in 2:1 ratio per RippedBody macro calculator slider rule).

### 6.2 RippedBody Macro Calculator Slider Rule
**Source:** `[rippedbody.com__macro-calculator.txt]`
- When adjusting CALORIES: **protein stays constant; carbs and fats adjust in a 2:1 ratio** (2 parts carbs to 1 part fat, by calories).
  - Equivalent to: 40 g carbs + 10 g fat per 250 kcal adjustment (160 kcal carbs + 90 kcal fat ≈ 2:1).
- When adjusting PROTEIN: calories stay constant; carbs/fat redistribute.
- When adjusting CARBS or FATS: protein and calories remain constant.

### 6.3 Keto Threshold
**Source:** `[rippedbody.com__keto.txt]`, `[fatcalc.com__macro.txt]`
- **Ketogenic diet: ≤50 g carbs/day** (RippedBody).
- FatCalc Standard Keto: carbs ≤10% of calories (20–50 g/day on 2,000 kcal).
- High Protein Keto: carbs ≤7% (~35 g/day on 2,000 kcal).
- "Low-carb" (non-keto) threshold: <26% of total calories (~130 g/day on 2,000 kcal) per FatCalc.
- RippedBody's "lower-carb" (non-keto) range: **0.5–1.5 g/lb (~1–3 g/kg) body weight**.

### 6.4 Training-Day vs Rest-Day Carb Cycling
**Source:** `[rippedbody.com__macro-calculator.txt]`, `[rippedbody.com__how-to-adjust-macros.txt]`
- RippedBody calculator offers optional macro cycling: training days higher calories than rest days, total weekly calories constant.
- Higher carbs on training days; rest days can be higher fat/lower carb.
- Number of training days (3–6) doesn't change total weekly energy — only distribution.
- An additional training day adds only ~43 kcal/day to energy needs.

### 6.5 Simplified Carb Counting Rules
**Source:** `[rippedbody.com__how-to-count-macros.txt]`
- 1 g carb = ~4 kcal.
- Raw potatoes: ~15 g carbs/100 g.
- Sweet potatoes: ~25 g/100 g.
- Dried rice: ~70 g/100 g (works for most dried pasta too).
- One medium fruit (apple/banana/pear/orange): ~25 g carbs.
- Leafy green vegetables: do NOT count (reasonable: 2–4 cups/day uncounted).
- Starchy vegetables (carrots, peas, corn, potatoes, parsnips): DO count.
- "Net carbs" labeling — ignore; count all carbs.

### 6.6 Fiber Guidelines
**Source:** `[rippedbody.com__micros.txt]`
- Current recommendation: **14 g fiber per 1,000 kcal**.
- Fiber content examples (per 100 g):
  - Asparagus, broccoli, cabbage, cauliflower, celery, eggplant, kale, lettuce, onion, spinach, zucchini: 1.3–2.9 g
  - Beans: ~5.1 g
  - Bran Flakes: 18 g
  - Oats: 11 g

### 6.7 Alcohol (4th macro)
**Source:** `[rippedbody.com__how-to-count-macros.txt]`, `[rippedbody.com__before-you-count.txt]`
- 1 g alcohol = ~7 kcal.
- Beer @5%: ~150 kcal, ~12 g carbs, ~14 g alcohol per 12 fl oz / 350 ml.
- White wine @10%: ~200 kcal, ~7 g carbs, ~25 g alcohol per 250 ml glass.
- Red wine @10%: ~210 kcal, ~9 g carbs, ~25 g alcohol.
- Spirit shot @40%: 70 kcal (25 ml) / 84 kcal (1 fl oz).
- Calculation: `kcal = volume_ml × ABV × 7`.
- Reduce carb/fat macros to compensate for alcohol calories.
- Two large whiskeys (~250 kcal), two pints beer (~300 kcal), or two large glasses wine (~400 kcal) erase 50–80% of a 500 kcal/day deficit.

---

## 7. Hydration

### 7.1 FatCalc Hydration Formula (multi-step)
**Source:** `[fatcalc.com__hydration-calculator.txt]`

**Step 1 — Base (body weight):**
```
Base water (L) = body_weight_kg × 0.030    [i.e., 30 mL/kg]
```
- Validated: 70 kg woman → 2.1 L (matches EFSA 2.0 L); 83 kg man → 2.49 L (matches EFSA 2.5 L).

**Step 2 — Gender adjustment:**
```
If male: add 300 mL (0.3 L)
```
- Based on EFSA differential (2.5 L men vs 2.0 L women = 500 mL; NAM: 3.7 L men vs 2.7 L women = 1,000 mL). Conservative 300 mL used.

**Step 3 — Exercise intensity (sweat rate):**
| Intensity | mL/hour | Examples |
|---|---|---|
| Light | 300 | Walking, gentle yoga, stretching, light swimming |
| Moderate | 500 | Jogging, recreational cycling, moderate swimming, aerobic classes |
| Intense/Vigorous | 800 | Running, HIIT, competitive sports, intense cycling |
- Sweat rate range in research: 0.3–2.0 L/hour.
- Personal sweat rate protocol: weigh (unclothed) before/after exercise; weight loss in kg = fluid loss in liters; divide by exercise hours.

**Step 4 — Climate multipliers (applied to total):**
| Climate | Multiplier |
|---|---|
| Cold (<20 °C / 68 °F) | ×0.95 (5% reduction) |
| Temperate (20–25 °C / 68–77 °F) | ×1.0 (baseline) |
| Hot (>25 °C / 77 °F) | ×1.3 (30% increase) |
| Hot and Humid (>25 °C + high humidity) | ×1.4 (40% increase) |

**Step 5 — Pregnancy adjustment:**
```
If pregnant: add 300 mL (0.3 L)
```
- Blood volume rises 40–50%; amniotic fluid 800–1,000 mL; BMR rises 15–20%.

**Step 6 — Breastfeeding adjustment:**
```
If breastfeeding: add 700 mL (0.7 L)
```
- Average milk production 750–800 mL/day; breast milk is ~87% water.

### 7.2 EFSA / NAM Reference Values
**Source:** `[fatcalc.com__hydration-calculator.txt]`
- EFSA Adequate Intake: women 2.0 L/day; men 2.5 L/day.
- NAM Adequate Intake: women 2.7 L/day; men 3.7 L/day.
- ~20% of daily fluid intake comes from food (fruits, vegetables, soups).
- Kidneys process ~800–1,000 mL/hour — spread intake throughout day.
- Target urine color: pale yellow (lemonade).
- Well-hydrated signs: pale yellow urine, 6–7 urinations/day, moist lips/mouth, good energy, elastic skin, rarely thirsty.
- Dehydration warning signs: dark yellow/amber urine, dry mouth/lips, headache, fatigue/dizziness, decreased urination, muscle cramps.
- Mild dehydration = 1–2% body weight loss → impairs cognition/performance.
- 2% body weight dehydration → physiological/performance impairment (esp. endurance in heat).

### 7.3 RippedBody Water Intake Guidelines (simpler, behavior-based)
**Source:** `[rippedbody.com__micros.txt]`
- Author rejects body-weight-based water targets due to sweat/climate variability.
- Rules of thumb:
  - Aim to be peeing clear by noon.
  - Have 5 clear urinations per day.
  - Not dehydrated at time of workouts.
  - Taper intake toward evening so you don't wake to pee.

---

## 8. Micronutrients

### 8.1 Micronutrient Importance
**Source:** `[rippedbody.com__micros.txt]`
- Vitamins = organic, from once-living things.
  - Fat-soluble (A, D, E, K): absorbed in gut; deficiencies/surpluses build over time.
  - Water-soluble (B-complex, C): hard to overdose (excreted in urine); need daily intake.
- Minerals = non-organic.
  - Macro minerals (greater quantities): calcium, sodium, potassium, magnesium.
  - Trace minerals: iron, copper, zinc, etc.
- Deficiency consequences:
  - Zinc → metabolism impacted.
  - Iron → strength impacted.
  - Calcium → bone health impacted.

### 8.2 Fruit & Vegetable Intake Guidelines (RippedBody)
**Source:** `[rippedbody.com__micros.txt]`

| Calorie Intake | Cups Fruit & Veg / Day |
|---|---|
| 1,200–2,000 | 2 cups each |
| 2,000–3,000 | 3 cups each |
| 3,000–4,000 | 4 cups each |
- US cup ≈ 250 mL (typical coffee mug size).
- Baseline: minimum 2 pieces of fruit/day + fist-sized portion of fibrous veg per meal + vary daily.
- As calories/macros drop, micronutrient deficiency risk rises.

### 8.3 Dieter At-Risk Nutrients (RippedBody)
**Source:** `[rippedbody.com__micros.txt]`
- Maintain dairy and red meat intake + regular outdoor sun exposure to avoid:
  - **Calcium** deficiency
  - **Zinc** deficiency
  - **Magnesium** deficiency
  - **Iron** deficiency
  - **Vitamin D** deficiency
- Green vegetables (spinach, rocket, beetroot) rich in nitrates → improve exercise tolerance by elevating plasma nitrate, reducing oxygen cost of exercise.

### 8.4 Fiber
**Source:** `[rippedbody.com__micros.txt]`
- **14 g fiber per 1,000 kcal** daily.
- Constipation = too little; loose stools = too much.
- High-fiber pitfalls: beans (~5.1 g/100 g), bran flakes (18 g/100 g), oats (11 g/100 g).

### 8.5 Vegan-Specific Micronutrient Supplementation
**Source:** `[rippedbody.com__advice-for-vegans.txt]`

| Nutrient | Reason | Daily Dose |
|---|---|---|
| Vitamin B12 | ~50% of vegans deficient; anemia + irreversible nervous system degeneration risk | **2.4–6 μg** |
| Iron | Lack of red meat | **14 mg (men) / 33 mg (women)** |
| Zinc | Poor absorption from plants | **16.5 mg (men) / 12 mg (women)** |
| Calcium | Poorer absorption | **500–1,000 mg** (supplement dose) |
| Omega-3 (EPA+DHA) | Lack of fish; algae-based supplement | **1–2 g EPA+DHA total** |
| Vitamin D3 | Not vegan-specific but lichen-based D3 available | **1,000–3,000 IU** (depends on body mass & sun exposure) |
| Creatine | Lack of red meat/fish/poultry; cognitive + performance benefits | **5 g** |
- Many vegan multivitamins cover B12, iron, zinc, calcium.
- Recommend bloodwork before supplementing.
- Author note: 70:30 pea:rice protein blend closely mimics whey amino acid profile.

### 8.6 FatCalc Macro Calculator — Vegan-Specific Notes
**Source:** `[fatcalc.com__macro.txt]`
- Vegan diet preset: 25% fat / 15% protein / 60% carbs.
- Protein set at 12–18% (lower bioavailability of plant proteins).
- **Absolute protein intake should be slightly higher than omnivore: ~1.0–1.1 g/kg body weight**.
- Ensure adequate omega-3 (ALA, EPA, DHA) via deliberate food choices or supplementation.
- Vegan diet requires careful planning for: protein bioavailability, omega-3, B12, iron, calcium.

---

## 9. Nutrition Pyramid Hierarchy

### 9.1 The RippedBody Nutrition Pyramid of Importance
**Source:** `[rippedbody.com__nutrition-pyramid-overview.txt]`, `[rippedbody.com__micros.txt]`

| Priority | Layer | Rationale |
|---|---|---|
| **#1 (Base)** | **Calorie Intake** (Energy Balance) | Determines whether weight is gained (surplus) or lost (deficit). Most important — disproportionate return on effort. |
| **#2** | **Macronutrients** (Protein / Carbs / Fat) | Determines whether weight change is fat or muscle mass. Get in the right ballpark. |
| **#3** | **Micronutrients** (Vitamins & Minerals) | Long-term health; can't stop short-term progress but long-term health crumbles without them. |
| **#4** | **Nutrient Timing** (Meal frequency, timing, cycling, IF) | Large flexibility; avoid extremes. Most people over-worry this. |
| **#5 (Apex)** | **Supplements** | Least important. Few work, those that do little, can't compensate for failures in layers 1–4. |

- All layers NOT of equal importance — focus on first few layers for disproportionate return.
- Original concept: Dr. Eric Helms (2015 YouTube video); expanded in Helms/Morgan/Valdez "Muscle and Strength Pyramid: Nutrition" book.

### 9.2 "Before You Count" Pre-Requisites (Big Wins)
**Source:** `[rippedbody.com__before-you-count.txt]`
- Most people should NOT start with calorie/macro counting — simpler strategies first.
- "10 Big-Impact Easy Wins" (in rough order of importance):
  1. Cut down alcohol.
  2. Stop drinking calories (sugary sodas, juices, lattes).
  3. Eat more vegetables.
  4. Learn to be OK with hunger.
  5. Quit snacking.
  6. Manage food environment (willpower alone insufficient).
  7. Chew food, eat slowly (20 chews/mouthful; 80% full).
  8. Don't let restaurants dictate calories.
  9. Eat at home more often (lean protein is cheaper/easier).
  10. Avoid all-or-nothing mentality.

---

## 10. Macro Adjustment Protocol

### 10.1 Cut-Phase Troubleshooting Checklist (decision framework)
**Source:** `[rippedbody.com__how-to-adjust-macros.txt]`

Order of consideration (calorie reduction is LAST):
1. **Adherence check** — fix before judging macros. (Solid week, throw away weekend = most common failure pattern.)
2. **Tracking accuracy check** — log everything for 2 weeks in a nutrition calculator.
3. **Hunger management:**
   - Swap liquid calories for whole food.
   - Cut down on highly-palatable sugary foods.
   - Eat more fruit, vegetables, salads, soups.
   - Lower meal frequency so meals are larger/more satisfying.
4. **Food environment management** — control surroundings to reduce temptation.
5. **Sleep quality** — poor sleep mimics stress, water retention.
6. **Stress management** — silent killer of muscle mass; recovery impact.
7. **Activity/NEAT check** — step count often drops with lethargy; set minimum 5,000 steps/day target.
8. **Cardio option** (before calorie reduction):
   - Cardio < half the time spent lifting (e.g., 4 h lifting → ≤2 h cardio).
   - Low-impact modalities preferred (incline walk, swim, elliptical, cycle).
   - Avoid HIIT (recovery cost, injury risk).
   - 180 lb person needs 25 min moderate cardio/day for 200 kcal deficit.
9. **Calorie reduction** (LAST resort):
   - **Option 1:** Repeat calculation from initial setup.
   - **Option 2 (preferred):** Decrease overall energy intake by **5–8%** → typically **100–200 kcal reduction**.

### 10.2 Cut Adjustment Math (when weekly weight loss rate off-target)
**Source:** `[rippedbody.com__how-to-adjust-macros.txt]`, `[rippedbody.com__macro-calculator.txt]`
```
calorie_delta = 0.5 lb_off_target × 500    = 250 kcal   [per 0.5 lb deviation, lbs]
calorie_delta = 0.5 kg_off_target × 1100   = 550 kcal   [per 0.5 kg deviation, kg]
```
- Lose too slowly → DECREASE intake by delta.
- Lose too fast → INCREASE intake by delta.
- For 250 kcal adjustment: **reduce carbs by 40 g AND fat by 10 g** (2:1 by calories).
- Protein stays constant unless significant body fat to lose.

### 10.3 Bulk-Phase Troubleshooting Checklist
**Source:** `[rippedbody.com__how-to-adjust-macros-bulk.txt]`

Order of consideration (calorie increase is LAST):
1. **Feeling too full?**
   - Swap whole food for liquid calories (preserve fruit/veg).
   - Eat faster.
   - Higher meal frequency (smaller meals) — consider re-adding breakfast.
   - Manage food environment (have food available at home/work).
2. **Revisit your "why"** — bulking can be a chore for hard gainers.
3. **Manage stress** — silent killer of gains; more fat, less muscle.
4. **Sleep** — poor sleep kills gains; more fat, less muscle.
5. **Activity level increase** — wait to see effect on rate of weight gain before proactively adjusting (don't proactively bump calories for app-estimated burn).
6. **Calorie increase** (LAST resort):
   - **Option 1:** Repeat calculation.
   - **Option 2 (preferred):** Increase overall energy intake by **~5%** → typically **150–200 kcal bump**.
- If gaining too fast (over target): **make a calorie decrease** (use Option 1 logic).
- Decision rule: "Make a calorie increase if weight gain is under target, decrease if over."

### 10.4 Bulk Adjustment Math (when monthly weight gain rate off-target)
**Source:** `[rippedbody.com__macro-calculator.txt]`
```
calorie_delta = 1.0 lb_off_target × 150    = 150 kcal   [per 1 lb deviation, lbs]
calorie_delta = 1.0 kg_off_target × 330    = 330 kcal   [per 1 kg deviation, kg]
```
- Gaining too slowly → INCREASE intake by delta.
- Gaining too fast → DECREASE intake by delta.
- Example: 1.5 lb/month slower → +225 kcal/day.
- Example: 0.5 kg/month faster → −165 kcal/day.
- Protein stays constant.

### 10.5 Initial Adjustments & Timing Rules
**Source:** `[rippedbody.com__calories.txt]`, `[rippedbody.com__how-to-adjust-macros.txt]`, `[rippedbody.com__macro-calculator.txt]`
- Suggested incremental change for CUT: **200–250 kcal/day**.
- Suggested incremental change for SLOW BULK: **100–150 kcal/day**.
- Always consider **3–4 weeks** of tracking data before adjusting.
- Ignore the FIRST WEEK of data (water/gut content/glycogen shifts).
- Use latest 4 weeks of data; if trend unclear, expand a few weeks further.
- Weigh daily, average weekly, compare across weeks.
- Measure stomach (navel, 3 fingers above, 3 fingers below) weekly.
- Approximate guide: **every 4–5 lb fat loss ≈ 2–2.5 cm (~1") reduction on stomach** in two or more places.

### 10.6 Reverse Diet / Maintenance Transition
**Source:** `[rippedbody.com__macro-calculator.txt]` (comment), `[rippedbody.com__how-to-adjust-macros.txt]`, `[rippedbody.com__how-to-adjust-macros-bulk.txt]`
- Author does NOT recommend using a calculator when transitioning between cut/bulk/maintenance — use real tracking data instead.
- After cut → maintenance: add back the calorie deficit + the calculated deficit-equivalent for desired rate; expect ~5 lb water/gut content/glycogen (WGG) regain initially.
- Example from comment: lost 1 lb/week at ~1,900 kcal → add 500 + 172 kcal to current intake = ~2,972 kcal maintenance. Make jump in one go, don't ramp slowly.
- WGG regain happens in first weeks of bulk — discount this from fat gain assessment.
- Expect 1.5–2.5 cm sudden increase in mid/lower stomach (gut content, not fat) when starting bulk.
- Fat regain happens in reverse order of fat loss (last place lost = first place regained).

### 10.7 Diet Breaks
**Source:** `[rippedbody.com__how-to-adjust-macros.txt]`, `[rippedbody.com__macro-calculator.txt]` (comments)
- Mentions of "two week diet break" in comments (a user reports taking one and regaining only ~3 lb water).
- General principle: return to **maintenance calorie intake** when injured, sick, or unable to train (unless very high body fat — fatter individuals lose less muscle in deficit).
- No explicit codified diet-break frequency/length given in these source files (would need `rippedbody.com__diet-progress-tracking.txt` or similar — out of scope).

### 10.8 Stalls & Whooshes
**Source:** `[rippedbody.com__calories.txt]`, `[rippedbody.com__how-to-adjust-macros.txt]`
- **Sudden stall** (multi-week scale freeze) → water retention masking fat loss; wait it out (minimum 4 weeks). Sudden stalls have no physiological explanation other than water.
- **Gradual slowdown** → real metabolic adaptation → make a downward calorie adjustment.
- **Whoosh** = sudden multi-kg drop after a stall (water release). More common in women.
- Causes of water retention: stress, cortisol, sleep issues.

### 10.9 Expected Measurement Patterns by Body Fat %
**Source:** `[rippedbody.com__how-to-adjust-macros.txt]`
- **>20% BF:** measurements drop uniformly (mostly visceral fat loss).
- **10–20% BF:** fat loss from upper abs first, works downward.
- **<10% BF:** minimal mid/upper stomach change; lower stomach and waist change most.
- **<8% BF:** abdominal fat essentially gone; visual change hard to see from front.

---

## 11. Keto Protocol

### 11.1 Entry Criteria (Who Should Consider Keto)
**Source:** `[rippedbody.com__keto.txt]`
- Vast majority of athletic, resistance-trained individuals should NOT use keto.
- Best candidates: **insulin-resistant** individuals.
- Insulin resistance risk factors:
  - Advancing age.
  - Family history of type 2 diabetes.
  - PCOS (women).
  - Oligomenorrhea (menstrual cycle >35 days).
  - Higher androgen levels in women (often over-represented in strength/power sports).
- Even insulin resistance is usually temporary — improves with diet + exercise.
- Research is "mixed bag" for healthy athletic individuals performing resistance training.

### 11.2 Keto Macro Split
**Source:** `[rippedbody.com__keto.txt]`, `[fatcalc.com__macro.txt]`
- Carb threshold: **≤50 g/day** (RippedBody) or ≤10% of calories / 20–50 g/day (FatCalc Standard Keto).
- Fat: **≥60% of total calories** (RippedBody); 65–75% (FatCalc).
- Protein: **20–25% of total calories** (FatCalc); excess protein can convert to glucose and suppress ketosis.
- High Protein Keto variant: 60% fat / 33% protein / 7% carbs (FatCalc).

### 11.3 Adaptation Timeline
**Source:** `[rippedbody.com__keto.txt]`
- **Initial 1–4 week adaptation period** with fatigue, irritability, decreased performance.
- Subsides after adaptation.
- Note: Author clarified in comments — adaptation symptoms occur with **>60% fat** diets (true keto), NOT with 40% fat (the testing protocol).

### 11.4 Systematic Testing Protocol (Off-Season)
**Source:** `[rippedbody.com__keto.txt]`

To test individual response to higher-fat vs higher-carb diet:
1. **Month 1:** Consume **40% fat diet** — keep protein and calories identical to baseline. Track daily 1–10 ratings for: mood, energy, gym quality (perceived effort, not performance).
2. **Month 2:** Switch to **20% fat diet** — keep protein and calories identical. Track same metrics.
3. **Repeat** the entire 4-month protocol (Months 3–4) for repeatability.
4. **Total commitment: 4 months.**
5. Average the daily ratings; compare.
6. **Outcome interpretation:** If 40% fat months consistently score higher → adopt higher-fat diet long-term.
- Caveat: Gym quality ≠ gym performance (not measuring volume/PRs — measuring perceived effort and mental state).
- Sample size note: Keep training approach broadly the same throughout.

### 11.5 "Higher-Fat, Lower-Carb" (Non-Keto) Threshold
**Source:** `[rippedbody.com__keto.txt]`
- High fat = ≥35% of total calories.
- Lower carb = 0.5–1.5 g/lb (~1–3 g/kg) body weight.
- "Ketogenic" = carbs ≤50 g/day, fat ≥60%.

### 11.6 Exit Criteria / Who Shouldn't Use Keto
**Source:** `[rippedbody.com__keto.txt]`, `[fatcalc.com__macro.txt]`
- Healthy, athletic, resistance-trained individuals — pros not worth cons.
- Individuals with kidney disease or diabetes (FatCalc) — medical supervision required.
- Not appropriate as default for physique competitors.

---

## 12. Vegan Adjustments

### 12.1 Protein Sourcing
**Source:** `[rippedbody.com__advice-for-vegans.txt]`
- Plant proteins often lack all 9 EAAs in sufficient abundance — but mixed-source diet across the day is fine (slow digestion spreads amino acid availability).
- Plant proteins have fewer BCAAs and less **leucine** specifically — key for muscle repair/growth.
- Recommended supplement: **70:30 pea:rice protein blend** (closely mimics whey amino acid profile).
- Soy protein NOT recommended — complete EAA profile but low BCAA content.
- 70 g pea + 30 g rice ≈ 100 g whey in amino quality.
- Total EAA content reference: pea powder should be ~38% of total protein content.
- If training fasted: **40 g vegan protein powder (or ~30 g of 70:30 pea:rice blend)** 30–60 min pre-workout.

### 12.2 Vegan Protein Targets (higher than omnivore)
**Source:** `[rippedbody.com__advice-for-vegans.txt]`
- Not dieting: **1.0 g/lb (2.2 g/kg) body weight**.
- Dieting: **1.2 g/lb (2.6 g/kg) body weight**.
- Compensates for lower bioavailability of plant proteins.

### 12.3 Vegan Fat Targets
**Source:** `[rippedbody.com__advice-for-vegans.txt]`
- **15–25% of daily calories from fat**.
- Absolute minimum: **0.25 g/lb (0.5 g/kg)**.
- Vegan diets naturally lower in fat — emphasize oils, nuts, seeds, half avocado/day to support testosterone.

### 12.4 Micro Gaps to Supplement (see also §8.5)
**Source:** `[rippedbody.com__advice-for-vegans.txt]`

| Nutrient | Daily Dose | Reason |
|---|---|---|
| Vitamin B12 | 2.4–6 μg | 50% of vegans deficient; anemia/nervous system risk |
| Iron | 14 mg men / 33 mg women | No red meat |
| Zinc | 16.5 mg men / 12 mg women | Poor plant absorption |
| Calcium | 500–1,000 mg (supplement) | Poorer absorption |
| Omega-3 (EPA+DHA) | 1–2 g total | No fish; algae-based |
| Vitamin D3 | 1,000–3,000 IU | Lichen-based D3 available (not vegan-specific) |
| Creatine | 5 g | No red meat/fish/poultry; cognitive + performance benefits |
- Recommend bloodwork before supplementing.
- Many vegan multivitamins cover B12, iron, zinc, calcium.

### 12.5 Calorie Density Tips (Vegan)
**Source:** `[fatcalc.com__macro.txt]`
- Vegan diet is highest-carbohydrate pattern (60% carbs) due to exclusive reliance on plant foods.
- Macro preset: 25% fat / 15% protein / 60% carbs.
- Protein set at 12–18% to reflect lower bioavailability of plant proteins.
- Absolute protein should be slightly higher than omnivore (~1.0–1.1 g/kg).
- Vegan diets require careful planning for: protein bioavailability, omega-3 (ALA/EPA/DHA), B12, iron, calcium.

---

## 13. Source Citations (Master Index)

### RippedBody sources
- `[rippedbody.com__nutrition-pyramid-overview.txt]` — Pyramid hierarchy (#1 Calories → #5 Supplements), 5-layer framework, "disproportionate return on first layers."
- `[rippedbody.com__calories.txt]` — Harris-Benedict original (1919) formulas (imperial + metric), 4-category activity multipliers (1.15/1.35/1.55/1.75), cut/bulk TDCI formulas (500 kcal/lb, 150 kcal/lb bulk adjustment), rate-of-loss 0.5–0.75%/wk, monthly gain rates by training tier, 3,500 kcal/lb fat, 2,500 kcal/lb muscle, 1:1 fat:muscle bulk ratio, BMR ±15% individual variance, 200–250 kcal cut / 100–150 kcal bulk adjustment increments.
- `[rippedbody.com__macro-calculator.txt]` — MacroFactor BMR formulas reference, metabolic adaptation (−5% if in deficit), weight-reduced state (−3% if >10% below max weight), 5-category activity multipliers (1.25/1.45/1.65/1.85/2.05), protein rules (LBM-based when BF% known: 1 g/lb bulk-recomp, 1.14 g/lb cut; body-weight based when unknown: 0.73 g/lb bulk-recomp, 1 g/lb target cut), bulking +50% NEAT adjustment, ±10% macro counting accuracy, 2:1 carb:fat calorie adjustment ratio, weekly/monthly adjustment formulas (500/lb or 1100/kg for cuts, 150/lb or 330/kg for bulks), height-based protein for obese (1 g/cm), 40–60 g fat minimum.
- `[rippedbody.com__best-macro-ratio.txt]` — "No best ratio" thesis, 1 g/lb protein default, 15–30% fat range, remainder carbs, protein set by LBM, fat set by LBM, macros not fixed ratios.
- `[rippedbody.com__how-to-count-macros.txt]` — Simplified counting rules (rice 70 g/100 g, potatoes 15 g/100 g, sweet potato 25 g/100 g, fruit 25 g/medium, eggs 8 g protein/5 g fat, meat 25 g protein/100 g), 1 g carb=4 kcal, 1 g protein=4 kcal, 1 g fat=9 kcal, 1 g alcohol=7 kcal, leafy greens uncounted (2–4 cups/day), ±10% accuracy tolerance (±5% for sub-10% BF), alcohol kcal formulas (volume × ABV × 7), MacroFactor protein-per-100-kcal table.
- `[rippedbody.com__how-to-adjust-macros.txt]` — Cut-phase troubleshooting checklist, 5–8% calorie reduction (~100–200 kcal), cardio <50% of lifting time, 4–5 lb fat loss ≈ 2–2.5 cm stomach reduction, 15–25% fat when cutting (20–30% maintenance/bulk), 2/3 carbs + 1/3 fat remainder split, saturated fat <10% ceiling, fat loss patterns by BF% (>20%, 10–20%, <10%, <8%), 5,000 step minimum, sudden stall vs gradual slowdown distinction, whoosh phenomenon.
- `[rippedbody.com__how-to-adjust-macros-bulk.txt]` — Bulk-phase troubleshooting checklist, +5% calorie increase (~150–200 kcal bump), increase if under target / decrease if over, WGG regain expectations, 1.5–2.5 cm mid/lower stomach gain (gut content not fat), fat regain reverse order of loss.
- `[rippedbody.com__micros.txt]` — Micros overview, fat-soluble vs water-soluble vitamins, macro vs trace minerals, deficiency consequences (zinc/iron/calcium), 14 g fiber/1,000 kcal, fruit & veg intake table (2/3/4 cups by calorie tier), water intake rules (clear pee by noon, 5 clear urinations/day), fiber content table.
- `[rippedbody.com__before-you-count.txt]` — "10 Big Wins" pre-counting strategies, 500 kcal/day deficit for 1 lb/wk loss, alcohol calorie examples.
- `[rippedbody.com__keto.txt]` — Keto threshold ≤50 g carbs, ≥60% fat, 1–4 week adaptation period, high-fat ≥35%, lower-carb 0.5–1.5 g/lb, 4-month systematic testing protocol (40% fat month vs 20% fat month, repeated twice), entry criteria (insulin resistance, PCOS, oligomenorrhea, age, family history), exit criteria.
- `[rippedbody.com__advice-for-vegans.txt]` — Vegan protein targets (1.0 g/lb not dieting, 1.2 g/lb dieting), 70:30 pea:rice blend recommendation, 15–25% fat range with 0.25 g/lb floor, vegan supplement table (B12 2.4–6 μg, iron 14/33 mg, zinc 16.5/12 mg, calcium 500–1000 mg, omega-3 1–2 g, D3 1000–3000 IU, creatine 5 g), 40 g pre-workout protein (or 30 g of pea:rice blend).

### FatCalc sources
- `[fatcalc.com__macro.txt]` — IOM AMDR (45–65% carbs, 10–35% protein, 20–35% fat), 11 diet presets with macro %, 1 g carb=4 kcal, 1 g protein=4 kcal, 1 g fat=9 kcal, vegan protein 1.0–1.1 g/kg, vegan diet requires B12/iron/calcium/omega-3 attention.
- `[fatcalc.com__protein-calculator.txt]` — Activity-based protein ranges (0.8–2.2 g/kg across sedentary→athlete), goal modifiers (+0.2 build/+0.3 lose/+0.1 endurance), >65 yr min 1.0–1.2 g/kg, pregnancy/breastfeeding +25 g, 20–40 g protein per meal, ISSN/ACSM 1.4–2.0 g/kg exercising, RDA 0.8 g/kg caveat.
- `[fatcalc.com__hydration-calculator.txt]` — Multi-step formula: 30 mL/kg base + 300 mL male + exercise sweat (300/500/800 mL/h by intensity) × climate multiplier (0.95/1.0/1.3/1.4) + 300 mL pregnant + 700 mL breastfeeding, EFSA 2.0/2.5 L, NAM 2.7/3.7 L, 20% from food, 800–1000 mL/h kidney capacity, 2% dehydration impairs performance.
- `[fatcalc.com__rmr-calculator.txt]` — Mifflin-St Jeor (9.99/6.25/4.92 coefficients), Harris-Benedict revised 1984 (13.397/4.799/5.677/88.362 men; 9.247/3.098/4.330/447.593 women), Cunningham/Katch-McArdle (370 + 21.6 × LBM), Jackson BMI→BF% equations (with African American adjustments), McMurray 2014 RMR reference values (kcal/kg/hr) by age/sex/BMI category, BMR vs RMR distinction (3–10% difference).
- `[fatcalc.com__tdee-calculator.txt]` — IOM DLW formulas, EER for healthy BMI, general burn ranges (1600–3500+ kcal/day), 200–500 kcal deficit recommendation, TDEE = BMR + TEF + NEAT + exercise.

---

## 14. Key Codification Notes for Python Engine

### 14.1 Formula Selection Logic
1. **BMR/RMR formula priority (FatCalc approach):**
   - Default: Mifflin-St Jeor.
   - If BF% known: also compute Cunningham (Katch-McArdle) — most accurate for athletic/muscular.
   - Harris-Benedict available for clinical/legacy comparison.
2. **BMR/RMR formula priority (RippedBody approach):**
   - Default: Harris-Benedict original (1919).
   - Apply **−5%** metabolic adaptation if in active deficit.
   - Apply **−3%** if weight-reduced state (>10% below all-time high).
   - MacroFactor BMR formulas when BF% known.

### 14.2 TDEE Activity Factor Tables
- Two RippedBody tables: 4-category (calories.txt) and 5-category (macro-calculator.txt). Use 5-category as default; 4-category available as simplified alternative.
- FatCalc uses IOM DLW/EER formulas — alternative methodology for healthy-BMI adults.

### 14.3 Calorie Target Decision Tree
```
if goal == "cut":
    TDCI = TDEE - (bodyweight × weekly_rate × 500)  # or × 1100 in kg
    # weekly_rate default 0.0075 (0.75%); range 0.005–0.01
elif goal == "bulk":
    TDCI = TDEE + (bodyweight × monthly_rate × 150)  # or × 330 in kg
    # monthly_rate by training tier: beginner 0.015-0.02, novice 0.01-0.015,
    #   intermediate 0.005-0.01, advanced ≤0.005
elif goal == "maintenance" or goal == "recomp":
    TDCI = TDEE
```

### 14.4 Protein Decision Tree
```
if bf_pct_known:
    lbm = bodyweight × (1 - bf_pct/100)
    if goal == "cut":
        protein_g = lbm_lb × 1.14   # or lbm_kg × 2.5
    else:  # bulk or recomp
        protein_g = lbm_lb × 1.0    # or lbm_kg × 2.2
else:
    if goal == "cut":
        protein_g = target_bodyweight_lb × 1.0   # or target_kg × 2.2
    else:  # bulk or recomp
        protein_g = bodyweight_lb × 0.73         # or bodyweight_kg × 1.6

# Overrides:
if obese: protein_g = height_cm × 1.0  # g per cm of height
if vegan and not dieting: protein_g = bodyweight_lb × 1.0   # 2.2 g/kg
if vegan and dieting: protein_g = bodyweight_lb × 1.2       # 2.6 g/kg
if age > 65: protein_per_kg = max(protein_per_kg, 1.0–1.2)
if pregnant or breastfeeding: protein_g += 25
```

### 14.5 Fat Decision Tree
```
if goal == "cut":
    fat_pct_range = (0.15, 0.25)
elif goal in ("maintenance", "bulk"):
    fat_pct_range = (0.20, 0.30)

fat_g = max(
    total_calories × fat_pct_range[0] / 9,   # % floor
    40,                                        # absolute floor (g) — general
    # 0.25 × bodyweight_lb                    # alternative floor (RippedBody)
)
# Cap saturated fat at 10% of total calories.
```

### 14.6 Carb Decision Tree
```
carb_calories = total_calories - (protein_g × 4) - (fat_g × 9)
carb_g = carb_calories / 4

# Keto override:
if keto:
    carb_g = min(carb_g, 50)         # ≤50 g/day
    fat_pct = 0.65–0.75 of calories
    protein_pct = 0.20–0.25 of calories

# Slider adjustment (RippedBody):
# When changing calories, protein constant; carbs:fats adjust 2:1 by calories.
# 250 kcal cut → -40 g carbs, -10 g fat
```

### 14.7 Hydration Formula
```python
def water_intake(weight_kg, sex, exercise_hours, exercise_intensity,
                 climate, pregnant, breastfeeding):
    base = weight_kg * 0.030
    if sex == "male":
        base += 0.3
    sweat_rate = {"light": 0.3, "moderate": 0.5, "intense": 0.8}
    base += exercise_hours * sweat_rate[exercise_intensity]
    climate_mult = {"cold": 0.95, "temperate": 1.0, "hot": 1.3, "hot_humid": 1.4}
    base *= climate_mult[climate]
    if pregnant:
        base += 0.3
    if breastfeeding:
        base += 0.7
    return base  # liters
```

### 14.8 Macro Adjustment Formula
```python
def cut_adjustment(delta_lb_off_target_weekly):
    # positive delta = losing too slowly → decrease
    # negative delta = losing too fast → increase
    return delta_lb_off_target_weekly * 500   # kcal/day

def bulk_adjustment(delta_lb_off_target_monthly):
    return delta_lb_off_target_monthly * 150  # kcal/day

# Macro redistribution for adjustment:
def redistribute(calorie_delta):
    # 2:1 carbs:fat by calories
    carb_kcal = calorie_delta * 2/3
    fat_kcal = calorie_delta * 1/3
    return carb_kcal / 4, fat_kcal / 9  # grams each
```

### 14.9 Micronutrient Codification
- Track: B12, iron, zinc, calcium, magnesium, vitamin D, omega-3 (EPA+DHA), fiber.
- Fiber target: `14 g per 1,000 kcal`.
- Fruit/veg cups: `2 cups per 1,000-2,000 kcal tier; +1 cup per 1,000 kcal above`.
- Vegan supplement table (see §8.5 / §12.4) — apply automatically when `diet_type == "vegan"`.

### 14.10 Open Items / Out-of-Scope
- Reverse diet step count protocol not codified (no explicit formula in these files).
- Diet break frequency/duration not explicitly defined (only general "two week" mention in user comment).
- MacroFactor BMR formula coefficients NOT given explicitly in `[rippedbody.com__macro-calculator.txt]` — only referenced as "Greg Nuckols' MacroFactor BMR formulas." Would need to source externally.
- EER formula coefficients (IOM DLW) NOT given explicitly in `[fatcalc.com__tdee-calculator.txt]` — referenced only.

---
**End of Cluster B analysis.**

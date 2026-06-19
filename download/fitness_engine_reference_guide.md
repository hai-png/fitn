# Fitness Engine — Reference Guide

**Version:** 1.0
**Scope:** Phase-1 engine for healthy omnivore adults 18–65.
**Purpose:** Codify every formula, threshold, and decision rule extracted from 50+ source URLs so the Python engine has a single source of truth.

Source clusters (full analysis preserved in `/resources/analysis/` and `/reports/`):
- Cluster A — Body composition & assessment (13 files)
- Cluster B — Nutrition & macros (16 files)
- Cluster C — Goal setting, progress tracking, bulking, reverse diet, recomp (13 files)
- Cluster D — Adaptive TDEE & calculator methodology (9 files)

> Convention: every rule cites its source file in `[brackets]`. Where a formula is reconstructed because the source text described but did not print it (e.g. adaptive TDEE, Ashwell WHtR bands), the citation is followed by `(reconstructed — consistent with source description)`.

---

## Table of Contents

1. [User Profile Inputs](#1-user-profile-inputs)
2. [Body Composition Assessment](#2-body-composition-assessment)
3. [Health Risk Metrics](#3-health-risk-metrics)
4. [Muscular Potential Models](#4-muscular-potential-models)
5. [Cut / Bulk / Recomp Decision Tree](#5-cut--bulk--recomp-decision-tree)
6. [Resting Metabolic Rate (RMR)](#6-resting-metabolic-rate-rmr)
7. [TDEE & Activity Factors](#7-tdee--activity-factors)
8. [Adaptive TDEE](#8-adaptive-tdee)
9. [Calorie Targets (Cut / Bulk / Maintenance / Recomp)](#9-calorie-targets)
10. [Macros (Protein / Fat / Carbs)](#10-macros)
11. [Hydration](#11-hydration)
12. [Micronutrients & Fiber](#12-micronutrients--fiber)
13. [Macro Adjustment Protocol](#13-macro-adjustment-protocol)
14. [Progress Tracking & Plateau Detection](#14-progress-tracking--plateau-detection)
15. [Training Module (Framework-Ready)](#15-training-module)
16. [Meal Plan Module (Framework-Ready)](#16-meal-plan-module)
17. [Engine Orchestration](#17-engine-orchestration)
18. [Master Constants & Lookup Tables](#18-master-constants--lookup-tables)

---

## 1. User Profile Inputs

The engine consumes a `UserProfile` with **Standard depth** inputs:

| Field | Type | Range / Allowed Values | Required |
|---|---|---|---|
| `age` | int | 18–65 | ✓ |
| `sex` | enum | `male` / `female` | ✓ |
| `height_cm` | float | 140–220 | ✓ |
| `weight_kg` | float | 35–250 | ✓ |
| `body_fat_pct` | float | 3–55 | optional |
| `neck_cm`, `waist_cm`, `hip_cm` | float | circumference measurements for Navy/ABSI/WHR | optional |
| `activity_level` | enum | `sedentary` / `mostly_sedentary` / `lightly_active` / `active` / `highly_active` | ✓ |
| `training_status` | enum | `beginner` / `novice` / `intermediate` / `advanced` | ✓ |
| `primary_goal` | enum | `fat_loss` / `muscle_gain` / `recomp` / `maintenance` | ✓ |
| `training_days_per_week` | int | 2–6 | ✓ |
| `equipment_access` | enum | `full_gym` / `home_gym` / `bodyweight_only` | ✓ |
| `diet_type` | enum | `omnivore` (Phase-1 only) | ✓ |

> Phase-1 locks `diet_type=omnivore`. The engine architecture allows later extension to `vegan`, `vegetarian`, `keto`, `paleo`, etc.

---

## 2. Body Composition Assessment

### 2.1 Body Fat % — US Navy Circumference Method (DEFAULT)

`[rippedbody.com__how-calculate-body-fat-percentage.txt]` `[fatcalc.com__bf.txt]`

**Inputs:** neck, waist (men: abdomen at navel / women: narrowest point), hip (women only), height — all in **same unit** (engine uses cm; conversion to inches for the canonical formula).

**Formulas (inches):**
```
Men:   BF% = 86.010 × log10(abdomen_in − neck_in) − 70.041 × log10(height_in) + 36.76
Women: BF% = 163.205 × log10(waist_in + hip_in − neck_in) − 97.684 × log10(height_in) − 78.387
```

**Accuracy:** ±3–4 %. Unreliable <10 % BF (men) because navel measurement barely changes.

### 2.2 Body Fat % — BMI-Based (Jackson et al. 2002)

`[fatcalc.com__rmr-calculator.txt]`

Used when no circumference measurements are provided (only height + weight).

```
Men:   BF% = 0.14 × age + 37.31 × ln(BMI) − 103.94
Women: BF% = 0.14 × age + 39.96 × ln(BMI) − 102.01
```
African-American adjustment: men −2.0, women −3.0. Standard error ±4–5 %.

### 2.3 Body Fat % — CUN-BAE (BMI + age + sex)

`[fatcalc.com__bf.txt]` (reconstructed from cited Gómez-Ambrosi 2012 paper)

```
BF% = -44.988 + (0.503 × age) + (10.689 × BMI) + (0.462 × sex_code)
where sex_code = 0 (men) / 1 (women)
```

### 2.4 Body Fat % Categories (ACE / WHO / ACSM canonical tables)

| Category | Men | Women |
|---|---|---|
| Essential Fat | 2–5 % | 10–13 % |
| Athletes | 6–13 % | 14–20 % |
| Fitness | 14–17 % | 21–24 % |
| Acceptable / Average | 18–24 % | 25–31 % |
| Obesity | ≥25 % | ≥32 % |

### 2.5 RippedBody Visual Scale (Men; Women add +8 %)

| BF% (men) | Marker |
|---|---|
| 7–9 % | Fitness-model look, lower-back fat gone |
| 10–11 % | Lean, defined |
| 12–14 % | Blurry six-pack may show with sufficient muscle |
| 15–17 % | Continue cutting; if bulking, end bulk soon |
| 18–20 % | If reached by cutting, great; if bulking — stop |
| 21–24 % | Above optimal |
| 25–29 % | Approaching obese |
| 30 %+ | Obesity threshold |

**Key thresholds (men; women +8 %):**
- Stop cut: **10 %** (men) / 18 % (women)
- Stop bulk: **20 %** (men) / 28 % (women)
- Operational range: **10–20 %** (men) / 18–28 % (women)

### 2.6 Lean Body Mass

```
LBM_kg = weight_kg × (1 − BF% / 100)
Fat_mass_kg = weight_kg − LBM_kg
```

### 2.7 Target Weight at a Given BF% (LBM constant)

`[fatcalc.com__bf.txt]`

```
target_weight_kg = LBM_kg / (1 − target_BF% / 100)
```

---

## 3. Health Risk Metrics

### 3.1 BMI

`[fatcalc.com__ibw-calculator.txt]` `[ultimateperformance.com__...txt]`

```
BMI = weight_kg / (height_m)²
```

| BMI | Category |
|---|---|
| <18.5 | Underweight |
| 18.5–24.9 | Normal |
| 25.0–29.9 | Overweight |
| ≥30.0 | Obese |

Healthy BMI weight range:
```
weight_low_kg  = 18.5 × (height_m)²
weight_high_kg = 24.9 × (height_m)²
```

### 3.2 Waist-to-Hip Ratio (WHR)

`[fatcalc.com__whr.txt]`

```
WHR = waist / hip   (same unit)
```

| Group | Concern | High Risk |
|---|---|---|
| Men | >0.90 | >1.0 |
| Women | >0.85 | >1.0 |

### 3.3 Waist-to-Height Ratio (WHtR)

`[fatcalc.com__whtr-calculator.txt]` (Ashwell 2012 sex-specific bands reconstructed)

```
WHtR = waist / height   (same unit)
```

| Risk | Men | Women |
|---|---|---|
| Underweight / no risk | <0.34 | <0.42 |
| Healthy | 0.43–0.52 | 0.42–0.48 |
| Overweight | 0.53–0.57 | 0.49–0.53 |
| Obese | ≥0.58 | ≥0.54 |

Universal boundary: `WHtR < 0.5`.

### 3.4 ABSI (A Body Shape Index)

`[fatcalc.com__absi.txt]`

```
ABSI = WC_m × weight_kg^(-2/3) × height_m^(5/6)
```

ABSI z-score computed against NHANES 1999–2004 norms (age- and sex-banded); engine ships with simplified age-band mean/SD tables.

| Category | z-score |
|---|---|
| Low | <−0.868 |
| Below Average | −0.868 to −0.272 |
| Average | −0.272 to +0.229 |
| Above Average | +0.229 to +0.798 |
| High | >+0.798 |

### 3.5 Ideal Body Weight (IBW)

`[fatcalc.com__ibw-calculator.txt]`

All four formulas use `H_in` (height in inches) and a baseline of 60 in (5 ft):

| Formula | Men | Women |
|---|---|---|
| Devine (1974) | `50 + 2.3 × (H_in − 60)` | `45.5 + 2.3 × (H_in − 60)` |
| Robinson (1983) | `52 + 1.9 × (H_in − 60)` | `49 + 1.7 × (H_in − 60)` |
| Miller (1983) | `56.2 + 1.41 × (H_in − 60)` | `53.1 + 1.36 × (H_in − 60)` |
| Hamwi (1964) | `48 + 2.7 × (H_in − 60)` | `45.4 + 2.2 × (H_in − 60)` |

Frame-size adjustment (wrist circumference): ±10 % for small / large frame.

### 3.6 Skeletal Muscle Mass % (Janssen 2000 reference ranges)

`[fatcalc.com__mm.txt]`

| Age | Female | Male |
|---|---|---|
| 18–29 | 28.4–39.8 % | 37.9–46.7 % |
| 30–39 | 25.0–36.2 % | 34.1–44.1 % |
| 40–49 | 24.2–34.2 % | 33.1–41.1 % |
| 50–59 | 24.7–33.5 % | 31.7–38.5 % |
| 60–69 | 22.7–31.9 % | 29.9–37.7 % |
| 70+ | 25.5–34.9 % | 28.7–43.3 % |

### 3.7 Visceral Fat Risk

`[ultimateperformance.com__...txt]`

- Visceral fat >10 % of total fat → dramatically elevated risk of type-2 diabetes, Alzheimer's, heart disease, colorectal cancer.
- Hard / pregnant-feeling stomach in overweight men = high visceral fat signal.
- Body fat ≥25 % (men) / ≥32 % (women) = obesity-class risk.
- Sustained <10 % BF (men) → reproductive function suppression; overweight/obesity = biggest risk factor for low testosterone.

---

## 4. Muscular Potential Models

### 4.1 FFMI (Fat-Free Mass Index)

`[rippedbody.com__maximum-muscular-potential.txt]`

```
FFMI = FFM_kg / (height_m)²
     = [weight_kg × (1 − BF%)] / (height_m)²
```

### 4.2 Normalized / Adjusted FFMI (Kouri 1995)

```
Normalized FFMI = FFMI + 6.1 × (1.8 − height_m)    # canonical Kouri form
```

### 4.3 Genetic Ceilings

| Ceiling | FFMI | Source |
|---|---|---|
| Common natural limit | 25 | Kouri 1995 |
| Demonstrably attainable naturally | 27.3 | Mr. America 1939–1953 data |
| "Pretty likely" naturally with modern methods | 28 | RippedBody editorial |
| Steroid-user average / max | 25 / 32 | Kouri 1995 |

> **Engine note:** Compute and report FFMI both raw and at a standardized 10 % BF for fair comparison against ceilings.

### 4.4 Berkhan Model (stage-shredded, 5–6 % BF)

`[rippedbody.com__maximum-muscular-potential.txt]`

```
Max_stage_weight_kg = height_cm − 100     (range 98–102)
Max_stage_FFM_kg    = Max_stage_weight_kg × (1 − 0.05)
```

Yields FFMI ≈ 23.8–24.2 across 173–188 cm — the *conservative* model.

### 4.5 Muscle Growth Rate by Training Status

`[rippedbody.com__updated-bulking-guidelines.txt]` `[fatcalc.com__body-recomp-calculator.txt]` (Lyle McDonald model)

| Status | Muscle Gain Rate (Men) | Energy Surplus |
|---|---|---|
| Beginner (Year 1) | 1.0–2.0 % BW/mo, ~1–1.4 kg/mo | 200–300 kcal/day |
| Novice (Year 2) | 0.75–1.5 % BW/mo, ~0.7–1.0 kg/mo (declining) | 100–200 kcal/day |
| Intermediate (Years 2–3) | 0.5–1.0 % BW/mo, ~0.45–0.7 kg/mo | ~100 kcal/day |
| Advanced (Years 4+) | <0.5 % BW/mo, <0.45 kg/mo | Slight surplus |

**Women:** ~50 % of men's rates.

### 4.6 Expected 1st-Year Muscle Gain (Beginner)

15–25 lb (7–11 kg) of muscle in the first year, distributed:
- First 3–6 months: 2–3 lb/mo (1–1.4 kg/mo)
- Following 6–9 months: 1–2 lb/mo (0.5–1 kg/mo)

---

## 5. Cut / Bulk / Recomp Decision Tree

`[rippedbody.com__cut-or-bulk.txt]` `[rippedbody.com__goal-setting-1.txt]` `[fatcalc.com__body-recomp-calculator.txt]`

### 5.1 Master Decision Table (men; women add +8 % BF)

| Situation | Recommendation |
|---|---|
| Overweight / obese (M ≥25 %, F ≥32 %) | **Cut** |
| Underweight (M <10 %, F <18 %) with low muscle | **Bulk** |
| Novice in 13–18 % BF (M) | **Recomp** |
| Experienced, >16 % BF (M) | **Cut** |
| Experienced, <16 % BF (M) | **Cut or Bulk by preference** |
| Skinny-fat (M 12–23 %, body-weight stable) | **Recomp** (slight deficit) |
| Obese beginner (>30 % BF, new to training) | **Habit change first** (cut if needed) |

### 5.2 Recomp Eligibility (FatCalc / McDonald model)

| BF% (men) | Recomp Potential |
|---|---|
| >25 % | Excellent (10–20 % deficit OK) |
| 15–25 % | Good (0–10 % deficit) |
| <15 % | Limited (use bulk/cut cycle instead) |

For women, shift thresholds by +8–10 %.

### 5.3 Operational Boundaries

- Bulk only if **<15 % BF** (M) / **<23 %** (F).
- Cap bulk at **20 % BF** (M) / **28 %** (F) — health ceiling.
- Don't cut below **10 % BF** (M) / **18 %** (F) if planning to bulk next — hormonal suppression.
- Min bulk duration: **5 months** (ideal 10 months) before interrupting for cut.

### 5.4 Goal-Setting Time Horizon

| Goal | Time Horizon |
|---|---|
| Fat loss | `(current_BF − target_BF) × weight_kg × 0.78 / (weekly_loss_rate × weight_kg × 52)` |
| Muscle gain | `(target_FFM − current_FFM) / monthly_gain_rate` |

> Energy constants: 1 kg fat ≈ 7,700 kcal; 1 kg muscle ≈ 5,500 kcal synthesis energy (≈2,500 kcal/lb).

---

## 6. Resting Metabolic Rate (RMR)

### 6.1 Mifflin-St Jeor (1990) — DEFAULT

`[fatcalc.com__rmr-calculator.txt]` `[gymgeek.com__calculators-calorie-calculator.txt]`

```
Men:   RMR = 9.99 × weight_kg + 6.25 × height_cm − 4.92 × age + 5
Women: RMR = 9.99 × weight_kg + 6.25 × height_cm − 4.92 × age − 161
```

±10 % accuracy vs measured values.

### 6.2 Harris-Benedict Original (1919) — RippedBody's preferred

`[rippedbody.com__calories.txt]`

```
Men:   BMR = 66 + 13.7 × weight_kg + 5 × height_cm − 6.8 × age
Women: BMR = 655 + 9.6 × weight_kg + 1.8 × height_cm − 4.7 × age
```

### 6.3 Harris-Benedict Revised (1984, Roza & Shizgal)

`[fatcalc.com__rmr-calculator.txt]`

```
Men:   RMR = 13.397 × weight_kg + 4.799 × height_cm − 5.677 × age + 88.362
Women: RMR = 9.247 × weight_kg + 3.098 × height_cm − 4.330 × age + 447.593
```

### 6.4 Cunningham / Katch-McArdle (1991) — body-composition-aware

`[fatcalc.com__rmr-calculator.txt]`

```
RMR (both sexes) = 370 + 21.6 × LBM_kg
```

Use when BF% is known and the user is athletic / muscular.

### 6.5 RMR Selection Logic

```
if bf_pct_known:
    use Cunningham  (best for athletic, muscular)
else:
    use Mifflin-St Jeor  (general-population default)
```

Apply metabolic adaptations (RippedBody):
- If in active deficit: **−5 %**
- If >10 % below all-time high body weight: **−3 %**
- Both: compounds (multiplicative)

### 6.6 BMR vs RMR

- True BMR requires 12–14 h fasted, sleep in lab, thermoneutral, dim light, motionless.
- RMR/REE is what online "BMR calculators" actually estimate.
- Difference typically 3–10 %.

---

## 7. TDEE & Activity Factors

### 7.1 TDEE Formula

```
TDEE = RMR × activity_multiplier
```

### 7.2 Activity Multiplier Table (RippedBody 5-category — DEFAULT)

`[rippedbody.com__macro-calculator.txt]`

| Level | Steps/day | Multiplier | Definition |
|---|---|---|---|
| Sedentary | <5,000 | ×1.25 | Desk job, drive everywhere, sit most of day |
| Mostly Sedentary + lifting | <5,000 | ×1.45 | As above + lift 3–6 d/wk |
| Lightly Active + lifting | 5,000–10,000 | ×1.65 | Light walking/movement + lift 3–6 d/wk |
| Active + lifting | 10,000–15,000 | ×1.85 | Physically active most of day + lift |
| Highly Active + lifting | 15,000+ | ×2.05 | Very physical job or intense exercise most days + lift |

### 7.3 Simplified 4-Category Alternative (RippedBody calories.txt)

| Level | Multiplier |
|---|---|
| Sedentary | ×1.15 |
| Mostly sedentary + 3–6 d/wk lifting | ×1.35 |
| Lightly active + 3–6 d/wk lifting | ×1.55 |
| Highly active + 3–6 d/wk lifting | ×1.75 |

### 7.4 Harris-Benedict SAF (FatCalc standard)

| Level | Multiplier |
|---|---|
| Sedentary (desk job, no exercise) | ×1.2 |
| Light (exercise 1–3 d/wk) | ×1.375 |
| Moderate (exercise 3–5 d/wk) | ×1.55 |
| Very Active (hard exercise 6–7 d/wk) | ×1.725 |
| Extra Active (2×/day training or labor job) | ×1.9 |

---

## 8. Adaptive TDEE

`[zolthealth.com__learn-what-is-adaptive-tdee.txt]` `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]` `[gymcreek.com__adaptive-tdee-calculator.txt]` `[macrofactor.com__bulk-or-cut.txt]`

### 8.1 First-Principles Observed-TDEE Identity

For a window of `N` days with daily intake `intake_i`, weight at start `W_start`, weight at end `W_end`:

```
avg_intake     = (1/N) × Σ intake_i                       [kcal/day]
Δweight_kg     = W_end − W_start                           [kg]

observed_TDEE  = avg_intake − (Δweight_kg × 7700) / N      [kcal/day]
              = avg_intake − (Δweight_lb × 3500) / N      [imperial]
```

If weight is stable → observed_TDEE = avg_intake.

### 8.2 Statistical-Model Adaptive TDEE (Bayesian blend)

```
prior_TDEE       = RMR × SAF                                # day-0 estimate

w_data(t)        = 0                          for t ≤ 7 days
                 = (t − 7) / 53               for 7 < t ≤ 60 days   # linear ramp
                 = 1.0                        for t > 60 days

adaptive_TDEE_t  = w_data(t) × observed_TDEE_t + (1 − w_data(t)) × prior_TDEE
```

### 8.3 Smoothing Window

- 7-day rolling average weight for daily-weigh users.
- Outlier detection: weight deltas > ±2 % in 24 h flagged.
- Statistical model produces an estimate from day 1; converges to user's true TDEE in 1–2 months.
- First-principles model needs ≥4 weeks; reliable after "a few months."
- Re-evaluate TDEE every 4–6 weeks.

### 8.4 Convergence Rules

| Days of data | Recommended behavior |
|---|---|
| 0–7 | Return prior (Mifflin-St Jeor × SAF) |
| 8–30 | Blend, mostly prior |
| 31–60 | Blend, mostly user data |
| 60+ | Pure observed TDEE (with outlier rejection) |

---

## 9. Calorie Targets

### 9.1 Energy Constants

| Quantity | Value |
|---|---|
| 1 lb body fat | 3,500 kcal |
| 1 kg body fat | 7,700 kcal |
| 1 lb muscle synthesis | 2,500 kcal |
| 1 kg muscle synthesis | 5,500 kcal |
| 1 lb/week loss | 500 kcal/day deficit |
| 1 kg/week loss | 1,100 kcal/day deficit |
| 1 lb/month gain (1:1 fat:muscle) | ~100 kcal/day surplus |
| 1 lb/month gain w/ NEAT buffer | **150 kcal/day** surplus |
| 1 kg/month gain w/ NEAT buffer | **330 kcal/day** surplus |
| Min calorie floor — women | 1,200 kcal/day |
| Min calorie floor — men | 1,500 kcal/day |
| Hard cap — weekly loss | 2 lb / 1 kg |

### 9.2 Cut (Fat Loss)

`[rippedbody.com__calories.txt]` `[macrofactor.com__cutting-calculator.txt]`

```
TDCI_cut = TDEE − (weight_lb × weekly_rate × 500)
         = TDEE − (weight_kg × weekly_rate × 1100)
```

`weekly_rate` is the **fraction** of body weight lost per week (e.g., 0.0075 = 0.75 %).

**Rate tiers (MacroFactor):**

| Tier | % BW/week | Relative deficit |
|---|---|---|
| Very Conservative | 0.10 % | <5 % |
| Conservative | 0.25 % | 5–10 % |
| Moderate (DEFAULT) | 0.50–0.75 % | 10–20 % |
| Slightly Aggressive | 1.00 % | 20–30 % |
| Aggressive | 1.50 % | >30 % |

**Defaults by leanness:**
- Sweet spot: 0.5 % BW/week
- High BF (>20 % M): up to 0.75–1.0 %/wk
- Lean (<10 % M): ≤0.5 %/wk
- Engine default: **0.75 %** (accounts for metabolic adaptation)

**Muscle-retention threshold (Murphy & Koehler 2021):**
- Deficits <500 kcal/day → recomp possible (lose fat, gain small muscle)
- Deficits >500 kcal/day → lean mass loss begins
- Optimal FFM-retention rate: **0.6–0.7 % BW/week**

### 9.3 Bulk (Muscle Gain)

`[rippedbody.com__how-to-bulk.txt]` `[rippedbody.com__updated-bulking-guidelines.txt]` `[macrofactor.com__bulking-calculator.txt]`

```
TDCI_bulk = TDEE + (weight_lb × monthly_rate × 150)
          = TDEE + (weight_kg × monthly_rate × 330)
```

`monthly_rate` is the **fraction** of body weight gained per month.

**Monthly gain rates by training status:**

| Status | Rate (% BW/month) |
|---|---|
| Beginner | 2.0 % |
| Novice | 1.5 % |
| Intermediate | 1.0 % |
| Advanced | 0.5 % |

**Weekly rates (MacroFactor table, % BW/week):**

| Tier | Beginner | Intermediate | Experienced |
|---|---|---|---|
| Conservative | 0.20 % | 0.15 % | 0.10 % |
| Happy Medium (DEFAULT) | 0.50 % | 0.325 % | 0.15 % |
| Aggressive | 0.80 % | 0.575 % | 0.35 % |
| Very Aggressive | 1.00 % | 0.80 % | 0.60 % |

Apply `min(percent_rate, absolute_cap_lb_per_week)` from the MacroFactor cap table.

**Composition outcome:**
- 0.16 %/week → ~85 % FFM / 15 % fat
- 0.38 %/week → ~65 % FFM / 35 % fat

### 9.4 Maintenance

```
TDCI_maintenance = TDEE   (no adjustment)
```

### 9.5 Recomp

`[fatcalc.com__body-recomp-calculator.txt]`

- High recomp potential: 10–20 % deficit
- Moderate recomp potential: 0–10 % deficit
- Limited recomp potential: switch to bulk/cut cycle

### 9.6 Calorie Floors (Hard Limits)

```
calorie_floor = 1200 if sex == "female" else 1500
final_calories = max(calculated_calories, calorie_floor)
```

### 9.7 Reverse Diet

`[fatcalc.com__reverse-diet-calculator.txt]`

| Aggressiveness | Weekly Increment | Duration (typical) |
|---|---|---|
| Conservative | +50 kcal/week | 12–20 weeks |
| Moderate (DEFAULT) | +100 kcal/week | 6–10 weeks |
| Aggressive | +150 kcal/week | 4–7 weeks |

Red flag: weekly weight gain >0.5 % BW → slow down.

---

## 10. Macros

### 10.1 Macro Energy Densities

```
1 g protein = 4 kcal
1 g carb    = 4 kcal
1 g fat     = 9 kcal
1 g alcohol = 7 kcal
```

### 10.2 Protein

`[rippedbody.com__macro-calculator.txt]` `[rippedbody.com__best-macro-ratio.txt]` `[fatcalc.com__protein-calculator.txt]`

**When BF% is KNOWN (use LBM):**
| Goal | g / lb LBM | g / kg LBM |
|---|---|---|
| Bulk or Recomp | 1.0 | 2.2 |
| Cut | 1.14 | 2.5 |

**When BF% is UNKNOWN (use body / target weight):**
| Goal | g / lb | g / kg |
|---|---|---|
| Bulk or Recomp (body weight) | 0.73 | 1.6 |
| Cut (target body weight) | 1.0 | 2.2 |

**Simple default:** 1 g protein / lb body weight (good for most).

**Protein by goal and diet (Helms/Morton meta-analyses):**

| Goal | Protein (g/kg BW) |
|---|---|
| Lean Bulk | 1.6–2.2 |
| Recomp | 1.8–2.4 |
| Cut | 2.0–2.7 |

**Vegan overrides (compensate for lower bioavailability):**
- Not dieting: 1.0 g/lb (2.2 g/kg)
- Dieting: 1.2 g/lb (2.6 g/kg)

**Obese override:** Protein = 1 g per cm of height (avoids excessive intake).

**Age >65:** Minimum 1.0–1.2 g/kg (anabolic resistance).

**Pregnancy / breastfeeding:** +25 g/day each.

### 10.3 Fat

`[rippedbody.com__best-macro-ratio.txt]` `[rippedbody.com__how-to-adjust-macros.txt]`

| Goal | Fat % of calories | Absolute floor |
|---|---|---|
| Cut | 15–25 % | 40–60 g/day OR 0.25 g/lb (0.5 g/kg) |
| Maintenance / Bulk | 20–30 % | same floor |
| Vegan | 15–25 % | 0.25 g/lb |

Saturated fat ceiling: <10 % of total calories.

```
fat_g = max(
    total_calories × fat_pct_min / 9,        # % floor
    40,                                        # absolute floor (g) — general
    bodyweight_lb × 0.25                      # alt floor (RippedBody)
)
```

### 10.4 Carbs

`[rippedbody.com__best-macro-ratio.txt]` `[rippedbody.com__macro-calculator.txt]`

```
carb_calories = total_calories − (protein_g × 4) − (fat_g × 9)
carb_g        = carb_calories / 4
```

**Keto override:**
- Carbs ≤ 50 g/day
- Fat ≥ 60 % of calories
- Protein 20–25 % of calories

**Slider rule (RippedBody macro calculator):** When adjusting CALORIES, protein stays constant; carbs and fats adjust in a **2:1 ratio by calories** (2 parts carbs : 1 part fat).
- 250 kcal cut → −40 g carbs, −10 g fat
- 250 kcal bulk → +40 g carbs, +10 g fat (bulk uses 3:1 — see §13)

### 10.5 Default Macro Computation Order

1. Set protein (per §10.2 rules).
2. Set fat (per §10.3 rules).
3. Carbs = remainder.
4. Verify: protein×4 + fat×9 + carb×4 ≈ total_calories (±1 %).

---

## 11. Hydration

`[fatcalc.com__hydration-calculator.txt]`

### 11.1 Multi-Step Formula

```python
def water_intake_l(
    weight_kg: float, sex: str, exercise_hours: float,
    exercise_intensity: str, climate: str,
    pregnant: bool = False, breastfeeding: bool = False,
) -> float:
    # Step 1: Base (body weight)
    water = weight_kg * 0.030                              # 30 mL/kg

    # Step 2: Sex adjustment
    if sex == "male":
        water += 0.300                                     # +300 mL

    # Step 3: Exercise sweat
    sweat_rate = {"light": 0.300, "moderate": 0.500, "intense": 0.800}  # L/h
    water += exercise_hours * sweat_rate[exercise_intensity]

    # Step 4: Climate multiplier (applied to total so far)
    climate_mult = {
        "cold": 0.95, "temperate": 1.0,
        "hot": 1.3, "hot_humid": 1.4,
    }
    water *= climate_mult[climate]

    # Step 5: Pregnancy
    if pregnant:
        water += 0.300

    # Step 6: Breastfeeding
    if breastfeeding:
        water += 0.700

    return water  # liters
```

### 11.2 Reference Values

| Authority | Women | Men |
|---|---|---|
| EFSA Adequate Intake | 2.0 L/day | 2.5 L/day |
| NAM Adequate Intake | 2.7 L/day | 3.7 L/day |

- ~20 % of daily fluid intake comes from food.
- Kidneys process 800–1,000 mL/h — spread intake.
- Target urine color: pale yellow.
- 2 % body-weight dehydration → performance impairment.

---

## 12. Micronutrients & Fiber

### 12.1 Fiber

`[rippedbody.com__micros.txt]`

```
fiber_g = 14 × (total_calories / 1000)
```

### 12.2 Fruit & Vegetable Intake

| Calorie Intake | Cups Fruit | Cups Veg |
|---|---|---|
| 1,200–2,000 | 2 | 2 |
| 2,000–3,000 | 3 | 3 |
| 3,000–4,000 | 4 | 4 |

### 12.3 At-Risk Nutrients for Dieters

`[rippedbody.com__micros.txt]`

Maintain dairy + red meat + sun exposure to avoid deficiencies in:
- Calcium (bone health)
- Zinc (metabolism)
- Magnesium
- Iron (strength)
- Vitamin D

### 12.4 Vegan Supplement Protocol (for future vegan support)

| Nutrient | Daily Dose | Reason |
|---|---|---|
| Vitamin B12 | 2.4–6 μg | 50 % of vegans deficient |
| Iron | 14 mg (M) / 33 mg (F) | No red meat |
| Zinc | 16.5 mg (M) / 12 mg (F) | Poor plant absorption |
| Calcium | 500–1,000 mg | Poorer absorption |
| Omega-3 (EPA+DHA) | 1–2 g | No fish — algae-based |
| Vitamin D3 | 1,000–3,000 IU | Lichen-based D3 |
| Creatine | 5 g | No red meat/fish/poultry |

---

## 13. Macro Adjustment Protocol

`[rippedbody.com__how-to-adjust-macros.txt]` `[rippedbody.com__how-to-adjust-macros-bulk.txt]`

### 13.1 Cut-Phase Troubleshooting (Calorie Reduction is LAST)

1. **Adherence check** — solid week incl. weekend.
2. **Tracking accuracy** — log everything 2 weeks.
3. **Hunger management** — swap liquid calories, cut sugary foods, more fruit/veg/soups, lower meal frequency.
4. **Food environment** — control surroundings.
5. **Sleep quality** — poor sleep mimics stress + water retention.
6. **Stress management.**
7. **Activity / NEAT** — set min 5,000 steps/day.
8. **Cardio** (before calorie reduction): low-impact, <50 % of lifting time, avoid HIIT. 180-lb person needs 25 min moderate cardio/day for 200 kcal deficit.
9. **Calorie reduction (LAST):**
   - Option 1: Repeat initial calculation
   - Option 2 (preferred): −5–8 % total intake (~100–200 kcal)

### 13.2 Cut Adjustment Math

```
calorie_delta_kcal = delta_lb_off_target × 500        # per 0.5 lb deviation, lbs
calorie_delta_kcal = delta_kg_off_target × 1100       # per 0.5 kg deviation, kg

# Losing too slowly (positive delta) → DECREASE intake
# Losing too fast (negative delta) → INCREASE intake

# Macro redistribution: 2:1 carbs:fat by calories
# 250 kcal adjustment → −40 g carbs, −10 g fat (or reverse for increase)
```

### 13.3 Bulk-Phase Troubleshooting (Calorie Increase is LAST)

1. Feeling too full? Swap whole food for liquid calories; eat faster; higher meal frequency; manage food environment.
2. Revisit "why" — bulking is a chore for hard gainers.
3. Manage stress.
4. Sleep.
5. Activity level increase — wait to see effect before proactively bumping.
6. Calorie increase (LAST):
   - Option 1: Repeat calculation
   - Option 2 (preferred): +5 % (~150–200 kcal)

### 13.4 Bulk Adjustment Math

```
calorie_delta_kcal = delta_lb_off_target_monthly × 150      # per 1 lb deviation, lbs
calorie_delta_kcal = delta_kg_off_target_monthly × 330      # per 1 kg deviation, kg

# Gaining too slowly → INCREASE intake
# Gaining too fast → DECREASE intake

# Bulk macro redistribution: 3:1 carbs:fat by calories
# 770 kcal increase → +135 g carbs (540 kcal), +25 g fat (225 kcal)
# 150 kcal increase → +25 g carbs, +5 g fat
```

### 13.5 Initial Adjustment Timing

`[rippedbody.com__initial-adjustment.txt]` `[rippedbody.com__how-to-adjust-macros.txt]`

| Phase | First-Adjustment Window |
|---|---|
| Cut | Wait until week 3 (ignore weeks 1–2 water shifts); women may need to wait until week 4 |
| Bulk | Wait until week 6–7 |
| Ongoing adjustments | Every 5 weeks |

### 13.6 Incremental Change Sizes

| Phase | Incremental Change |
|---|---|
| Cut | 200–250 kcal/day |
| Slow bulk | 100–150 kcal/day |

### 13.7 Stall vs Whoosh

`[rippedbody.com__calories.txt]`

- **Sudden stall** (multi-week scale freeze): water retention masking fat loss; wait minimum 4 weeks before adjusting.
- **Gradual slowdown**: real metabolic adaptation → make downward adjustment.
- **Whoosh**: sudden multi-kg drop after a stall (water release); more common in women.
- Causes of water retention: stress, cortisol, sleep issues.

### 13.8 Expected Measurement Patterns by BF%

| BF% (men) | Fat Loss Pattern |
|---|---|
| >20 % | Measurements drop uniformly (mostly visceral) |
| 10–20 % | Fat loss from upper abs first, downward |
| <10 % | Minimal mid/upper stomach change; lower stomach + waist change most |
| <8 % | Abdominal fat essentially gone; visual change hard from front |

---

## 14. Progress Tracking & Plateau Detection

`[rippedbody.com__diet-progress-tracking.txt]` `[rippedbody.com__training-plateaus.txt]`

### 14.1 Tracking Standards

| Metric | Frequency |
|---|---|
| Body weight | Daily (morning, post-bathroom, fasted); average weekly |
| Waist (navel, +3 fingers, −3 fingers) | Weekly |
| 9-site circumference | Weekly |
| Progress photos | Monthly |
| Strength (working weights) | Every session |
| Adherence (training + nutrition) | Weekly |

### 14.2 Plateau Detection

**Cut plateau:** 3+ weeks with weekly-average weight within ±0.3 % of prior weekly average.
**Bulk plateau:** 4+ weeks with monthly-average weight within ±0.5 % of prior month.

### 14.3 Plateau Diagnosis Sequence

1. Sleep (≤6 h/night → cortisol, water retention, hunger)
2. Calories (adherence + tracking accuracy)
3. Protein (insufficient → muscle loss, hunger)
4. RPE / training intensity
5. Frequency / volume
6. Technique
7. Joint pain / injury

### 14.4 Adherence Scoring

```
dietary_adherence_pct  = (consumed_kcal / target_kcal) × 100
training_adherence_pct = (sessions_completed / sessions_planned) × 100

# <85 % training adherence → red flag; fix before adjusting macros
```

### 14.5 Expected Conversion Rules

- 4–5 lb fat loss ≈ 2–2.5 cm (~1 in) stomach circumference reduction.
- ~1.5–2.5 cm sudden stomach increase at start of bulk = gut content (not fat).
- ~5 lb sudden weight increase at start of maintenance after cut = water/gut/glycogen regain.

### 14.6 Diet Breaks

- Return to maintenance when injured, sick, or unable to train (unless very high BF — fatter individuals lose less muscle in deficit).
- Typical break: 2 weeks at maintenance.

---

## 15. Training Module

> **Phase-1 status: framework-ready.** The user will supply detailed exercise resources later. The engine ships with a generic periodized template for healthy omnivore adults 18–65, extensible via the `exercise_library.py` registry.

### 15.1 Training Days Selection by Goal

| Goal | Default Split | Days/Week |
|---|---|---|
| Fat loss | Full-body or upper/lower | 3–4 |
| Muscle gain | Upper/lower or push/pull/legs | 4–5 |
| Recomp | Upper/lower | 3–4 |
| Maintenance | Original split preserved | 3–5 |

### 15.2 Default Split Recommendation Logic

```
if training_days <= 3:
    split = "full_body"  # 3x/week, alternate days
elif training_days == 4:
    split = "upper_lower"  # 2x cycle
elif training_days == 5:
    split = "push_pull_legs_upper_lower"  # PPLUL
elif training_days == 6:
    split = "push_pull_legs_2x"  # PPL ×2
```

### 15.3 Volume Standards (recomp / general)

`[fatcalc.com__body-recomp-calculator.txt]`

- Train each muscle group ≥2×/week
- 10–20 hard sets per muscle group per week
- Compound movements as foundation
- Progressive overload: gradually increase weight/reps/volume

### 15.4 Progression Scheme (default)

- Linear progression for beginners (add load weekly)
- Daily Undulating Periodization (DUP) for intermediates
- Block periodization for advanced

### 15.5 Exercise Library (Phase-1 minimal set)

The engine ships with a minimal registry of ~30 compound + accessory exercises (squat, deadlift, bench press, OHP, row, pull-up, RDL, lunge, etc.). The user will later provide a detailed exercise library to extend this registry.

---

## 16. Meal Plan Module

> **Phase-1 status: framework-ready.** The user will supply detailed meal resources later. The engine ships with a generic meal-template scaffolding and minimal food database.

### 16.1 Meal Frequency Options

- 3 meals/day (default — breakfast, lunch, dinner)
- 4 meals/day (add snack)
- 5 meals/day (add 2 snacks)
- 2 meals/day (intermittent fasting — 16:8)

### 16.2 Macro Allocation per Meal

| Meal pattern | Breakfast | Lunch | Dinner | Snack 1 | Snack 2 |
|---|---|---|---|---|---|
| 3 meals | 30 % | 35 % | 35 % | — | — |
| 4 meals | 25 % | 30 % | 30 % | 15 % | — |
| 5 meals | 20 % | 25 % | 25 % | 15 % | 15 % |
| 2 meals (IF) | — | 45 % | 55 % | — | — |

### 16.3 Per-M Meal Protein Target

`[fatcalc.com__protein-calculator.txt]`

20–40 g high-quality protein per meal, divided across 3–5 meals.

### 16.4 Food Database (Phase-1 minimal)

The engine ships with ~50 staple foods covering proteins, carbs, fats, vegetables, and fruits — enough to generate 7-day meal templates. The user will later provide a detailed food database to extend this.

### 16.5 Meal Plan Generation Algorithm

```
1. Compute total daily macros (from nutrition module).
2. Determine meal frequency (user preference or default 3).
3. Allocate macros per meal using §16.2 percentages.
4. For each meal, select foods from database that fit the per-meal macro targets.
5. Generate 7 distinct day-plans varying protein sources and carb sources.
6. Output: list of 7 DayPlans, each with 3–5 Meals, each Meal with food items + gram amounts.
```

---

## 17. Engine Orchestration

### 17.1 Top-Level API

```python
from fitness_engine import assess_profile, propose_plan, UserProfile

# 1. Assessment
profile = UserProfile(age=30, sex="male", height_cm=178, weight_kg=82,
                      body_fat_pct=18, neck_cm=38, waist_cm=86, hip_cm=98,
                      activity_level="mostly_sedentary", training_status="novice",
                      primary_goal="fat_loss", training_days_per_week=4,
                      equipment_access="full_gym", diet_type="omnivore")

assessment = assess_profile(profile)
# → AssessmentResult(body_composition, health_risk, muscular_potential, recommended_strategy)

# 2. Plan proposal
plan = propose_plan(profile, assessment)
# → FitnessPlan(nutrition_plan, training_plan, meal_plan, timeline)
```

### 17.2 Pipeline

```
UserProfile
    │
    ▼
┌──────────────────────────────────────────┐
│ Assessment Module                        │
│  - Body composition (BF%, LBM, FFMI)     │
│  - Health risk (BMI, WHR, WHtR, ABSI)   │
│  - Muscular potential (FFMI ceiling)     │
│  - Cut/bulk/recomp decision              │
└──────────────────────────────────────────┘
    │
    ▼ AssessmentResult
┌──────────────────────────────────────────┐
│ Nutrition Module                         │
│  - RMR (Mifflin or Cunningham)           │
│  - TDEE (RMR × activity factor)          │
│  - Adaptive TDEE (if logs provided)      │
│  - Calorie target (cut/bulk/maint/recomp)│
│  - Macros (protein → fat → carbs)        │
│  - Hydration                             │
│  - Fiber + fruit/veg targets             │
└──────────────────────────────────────────┘
    │
    ▼ NutritionPlan
┌──────────────────────────────────────────┐
│ Training Module                          │
│  - Split selection (days/week)           │
│  - Exercise selection (from library)     │
│  - Progression scheme                    │
│  - Mesocycle plan                        │
└──────────────────────────────────────────┘
    │
    ▼ TrainingPlan
┌──────────────────────────────────────────┐
│ Meal Plan Module                         │
│  - Macro allocation per meal             │
│  - Food selection from database          │
│  - 7-day template generation             │
└──────────────────────────────────────────┘
    │
    ▼ FitnessPlan (final deliverable)
```

### 17.3 Future Extensions (Phase-2 hooks)

- Adaptive TDEE with logged intake + weight time-series
- Vegan / vegetarian / keto / paleo diet modules
- Detailed exercise library (user-supplied)
- Detailed food database (user-supplied)
- Older adults (>65) with adjusted protein and recovery
- Athlete / contest-prep peak week protocol
- REST API + CLI interfaces

---

## 18. Master Constants & Lookup Tables

### 18.1 Energy Constants

```python
KCAL_PER_GRAM = {"protein": 4, "carb": 4, "fat": 9, "alcohol": 7}
KCAL_PER_LB_FAT = 3500
KCAL_PER_KG_FAT = 7700
KCAL_PER_LB_MUSCLE = 2500
KCAL_PER_KG_MUSCLE = 5500
SURPLUS_KCAL_PER_LB_PER_MONTH = 150       # bulk (with NEAT buffer)
SURPLUS_KCAL_PER_KG_PER_MONTH = 330
DEFICIT_KCAL_PER_LB_PER_WEEK = 500         # cut
DEFICIT_KCAL_PER_KG_PER_WEEK = 1100
```

### 18.2 Calorie Floors

```python
MIN_CALORIES = {"female": 1200, "male": 1500}
MAX_WEEKLY_LOSS_LB = 2.0
MAX_WEEKLY_LOSS_KG = 1.0
```

### 18.3 Activity Multipliers (RippedBody 5-category — DEFAULT)

```python
ACTIVITY_FACTORS_RIPPEDBODY = {
    "sedentary":          1.25,
    "mostly_sedentary":   1.45,
    "lightly_active":     1.65,
    "active":             1.85,
    "highly_active":      2.05,
}
```

### 18.4 Activity Multipliers (Harris-Benedict SAF)

```python
ACTIVITY_FACTORS_HARRIS_BENEDICT = {
    "sedentary":          1.20,
    "light":              1.375,
    "moderate":           1.55,
    "very_active":        1.725,
    "extra_active":       1.90,
}
```

### 18.5 Cut Rate Tiers

```python
CUT_RATE_TIERS = [
    {"name": "very_conservative", "pct_bw_per_week": 0.0010, "relative_deficit": "<5%"},
    {"name": "conservative",      "pct_bw_per_week": 0.0025, "relative_deficit": "5-10%"},
    {"name": "moderate",          "pct_bw_per_week": 0.0075, "relative_deficit": "10-20%"},  # DEFAULT
    {"name": "aggressive",        "pct_bw_per_week": 0.0100, "relative_deficit": "20-30%"},
    {"name": "very_aggressive",   "pct_bw_per_week": 0.0150, "relative_deficit": ">30%"},
]
DEFAULT_CUT_RATE = 0.0075   # 0.75 % BW/week
SWEET_SPOT_CUT_RATE = 0.005  # 0.5 % BW/week
MAX_CUT_RATE = 0.015
```

### 18.6 Bulk Rate by Training Status (monthly % BW)

```python
BULK_RATE_BY_STATUS = {
    "beginner":     0.020,
    "novice":       0.015,
    "intermediate": 0.010,
    "advanced":     0.005,
}
```

### 18.7 Bulk Rate Tiers (MacroFactor weekly % BW)

```python
BULK_WEEKLY_RATE_TIERS = {
    # (beginner, intermediate, experienced)
    "conservative":     (0.0020, 0.0015, 0.0010),
    "happy_medium":     (0.0050, 0.00325, 0.0015),  # DEFAULT
    "aggressive":       (0.0080, 0.00575, 0.0035),
    "very_aggressive":  (0.0100, 0.00800, 0.0060),
}

BULK_WEEKLY_CAP_LB = {
    "conservative":     (0.33, 0.26, 0.18),
    "happy_medium":     (0.88, 0.57, 0.26),
    "aggressive":       (1.41, 1.01, 0.62),
    "very_aggressive":  (1.76, 1.41, 1.06),
}
```

### 18.8 BF% Categories (ACE)

```python
BF_CATEGORIES = {
    "male":   [
        ("Essential Fat",  2,  5),
        ("Athletes",       6, 13),
        ("Fitness",       14, 17),
        ("Acceptable",    18, 24),
        ("Obesity",       25, 999),
    ],
    "female": [
        ("Essential Fat", 10, 13),
        ("Athletes",      14, 20),
        ("Fitness",       21, 24),
        ("Acceptable",    25, 31),
        ("Obesity",       32, 999),
    ],
}
```

### 18.9 Cut/Bulk BF Boundaries (men; women +8 %)

```python
CUT_BULK_BOUNDARIES = {
    "male":   {"cut_floor": 10, "bulk_ceiling": 20, "bulk_start": 15, "operational": (10, 20)},
    "female": {"cut_floor": 18, "bulk_ceiling": 28, "bulk_start": 23, "operational": (18, 28)},
}
```

### 18.10 Macro Percentages by Diet Type

```python
DIET_PRESETS = {
    "balanced":        {"fat": 0.25, "protein": 0.18, "carb": 0.57},
    "low_fat":         {"fat": 0.18, "protein": 0.17, "carb": 0.65},
    "low_carb":        {"fat": 0.45, "protein": 0.28, "carb": 0.27},
    "high_protein":    {"fat": 0.25, "protein": 0.35, "carb": 0.40},
    "standard_keto":   {"fat": 0.70, "protein": 0.22, "carb": 0.08},
    "high_protein_keto":{"fat": 0.60, "protein": 0.33, "carb": 0.07},
    "mediterranean":   {"fat": 0.38, "protein": 0.17, "carb": 0.45},
    "paleo":           {"fat": 0.40, "protein": 0.30, "carb": 0.30},
    "vegetarian":      {"fat": 0.30, "protein": 0.17, "carb": 0.53},
    "vegan":           {"fat": 0.25, "protein": 0.15, "carb": 0.60},
    "gluten_free":     {"fat": 0.30, "protein": 0.18, "carb": 0.52},
}
```

### 18.11 FFMI Ceilings

```python
FFMI_CEILINGS = {
    "natural_common":       25.0,    # Kouri 1995
    "natural_attainable":  27.3,    # Mr. America 1939-1953
    "natural_likely_max":  28.0,    # RippedBody editorial
    "steroid_avg":         25.0,
    "steroid_max":         32.0,
}
```

### 18.12 Hydration Constants

```python
HYDRATION = {
    "base_ml_per_kg":          30,           # 30 mL/kg
    "sex_add_ml_male":        300,
    "sweat_rate_ml_per_hr":   {"light": 300, "moderate": 500, "intense": 800},
    "climate_multiplier":     {"cold": 0.95, "temperate": 1.0, "hot": 1.3, "hot_humid": 1.4},
    "pregnancy_add_ml":       300,
    "breastfeeding_add_ml":   700,
}
```

### 18.13 Fiber & Fruit/Veg

```python
FIBER_G_PER_1000_KCAL = 14

FRUIT_VEG_TIERS = [
    (2000, 2, 2),   # max_cal, cups_fruit, cups_veg
    (3000, 3, 3),
    (4000, 4, 4),
    (float("inf"), 4, 4),
]
```

### 18.14 IBW Formula Coefficients

```python
IBW_FORMULAS = {
    "devine":   {"male": (50.0, 2.3),  "female": (45.5, 2.3)},
    "robinson": {"male": (52.0, 1.9),  "female": (49.0, 1.7)},
    "miller":   {"male": (56.2, 1.41), "female": (53.1, 1.36)},
    "hamwi":    {"male": (48.0, 2.7),  "female": (45.4, 2.2)},
}
# IBW_kg = base + multiplier × (height_in - 60)
```

### 18.15 Reverse Diet Presets

```python
REVERSE_DIET_PRESETS = {
    "conservative":  {"weekly_increment_kcal": 50,  "duration_weeks": (12, 20)},
    "moderate":      {"weekly_increment_kcal": 100, "duration_weeks": (6, 10)},   # DEFAULT
    "aggressive":    {"weekly_increment_kcal": 150, "duration_weeks": (4, 7)},
}
RED_FLAG_WEEKLY_GAIN_PCT = 0.005  # 0.5 % BW/week
```

---

**End of reference guide.** All formulas, thresholds, and decision rules are now codified and ready for Python implementation in `fitness_engine/`.

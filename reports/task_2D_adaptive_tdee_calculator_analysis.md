# Task 2-D — Adaptive TDEE & Calculator Methodology Analysis

**Agent:** cluster-D-analyzer
**Sources analyzed:** 9 files in `/home/z/my-project/resources/synthesized/`
**Topic:** Adaptive TDEE, calculator math, bulk/cut decisioning, dynamic TDEE updating

---

## 1. Adaptive TDEE Concept

**Definition.** Adaptive TDEE is a *dynamic* method of calculating Total Daily Energy Expenditure (TDEE) that adjusts based on the user's **actual** weight changes and food intake over time, rather than on a static population formula. `[zolthealth.com__learn-what-is-adaptive-tdee.txt]` `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]` `[gymcreek.com__adaptive-tdee-calculator.txt]`

**TDEE composition.** TDEE = BMR + Thermic Effect of Food (~10 % of daily burn) + Physical Activity calories. `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]` `[gymgeek.com__calculators-calorie-calculator.txt]`

**Why static formulas fail:**
- Population formulas (Harris-Benedict, Mifflin-St Jeor, Katch-McArdle) are typically **10–15 % off** for many people, and far more for some. `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]`
- Two people with identical height/weight/age/activity can differ by **200–400 kcal/day** (genetics, muscle mass, hormones, gut microbiome). `[zolthealth.com__learn-what-is-adaptive-tdee.txt]`
- **Metabolic adaptation** reduces TDEE by **15–25 %** during prolonged calorie restriction (Rosenbaum & Leibel 2010; Minnesota Starvation Experiment). Static formulas cannot capture this. `[zolthealth.com__learn-what-is-adaptive-tdee.txt]`
- Self-reported activity level is unreliable (people over- or under-estimate). `[zolthealth.com__learn-what-is-adaptive-tdee.txt]` `[gymcreek.com__adaptive-tdee-calculator.txt]`
- Mifflin-St Jeor does **not** account for muscle mass — underestimates BMR for very muscular, overestimates for overweight/obese. `[gymgeek.com__calculators-maintenance-calories-calculator.txt]` `[gymgeek.com__calculators-calorie-calculator.txt]`

**What adaptive TDEE solves:**
- Captures metabolic adaptation as it happens (TDEE falls during a cut). `[zolthealth.com__learn-what-is-adaptive-tdee.txt]`
- Captures increased burn when activity increases. `[zolthealth.com__learn-what-is-adaptive-tdee.txt]`
- Filters out daily weight noise (water, sodium, digestion) to find the true trend. `[zolthealth.com__learn-what-is-adaptive-tdee.txt]`
- Detects outliers (forgotten/incomplete logs, fasts). `[zolthealth.com__learn-what-is-adaptive-tdee.txt]`

**Two algorithm families** `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]`:
1. **First-principles** — uses only intake + weight change; needs months of data to be reliable. Examples: nSuns spreadsheet, Reddit spreadsheets. `[zolthealth.com__learn-what-is-adaptive-tdee.txt]` `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]`
2. **Statistical model** — Bayesian/weighted blend of Mifflin-St Jeor prior with personal intake/weight data; gives an estimate from day 1 and converges over time. Used by Gym Geek app and Zolt. `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]` `[zolthealth.com__learn-what-is-adaptive-tdee.txt]`

**Reference constants cited across sources:**
- 1 lb body fat ≈ **3,500 kcal** `[gymgeek.com__calculators-calorie-calculator.txt]` `[zolthealth.com__learn-what-is-adaptive-tdee.txt]` `[gymcreek.com__adaptive-tdee-calculator.txt]`
- Implied 1 kg body fat ≈ **7,700 kcal** (derived from 3500 / 0.4536 ≈ 7716).
- Thermic effect of food ≈ **10 %** of daily burn `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]`
- Adding 1 lb of muscle raises TDEE by ~**10–12 kcal/day** `[gymcreek.com__adaptive-tdee-calculator.txt]`
- 500 kcal/day deficit → ~1 lb/week loss; 1000 kcal/day → ~2 lb/week. `[gymgeek.com__calculators-calorie-calculator.txt]` `[zolthealth.com__learn-what-is-adaptive-tdee.txt]` `[gymcreek.com__adaptive-tdee-calculator.txt]`

---

## 2. Adaptive TDEE Formula(s)

> **None of the nine source files publish the *exact* closed-form equation.** All four adaptive-TDEE sources describe the algorithm *conceptually* and rely on client-side JS / server-side APIs. The formula below is the **implicit first-principles identity** that is consistent with every claim made across the four sources. It is the standard nSuns/Reddit formulation explicitly named in `[zolthealth.com__learn-what-is-adaptive-tdee.txt]`.

### 2a. First-principles observed-TDEE identity

For a window of `N` days with daily intake `intake_i` and weight measurements at start (`W_start`) and end (`W_end`):

```
avg_intake      = (1/N) · Σ intake_i                   [kcal/day]
Δweight         = W_end − W_start                       [kg  or  lb]

# Imperial (lb)
observed_TDEE   = avg_intake − (Δweight_lb  × 3500) / N     [kcal/day]

# Metric (kg)
observed_TDEE   = avg_intake − (Δweight_kg  × 7700) / N     [kcal/day]
```

**Interpretation consistent with every source:**
- If weight is stable (Δweight = 0) → `observed_TDEE = avg_intake`. ("If you eat a certain number of calories consistently and your weight stays stable, that's your TDEE.") `[zolthealth.com__learn-what-is-adaptive-tdee.txt]`
- If weight drops faster than expected → observed TDEE > prior estimate → raise TDEE. `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]` `[zolthealth.com__learn-what-is-adaptive-tdee.txt]`
- If weight doesn't drop → observed TDEE < prior estimate → lower TDEE. `[zolthealth.com__learn-what-is-adaptive-tdee.txt]`

### 2b. Statistical-model adaptive TDEE (Gym Geek / Zolt style)

Not given as a closed formula, but the **mechanism** is fully specified `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]` `[zolthealth.com__learn-what-is-adaptive-tdee.txt]`:

```
prior_TDEE      = MifflinStJeor_BMR × SAF       # day-0 estimate
# blend:
adaptive_TDEE_t = w_data(t) · observed_TDEE_t + (1 − w_data(t)) · prior_TDEE
# where w_data(t) increases with sample size (Bayesian shrinkage / EWMA-like).
```

Behavior described:
- `w_data` ≈ 0 with 1 week of data → output ≈ Mifflin-St Jeor prior. `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]`
- After **1–2 months**, `w_data` ≈ 1 → output ≈ user's own observed TDEE. `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]`
- Zolt adds outlier detection, intelligent smoothing, rolling recalculation, and data-quality indicators. `[zolthealth.com__learn-what-is-adaptive-tdee.txt]`

### 2c. Inputs required

| Input | Source files |
|---|---|
| Daily calorie intake (`intake_i`) | all four |
| Daily (or ≥ weekly) body weight (`W_i`) | all four |
| Height, age, gender, activity level (for prior) | `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]` `[gymcreek.com__adaptive-tdee-calculator.txt]` |
| Optional body-fat % → switches BMR prior to Katch-McArdle | `[gymcreek.com__adaptive-tdee-calculator.txt]` |

### 2d. Smoothing / windowing

| Method | Window / rule | Source |
|---|---|---|
| 7-day rolling average weight (recommended for daily-weigh users) | 7 days | `[gymcreek.com__adaptive-tdee-calculator.txt]` |
| Spreadsheet method reaches accuracy | ~4 weeks of entries | `[gymcreek.com__adaptive-tdee-calculator.txt]` |
| Some apps deliver an adaptive value | ~10 entries | `[gymcreek.com__adaptive-tdee-calculator.txt]` |
| First-principles accuracy | "at least a few months of data" | `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]` |
| Statistical model produces an estimate | day 1 / 1 week of data | `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]` |
| Statistical model: user data dominates prior | after 1–2 months | `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]` |
| Re-evaluate TDEE periodically | every 4–6 weeks | `[gymcreek.com__adaptive-tdee-calculator.txt]` |
| Review progress and adjust calories | after 3–4 weeks | `[gymgeek.com__calculators-calorie-calculator.txt]` |
| Minimum useful data — "a week or two isn't enough" | > 2 weeks | `[zolthealth.com__learn-what-is-adaptive-tdee.txt]` |

---

## 3. Cutting Calculator Math

Source: `[macrofactor.com__cutting-calculator.txt]`

### 3a. Default recommended rate of weight loss

| Tier | % body weight / week | Relative energy deficit |
|---|---|---|
| Very Conservative | 0.10 % | < 5 % |
| Conservative | 0.25 % | 5–10 % |
| Moderate | 0.5–0.75 % | 10–20 % |
| Slightly Aggressive | 1.00 % | 20–30 % |
| Aggressive | 1.50 % | > 30 % |

**Default target range:** 0.25–1.0 % body weight/week, ≈ 0.5–1.5 lb (0.25–0.75 kg) per week.
**Wider permissible range:** 0.1–1.5 % body weight/week.
**Hard upper limit:** **2 lb / 1 kg per week**, regardless of bodyweight.
**Daily energy deficits above 1000 kcal/day** become unsustainable/unpleasant for most people.

### 3b. Converting weekly rate → daily calorie deficit

Using the 3500 kcal/lb rule (cited explicitly in `[gymgeek.com__calculators-calorie-calculator.txt]`, `[zolthealth.com__learn-what-is-adaptive-tdee.txt]`, `[gymcreek.com__adaptive-tdee-calculator.txt]`):

```
# Imperial
daily_deficit_kcal = weekly_rate_lb × 3500 / 7
                   = weekly_rate_lb × 500

# Metric
daily_deficit_kcal = weekly_rate_kg × 7700 / 7
                   = weekly_rate_kg × 1100

# Bodyweight-percent form
daily_deficit_kcal = (pct/100) × bodyweight_lb × 3500 / 7
                   = (pct/100) × bodyweight_lb × 500        # per week
                   divided by 7 → daily
```

### 3c. Muscle-retention threshold

- **Murphy & Koehler 2021 meta-analysis:** deficits **< ~500 kcal/day** (≈ 1 lb / 0.5 kg per week loss) → body recomposition is possible (lose fat, gain a little muscle).
- Deficits **> 500 kcal/day** → lean mass loss begins; rate of lean loss increases with deficit size.
- Recommended optimal rate (fat loss + FFM retention): **0.6–0.7 % BW/week** ≈ 1 lb / 0.5 kg per week.

### 3d. Non-linear scaling warning (bodyweight)

The same percentage yields very different relative deficits at different bodyweights `[macrofactor.com__cutting-calculator.txt]`:

| Bodyweight | TDEE (norm) | 1 %/week loss | Daily deficit | Relative deficit |
|---|---|---|---|---|
| 150 lb (~68 kg) | ~2400 kcal/day | 1.5 lb/week | 750 kcal/day | ~31 % |
| 300 lb (~136 kg) | ~3600 kcal/day | 3.0 lb/week | 1500 kcal/day | ~42 % |

→ do not scale percentages of body weight indefinitely; cap at 2 lb / 1 kg per week absolute.

### 3e. Stop / adjustment conditions

- Review progress after 3–4 weeks, then adjust intake. `[gymgeek.com__calculators-calorie-calculator.txt]`
- Re-evaluate TDEE every 4–6 weeks. `[gymcreek.com__adaptive-tdee-calculator.txt]`
- Stop or ease if performance drops, hunger/mood intolerable, or deficit exceeds 1000 kcal/day / > 40 % relative.
- Hard floor on intake (women: 1200 kcal/day, men: 1500 kcal/day); VLCD < 1200 / < 800 only under medical supervision. `[gymgeek.com__calculators-calorie-calculator.txt]` `[gymgeek.com__calculators-maintenance-calories-calculator.txt]`

### 3f. GymCreek fixed-step cut table

`[gymcreek.com__adaptive-tdee-calculator.txt]` provides a discrete cut ladder (used as goal presets):

| Goal | Daily adjustment | Weekly change | Expected result |
|---|---|---|---|
| Aggressive Cut | −750 kcal/day | −5,250 kcal/week | ~1.5 lb fat loss/week |
| Standard Cut | −500 kcal/day | −3,500 kcal/week | ~1 lb fat loss/week |
| Mild Cut | −250 kcal/day | −1,750 kcal/week | ~0.5 lb fat loss/week |

---

## 4. Bulking Calculator Math

### 4a. MacroFactor bulking tables `[macrofactor.com__bulking-calculator.txt]`

**Training-age definitions:**
- **Beginner:** strength ≥ +2 %/week; typically < 3–6 months serious training.
- **Intermediate:** strength ~ +1 %/week; typically < 1 year serious training.
- **Experienced:** strength gains < 1 %/week; typically ≥ 1–2 years serious training.

**Recommended rate of weight gain (% body weight / week):**

| Tier | Beginner | Intermediate | Experienced |
|---|---|---|---|
| Conservative | 0.20 % | 0.15 % | 0.10 % |
| Happy Medium | 0.50 % | 0.325 % | 0.15 % |
| Aggressive | 0.80 % | 0.575 % | 0.35 % |
| Very Aggressive | 1.00 % | 0.80 % | 0.60 % |

**Absolute caps (kg / week):**

| Tier | Beginner | Intermediate | Experienced |
|---|---|---|---|
| Conservative | 0.16 | 0.12 | 0.08 |
| Happy Medium | 0.40 | 0.26 | 0.12 |
| Aggressive | 0.64 | 0.46 | 0.28 |
| Very Aggressive | 0.80 | 0.64 | 0.48 |

**Absolute caps (lb / week):**

| Tier | Beginner | Intermediate | Experienced |
|---|---|---|---|
| Conservative | 0.33 | 0.26 | 0.18 |
| Happy Medium | 0.88 | 0.57 | 0.26 |
| Aggressive | 1.41 | 1.01 | 0.62 |
| Very Aggressive | 1.76 | 1.41 | 1.06 |

→ Apply `min(percent_based_rate, absolute_cap)` because bodyweight-percent scaling doesn't extrapolate to very heavy or very light individuals.

**Composition outcomes cited (regression evidence):**
- Beginner/untrained @ up to ~0.5 % BW/week: large FFM gain, little-to-no fat gain (Rozenek; Smith recomp threshold < ~0.55 %/week). `[macrofactor.com__bulking-calculator.txt]`
- Intermediate/experienced: faster gain → mostly fat gain, small FFM gain (Helms, Garthe, Sanchez studies).
- 0.16 %/week → ~85 % FFM / 15 % fat.
- 0.38 %/week → ~65 % FFM / 35 % fat.

### 4b. GymGeek bulking calculator `[gymgeek.com__calculators-bulking-calculator.txt]`

**Surplus ladder** (4 outputs, 0.5 / 1.0 / 1.5 / 2.0 lb per week):
- Typical bulk target: **0.5–1 lb/week** (2 lb/week → mostly fat gain, even with resistance training).
- Conversion: 1 lb/week = **+500 kcal/day** surplus; 2 lb/week = **+1000 kcal/day** surplus (implied by 3500 kcal/lb rule).

**Protein rules:**
- Tailored ratio: **1.6 g/kg BW/day** if training; **1.2 g/kg BW/day** if sedentary.
- High-protein ratio: **1.8 g/kg BW/day** if training; **1.6 g/kg BW/day** if sedentary.
- Protein capped at **35 % of total calories** to avoid overconsumption.
- General bulking protein band: **1.2–1.6 g/kg/day** (sufficient); hard-training up to **1.6–1.8 g/kg/day**.

**Fat rules:**
- Default: **30 % of calories**.
- Reduced as needed to keep carbs ≥ 45 % (Tailored) or ≥ 40 % (High-Protein).
- Absolute floor: **0.5 g/kg BW/day** (essential fatty acid minimum).
- General recommended fat range: 20–35 % of calories.

**Carb rules:**
- Receive the remainder of calories after protein + fat.
- General recommended range: **45–65 % of calories**.

**Macro energy densities:** Carbs 4 kcal/g · Protein 4 kcal/g · Fat 9 kcal/g. `[gymgeek.com__calculators-bulking-calculator.txt]`

**Preset macro ratios offered:**

| Preset | Carbs | Fat | Protein |
|---|---|---|---|
| Tailored (recommended, output sample) | 51 % | 30 % | 19 % |
| Standard | 50 % | 30 % | 20 % |
| Low Carb | 40 % | 30 % | 30 % |
| High Protein | 44 % | 30 % | 26 % |

### 4c. GymCreek bulk ladder `[gymcreek.com__adaptive-tdee-calculator.txt]`

| Goal | Daily adjustment | Weekly change | Expected result |
|---|---|---|---|
| Lean Bulk | +250 kcal/day | +1,750 kcal/week | ~0.25–0.5 lb gain/week |
| Standard Bulk | +500 kcal/day | +3,500 kcal/week | ~0.5–1 lb gain/week |
| Maintain / Recomp | ±0 kcal/day | 0 | weight stable |

### 4d. Stop / adjustment conditions

- If rate of strength gain slows → reduce target rate of weight gain. `[macrofactor.com__bulking-calculator.txt]`
- If gaining fat faster than desired → reduce target rate rather than plan to cut sooner.
- Prefer Conservative-to-Happy-Medium rates to extend bulking duration before cut needed.
- Re-evaluate TDEE every 4–6 weeks. `[gymcreek.com__adaptive-tdee-calculator.txt]`

---

## 5. Bulk-or-Cut Decision Matrix

Source: `[macrofactor.com__bulk-or-cut.txt]`

### 5a. Default recommendation

> "Go with whichever option excites you more."
> If unsure → **maintenance** (enables body recomp) or **bulk** (because muscle growth is the long pole).

### 5b. Body-fat health thresholds (criteria to prefer cutting)

| Threshold type | Men | Women |
|---|---|---|
| Health risk begins above | **25 % BF** | **35 % BF** |
| "Better safe than sorry" cutoff | **20 % BF** | **30 % BF** |
| Tolerable upper limit | **30 % BF** | **40 % BF** |

> "Men might want to consider cutting if they're above 25 % body fat, and women might want to consider cutting if they're above 35 % body fat." `[macrofactor.com__bulk-or-cut.txt]`

### 5c. Body-fat category reference (GymCreek) `[gymcreek.com__adaptive-tdee-calculator.txt]`

| Category | Male BF % | Female BF % | BMR impact |
|---|---|---|---|
| Essential Fat | 2–5 % | 10–13 % | Very high metabolic rate |
| Athletic | 6–13 % | 14–20 % | High lean mass, higher BMR |
| Fitness | 14–17 % | 21–24 % | Average–high BMR |
| Average | 18–24 % | 25–31 % | Average BMR |
| Obese | 25 %+ | 32 %+ | Relatively lower BMR per lb |

### 5d. Reasons to cut

1. **Health** — BF% above thresholds (5b).
2. **Aesthetics** — personal preference for leanness; explicitly endorsed as a valid reason.
3. **Competition** — sports where power-to-weight matters, weight classes, endurance economy, physique sports.
4. **Burned out from bulking** — psychological break, especially for naturally skinny / high-TDEE people.

### 5e. Reasons *not* to cut (debunked)

- "You build muscle better when you're leaner" → **debunked** by MacroFactor subject-level meta-regression (no relationship between baseline BF% and FFM gains from resistance training) and Hall (2007) re-analysis removing anorexia weight-regain data from Forbes (2000).

### 5f. Long-term trajectory (muscle vs. fat time-cost)

- Drug-free male lifters add ~**20–30 lb total FFM** over lifetime (women: ~12–20 lb).
- Largest chunk occurs in year 1; rest accrues gradually over 5–10+ years.
- Losing 20 lb of fat takes "a few months."
- → Spend most of time in **neutral-to-positive energy balance** (maintain or bulk).

---

## 6. Maintenance Calories Calculator

Source: `[gymgeek.com__calculators-maintenance-calories-calculator.txt]` and `[gymgeek.com__calculators-calorie-calculator.txt]`

### 6a. BMR formula used — **Mifflin-St Jeor (1990)**

```
# Weight in kg, Height in cm, Age in years
BMR_male   = 9.99 × Weight + 6.25 × Height − 4.92 × Age +  5
BMR_female = 9.99 × Weight + 6.25 × Height − 4.92 × Age − 161

# Simplified rounding (cited as equivalent):
BMR_male   = 10 × Weight + 6.25 × Height − 5 × Age +  5
BMR_female = 10 × Weight + 6.25 × Height − 5 × Age − 161
```

Origin: Mifflin et al. (1990), n = 498 healthy individuals, both sexes, all adult ages, normal-weight & obese. Frankenfield (2005) systematic review found it estimates within 10 % more often than other equations. `[gymgeek.com__calculators-maintenance-calories-calculator.txt]` `[gymgeek.com__calculators-calorie-calculator.txt]`

### 6b. TDEE formula

```
TDEE = BMR × SAF        # SAF = Standard Activity Factor (Harris-Benedict)
Maintenance calories == TDEE
```

### 6c. Unit conversions

- 1 kcal = **4.184 kJ** `[gymgeek.com__calculators-calorie-calculator.txt]`
- 1 lb = 0.4536 kg (implied by 3500/7700 ratio).
- 1 inch = 2.54 cm.
- Weight input accepted in kg, lb, or stone+pounds.
- Height input accepted in cm or ft+in.

### 6d. Validation bounds / exclusions

- Age: **18+ only** (under-18 not appropriate for BMR/TDEE estimates).
- Population: healthy adults (project scope: 18–65).
- Not for: pregnancy, eating disorders, pre-existing medical conditions.
- Calculator hard floor on displayed output: **1,200 kcal/day for women, 1,500 kcal/day for men.** `[gymgeek.com__calculators-maintenance-calories-calculator.txt]` `[gymgeek.com__calculators-calorie-calculator.txt]`
- VLCD: < 1200 kcal/day; Very-Low: < 800 kcal/day → medical supervision only. `[gymgeek.com__calculators-calorie-calculator.txt]`
- Healthy BMI band: **18.5–24.9**. `[gymgeek.com__calculators-bulking-calculator.txt]` `[gymgeek.com__calculators-calorie-calculator.txt]`

### 6e. General-population defaults cited

- Average healthy-weight woman: ~2,000 kcal/day.
- Average healthy-weight man: ~2,500 kcal/day.
- Typical man burns 2,000–2,500 kcal/day; typical woman 1,600–2,000 kcal/day. `[gymgeek.com__calculators-maintenance-calories-calculator.txt]` `[gymgeek.com__calculators-calorie-calculator.txt]`

### 6f. Maintenance + weight-goal ladder (GymGeek calorie calculator)

Outputs 4 deficits/surpluses at 0.5 / 1.0 / 1.5 / 2.0 lb per week:

| Weekly Δ | Daily Δ (kcal) |
|---|---|
| 0.5 lb/week | ±250 |
| 1.0 lb/week | ±500 |
| 1.5 lb/week | ±750 |
| 2.0 lb/week | ±1000 |

Review progress after **3–4 weeks**, then adjust.

---

## 7. Activity Factor Definitions (Harris-Benedict SAF / PAL)

Sources: `[gymgeek.com__calculators-maintenance-calories-calculator.txt]`, `[gymgeek.com__calculators-calorie-calculator.txt]`, `[gymgeek.com__calculators-bulking-calculator.txt]`, `[gymcreek.com__adaptive-tdee-calculator.txt]`.

| Level | SAF | GymGeek name | GymCreek name | Definition | Typical male TDEE | Typical female TDEE |
|---|---|---|---|---|---|---|
| 1 | **1.200** | Sedentary | Sedentary | Little to no exercise; desk-based job; spare time indoors | 1,900–2,200 | 1,500–1,800 |
| 2 | **1.375** | Light Activity | Lightly Active | Light exercise/sports 1–3 days/week; on-feet job | 2,200–2,600 | 1,700–2,100 |
| 3 | **1.550** | Moderate Activity | Moderately Active | Moderate exercise/sports 3–5 days/week (jogging/cycling/swimming ≥ 30 min/day) | 2,500–3,000 | 2,000–2,500 |
| 4 | **1.725** | Very Active | Very Active | Moderate-to-vigorous exercise 6–7 days/week; running or competitive sports | 2,900–3,500 | 2,300–2,900 |
| 5 | **1.900** | Extra Active | Extremely Active | Vigorous training 2×/day OR hard physical-labor job | 3,300–4,000 | 2,600–3,300 |

**Validation note** — GymGeek states "around 1 in 2 users" self-classify as Moderately Active; about "1 in 3 dieters" aim to lose 2 lb/week. `[gymgeek.com__calculators-calorie-calculator.txt]`

---

## 8. Convergence / Smoothing Rules

| Rule | Numeric threshold | Source |
|---|---|---|
| Minimum data for *any* useful adaptive estimate | ~10 entries | `[gymcreek.com__adaptive-tdee-calculator.txt]` |
| Minimum data for spreadsheet (first-principles) accuracy | ~4 weeks | `[gymcreek.com__adaptive-tdee-calculator.txt]` |
| Minimum data for *reliable* first-principles estimate | "at least a few months" | `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]` |
| Statistical model: produces initial estimate from | 1 week of data | `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]` |
| Statistical model: declared activity level dominates for | first 1–2 months | `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]` |
| Statistical model: own data dominates prior after | 1–2 months | `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]` |
| Periodic TDEE re-evaluation cadence | every 4–6 weeks | `[gymcreek.com__adaptive-tdee-calculator.txt]` |
| Calorie-target review cadence (any plan) | after 3–4 weeks | `[gymgeek.com__calculators-calorie-calculator.txt]` |
| Daily weight smoothing | 7-day rolling average | `[gymcreek.com__adaptive-tdee-calculator.txt]` |
| "A week or two of data isn't enough" | > 2 weeks required | `[zolthealth.com__learn-what-is-adaptive-tdee.txt]` |
| Expected metabolic-adaptation drop during prolonged deficit | 15–25 % reduction in TDEE | `[zolthealth.com__learn-what-is-adaptive-tdee.txt]` |
| Inter-individual variation (same profile) | ±200–400 kcal/day | `[zolthealth.com__learn-what-is-adaptive-tdee.txt]` |
| Thermic effect of food | ~10 % of daily burn | `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]` |
| Muscle mass effect on TDEE | +10–12 kcal/day per lb muscle added | `[gymcreek.com__adaptive-tdee-calculator.txt]` |

**Smoothing algorithm features specified** `[zolthealth.com__learn-what-is-adaptive-tdee.txt]`:
- **Outlier detection** — flags forgotten/incomplete/unusual-logging days (e.g., fasting).
- **Intelligent smoothing** — reduces day-to-day noise while preserving real trend signal.
- **Rolling recalculation** — TDEE continuously recomputed from recent window.
- **Data-quality indicators** — confidence flag; holds prior value when recent data insufficient.
- **Multiple methods** — adaptive (weight+food), wearable (BMR + measured activity), formula-only.

---

## 9. Source Citations (file-by-file index)

| File | Primary contribution |
|---|---|
| `[macrofactor.com__cutting-calculator.txt]` | Cutting-rate tiers, 500 kcal/day muscle-preservation threshold, 2 lb / 1 kg hard cap, bodyweight-scaling warning, Murphy & Koehler 2021. |
| `[macrofactor.com__bulk-or-cut.txt]` | Default decision rule, BF% health thresholds (M 25 % / F 35 %, conservative 20/30, tolerant 30/40), Forbes debunk, lifetime FFM gain ranges. |
| `[macrofactor.com__bulking-calculator.txt]` | Bulking rate table (% BW/week by training age × tier), absolute kg/lb caps, training-age definitions (Beginner/Intermediate/Experienced), composition-outcome citations (Rozenek, Smith, Helms, Sanchez, Garthe). |
| `[gymgeek.com__calculators-maintenance-calories-calculator.txt]` | Mifflin-St Jeor formula (full + simplified), SAF 1.2–1.9 table with definitions, kcal/kJ conversion, 1200/1500 kcal floors, 18+ age limit. |
| `[gymgeek.com__calculators-calorie-calculator.txt]` | 3500 kcal/lb rule, ±250/500/750/1000 kcal ladder for 0.5–2 lb/week, 3–4 week review cadence, VLCD definition, 4.184 kJ/kcal, metabolic-adaptation context, hidden-calorie guidance. |
| `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]` | Two adaptive-TDEE algorithm families (first-principles vs statistical model), convergence behavior (1 week → estimate, 1–2 months → data-dominant), thermic-effect 10 %, prior blend with Mifflin-St Jeor. |
| `[gymgeek.com__calculators-bulking-calculator.txt]` | Bulking protein/fat/carb rules (1.6/1.2 g/kg protein, 30 % fat default, 0.5 g/kg fat floor, 45–65 % carb, 35 % protein cap), macro energy densities (4/9/4), preset ratios (50/30/20, 40/30/30, 44/30/26, 51/30/19). |
| `[gymcreek.com__adaptive-tdee-calculator.txt]` | Activity-multiplier reference table with TDEE ranges per sex, body-fat category table, cut/bulk calorie-adjustment ladder (±250/500/750), macro-split presets (Balanced/High-Protein/Low-Carb/Keto/High-Carb), 7-day average weight, 4–6 week re-evaluation, 4-week spreadsheet convergence, ~10-entry app convergence, +10–12 kcal/lb muscle TDEE boost. |
| `[zolthealth.com__learn-what-is-adaptive-tdee.txt]` | Conceptual foundation, 200–400 kcal inter-individual variation, 15–25 % metabolic adaptation, nSuns spreadsheet reference, outlier detection / intelligent smoothing / rolling recalculation / data-quality indicators / multiple-methods architecture, ≥2 weeks minimum, Martins et al. 2020 citation. |

---

## 10. Codification Notes (for the Python engine)

The following constants / functions should be encoded as pure functions in `fitness_engine/nutrition/`:

1. **`BMR_MIFFLIN(weight_kg, height_cm, age_yrs, sex)`** → kcal/day (use full 9.99/6.25/4.92 form).
2. **`BMR_KATCH_MCARDLE(lbm_kg)`** → `370 + 21.6 × LBM` (referenced in `[gymcreek.com__adaptive-tdee-calculator.txt]` as the BF%-aware alternative).
3. **`TDEE_STATIC(bmr, saf)`** → `bmr × saf`.
4. **`SAF_TABLE`** — dict of 5 levels → multipliers (1.2, 1.375, 1.55, 1.725, 1.9) with definitions.
5. **`OBSERVED_TDEE(avg_intake, delta_weight, days, unit)`** → first-principles identity from §2a (3500 kcal/lb or 7700 kcal/kg).
6. **`ADAPTIVE_TDEE(prior, observed, w_data)`** → `w_data × observed + (1 − w_data) × prior`; `w_data` should grow monotonically with `n_days` and data-quality score.
7. **`W_DATA_SCHEDULE(n_days, quality_score)`** — empirically: ≈ 0 for n ≤ 7; ≈ 0.5 by n ≈ 30; ≈ 1.0 by n ≥ 60 (per `[gymgeek.com__calculators-adaptive-tdee-calculator.txt]` 1–2 month window).
8. **`WEEKLY_RATE_TO_DAILY_KCAL(weekly_lb_or_kg)`** → × 500 (lb) or × 1100 (kg).
9. **`PCT_TO_DAILY_KCAL(pct, bodyweight, unit)`** → `(pct/100) × bodyweight × 500` (lb) or `× 1100` (kg); apply absolute cap of 2 lb or 1 kg/week.
10. **`CUT_TIER_TABLE`** / **`BULK_TIER_TABLE`** — literal dicts from §3a and §4a (3 × 4 / 5 × 4 tables).
11. **`BULK_CAPS_KG`** / **`BULK_CAPS_LB`** — apply `min(pct_rate, cap)` from §4a.
12. **`BULK_OR_CUT_DECISION(bf_pct, sex)`** — returns `cut` if `bf_pct > 25 (M) / 35 (F)`, `cut_conservative` if `> 20 (M) / 30 (F)`, `cut_tolerant` if `> 30 (M) / 40 (F)`, else `bulk_or_maintain`.
13. **`MIN_CAL_FLOOR(sex)`** → 1200 (F) / 1500 (M).
14. **`CAL_PER_GRAM`** → `{carb:4, protein:4, fat:9}`.
15. **`KJ_PER_KCAL = 4.184`**.
16. **`LB_PER_KG = 0.453592`**; **`CM_PER_IN = 2.54`**.

All formulas are unit-testable pure functions; no I/O required.

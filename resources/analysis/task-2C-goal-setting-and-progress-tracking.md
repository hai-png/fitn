# Task 2-C — Goal Setting, Progress Tracking, Plateaus, Bulking, Reverse Diet, Recomp, Fat Loss Limits

**Agent**: cluster-C-analyzer
**Sources analyzed**: 13 files in `/home/z/my-project/resources/synthesized/`
**Purpose**: Codify every formula, threshold, decision rule, and methodology into a Python fitness engine.

> Convention: each claim is prefixed with its source filename in brackets `[file]` for traceability. All formulas are presented in a Python-friendly way.

---

## 1. Goal Setting Framework

### 1.1 Trainee Categorization (RippedBody 9-category system)

`[rippedbody.com__goal-setting-1.txt]` `[rippedbody.com__goal-setting-2.txt]` `[rippedbody.com__goal-setting-3.txt]`

The RippedBody framework classifies trainees into 9 categories to set realistic goals and time horizons:

| # | Category | Body fat range | Strategy |
|---|----------|---------------|----------|
| 1 | Stubborn (mental attitude) | n/a | Mindset shift required |
| 2 | Fat but muscled | ~20–30% | Cut |
| 3 | Muscled, a few pounds to lose | 7–15% | Cut (slower as leaner) |
| 4 | Skinny (low muscle, low fat) | <10% | Bulk |
| 5 | Shredded (defined abs) | 7–11% | Maintenance or slow-bulk |
| 6 | Fat & Weak | 23–30% | Cut while gaining strength (recomp-style) |
| 7 | Obese | >30% BF | Change habits; cut; ≤2 lb/week cap |
| 8 | Skinny-fat | 12–23% | Recomp (slight deficit) |
| 9 | Limbo / Purgatory | 12–18% | Decide cut OR bulk; commit |

`[rippedbody.com__goal-setting-1.txt]` defines leanness labels:
- **Shredded** = ~7–8% BF (men) with decent muscle
- **Stage-shredded** = 5–8% BF (naturals)
- **Ripped** = 9–11% BF
- "Decent enough muscle" = not "skinny" at the beach (>90% of observers)

### 1.2 Goal Categories (priority / eligible populations)

`[rippedbody.com__goal-setting-1.txt]` `[rippedbody.com__goal-setting-2.txt]` `[rippedbody.com__goal-setting-3.txt]` `[fatcalc.com__body-recomp-calculator.txt]`

Five goal categories:
1. **Fat loss / Cut** — primary goal when BF% > target and trainee has muscular base (or for obese/fat-and-weak)
2. **Muscle gain / Bulk** — primary goal when skinny, or shredded & wanting more muscle
3. **Recomp** — simultaneous fat loss + muscle gain; eligible for: beginners, higher BF%, those not at genetic ceiling
4. **Maintenance** — when at target physique
5. **Reverse diet** — transition phase after a cut, before bulk or maintenance

### 1.3 Cut/Bulk Cycle Boundaries

`[rippedbody.com__how-to-bulk.txt]` lines 190–209:
- Anabolic signaling drops off **under ~10% BF** and **after ~20% BF**.
- **Cut–bulk cycles should stay within ~10–20% BF** (men).
- **Don't bulk past 20% BF** (health risks + partitioning decline).
- **Don't cut beyond 10% BF if intending to bulk immediately** (hormonal function suppressed).
- Therefore only **start a bulk if currently <15% BF** (otherwise no uninterrupted bulk time before needing to cut again).
- Purgatory cycle recommendation: stay within **9–15% BF** boundary `[rippedbody.com__goal-setting-3.txt]` line 177.

### 1.4 Muscle Growth Potential (rate by training status)

`[rippedbody.com__goal-setting-2.txt]` lines 32–38 & 160–166:

**Table A — Beginner/Intermediate (Pt. 2)**:
| Training Status | Gains/month (muscle) | Energy Surplus/day |
|---|---|---|
| Beginner | 2–3 lbs (~1–1.4 kg) | ~200–300 kcal |
| Intermediate | 1–2 lbs (~0.5–1 kg) | ~100–200 kcal |
| Advanced | 0.5 lbs (~0.25 kg) | slight surplus |

`[rippedbody.com__how-to-bulk.txt]` lines 237–247 (more granular, % of body weight):
| Training Status | Muscle growth potential (% BW/month) |
|---|---|
| Beginner | 1.0–1.5% BW/month |
| Novice | 0.75–1.25% BW/month |
| Intermediate | 0.5–0.75% BW/month |
| Advanced | <0.5% BW/month |

`[rippedbody.com__goal-setting-2.txt]` line 30: A beginner can expect **15–25 lbs of muscle over the first year** (2–3 lb/mo for 3–6 mo, then 1–2 lb/mo for following 6–9 mo).

`[fatcalc.com__body-recomp-calculator.txt]` lines 30–36 (McDonald's model):
**Men — Expected Monthly Muscle Gain**:
- Beginner (Year 1): 0.7–1.0 kg/month
- Intermediate (Years 2–3): 0.45–0.7 kg/month
- Advanced (Years 4–7): 0.2–0.45 kg/month
- Elite (7+ years): <0.2 kg/month

**Women**: ~50% of men's rates.

### 1.5 Time-Horizon Estimation Formulas

`[fatcalc.com__rwl.txt]` lines 32–48 — **Replaces the 3500-kcal rule**:
- The 3500-kcal rule (500 kcal/day deficit → 1 lb/week loss) "grossly overestimates" actual weight loss.
- Use **Kevin Hall's mathematical model** (Lancet 2011) which factors in: body fat vs lean mass changes, glycogen, sodium, extracellular fluid, TEF.
- Example given: 37-yo 6-ft 265-lb sedentary male, 1600 kcal/day (1000 kcal deficit):
  - 3500-kcal rule predicts 2 lb/week → 43 weeks for 85-lb loss.
  - Hall model: ~70 weeks for same loss (nonlinear plateau).
- Calorie floors: **Women ≥ 1200 kcal/day, Men ≥ 1500 kcal/day** `[fatcalc.com__rwl.txt]` line 55.

### 1.6 Priority Order for Goal Selection

`[rippedbody.com__goal-setting-1.txt]` `[rippedbody.com__how-to-bulk.txt]` lines 81–99 — factors in descending order of importance:
1. Genetics (and drug use) — not controllable
2. Calorie intake
3. Training stimulus
4. Sufficient protein intake
5. Sleep & stress
6. (Carb/fat ratio, micros, timing, supplements — minor)

`[rippedbody.com__goal-setting-1.txt]` lines 50–66 — fundamentals:
- Fat can be burned far quicker than muscle is gained.
- Muscle is denser than fat → measure smaller at same weight with more muscle.
- The more fat you have to lose, the quicker you can lose it without losing muscle.
- People new to strength training experience the most lean-mass gains.
- Strength gains/losses correlate with muscle gains/losses (maintenance of strength = muscle retention).

---

## 2. Body Recomposition Rules

### 2.1 Eligibility Criteria

`[fatcalc.com__body-recomp-calculator.txt]` lines 22–65:

**Training Status**: Beginners get "newbie gains" — significant muscle mass even in caloric deficit (Ribeiro 2019). Diminishing returns as experience increases.

**Body Fat % — Recomp Potential** (men):
| BF% | Recomp Potential |
|---|---|
| >25% | Excellent |
| 15–25% | Good |
| <15% | Limited |

**Body Fat % — Recomp Potential** (women):
| BF% | Recomp Potential |
|---|---|
| >35% | Excellent |
| 25–35% | Good |
| <25% | Limited |

Rationale (P-ratio, Forbes 2000 / Hall 2007): individuals with higher BF% lose a greater proportion of fat vs muscle during energy restriction → favors recomp.

**Current muscularity (FFMI)**:
- FFMI = Lean Body Mass (kg) ÷ Height (m)²
- Normalized FFMI = FFMI + 6.3 × (1.8 − Height_m)
- The further from genetic potential, the more recomp room.

### 2.2 Calorie Setup for Recomp

`[fatcalc.com__body-recomp-calculator.txt]` lines 84–90:
- **High recomp potential** (beginner + higher BF): moderate deficit **10–20% below maintenance**.
- **Moderate recomp potential**: eat **at or slightly below maintenance (0–10% deficit)**.
- **Limited recomp potential**: traditional bulk/cut cycles are more effective.

### 2.3 Protein Targets for Recomp

`[fatcalc.com__body-recomp-calculator.txt]` lines 92–108:
- Morton et al. (2018): 1.6 g/kg/day maximizes RT-induced gains; up to 2.2 g/kg/day shows no additional benefit.
- Helms et al. (2014): for athletes in caloric restriction: **2.3–3.1 g/kg LBM**.

Protein ranges by goal:
| Goal | Protein Range (g/kg body weight) |
|---|---|
| Lean Bulk | 1.6–2.2 |
| Recomposition | 1.8–2.4 |
| Cut | 2.0–2.7 |

### 2.4 Skinny-Fat Recomp Specifics (RippedBody)

`[rippedbody.com__goal-setting-3.txt]` lines 86–125:
- **Skinny-fat = 12–23% BF** (men), body-weight stable.
- Strategy: chase muscle gain while losing fat via **slight calorie deficit** while pushing hard on lifts.
- Calorie level scales with BF%:
  - Bottom of range (12%): no deficit (maintenance).
  - Top of range (23%): deficit targeting **0.75–1.0 lb/week** loss.
- Set calorie level to **0–1 lb/week weight loss**, scaling across 12–23% BF range.
- Calipers useful only at **≤15% BF** with an experienced user.
- Best progress gauges: strength gains + stomach measurement decreases.
- When recomp stops working → move to Purgatory category → choose cut OR bulk.

### 2.5 Recomp Adjustment & Exit

`[rippedbody.com__initial-adjustment.txt]` lines 540–546 (Andy Morgan Q&A):
- Recomp defined: 1) body weight stable, 2) muscle gained as fat lost.
- **Unless activity changes, calories held constant. Protein held constant.**
- When recomp stops measurably working → choose cut or bulk (no further recomp adjustment).

### 2.6 Expected Recomp Duration / Reassessment

`[fatcalc.com__body-recomp-calculator.txt]` lines 110–120:
- Calculator provides **12-week projection**.
- Assumptions: RT 3–6 days/week, adherence to calorie/protein, sleep 7–9 hours, moderate stress.
- **Reassess every 4–6 weeks**.
- Scale weight stable but measurements/appearance changing = strong recomp indicator.

### 2.7 Training Volume for Recomp

`[fatcalc.com__body-recomp-calculator.txt]` lines 130–132:
- Progressive overload (gradually increase weight/reps/volume).
- Train each muscle group **≥2×/week**.
- Volume: **10–20 hard sets per muscle group per week**.
- Compound movements as foundation.

---

## 3. Bulking Protocol

### 3.1 Three Bulk Methods

`[rippedbody.com__how-to-bulk.txt]` lines 251–346:

| Method | Description | Recommended? |
|---|---|---|
| **Relaxed bulk** | Maximize muscle growth, no macro counting; more fat gain | Acceptable for simplicity |
| **Lean bulk** | Maximize leanness, slow progress, hard to measure | Not recommended (theory only) |
| **Controlled/slow bulk** | Maximize muscle growth while accepting 1:1 fat:muscle ratio | **Recommended** |

### 3.2 Target Rates of Weight Gain (% body weight/month)

`[rippedbody.com__updated-bulking-guidelines.txt]` lines 38–43 — **CURRENT/UPDATED guidelines**:
| Training Status | Rate (% BW/month) | Definition |
|---|---|---|
| Beginner | 2% | New to serious training, first few months |
| Novice | 1.5% | Progresses most loads week-to-week |
| Serious Intermediate | 1% | Progresses most loads month-to-month |
| Advanced | 0.5% | Progress evident only over multiple months/year |

`[rippedbody.com__how-to-bulk.txt]` lines 354–364 — Controlled bulk rates (consistent with above):
| Training Status | Controlled Bulk Rate (% BW/month) |
|---|---|
| Beginner | 2% |
| Novice | 1.5% |
| Intermediate | 1% |
| Advanced | 0.5% |

`[rippedbody.com__how-to-bulk.txt]` lines 282–288 — Relaxed bulk rates (more aggressive):
| Training Status | Relaxed Bulk Rate (% BW/month) |
|---|---|
| Beginner & Novice | ~3% |
| Intermediate | ~2% |
| Advanced | ~1% |

Relaxed bulk calorie intake = **2.0–2.5× maximum muscular gain potential**.

### 3.3 Surplus Size — Daily Calorie Math

`[rippedbody.com__how-to-bulk.txt]` lines 380–390 & `[rippedbody.com__updated-bulking-guidelines.txt]` lines 55–73:

Foundational energy constants:
- **~2500 kcal to synthesize 1 lb of muscle** (~5500 kcal/kg)
- **~3500 kcal to store/burn 1 lb of fat** (~7700 kcal/kg)

With assumed **1:1 fat:muscle gain** and 30-day month:
- 1 lb of tissue gain = (3500/2 + 2500/2) = **3000 kcal surplus/month = 100 kcal/day surplus**.
- Accounting for NEAT increase (+50% buffer):
  - **To gain 1 lb/month → add 150 kcal/day** (or **330 kcal/day per 1 kg/month**).

`[rippedbody.com__goal-setting-2.txt]` lines 32–38 — Muscle Growth Potential table (Beginner surplus ~200–300 kcal/day; Intermediate ~100–200 kcal/day; Advanced = slight surplus).

### 3.4 Surplus Calculation Formula (initial setup)

`[rippedbody.com__how-to-bulk.txt]` lines 406–416:

```python
# Example: 180 lb intermediate finishing a cut, was losing 1.0 lb/week
target_weight_gain_pct = 0.01  # 1% BW/month
current_bodyweight_lb = 180
target_weight_gain_lb = current_bodyweight_lb * target_weight_gain_pct  # 1.8 lb/month
current_daily_deficit_kcal = 500  # (1.0 lb/week * 3500 / 7)

# Initial calorie increase to transition cut → controlled bulk
daily_increase_kcal = current_daily_deficit_kcal + target_weight_gain_lb * 150
# = 500 + 1.8 * 150 = 770 kcal/day increase
```

Or for someone at maintenance:
```python
# Example: 160 lb novice at maintenance
target_weight_gain_lb = 160 * 0.015  # 2.4 lb/month
daily_increase_kcal = target_weight_gain_lb * 150  # 360 kcal/day
```

### 3.5 Macro Adjustment Ratio When Bulking

`[rippedbody.com__how-to-bulk.txt]` lines 422–428 & `[rippedbody.com__initial-adjustment.txt]` lines 165–172:
- **Leave protein unchanged.**
- Increase **carbs : fat in a 3:1 ratio** (calorie basis) for normal increases.
- **Fat intake kept in 20–30% of total calorie range** when bulking (or maintenance).
- For post-cut bulk, first increase may skew slightly more toward fat to replenish depleted fat intake.

Macro split when bulking (approx 75/25 favoring carbs):
- Example: 770 kcal increase = **25 g fat (225 kcal) + 135 g carbs (540 kcal)** ≈ 770 kcal.
- Smaller 150 kcal increase = **25 g carbs + 5 g fat** (100 + 45 = 145 kcal, rounded).

### 3.6 Bulk Duration & End Conditions

`[rippedbody.com__how-to-bulk.txt]` lines 190–209:
- **Cap bulk at 20% BF (men).**
- Start bulk only if <15% BF (to allow uninterrupted bulk time).
- Don't go below 10% BF before bulking (hormonal function suppressed).

`[rippedbody.com__goal-setting-2.txt]` lines 170–174:
- For maximal hypertrophy: set weight gain at **50–100% above** the muscle growth potential table.
- For maximal leanness: increase calories only when training fails to progress (not weight-target-based).
- **Keep BF <15%**; if hit 15%, cut back to abs (10%) then start another slow-bulk cycle.
- 9–15% BF cycle boundary recommended for purgatory escapees `[rippedbody.com__goal-setting-3.txt]` line 177.

### 3.7 Bulk Minimum Duration

`[rippedbody.com__how-to-bulk.txt]` lines 3208 (Andy's Q&A):
- **Minimum bulk duration: 5–6 months** before switching to cutting.
- Between bulk and cut: optionally spend ~2 weeks at maintenance to reduce shock.

### 3.8 Tracking Interval for Bulk Adjustments

`[rippedbody.com__how-to-bulk.txt]` lines 442–484:
- Track scale weight for **5 weeks** before adjusting.
- **Discard week-1 data** (glycogen + water + gut content spike).
- Compute weekly avg from end of week 1 → end of week 5.
- Adjustment formula:
  ```python
  actual_gain_lb = week5_avg - week1_avg
  monthly_target_lb = bodyweight * target_pct
  shortfall_lb = monthly_target_lb - actual_gain_lb  # in 4 weeks
  daily_kcal_change = shortfall_lb * 150  # add if positive, subtract if negative
  ```
- **Do not adjust more frequently than every 5 weeks** — changes when bulking are small relative to scale noise.

### 3.9 Per-Trainee Examples (RippedBody)

`[rippedbody.com__how-to-bulk.txt]` lines 282–296:
- 160 lb novice relaxed bulk → ~5 lb/month (160 × 3%)
- 180 lb intermediate relaxed bulk → ~3.5 lb/month (180 × 2%)

`[rippedbody.com__goal-setting-2.txt]` line 74:
- Skinny beginner weight-gain target ~50% above muscle-growth potential table.
- Tall guys ~4.5 lb/month; shorter guys ~3 lb/month.

---

## 4. Cutting Protocol

### 4.1 Recommended Rate of Weight Loss by BF%

`[rippedbody.com__goal-setting-1.txt]` lines 108–152 — fat-loss ceilings by BF%:

| Body Fat % | Max Recommended Fat Loss / Week |
|---|---|
| 20–30% | ~2 lb / 0.9 kg |
| 15–20% | 1.25–1.5 lb / 0.45–0.7 kg |
| 12–15% | 1–1.25 lb / 0.45–0.6 kg |
| 9–12% | 0.75–1 lb / 0.35–0.45 kg |
| 7–9% | 0.5–0.75 lb / 0.2–0.35 kg |
| <7% | ~0.5 lb / 0.2 kg |

`[rippedbody.com__goal-setting-1.txt]` line 655 (Andy Q&A): The "sweet spot" tends to be **0.5–0.75% of body weight per week**, with **0.5% for those ~12% BF and below**.

`[rippedbody.com__initial-adjustment.txt]` line 112: Recommended rates of weight loss are **typically 0.5–1% per week**; recommended rates of weight gain are **0.5–2% of body weight per month**.

### 4.2 Specific Population Targets

`[rippedbody.com__goal-setting-1.txt]` line 106:
- "Fat but muscled" category: typically **1–1.25 lb/week** of fat loss.
- Higher than that "tends to push the boundaries of what is sustainable in terms of adherence."

`[rippedbody.com__goal-setting-1.txt]` line 142:
- "Muscled, a few pounds to lose": **0.75–1.25 lb/week**, lower end as they get leaner.

`[rippedbody.com__goal-setting-3.txt]` lines 25–51 (Fat & Weak category, 23–30% BF):
- Could lose ~2 lb/week without muscle risk — but **NOT recommended** (hamstrings newbie muscle growth).
- **Target 1.25–1.5 lb/week** of fat loss.
- Expected muscle growth (despite deficit, due to high BF + newbie gains): close to **2–3 lb/month** (slightly less than bulking novice).
- Monthly weight target: **3–5 lb/month net** (fat loss minus muscle gain).
  - Fatter & taller: 8 lb fat loss − 3 lb muscle gain = 5 lb net.
  - Leaner & shorter: 5 lb fat loss − 2 lb muscle gain = 3 lb net.

`[rippedbody.com__goal-setting-3.txt]` lines 53–80 (Obese, >30% BF):
- **Cap at 2 lb/week max** for skin elasticity reasons.
- Scale weight and strength gains are primary barometers.

### 4.3 Maximum Fat Loss Rate (Alpert limit)

`[fatcalc.com__mfl.txt]` lines 24–36 — **THE CORE FORMULA**:

Theoretical max energy transfer rate from fat mass (FM) to fat-free mass (FFM):
- Original Alpert (J Theor Biol 2005): **~31 kcal/lb fat/day**.
- Alpert's corrected value (subsequently unpublished due to his passing): **~22 kcal/lb fat/day**.

**Practical formula**:
```python
max_daily_deficit_kcal = body_fat_lb * 22  # corrected Alpert limit
# OR
max_daily_deficit_kcal = body_fat_lb * 31  # original Alpert (more permissive)

# Example: 200 lb male, 20% BF
body_fat_lb = 200 * 0.20  # 40 lb
max_daily_deficit_kcal = 40 * 22  # = 880 kcal/day

# If TDEE = 2600 kcal/day → optimal cutting intake = 2600 − 880 = 1720 kcal/day
optimal_intake_kcal = tdee - max_daily_deficit_kcal

# Theoretical max weekly fat loss
max_weekly_fat_loss_lb = (max_daily_deficit_kcal * 7) / 3500
# = (880 * 7) / 3500 = 1.76 lb/week
```

**Decision rule**: Consuming fewer than TDEE − max_daily_deficit forces muscle breakdown. Staying within the limit minimizes (but doesn't eliminate) muscle loss.

`[fatcalc.com__rwl.txt]` lines 32–48: 3500-kcal rule "grossly overestimates" actual weight loss — use Hall's model instead.

### 4.4 Daily Calorie Floor

`[fatcalc.com__rwl.txt]` line 55:
- **Women: ≥ 1200 kcal/day**
- **Men: ≥ 1500 kcal/day**

### 4.5 Deficit Size & Calorie Adjustment Formula (when cutting)

`[rippedbody.com__initial-adjustment.txt]` lines 47–54:

**The cutting adjustment formula**:
```python
# We need ~500 kcal daily deficit to lose 1 lb of fat per week
daily_calorie_adjustment = (actual_rate_of_weight_loss_lb_week - target_rate_of_weight_loss_lb_week) * 500
# Positive = losing faster than target → ADD calories
# Negative = losing slower than target → SUBTRACT calories

# Example: target 1 lb/week, actual 0.5 lb/week → adjust by -250 kcal/day
# Example: target 1 lb/week, actual 1.4 lb/week → adjust by +200 kcal/day
```

### 4.6 Macro Adjustment Ratio When Cutting

`[rippedbody.com__initial-adjustment.txt]` lines 61–82:
- Keep protein the same.
- Reduce calories from **carbs : fat in 1:1 to 2:1 ratio** (calorie basis) — slightly more carb reduction.
- Daily macros rounded to **nearest 5 g**.

Reference table (when cutting):
| Calorie Change | Carbs (g) | Fat (g) |
|---|---|---|
| −250 kcal | −30 | −15 |
| −250 kcal (alt) | −40 | −10 |
| +200 kcal | +25 | +10 |
| +200 kcal (alt) | +40 | +5 |

### 4.7 Diet Breaks

`[rippedbody.com__goal-setting-1.txt]` line 156:
- **Diet breaks should be more frequent the leaner you get — every 6–8 weeks or so.**

### 4.8 Cut Duration / End Conditions

`[rippedbody.com__goal-setting-1.txt]` lines 130–152 (Muscular Cut):
- Diet breaks more frequent as leaner (6–8 weeks).
- Body measurements become more important than scale as you approach 10% BF (fat comes off lower back/thighs, not visible).
- For competitors: cut to stage-shredded (5–8% naturals). For general: cut to abs visible (9–12%).

`[rippedbody.com__how-to-bulk.txt]` lines 195–209:
- **Don't cut beyond 10% BF if intending to bulk immediately** (hormonal function off).

---

## 5. Reverse Diet Protocol

### 5.1 Definition & Rationale

`[fatcalc.com__reverse-diet-calculator.txt]` lines 14–37:
- Strategic gradual calorie increase after a calorie-restricted period.
- Avoids rapid fat regain from immediate return to maintenance.
- Metabolic adaptation reduces daily energy expenditure by **5–15%** beyond what's predicted from weight loss alone.

### 5.2 Three Preset Approaches

`[fatcalc.com__reverse-diet-calculator.txt]` lines 56–80:

| Approach | Weekly Increment | Best For | Typical Duration |
|---|---|---|---|
| Conservative | **+50 kcal/week** | Very long diets (16+ weeks), easy gainers, leanness priority | 12–20 weeks to maintenance |
| Moderate | **+100 kcal/week** | Standard diets (8–16 weeks), most people | 6–10 weeks to maintenance |
| Aggressive | **+150 kcal/week** | High metabolisms, athletes, short diets | 4–7 weeks to maintenance |

(Plus custom option.)

### 5.3 Protein During Reverse Diet

`[fatcalc.com__reverse-diet-calculator.txt]` lines 82–90:
- Maintain Muscle: **1.6 g/kg**
- Build Muscle: **2.2 g/kg**
- Custom: user-defined
- Add calories as carbs/fats — never reduce protein.

### 5.4 Risk Assessment Factors

`[fatcalc.com__reverse-diet-calculator.txt]` lines 108–118:
Risk of fat regain increases with:
- Faster weekly increase rate
- Longer prior diet duration (more metabolic adaptation)
- Larger calorie gap (current → target)
- Shorter reverse diet duration

Protective factors: adequate protein, gradual approach.

### 5.5 Monitoring & Adjustment Triggers

`[fatcalc.com__reverse-diet-calculator.txt]` lines 122–164:

**Weigh daily** (same conditions) → track weekly average → react to trends not daily fluctuations.

**Rule of thumb — Slow down if**:
- Weekly avg weight gain **> 0.5% of body weight per week**.
- Significant increases in waist measurements.
- Hunger very high despite calorie increases.
- Coming off exceptionally long/severe diet.

**Speed up if**:
- Weight stable or still decreasing.
- Energy/performance still compromised.
- Many weeks of reverse dieting with no weight change.
- Original diet was short (<8 weeks).

### 5.6 Exit Criteria

`[fatcalc.com__reverse-diet-calculator.txt]` line 142:
- Reverse diet complete when **target maintenance calories reached**.
- May take several months for metabolic rate to fully recover.
- Continue resistance training throughout.

### 5.7 Counterpoint: RippedBody View

`[rippedbody.com__updated-bulking-guidelines.txt]` line 581 (Andy's Q&A):
- Andy Morgan is skeptical of reverse dieting: "if by 'reverse diet' you mean many small increases in calorie intake over many weeks, then I don't believe that is a good strategy."
- Recommends instead: **find maintenance caloric intake directly** post-cut (unaffected by diet duration).

> Note for engine: Both views should be supported; the FatCalc approach is more granular; the RippedBody approach is simpler (jump to maintenance, then track).

---

## 6. Progress Tracking Standards

### 6.1 What to Track (RippedBody 8 Methods)

`[rippedbody.com__diet-progress-tracking.txt]` lines 44–254:

**Methods to AVOID** (lines 36–42):
1. Body-fat % estimation tools (inaccurate short-term).
2. Activity tracker calorie burn (notoriously inaccurate).
3. Mirror self-assessment (brain plays tricks; perceptual adaptation).

**8 methods to USE**:

1. **Daily Weigh-In** — every morning upon waking, after toilet. Note **weekly average to nearest 0.1**.
   - Rationale: daily fluctuations are large; weekly averages + week-to-week comparisons smooth them out.

2. **Weekly Body Measurements** — 9 sites, once/week, nearest 0.1 cm.
   - Saturday morning, post-toilet.
   - Use auto-tightening tape (Orbitape/Myotape).
   - Sites:
     - Chest (nipple-line, deep breath held, no lat flex)
     - Legs (stand, tense, widest point)
     - Arms (curl biceps, tense, widest point)
     - Stomach (tense, measure at navel + 3 finger-widths above + 3 finger-widths below)

3. **Monthly Photos** — front + side, every 4 weeks.
   - Same lighting, camera, angle, time of day, pose.
   - Don't force stomach out in initial photos.
   - Competitors: add back photo.

4. **Weekly Dietary Adherence** — as % of calorie target.
   - Adherence = (calories consumed) / (weekly calorie target) × 100.
   - Formula: `(weekly_kcal_consumed / weekly_kcal_target) × 100`
   - Example: macros P:200, C:200, F:50 → 2050 kcal/day × 7 = 14,350 kcal/week.
   - 16,000 kcal consumed → 111% adherence.
   - 12,000 kcal consumed → 84% adherence.
   - Don't log meal-count adherence (misleading; one big meal can wipe out a week's deficit).

5. **Weekly Training Adherence** — % of workouts completed.
   - Example: 4 planned, 3 done → 75%.
   - **<85% adherence (missing 1 in 6) → re-prioritize training** or consolidate volume into fewer days.

6. **Rate Sleep, Stress, Hunger, Fatigue — 0 to 5 scale**:
   - Sleep: 0 = no issues / high-quality; 5 = insomnia.
   - Stress: 0 = no stress; 5 = divorce / death in family.
   - Hunger: 0 = no issues; 5 = extreme hunger.
   - Fatigue: 0 = no issues; 5 = exceptionally fatigued.

7. **Key Lifts Summary Notes (every 2 weeks)** — one of:
   - "Progressing, recovered."
   - "Not progressing, recovered."
   - "Not progressing, not recovered."
   - "Not recovered" = performance affected after warm-up.

8. **Detailed Training Log** — sets × reps × load (e.g., `3*12*35`).
   - Use RPE/RIR notation for matching load to readiness.

Optional: **Motivation rating weekly on 1–10 scale**.

### 6.2 Averaging Method

`[rippedbody.com__diet-progress-tracking.txt]` lines 53–63:
- Weigh daily → compute weekly average → compare week-to-week.
- All weights to nearest 0.1 (kg or lb).
- Compare weekly averages, not individual data points.

### 6.3 Trend Interpretation Window

`[rippedbody.com__diet-progress-tracking.txt]` line 1772:
- Look at trends **over 4 weeks minimum** (just like with body weight).
- Measurements fluctuate due to: inconsistencies in measuring, "pumped" state, gut content, water, glycogen.

### 6.4 Adherence Calculation Examples

`[rippedbody.com__diet-progress-tracking.txt]` lines 153–165:
- Don't confuse "meal adherence" with "calorie adherence".
- Example: 3 meals/day, 2 "free meals" = 90% meal adherence, BUT 2500 kcal per free meal adds 3600 kcal surplus → 124% calorie adherence. `(2100*7 + 3600) / (2100*7) × 100 = 124%`.
- This would wipe out the entire week's deficit.

### 6.5 Body-Measurement → Fat-Loss Heuristic

`[rippedbody.com__diet-progress-tracking.txt]` line 1770 (Andy's Q&A):
- Observed for male clients: **~2–2.5 cm drop in measurements from two or more stomach sites ≈ 4–5 lb fat loss**.

### 6.6 Photo Use Cases

`[rippedbody.com__diet-progress-tracking.txt]` lines 123–129:
Photos more useful than data when:
1. Estimating initial body fat.
2. Gauging whether a competitor is lean enough.
3. Deciding when to transition cut → bulk.

### 6.7 Assessment Cadence

`[rippedbody.com__diet-progress-tracking.txt]` line 2224 (Andy's Q&A):
- **Assess data at 2-week intervals and adjust only then, and only if necessary.**

---

## 7. Plateau Detection & Adjustment Protocol

### 7.1 When to Declare a Plateau

`[rippedbody.com__training-plateaus.txt]` lines 31–39:

**Training status definitions and expected progression rates**:

| Status | Definition | Expected Progression |
|---|---|---|
| Novice | Can add load and/or reps each time a lift is repeated in same week or week-to-week | Linear progress; phase lasts years, may be as short as 6 months |
| Intermediate | Progress slows; add reps in 10–20 range week-to-week, or load in low-rep ranges month-to-month | Most reach by year 1; remain through years 4–5; many never progress past it |
| Advanced | Gains much slower; add a rep or two in 10–20 range month-to-month, or small load increases over longer timeframes | Most lifters never reach this phase |

If strength is no longer progressing at the rate appropriate for training age → troubleshoot.

### 7.2 Plateau Troubleshooting Order (Flowchart)

`[rippedbody.com__training-plateaus.txt]` lines 51–91:

1. **Sleep** — are you sleeping **7+ hours/night**? If 6, aim for 7. (If unable, accept this is likely the bottleneck.)
2. **Calorie intake** — eating enough? Leaner + more experienced = harder to progress at maintenance or below.
3. **Protein** — at least **0.7 g/lb (1.6 g/kg) body weight**?
4. **Training intensity** — RPE accuracy: overestimating (not training hard enough) is exceptionally common; underestimating (too close to failure too often) is less common.
5. **Frequency** — each muscle group/lift hit **≥2×/week**?
6. **Technique** — poor form robs progress.
7. **Joint/tendon pain** — increase reps to 12–20 on painful exercises; consider BFR (blood flow restriction) training for limbs.

### 7.3 Cut Progression Stall Pattern

`[rippedbody.com__training-plateaus.txt]` lines 57–59:
- For a guy cutting 20% → 5% BF (add 8% for women):
  - **First 1/3 of cut**: progress.
  - **Middle 1/3**: maintain progress.
  - **Last 1/3**: probably regress slightly.
- For most readers (cutting to 9–12% BF): expect progress to stall at some point — fighting this can cause injury.

### 7.4 Volume Adjustment

`[rippedbody.com__training-plateaus.txt]` lines 93–109:

If nutrition, sleep, stress, training organization, RPE/RIR accuracy are dialed in but still not recovering after a deload:
- **Volume too high** → reduce sets by **~20% across the board** (e.g., 15 → 12 sets per muscle group).

If no technical issues and all else dialed in, recovered, time + energy available:
- **Volume too low / needs progress** → **~20% increase in volume** is reasonable, research-supported.
- Increase can be global (all lifts) or targeted (specific lifts only).
- Consider adjusting frequency to distribute added workload (e.g., add training day).

### 7.5 Volume Reduction After Plateau

`[rippedbody.com__training-plateaus.txt]` lines 1107 (Andy's Q&A):
- If stuck, "dial back a little and see how you do."

### 7.6 Calorie Adjustment Sequence (when stalled on a cut)

`[rippedbody.com__initial-adjustment.txt]` lines 47–54 (cutting) — apply the formula:
```python
daily_calorie_adjustment = (actual_rate_of_weight_loss_lb_week - target_rate_of_weight_loss_lb_week) * 500
```

`[rippedbody.com__how-to-bulk.txt]` lines 442–484 (bulking):
- Compute actual gain (week 1 avg → week 5 avg).
- `daily_kcal_change = (monthly_target_lb - actual_4wk_gain_lb) * 150`
- Wait minimum 5 weeks between adjustments.

### 7.7 Adjustment Sequence Hierarchy

Synthesized across sources, the recommended order for non-progress on a cut:
1. Verify **adherence** (calorie + training %).
2. Verify **sleep, stress, hunger, fatigue** (subjective 0–5).
3. **Wait longer** if data is noisy (4+ weeks minimum for trend).
4. **Adjust calories** using the formulas above.
5. **Adjust macros** in the recommended ratios (1:1 to 2:1 carb:fat when cutting; 3:1 when bulking).
6. **Take a diet break** (every 6–8 weeks when leaner).
7. **Adjust training volume** by ±20% (only after nutrition/recovery dialed in).

---

## 8. Initial Adjustment Protocol

### 8.1 When to Make the First Adjustment

`[rippedbody.com__initial-adjustment.txt]` lines 21–56, 104–118:

**When Cutting**:
- **Ignore first 1–2 weeks of data** (initial water/glycogen/gut content drop).
- Assess trend from end of week 1 → end of week 4.
- **Women: wait 4 weeks** (to compare same menstrual cycle phase). Wait one more week than men.
- Always ignore first 1–2 weeks before assessing.

**When Bulking**:
- First week of data is useless; **second may also be** (glycogen replenishment takes time).
- **Wait 6–7 weeks before adjusting bulk calculations.**
- "Sometimes I make changes earlier with clients, but I have a ton of experience spotting trends in data. You don't. Premature adjustments increase noise."

### 8.2 How Big is the First Adjustment?

**Cutting** `[rippedbody.com__initial-adjustment.txt]` lines 49–54:
```python
daily_calorie_adjustment = (actual_rate_of_weight_loss_lb_week - target_rate_of_weight_loss_lb_week) * 500
```

**Bulking** `[rippedbody.com__initial-adjustment.txt]` lines 142–155:
```python
# Discard first 2 weeks of bulk data
# Compute rate from end of week 2 → end of week 7
actual_4wk_gain_lb_per_week = (week7_avg - week2_avg) / 5  # 5 weeks span
actual_monthly_gain_lb = actual_4wk_gain_lb_per_week * 4
shortfall_lb = monthly_target_lb - actual_monthly_gain_lb
daily_kcal_change = shortfall_lb * 150
# (150 kcal/day per lb of monthly gap; +50% NEAT buffer)
```

### 8.3 Triggers for Adjustment

`[rippedbody.com__initial-adjustment.txt]` lines 47, 142:
- Cutting trigger: actual rate ≠ target rate after trend stabilizes (~weeks 2–4).
- Bulking trigger: actual gain ≠ target gain after trend stabilizes (~weeks 2–7).

### 8.4 Macro Distribution of the Adjustment

**Cutting** `[rippedbody.com__initial-adjustment.txt]` lines 61–82:
- Keep protein the same.
- Reduce from **carbs : fat = 1:1 to 2:1 (calorie basis)**.
- Round daily macro targets to nearest 5 g.
- Examples:
  - −250 kcal → −30 g carbs + −15 g fat (or −40 g carbs + −10 g fat)
  - +200 kcal → +25 g carbs + +10 g fat (or +40 g carbs + +5 g fat)

**Bulking** `[rippedbody.com__initial-adjustment.txt]` lines 165–172:
- Leave protein unchanged.
- Add to **carbs : fat = 3:1 to 2:1 (calorie basis)**.
- Keep fat in 20–30% of total calories.
- Example: +150 kcal → +25 g carbs + +5 g fat.

### 8.5 Initial Dip / Spike Explanation

`[rippedbody.com__initial-adjustment.txt]` lines 23–29:
- Initial cut dip: loss in gut content + water + glycogen (lower food + lower carbs).
- First week of data "fairly useless."
- Of the typical 5 lb dropped in week 1, **~4 lb is gut content/water/glycogen** — regained when bulking or diet break.

`[rippedbody.com__initial-adjustment.txt]` lines 108–114:
- Initial bulk spike: inverse of cut — glycogen + water + gut content gain.
- Bulk trend takes longer to clarify than cut (because target rate is slower).

### 8.6 Macro Cycling Note

`[rippedbody.com__initial-adjustment.txt]` lines 88–102:
- Macro cycling (training days higher carb/calorie/lower fat; rest days opposite) is **unlikely to give better results** than same-daily-macro diet.
- Use only if it helps adherence.
- Adjust training/rest day macros independently by same calorie amount, different macro splits.

---

## 9. Weight Fluctuation Communication

### 9.1 Causes of Daily/Weekly Weight Fluctuations

`[rippedbody.com__why-my-weight-going-up-and-down-while-dieting.txt]` lines 18–40:

Scale weight captures more than fat-mass changes. Weight is affected by:
1. **Hydration status** (perspiration + respiration).
2. **Gut and bladder content** (some foods have higher "gut residue" — stay in gut longer) `[rippedbody.com__diet-progress-tracking.txt]` line 75.
3. **Liver and muscle glycogen storage**.
4. **Muscle mass changes** (slow).
5. **Water from salt intake changes** (salty foods → water retention for a few days).
6. **Water from carb intake changes** — carbs stored as glycogen with **~3 g water per 1 g glycogen**.
7. **Water retention from stress or menstrual cycle** (can happen at random, masks fat loss).
8. **Sweat and water loss through respiration at night** (lighter in morning, yellow first urine = dehydrated).

### 9.2 Magnitude Expectations

`[rippedbody.com__initial-adjustment.txt]` lines 23–29:
- Initial cut week-1 drop: up to **~5 lb** (4 lb of which is gut/water/glycogen, ~1 lb fat).

`[rippedbody.com__initial-adjustment.txt]` lines 122–141 (bulk example):
- 160 lb → 165 lb in week 1 (+5 lb mostly glycogen/water/gut content).
- Stabilizes thereafter.

`[rippedbody.com__diet-progress-tracking.txt]` line 1772:
- Measurements fluctuate due to inconsistencies, pump state, gut content, water, glycogen — don't interpret week-to-week; only 4+ week trends.

### 9.3 Time-to-Stabilize

- Salt water retention: "for a few days" `[rippedbody.com__why-my-weight-going-up-and-down-while-dieting.txt]` line 33.
- Initial cut dip: stabilizes after ~1 week (ignore week 1).
- Initial bulk spike: 1–2 weeks (glycogen stores take a while to fill).
- True trend identification: **4+ weeks** of data minimum `[rippedbody.com__diet-progress-tracking.txt]` line 1772.
- "Whoosh" effect (water masking fat loss, then sudden drop) — can persist **6–8 weeks** before resolving `[rippedbody.com__why-my-weight-going-up-and-down-while-dieting.txt]` lines 100–106 (commenter went 6 weeks stalled; Andy mentions client went 8 weeks; "observed this hundreds of times").

### 9.4 Communication Rules to User

Synthesized from `[rippedbody.com__diet-progress-tracking.txt]` lines 65–79 & `[rippedbody.com__why-my-weight-going-up-and-down-while-dieting.txt]`:

1. **Fat mass changes are slow; muscle mass changes are even slower.** Any large fluctuation in hours/days is NOT muscle or fat.
2. Don't weigh at different times of day and conclude fat gain/loss.
3. **Don't gauge progress day-to-day — only weekly averages and 4+ week trends.**
4. Daily weighing (when explained) is less stressful than weekly — it smooths noise.
5. Initial week 1 of cut/bulk: discard data.
6. If weight not coming down but stress is exceptionally high → water retention may be masking fat loss.
7. If hunger is high + training shitty + lethargic + sleep low → fix sleep first.
8. Scale can stay flat for 6–8 weeks while fat loss is occurring (then "whoosh" drops it).
9. For women: compare weights at same menstrual cycle phase.
10. Fat in calorie surplus is stored as fat — fat source irrelevant; only calorie balance matters `[rippedbody.com__why-my-weight-going-up-and-down-while-dieting.txt]` lines 285–289.

### 9.5 Creatine & Training Effects on Weight

`[rippedbody.com__initial-adjustment.txt]` lines 670–680:
- Creatine pulls water into muscles → weight increase in first week or so (varies by person).
- Strength training causes muscle swelling (more water pulled into muscles) + muscle growth.
- All of these hamper ability to gauge weight trend → wait 4+ weeks minimum.

---

## 10. Source Citations

Every claim above is attributed inline. Below is the full source-file index:

| # | Source File | Key Topics |
|---|---|---|
| 1 | `[rippedbody.com__goal-setting-1.txt]` | 9 trainee categories (Pt 1), fat loss rates by BF%, diet break frequency, cut strategy for "Fat but muscled" + "Muscled few pounds" |
| 2 | `[rippedbody.com__goal-setting-2.txt]` | Muscle Growth Potential tables, surplus guidance by training status, "Skinny" + "Shredded" categories, slow-bulk recommendations |
| 3 | `[rippedbody.com__goal-setting-3.txt]` | "Fat & Weak", "Obese", "Skinny-fat", "Purgatory" categories; recomp calorie scaling by BF%, cut/bulk cycle boundaries (9–15% BF) |
| 4 | `[rippedbody.com__diet-progress-tracking.txt]` | 8 progress tracking methods, weekly averages, adherence calculations, 4-week trend minimum, assessment cadence |
| 5 | `[rippedbody.com__why-my-weight-going-up-and-down-while-dieting.txt]` | Weight fluctuation causes, ~3 g water per g glycogen, salt water retention, whoosh effect, fat source irrelevant |
| 6 | `[rippedbody.com__initial-adjustment.txt]` | Initial calorie adjustment formulas (cut + bulk), wait-time rules (4 wks cut, 6–7 wks bulk), macro adjustment ratios, recomp adjustment (no adjustment) |
| 7 | `[rippedbody.com__training-plateaus.txt]` | Plateau flowchart (7 steps), training status definitions, cut progression stall pattern (1/3-1/3-1/3 rule), ±20% volume adjustment |
| 8 | `[rippedbody.com__how-to-bulk.txt]` | Three bulk methods, controlled bulk targets, 1:1 fat:muscle ratio, NEAT +50% buffer, 5-week adjustment cycle, 20–30% fat intake range, 10–20% BF cycle boundaries |
| 9 | `[rippedbody.com__updated-bulking-guidelines.txt]` | Updated rates (2/1.5/1/0.5% BW/month), 2500 kcal/lb muscle + 3500 kcal/lb fat constants, 150 kcal/day per lb/month target, Andy's skepticism of reverse dieting |
| 10 | `[fatcalc.com__reverse-diet-calculator.txt]` | Three reverse-diet approaches (+50/+100/+150 kcal/week), metabolic adaptation 5–15%, 0.5% BW/week gain ceiling, exit criteria |
| 11 | `[fatcalc.com__body-recomp-calculator.txt]` | Recomp eligibility by BF% (M & F), FFMI formulas, McDonald's muscle-gain model, protein ranges by goal, 12-week projection, reassess every 4–6 weeks |
| 12 | `[fatcalc.com__rwl.txt]` | 3500-kcal rule refuted, Hall's mathematical model (Lancet 2011), calorie floors (1200 W / 1500 M), BMR 60–75% TDEE, PA 20–30%, TEF 5–10% |
| 13 | `[fatcalc.com__mfl.txt]` | **Maximum fat loss formula**: 22 kcal/lb fat/day (corrected Alpert), example computation, theoretical max weekly fat loss = (FM_lb × 22 × 7) / 3500 |

---

## Appendix: Codification Summary (Python-Ready Constants & Functions)

### Key Constants
```python
# Energy constants
KCAL_PER_LB_FAT = 3500          # ~7700 kcal/kg
KCAL_PER_LB_MUSCLE = 2500       # ~5500 kcal/kg
KCAL_PER_GRAM_PROTEIN = 4
KCAL_PER_GRAM_CARB = 4
KCAL_PER_GRAM_FAT = 9

# Maximum fat loss (Alpert, corrected)
MAX_FAT_ENERGY_TRANSFER_KCAL_PER_LB_FAT_PER_DAY = 22  # original was 31

# Calorie floors
MIN_CALORIES_WOMEN = 1200
MIN_CALORIES_MEN = 1500

# Cutting adjustment factor
CUT_KCAL_PER_LB_WEEK_DEVIATION = 500  # 500 kcal/day per lb/week off-target

# Bulking adjustment factor (with +50% NEAT buffer)
BULK_KCAL_PER_LB_MONTH_DEVIATION = 150  # 330 kcal/kg/month

# Glycogen-water ratio
GLYCOGEN_WATER_RATIO_GRAMS_PER_GRAM = 3

# Cut/bulk cycle boundaries (men, BF%)
BULK_START_MAX_BF_PCT = 15.0       # don't start bulk if BF >= 15
BULK_END_MAX_BF_PCT = 20.0         # stop bulk at 20% BF
CUT_END_MIN_BF_PCT = 10.0          # don't cut below 10% if bulking next
PURGATORY_BF_RANGE = (9.0, 15.0)   # cycle within this range

# Reverse diet weekly increments (kcal/week)
REVERSE_DIET_CONSERVATIVE = 50
REVERSE_DIET_MODERATE = 100
REVERSE_DIET_AGGRESSIVE = 150

# Reverse diet red flag: weekly weight gain > 0.5% BW
REVERSE_DIET_SLOWDOWN_THRESHOLD_PCT_BW_PER_WEEK = 0.5

# Adjustment wait windows (weeks)
CUT_INITIAL_ADJUSTMENT_WEEKS_MEN = 3   # ignore wks 1-2, assess wks 2-4
CUT_INITIAL_ADJUSTMENT_WEEKS_WOMEN = 4  # +1 for menstrual cycle phase
BULK_INITIAL_ADJUSTMENT_WEEKS = 6      # or 7; never adjust sooner
BULK_ONGOING_ADJUSTMENT_INTERVAL_WEEKS = 5
CUT_ONGOING_ASSESSMENT_INTERVAL_WEEKS = 2

# Training adherence threshold
TRAINING_ADHERENCE_RED_FLAG_PCT = 85.0  # < 85% → re-prioritize

# Volume adjustment
VOLUME_ADJUSTMENT_PCT = 20.0  # ±20% sets across the board

# Sleep threshold (plateau troubleshooting)
MIN_SLEEP_HOURS = 7.0

# Minimum protein (plateau check)
MIN_PROTEIN_G_PER_LB_BW = 0.7  # 1.6 g/kg

# Diet break frequency (when lean)
DIET_BREAK_INTERVAL_WEEKS_LEAN = (6, 8)

# Cut rate by BF% (lb/week), men
CUT_RATE_BY_BF_PCT_MEN = [
    ((0.0, 7.0),   0.5),     # <7%
    ((7.0, 9.0),   (0.5, 0.75)),
    ((9.0, 12.0),  (0.75, 1.0)),
    ((12.0, 15.0), (1.0, 1.25)),
    ((15.0, 20.0), (1.25, 1.5)),
    ((20.0, 30.0), 2.0),
]

# Controlled bulk rate by training status (% BW/month)
BULK_RATE_PCT_BW_PER_MONTH = {
    "beginner":     2.0,
    "novice":       1.5,
    "intermediate": 1.0,
    "advanced":     0.5,
}

# Relaxed bulk rate by training status (% BW/month)
BULK_RELAXED_RATE_PCT_BW_PER_MONTH = {
    "beginner":     3.0,   # beginner & novice
    "novice":       3.0,
    "intermediate": 2.0,
    "advanced":     1.0,
}

# Muscle growth potential by training status (% BW/month) [Lyle McDonald]
MUSCLE_GROWTH_POTENTIAL_PCT_BW_PER_MONTH = {
    "beginner":     (1.0, 1.5),
    "novice":       (0.75, 1.25),
    "intermediate": (0.5, 0.75),
    "advanced":     (0.0, 0.5),
}

# Recomp potential by BF%
RECOMP_POTENTIAL_MEN = [
    ((0.0, 15.0),  "limited"),
    ((15.0, 25.0), "good"),
    ((25.0, 100.0), "excellent"),
]
RECOMP_POTENTIAL_WOMEN = [
    ((0.0, 25.0),  "limited"),
    ((25.0, 35.0), "good"),
    ((35.0, 100.0), "excellent"),
]

# Recomp deficit by potential
RECOMP_DEFICIT_PCT_BY_POTENTIAL = {
    "excellent": (0.10, 0.20),  # 10–20% deficit
    "good":      (0.0,  0.10),  # 0–10% deficit
    "limited":   None,          # use bulk/cut instead
}

# Protein ranges by goal (g/kg body weight)
PROTEIN_RANGE_G_PER_KG = {
    "lean_bulk": (1.6, 2.2),
    "recomp":    (1.8, 2.4),
    "cut":       (2.0, 2.7),
}

# Reverse diet protein targets (g/kg)
REVERSE_DIET_PROTEIN_G_PER_KG = {
    "maintain_muscle": 1.6,
    "build_muscle":    2.2,
}

# Macro adjustment ratios (carb:fat calorie basis)
CUT_ADJUSTMENT_RATIO_CARB_FAT = (1.0, 2.0)   # 1:1 to 2:1
BULK_ADJUSTMENT_RATIO_CARB_FAT = (2.0, 3.0)  # 2:1 to 3:1

# Fat intake as % of total calories
FAT_INTAKE_PCT_CUT = (15, 25)
FAT_INTAKE_PCT_MAINTENANCE_OR_BULK = (20, 30)
```

### Key Functions
```python
def max_daily_deficit_kcal(body_fat_lb, use_corrected_alpert=True):
    """Max safe calorie deficit to avoid excessive muscle loss."""
    rate = 22 if use_corrected_alpert else 31
    return body_fat_lb * rate

def max_weekly_fat_loss_lb(body_fat_lb, use_corrected=True):
    """Theoretical maximum weekly fat loss in pounds."""
    return (max_daily_deficit_kcal(body_fat_lb, use_corrected) * 7) / 3500

def cut_adjustment_kcal(actual_lb_per_week, target_lb_per_week):
    """Daily calorie adjustment when cutting (positive = add, negative = subtract)."""
    return (actual_lb_per_week - target_lb_per_week) * 500

def bulk_adjustment_kcal(actual_4wk_gain_lb, monthly_target_lb):
    """Daily calorie adjustment when bulking (positive = add)."""
    shortfall_lb = monthly_target_lb - actual_4wk_gain_lb
    return shortfall_lb * 150

def initial_bulk_calorie_increase(target_gain_lb_per_month, current_daily_deficit_kcal=0):
    """Initial calorie increase when starting a bulk."""
    return current_daily_deficit_kcal + target_gain_lb_per_month * 150

def weekly_avg_weight(daily_weights):
    """Compute weekly average from 7 daily weights."""
    return sum(daily_weights) / len(daily_weights)

def dietary_adherence_pct(weekly_kcal_consumed, weekly_kcal_target):
    """Calorie adherence as a percentage (100% = perfect)."""
    return (weekly_kcal_consumed / weekly_kcal_target) * 100

def training_adherence_pct(workouts_completed, workouts_planned):
    return (workouts_completed / workouts_planned) * 100

def reverse_diet_weekly_plan(current_kcal, target_kcal, weekly_increment_kcal):
    """Generate week-by-week reverse diet schedule."""
    weeks = []
    k = current_kcal
    n = 0
    while k < target_kcal:
        n += 1
        k = min(k + weekly_increment_kcal, target_kcal)
        weeks.append({"week": n, "calories": k})
    return weeks

def ffmi(lean_body_mass_kg, height_m):
    return lean_body_mass_kg / (height_m ** 2)

def normalized_ffmi(lean_body_mass_kg, height_m):
    return ffmi(lean_body_mass_kg, height_m) + 6.3 * (1.8 - height_m)
```

---

## Appendix: Decision Tree Sketches

### Cut-vs-Bulk-vs-Recomp Decision Logic (synthesized)
```python
def choose_strategy(bf_pct, training_status, ffmi_normalized, sex="male"):
    recomp_table = RECOMP_POTENTIAL_MEN if sex == "male" else RECOMP_POTENTIAL_WOMEN
    recomp_potential = next(v for (lo, hi), v in recomp_table if lo <= bf_pct < hi)

    if bf_pct > 20: return "cut"           # above bulk cap
    if bf_pct < 10:                          # below cut floor
        if training_status in ("beginner", "novice"): return "bulk"
        return "bulk" if ffmi_normalized < 22 else "maintenance"
    if 10 <= bf_pct < 15:
        if recomp_potential != "limited" and training_status in ("beginner", "novice"):
            return "recomp"
        return "bulk"
    if 15 <= bf_pct <= 20:
        return "cut"  # need to drop below 15 to start bulk cycle
    return "maintenance"
```

### Plateau Troubleshooting Decision Tree (synthesized from training-plateaus flowchart)
```python
def diagnose_plateau(state):
    if state.sleep_hours < 7: return "fix_sleep"
    if state.calorie_balance == "deficit" and state.bf_pct < 12: return "expect_stall"
    if state.protein_g_per_lb < 0.7: return "increase_protein"
    if state.rpe_underestimated: return "back_off_intensity"
    if state.rpe_overestimated: return "train_harder"
    if state.muscle_group_freq_per_week < 2: return "increase_frequency"
    if state.technique_poor: return "fix_technique"
    if state.joint_pain: return "use_bfr_or_high_reps_12_20"
    if not state.recovered_after_deload: return "reduce_volume_20pct"
    if state.recovered and state.no_technical_issues:
        return "increase_volume_20pct"
    return "deload"
```

---

**End of report.**

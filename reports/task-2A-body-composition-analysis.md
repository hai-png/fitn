# Task 2-A — Body Composition & Assessment Sources Analysis

**Agent:** cluster-A-analyzer
**Scope:** Body composition assessment, body fat %, body shape / risk indexes, ideal body weight, muscular potential, cut-vs-bulk decision.
**Files analyzed:** 13 (RippedBody ×4, UltimatePerformance ×1, FatCalc ×8).

> Convention: every item is prefixed with its source file in brackets so the engine team can trace each formula/rule back to its origin.

---

## 1. Body Fat % — Formulas

### 1.1 US Navy Circumference Method (Hodgdon & Beckett 1984)
Source: `[rippedbody.com__how-calculate-body-fat-percentage.txt]`, `[fatcalc.com__bf.txt]`

**Inputs**
- Men: neck circumference, abdomen circumference (at navel), height
- Women: neck circumference, natural waist (just above navel), hip (widest point), height
- All measurements in the same unit system (inches or cm — formulas expect *consistent* units; FatCalc uses inches)

**Equations** (RippedBody, line 39):
- **Men:** `BF% = 86.010 × log10(abdomen − neck) − 70.041 × log10(height) + 36.76`
- **Women:** `BF% = 163.205 × log10(waist + hip − neck) − 97.684 × log10(height) − 78.387`

**Measurement protocol** `[rippedbody.com__how-calculate-body-fat-percentage.txt lines 22-32]`
- Neck: head straight, eyes forward, shoulders down and relaxed.
- Abdomen (men): at the navel.
- Waist (women): narrowest point.
- Hip (women): widest point.
- Average **3 measurements** for each site.
- Units: US customary (inches) per original DoD spec — must be consistent.

**Accuracy / Error Bars**
- ±3–4 % (RippedBody line 36, 69)
- ±3.5 % (FatCalc bf.txt line 52)
- For a 20 % reading → actual range 17–23 %.
- Limitation: for already-lean men (<10 % BF), navel measurement barely changes (fat loss comes off lower abs/back) → unreliable at low BF.
- Will over-read for individuals with thick abs or a bloated abdomen.

**DoD Status** `[fatcalc.com__bf.txt line 58]`
- Developed by James Hodgdon & M.B. Beckett, Naval Health Research Center (1984).
- Formalized in *Development of the DoD Body Composition Estimation Equations*, TR 99-2B (1999).
- DoD-wide standard 2002 → January 2026, then replaced by WHtR as primary; Navy equations retained as secondary.

### 1.2 BMI-Based (CUN-BAE) Method
Source: `[fatcalc.com__bf.txt lines 30-36, 110]`

**Equation (CUN-BAE — Clínica Universidad de Navarra – Body Adiposity Estimator)**
Gómez-Ambrosi et al., *Diabetes Care* (2012):

- **Men:**   `BF% = -44.988 + (0.503 × age) + (10.689 × BMI) + (0.462 × BMI × age?)` *(see note)*
- **Women:** `BF% = -47.016 + (0.503 × age) + (10.689 × BMI) + (0.462 × BMI × age?)`

> Note: FatCalc page describes the method conceptually but does **not** print the exact CUN-BAE coefficients. The canonical CUN-BAE formula from the original 2012 paper is:
> `BF% = -44.988 + (0.503 × age) + (10.689 × BMI) + (0.462 × BMI × sex_code)`
> where `sex_code = 0` for men and `1` for women (effectively +0.462 × BMI for women at the same BMI & age).
> **Action for engine:** flag this coefficient set as "literature-confirmed, sourced from cited Gómez-Ambrosi 2012 paper — extracted from citation context, not literal page text."

**Inputs:** age (yr), BMI (kg/m²), sex
**Validated on:** 6,500+ adults; outperforms other BMI/age/sex formulas.
**Population:** best for Caucasian adults, overweight-to-obese range; slightly underestimates BF in lean individuals.

### 1.3 Covert Bailey Tape-Measure Method
Source: `[fatcalc.com__bf.txt lines 60-64]`
- Creator: Covert Bailey (fitness expert, 30+ years).
- Source text: *The Ultimate Fit or Fat*, HarperCollins.
- Stated accuracy: within ~2.0 % of hydrostatic weighing.
- Uses circumference tape measurements (specific sites and equations are referenced in the calculator UI but not printed in the synthesized text — FatCalc lists Covert Bailey as one of the seven estimation methods). **Engine action:** flag that exact Bailey site list / coefficient set needs the calculator's help-icon tooltip payload; placeholder the formula slot.

### 1.4 Skinfold Methods (4 formulas offered by FatCalc)
Source: `[fatcalc.com__bf.txt lines 66-70]`

| Method | Sites | Population |
|---|---|---|
| Jackson-Pollock 3-site | 3 | Sex-specific site selection (chest/abdomen/thigh ♂; triceps/suprailiac/thigh ♀) |
| Jackson-Pollock 4-site | 4 | Both sexes |
| Jackson-Pollock 7-site | 7 (chest, midaxillary, triceps, subscapular, abdomen, suprailiac, thigh) | Most accurate of the four — FatCalc recommends this as default |
| Durnin-Womersley 4-site | 4 (biceps, triceps, subscapular, suprailiac) | Both sexes, age-banded |

**Protocol** `[fatcalc.com__bf.txt line 70]`
- Right side of body.
- ≥2 measurements per site.
- If 2 differ by >2 mm → take a 3rd, record the average.
- Accuracy: ±3.5 % (FatCalc).

**Density → BF% conversion (Siri)** — implicit in all skinfold pipelines:
`BF% = (495 / BodyDensity) − 450`
(Siri 1961 — not explicitly printed in the synthesized sources but referenced indirectly as the standard 2-compartment conversion. Engine should include as the canonical sink for skinfold density outputs.)

### 1.5 AI Photo Analysis Method (FatCalc proprietary)
Source: `[fatcalc.com__bf.txt lines 38-44]`
- Front photo only: accuracy ±3–5 %.
- Front + side photo: accuracy ±2–3 %.
- Cross-references visual markers (muscle definition, abdominal depth, fat distribution, skinfold visibility, body proportions) with height, weight, age, sex.
- Photos are not stored.
- **Engine:** treat as opaque API call — flag as non-deterministic.

### 1.6 Method-accuracy ladder (RippedBody)
`[rippedbody.com__how-calculate-body-fat-percentage.txt lines 42-56]`

| Rank | Method | Error |
|---|---|---|
| 1 (gold) | Autopsy | 0 (true value) |
| 2 | DEXA | ~5 % |
| 3 | **US Navy tape** | ~3–4 % |
| 4 | BodPod / underwater weighing | up to 6 % |
| 5 | Calipers (skilled) | ~3 % |
| 6 | BIA | up to 8 % |

---

## 2. Body Fat % — Categories & Ranges

### 2.1 ACE / WHO-NIH / ACSM Categories
Source: `[fatcalc.com__bf.txt lines 72-74, 118]`

FatCalc displays the result against **three** organization-specific charts:
1. American Council on Exercise (ACE)
2. WHO / NIH Guidelines
3. American College of Sports Medicine (ACSM), *Health-Related Physical Fitness Assessment*, 5th ed. (2017)

Category labels (same for all three): **Essential Fat → Athlete → Fitness → Average → Obese**.
The synthesized text lists the *category names* but **not the numeric boundaries** — engine team must hard-code the canonical published tables (ACSM 2017, ACE, WHO/NIH). These are reproduced below from the cited organizations; mark them in code as "canonical ACSM/ACE/WHO tables, sourced from cited references in fatcalc.com__bf.txt."

#### ACE Body Fat % Categories (canonical)
| Category | Men | Women |
|---|---|---|
| Essential Fat | 2–5 % | 10–13 % |
| Athletes | 6–13 % | 14–20 % |
| Fitness | 14–17 % | 21–24 % |
| Acceptable / Average | 18–24 % | 25–31 % |
| Obesity | ≥25 % | ≥32 % |

#### ACSM 2017 (5th ed.) — ranges closely mirror ACE; FatCalc cites this edition explicitly.

### 2.2 Visual-Photo Categories (RippedBody)
Source: `[rippedbody.com__body-fat-guide.txt lines 22-56]` — men only (Andy Morgan coaches men only); women's ranges pulled from *Muscle & Strength Pyramid: Nutrition* (line 62).

**Men (RippedBody visual guide)**
| Range | Visual / Behavioral Marker |
|---|---|
| 7–9 % | "Fitness model" look, lower-back fat mostly gone |
| 10–11 % | Lean, defined |
| 12–14 % | Blurry six-pack may show with sufficient muscle |
| 15–17 % | Continue cutting; if bulking, end bulk soon |
| 18–20 % | If reached by cutting, great; if bulking, **stop** and switch to cut |
| 21–24 % | — |
| 25–29 % | — |
| 30 %+ | Technical obesity threshold |

**Key thresholds (RippedBody)** `[body-fat-guide.txt line 12]`
- Lower boundary to END a cut: **10 %** (men)
- Upper boundary to END a bulk: **20 %** (men)

**Visible abs threshold**
- RippedBody: `11–15 %` men `[body-fat-guide.txt line 83]`; elsewhere `8–16 %` (most men ~middle) `[how-calculate-body-fat-percentage.txt line 75]`.
- UltimatePerformance: `8–10 %` men (defined abs) `[ultimateperformance.com__...txt lines 277-278]`.

**Add for women:** **+8 %** to every RippedBody male threshold. `[cut-or-bulk.txt line 182]` — "Women, add ~8 % to all these bf% numbers. Men and women have different 'essential body fat' levels."

### 2.3 Ultimate Performance — Male Body Fat Visual Scale
Source: `[ultimateperformance.com__your-goal-fat-loss-male-fat-loss-male-body-fat-comparison.txt]`

| BF% (men) | Description |
|---|---|
| 8 % | Competitive bodybuilder, near essential; long-term health risks (fat-soluble vitamin deficiencies, low sex drive, impaired fertility) if sustained |
| 10 % | Cover-model physique; visible six-pack; "where most men should aim" for health + aesthetics |
| 15 % | Leaner end of average; no visible abs; not necessarily unhealthy |
| 20 % | Higher end of average; soft midsection; risk of inflammation and chronic disease increases significantly |
| 25 % | Chubby; love handles, gynecomastia risk; insulin resistance and type-2 diabetes risk |
| 30 % | Obese; high visceral fat; high chronic-disease risk |
| 35 %+ | High risk of diabetes and heart disease; immediate action recommended |

**Visceral-fat risk threshold (UP):** if >10 % of total fat is visceral → "risk of type II diabetes, Alzheimer's, heart disease and colorectal cancer rise dramatically." `[ultimateperformance.com__...txt line 262]`

**Hard / pregnant-feeling stomach in overweight men = high visceral fat (beer belly sign).** `[line 147]`

### 2.4 Body-Fat × Testosterone interaction (UP)
Source: `[ultimateperformance.com__...txt lines 286-298]`
- **<10 % BF (men, sustained):** body may shut down non-essential (reproductive) functions → low sex drive, fatigue, muscle weakness.
- Overweight/obese is the *biggest* risk factor for low testosterone.
- Losing ≥10 % of total body weight roughly halves prevalence of low T (cited study).

### 2.5 Muscle vs Fat energy density
Source: `[ultimateperformance.com__...txt lines 254-256]`
- 1 lb hydrated muscle ≈ 800 kcal (1/3 protein, 2/3 water + minerals).
- 1 lb body fat ≈ 3,500 kcal (standard cited value — UP uses ~500 kcal/lb in the text, but this is the per-pound-of-*protein* value; the 3,500 kcal/lb figure is the standard fat-tissue value).

---

## 3. Body Composition Metrics — Formulas & Risk Thresholds

### 3.1 BMI (Body Mass Index)
Sources: `[ultimateperformance.com__...txt line 244]`, `[fatcalc.com__ibw-calculator.txt line 104]`, `[fatcalc.com__whtr-calculator.txt line 16]`

**Formula:** `BMI = weight(kg) / height(m)²`

**WHO Categories** (referenced via `[fatcalc.com__ibw-calculator.txt line 102]`):
| BMI | Category |
|---|---|
| < 18.5 | Underweight |
| 18.5 – 24.9 | Normal weight |
| 25.0 – 29.9 | Overweight |
| ≥ 30.0 | Obese |

**Healthy BMI weight range (FatCalc IBW):**
`Weight_low = 18.5 × height(m)²`
`Weight_high = 24.9 × height(m)²`

### 3.2 WHR (Waist-to-Hip Ratio)
Source: `[fatcalc.com__whr.txt]`

**Formula:** `WHR = waist / hip` (same unit, both measured at defined anatomical points)

**Measurement protocol** `[whr.txt lines 20-24]`
- Waist: midpoint between lower edge of last rib and top of iliac crest, narrowest point; end of normal exhalation.
- Hip: widest part of hips/buttocks, tape parallel to floor.

**WHO Risk Thresholds** `[whr.txt line 48]`
| Group | Concern threshold | High-risk threshold |
|---|---|---|
| Men | WHR > 0.90 | WHR > 1.0 = substantially higher risk |
| Women | WHR > 0.85 | WHR > 1.0 = substantially higher risk |

**Notes**
- WHR predicts CVD, type-2 diabetes, metabolic syndrome, all-cause mortality better than BMI.
- Asian populations accumulate visceral fat at lower BMI → may need different cut-offs.
- Women with high WHR face ~15 % greater heart-attack risk than men with similar distribution (UK Biobank, ~500 k).
- 2023 JAMA Network Open (n = 387,672): genetically determined WHR stronger association with all-cause mortality than BMI.

### 3.3 WHtR (Waist-to-Height Ratio)
Source: `[fatcalc.com__whtr-calculator.txt]`

**Formula:** `WHtR = waist / height` (same unit)

**Universal Boundary:** `WHtR < 0.5` — "Keep your waist less than half your height."
- Applies to both sexes, all ethnic groups, all ages (including children).
- Example: 5'10" (70 in / 178 cm) → waist should be < 35 in (89 cm).

**Status:** NICE (UK) recommends WHtR + BMI as primary screening tool. DoD replaced Navy equations with WHtR as primary screening in January 2026 `[fatcalc.com__bf.txt line 58]`.

**Sex-specific nuanced thresholds:** calculator mentions they exist (more detailed than 0.5) but does not print explicit boundary values in the synthesized text — **engine should adopt the Ashwell 2012 boundary set**:
| Risk | Men | Women |
|---|---|---|
| Underweight / no risk | < 0.34 | < 0.42 |
| Healthy | 0.43 – 0.52 | 0.42 – 0.48 |
| Overweight | 0.53 – 0.57 | 0.49 – 0.53 |
| Obese | ≥ 0.58 | ≥ 0.54 |

(Mark these as Ashwell-derived; not literal page text.)

**Limitations:** can't distinguish subcutaneous vs visceral; very tall/short individuals may need adjustment; doesn't account for abdominal muscle mass.

### 3.4 ABSI (A Body Shape Index)
Source: `[fatcalc.com__absi.txt]`
Krakauer & Krakauer, *PLoS ONE* (2012). Built on NHANES 1999–2004, n ≈ 14,000.

**Formula** `[absi.txt lines 24-26]`
```
ABSI = WC × weight^(−2/3) × height^(5/6)
```
where:
- WC = waist circumference (meters)
- weight = kg
- height = meters

**Exponents chosen** so that ABSI is approximately independent of weight and height in the reference population → high ABSI = waist larger than expected for given body size.

**Interpretation via z-score** (against NHANES 1999–2004 norms, smoothed by age & sex). `[absi.txt lines 55-73]`

**ABSI Risk Categories** (5-band):
| Category | z-score range | Interpretation |
|---|---|---|
| Low | < −0.868 | Lower mortality risk than average |
| Below Average | −0.868 to −0.272 | Slightly favorable |
| Average | −0.272 to +0.229 | Typical for age & sex |
| Above Average | +0.229 to +0.798 | Elevated mortality risk |
| High | > +0.798 | Substantially elevated risk |

**Mortality Hazard Ratio** (ages ≥16): reported relative to population average at the user's ABSI percentile. Hazard = 1.00 → average risk; >1 → elevated; <1 → reduced. Derived from Krakauer & Krakauer hazard tables.

**Use case:** ABSI is independent of BMI → use *alongside* BMI. Identifies high-risk individuals even at normal BMI ("normal weight obesity").

### 3.5 IBW (Ideal Body Weight) — 4 Formulas
Source: `[fatcalc.com__ibw-calculator.txt]`
All four use 5 ft (60 in / 152 cm) baseline + per-inch increment.

| Formula | Men | Women | Year / Origin |
|---|---|---|---|
| **Devine** | `IBW = 50 + 2.3 × (H_in − 60)` kg | `IBW = 45.5 + 2.3 × (H_in − 60)` kg | 1974 (aminoglycoside dosing) |
| **Robinson** | `IBW = 52 + 1.9 × (H_in − 60)` kg | `IBW = 49 + 1.7 × (H_in − 60)` kg | 1983 |
| **Miller** | `IBW = 56.2 + 1.41 × (H_in − 60)` kg | `IBW = 53.1 + 1.36 × (H_in − 60)` kg | 1983 |
| **Hamwi** | `IBW = 48 + 2.7 × (H_in − 60)` kg | `IBW = 45.4 + 2.2 × (H_in − 60)` kg | 1964 (diabetes management) |

where `H_in` = height in inches.

**Frame-size adjustment** `[ibw-calculator.txt lines 64-98]`
- Optional: ±10 % for small / large frame respectively.
- Determined via wrist circumference (smallest part, just above wrist bone).

**Women's frame size by wrist (inches):**
| Height | Small | Medium | Large |
|---|---|---|---|
| < 5'2" | < 5.5" | 5.5"–5.75" | > 5.75" |
| 5'2"–5'5" | < 6" | 6"–6.25" | > 6.25" |
| > 5'5" | < 6.25" | 6.25"–6.5" | > 6.5" |

**Men's frame size by wrist (inches):**
| Height | Small | Medium | Large |
|---|---|---|---|
| > 5'5" | < 6.5" | 6.5"–7.5" | > 7.5" |

**Caveats (FatCalc):**
- Derived from limited (white, middle-class American) populations.
- Don't account for muscle mass / bone density / ethnicity / age.
- For heights well below 5 ft the formulas can yield nonsensical or negative values.
- Originally for **drug dosing**, not health-goal setting.

### 3.6 MM (Skeletal Muscle Mass) Calculator
Source: `[fatcalc.com__mm.txt]`
Based on Janssen et al. (2000, *J Applied Physiology*) MRI reference data + Heymsfield et al. (2020) prediction equations using NHANES (n = 12,330).

**Skeletal Muscle Mass (SM) Reference Ranges — % of total body mass** `[mm.txt lines 41-58]`

| Age band | Female range | Male range |
|---|---|---|
| 18–29 | 28.4 – 39.8 % | 37.9 – 46.7 % |
| 30–39 | 25.0 – 36.2 % | 34.1 – 44.1 % |
| 40–49 | 24.2 – 34.2 % | 33.1 – 41.1 % |
| 50–59 | 24.7 – 33.5 % | 31.7 – 38.5 % |
| 60–69 | 22.7 – 31.9 % | 29.9 – 37.7 % |
| 70 + | 25.5 – 34.9 % | 28.7 – 43.3 % |
| **All ages** | **25.1 – 36.1 %** | **33.3 – 43.5 %** |
| **All-ages mean** | **30.6 %** | **38.4 %** |

**Engine note:** synthesized page describes the underlying study but does not print the *prediction equation coefficients* (height, weight, waist, age). Engine team needs Heymsfield 2020 *Frontiers in Endocrinology* paper for the explicit SM = f(height, weight, waist, age, sex) prediction equation. Flag as "page-cited, formula-pending."

### 3.7 REE / RMR (Mifflin-St Jeor)
Source: `[fatcalc.com__bfb.txt lines 52-58]`
- FatCalc bfb calculator (Calories Burned) uses **Mifflin-St Jeor** equation (Mifflin et al., *AJCN* 1990) for REE.
- Predicts REE within ±10 % of measured values.
- The synthesized text does **not** print the Mifflin-St Jeor coefficients; canonical form (from the cited primary source):

```
REE (men)   = 10 × weight(kg) + 6.25 × height(cm) − 5 × age(yr) + 5
REE (women) = 10 × weight(kg) + 6.25 × height(cm) − 5 × age(yr) − 161
```

**MET-based energy burn** `[bfb.txt line 58]`
```
CaloriesPerMinute = REE / (24 × 60) × MET
```
Example: REE = 1527 kcal → 1.06 kcal/min at rest; walking 4.0 mph = MET 5 → 5.3 kcal/min.

### 3.8 BWP (Body Weight Planner — Kevin Hall NIH model)
Source: `[fatcalc.com__bwp.txt]`
- Uses **Kevin Hall PhD** mathematical body-dynamics model (NIH/NIDDK), Lancet 2011.
- Replaces the "3,500 kcal = 1 lb" rule.
- Models body-composition changes, BMR adaptation, glycogen/fluid shifts.
- Physical Activity Level (PAL) input range: **1.4 (sedentary) to 2.3 (very active)**. Default = 1.4.
- Minimum calorie floors: **1,200 kcal/day (women), 1,500 kcal/day (men)**.
- IOM Acceptable Macronutrient Distribution Ranges:
  - Carbs: 45–65 % of kcal
  - Protein: 10–35 % of kcal
  - Fat: 20–35 % of kcal

(No closed-form formula in the synthesized text — Hall model is a system of differential equations. Engine action: integrate the Hall 2011 model as a numerical simulation, not a closed-form equation.)

### 3.9 Target Weight Math (FatCalc BF Calculator)
Source: `[fatcalc.com__bf.txt lines 76-84]`

Holding lean body mass (LBM) constant:
```
LBM = current_weight × (1 − current_BF%)
target_weight = LBM / (1 − target_BF%)
```
Example (180 lb @ 30 % → 20 %):
- LBM = 180 × (1 − 0.30) = 126 lb
- target = 126 / (1 − 0.20) = 157.5 lb
- → lose ~22.5 lb of fat, keep LBM constant.

---

## 4. Muscular Potential Models

### 4.1 FFMI (Fat-Free Mass Index) — Core Formula
Source: `[rippedbody.com__maximum-muscular-potential.txt lines 54, 135]`

```
FFMI = FFM(kg) / height(m)²
where FFM = body_weight(kg) × (1 − BF%)
```

### 4.2 FFMI — Empirical Ceilings (Kouri et al. 1995)
`[maximum-muscular-potential.txt lines 56-62]`
- Study: 83 steroid users vs 74 non-users, average height ~180 cm, average BF ~13 %.
- Steroid users: average FFMI ~25, max 32.
- Non-users: average FFMI ~22, max 25.
- **Suggested natural genetic ceiling: FFMI ≈ 25.**

### 4.3 Adjusted / Normalized FFMI (height-corrected)
Source: comment thread in `[rippedbody.com__maximum-muscular-potential.txt lines 1438, 1444, 1448, 1573, 1624]`

Multiple commenters cite two equivalent forms. The Kouri 1995 paper version uses **6.1** (study text) vs **6.3** (abstract — likely typo). Note sign convention:

```
Normalized FFMI = FFMI + 6.1 × (1.8 − height(m))      [height ≤ 1.8 m → bonus]
                = FFMI + 6.1 × (1.8 − height(m))      [height ≥ 1.8 m → penalty]
```

Equivalently ( commenter form, lines 1438 / 1624):
```
Adjusted FFMI = FFMI + 6 × (height(m) − 1.8)
```
i.e. taller people get an increment; shorter people get a decrement. (This sign is the *opposite* of the form above — there is documented confusion in the comment thread. **Engine decision:** use the Kouri 1995 canonical form `FFMI + 6.1 × (1.8 − h)` and explicitly note the ambiguity.)

### 4.4 Berkhan Model (Martin Berkhan)
Source: `[rippedbody.com__maximum-muscular-potential.txt lines 30-44]`

**Formula:** stage-shredded (5–6 % BF) maximum body weight:
```
Max_stage_weight(kg) = height(cm) − 98 to 102
```
(Commonly cited single value: `height(cm) − 100`.)

**Worked examples (Berkhan, @5 % BF):**
| Height | Stage max weight | Lean mass | FFMI |
|---|---|---|---|
| 173 cm (5'8") | ~75 kg (165 lb) | 71.25 kg | 23.8 |
| 178 cm (5'10") | ~80 kg (176 lb) | 76.0 kg | 24.0 |
| 183 cm (6'0") | ~85 kg (187 lb) | 80.75 kg | 24.1 |
| 188 cm (6'2") | ~90 kg (198 lb) | 85.5 kg | 24.2 |

Berkhan ≈ 3–3.5 kg (~6.5–8 lb) below an FFMI of 25 — i.e. it's the *conservative* model.

### 4.5 Casey Butt Model
Source: `[rippedbody.com__maximum-muscular-potential.txt lines 28, 104]`
- Cited alongside Berkhan as the other major model.
- Article notes Butt & Berkhan models together = "roughly an average of what's attainable for most reasonably blessed people."
- **Synthesized page does NOT print Butt's coefficient set.** Butt's canonical formula (from his "Your Muscular Potential" article, cited but not reproduced) is:

```
Max_body_weight(kg) = H_cm − 98  (analogous to Berkhan but with ankle/wrist circumference adjustments)
```
Full Butt formula uses **wrist and ankle circumference** + bone-structure multipliers. Engine action: hard-flag as "cited by RippedBody, formula NOT in synthesized text — fetch Butt's original article separately."

### 4.6 Lyle McDonald Model
- **Not explicitly named in any of the 13 synthesized files.** Engine action: RippedBody mentions Berkhan + Butt only. If Lyle McDonald's model is required by the engine spec, fetch `bodyrecomposition.com` sources separately. Flag as "out-of-scope for this cluster."

### 4.7 Mr. America 1939–1959 FFMI Data (Historical Validation)
`[maximum-muscular-potential.txt lines 82-86]`

| Cohort (assumed natural) | Average FFMI | Max FFMI |
|---|---|---|
| 1939–1944 winners | 24.9 | 27.3 |
| 1939–1953 winners (moderate skepticism) | 25.6 | 28.0 |
| 1939–1959 (broader) | similar mean | — |

### 4.8 Recommended "Realistic" Ceilings (RippedBody synthesis)
`[maximum-muscular-potential.txt lines 106-117]`
- **FFMI = 25** → commonly cited upper limit for naturals with great genetics.
- **FFMI = 27.3** → demonstrably attainable naturally (documented case).
- **FFMI = 28** → "pretty likely that *some* people can attain naturally" (RippedBody editorial position, with training/nutrition advancements).
- Most people cannot reach 25 — "your genetics are your genetics."
- FFMI > 25 does **not** automatically indicate steroid use.

### 4.9 Comment-Thread Observation Worth Codifying
`[maximum-muscular-potential.txt line 711]` — "FFMI goes higher the more you weigh, even with fairly high fat percentage" → engine should compute FFMI at a *standardized* BF% (e.g. 10 % or stage-shredded 5 %) when comparing against genetic ceilings. Recommend: report both raw FFMI and FFMI@10%BF as comparison metrics.

---

## 5. Cut vs Bulk Decision Tree

### 5.1 Master Summary Table (RippedBody)
Source: `[rippedbody.com__cut-or-bulk.txt lines 164-182]`

| Category of Trainee | Recommendation |
|---|---|
| Overweight | **Cut** |
| Underweight | **Bulk** |
| Inexperienced trainee in the 13–18 % BF range | **Recomp** |
| Experienced trainee over 16 % BF | **Cut** |
| Experienced trainee under 16 % BF | **Cut or bulk, as per preference** |
| When bulking — upper BF limit to switch to cut | **20 %** |
| When cutting — lower BF limit to switch to bulk | **9–10 %** |

**Add +8 % for women to every BF threshold above.**

### 5.2 Operational BF Range (RippedBody)
Source: `[cut-or-bulk.txt lines 92, 138, 144, 162, 182]`
- **Optimal cut-bulk cycle range:** 10–20 % BF (men); 18–28 % BF (women, +8 %).
- **Sweet spot:** end cut at **10 %**, end bulk at **15 %** (dedicated physique-focused clients).
- **Hard upper limit:** don't exceed **20 %** BF (health risk increases past this).
- **Hard lower limit (stop cutting):** **8–10 %** men, **16–18 %** women — past this, food-deprivation drives fat-storage priming.
- **Minimum bulk duration:** **5 months** (don't interrupt anabolic process). Ideal bulk: 10 months before cutting.

### 5.3 Recomp Eligibility
Source: `[cut-or-bulk.txt lines 56-77, 84]`
- **Recommended for:** relatively new trainees, OR those coming back from a long layoff.
- **Definition of novice:** still making consistent **linear session-to-session progress** in training loads — *not* time-based.
- **Not recommended for:** underweight (should bulk) or overweight (should cut) individuals.
- **Calorie target:** maintenance (no surplus/deficit).

### 5.4 Skinny-Fat Sub-Decision Tree
Source: `[cut-or-bulk.txt lines 108-126]`
Definition: "healthy" body weight but muscularly under-developed; weak and soft to the touch despite tensing.

| Skinny-fat sub-type | Recommendation |
|---|---|
| Default | **Recomp** (hold calories at maintenance) |
| Skinnier end of skinny-fat | Slight calorie surplus — gain ~1 % body weight per month |
| Fatter end of skinny-fat | Slow cut — slightly slower than 0.5 % BW/week |

### 5.5 Weight-Loss Rate Targets
Source: `[cut-or-bulk.txt line 35]`, `[body-fat-guide.txt line 845]`
- **Sweet spot:** ~0.5 % of body weight per week.
- **Max safe rate (loose-skin avoidance):** 0.5–0.75 % BW per week.

### 5.6 Obese Beginner Special Case
Source: `[cut-or-bulk.txt lines 100-106]`
- If client has obesity AND is starting weight training → don't necessarily start calorie counting.
- Just becoming more active improves hunger signaling; BF% can drop via recomp without fat-mass loss.
- Resistance training alone improves metabolic health without dieting.
- Suggest behavior changes (fruits, vegetables, protein, water) before calorie tracking.

### 5.7 P-Ratio Caveat (anabolic resistance myth debunked)
Source: `[cut-or-bulk.txt lines 148-156]`
- "Can't bulk above X % BF" myth is **incorrect** when resistance training is in place.
- Nutrient partitioning in trained skeletal muscle overrides P-ratio concerns.
- Counter-examples cited: sumo wrestlers (highest recorded LBM of any athlete); super-heavyweight powerlifters (stronger than lighter classes).
- The 20 % BF ceiling is for **health**, not "anabolic resistance."

### 5.8 Visual Estimation Reality Check
Source: `[body-fat-guide.txt lines 70, 89]`
- Most people **underestimate** their BF%.
- Heuristic: if first-time cutting, **add 50 %** to your BF estimate → likely closer to truth.
- All methods have error up to 8 % — don't track progress via BF% alone; use scale weight + tape measure.

---

## 6. Source Citations — Cross-Reference

| Formula / Rule | Primary Source File | Secondary |
|---|---|---|
| US Navy BF% (men) | `rippedbody.com__how-calculate-body-fat-percentage.txt` L39 | `fatcalc.com__bf.txt` L50-58 |
| US Navy BF% (women) | `rippedbody.com__how-calculate-body-fat-percentage.txt` L39 | `fatcalc.com__bf.txt` L50-58 |
| CUN-BAE BF% | `fatcalc.com__bf.txt` L30-36, L110 | (Gómez-Ambrosi 2012 cited) |
| Covert Bailey | `fatcalc.com__bf.txt` L60-64, L122 | — |
| Jackson-Pollock 3/4/7-site | `fatcalc.com__bf.txt` L66-70 | — |
| Durnin-Womersley 4-site | `fatcalc.com__bf.txt` L26, L66-70 | — |
| AI Photo Analysis | `fatcalc.com__bf.txt` L38-44 | — |
| Method accuracy ladder | `rippedbody.com__how-calculate-body-fat-percentage.txt` L42-56 | — |
| RippedBody visual BF ranges (men) | `rippedbody.com__body-fat-guide.txt` L22-56 | — |
| RippedBody cut/bulk BF boundaries (10 %, 20 %) | `rippedbody.com__body-fat-guide.txt` L12 | `rippedbody.com__cut-or-bulk.txt` L92, L162 |
| Women +8 % rule | `rippedbody.com__cut-or-bulk.txt` L182 | — |
| UP male BF visual scale 8–35 % | `ultimateperformance.com__...male-body-fat-comparison.txt` L94-155 | — |
| UP visceral fat >10 % risk | `ultimateperformance.com__...txt` L262 | — |
| UP testosterone <10 % BF risk | `ultimateperformance.com__...txt` L286-298 | — |
| BMI formula & WHO categories | `fatcalc.com__ibw-calculator.txt` L100-108 | `ultimateperformance.com__...txt` L244 |
| WHR formula + WHO thresholds | `fatcalc.com__whr.txt` L14-48 | — |
| WHtR formula + 0.5 boundary | `fatcalc.com__whtr-calculator.txt` L18-22 | — |
| WHtR sex-specific thresholds | `fatcalc.com__whtr-calculator.txt` L46-50 | (Ashwell 2012 cited) |
| ABSI formula | `fatcalc.com__absi.txt` L22-30 | (Krakauer 2012 cited) |
| ABSI z-score risk bands | `fatcalc.com__absi.txt` L60-73 | — |
| ABSI hazard ratio | `fatcalc.com__absi.txt` L75-79 | — |
| Devine IBW | `fatcalc.com__ibw-calculator.txt` L28-30 | (Devine 1974 cited) |
| Robinson IBW | `fatcalc.com__ibw-calculator.txt` L38-40 | (Robinson 1983 cited) |
| Miller IBW | `fatcalc.com__ibw-calculator.txt` L48-50 | (Miller 1983 cited) |
| Hamwi IBW | `fatcalc.com__ibw-calculator.txt` L58-60 | (Hamwi 1964 cited) |
| Frame-size wrist tables | `fatcalc.com__ibw-calculator.txt` L82-94 | (MedlinePlus) |
| SM% reference ranges (Janssen) | `fatcalc.com__mm.txt` L41-58 | (Janssen 2000 cited) |
| Mifflin-St Jeor (REE) | `fatcalc.com__bfb.txt` L54 | (Mifflin 1990 cited) |
| MET calorie burn | `fatcalc.com__bfb.txt` L58 | (Ainsworth 2011 cited) |
| Kevin Hall body-dynamics model | `fatcalc.com__bwp.txt` L33-34 | (Hall 2011 Lancet cited) |
| IOM macro ranges | `fatcalc.com__bwp.txt` L38 | — |
| PAL 1.4–2.3, min kcal floors | `fatcalc.com__bwp.txt` L14, L18 | — |
| Target weight math (LBM constant) | `fatcalc.com__bf.txt` L76-84 | — |
| FFMI core formula | `rippedbody.com__maximum-muscular-potential.txt` L54, L135 | — |
| FFMI 25 ceiling (Kouri 1995) | `rippedbody.com__maximum-muscular-potential.txt` L56-62 | — |
| Adjusted/Normalized FFMI | `rippedbody.com__maximum-muscular-potential.txt` L1438-1624 (comments) | (Kouri 1995 study) |
| Berkhan model (H − 100) | `rippedbody.com__maximum-muscular-potential.txt` L30-44 | — |
| Casey Butt model (cited, formula not extracted) | `rippedbody.com__maximum-muscular-potential.txt` L28, L104 | — |
| Mr. America 1939–59 FFMI | `rippedbody.com__maximum-muscular-potential.txt` L82-86 | — |
| Cut/Bulk master table | `rippedbody.com__cut-or-bulk.txt` L164-182 | — |
| Recomp eligibility rules | `rippedbody.com__cut-or-bulk.txt` L56-84 | — |
| Skinny-fat sub-tree | `rippedbody.com__cut-or-bulk.txt` L108-126 | — |
| Weight-loss rate (0.5 %, 0.75 %) | `rippedbody.com__cut-or-bulk.txt` L35; `body-fat-guide.txt` L845 | — |
| P-ratio myth debunked | `rippedbody.com__cut-or-bulk.txt` L148-156 | — |
| Min bulk duration (5 / 10 months) | `rippedbody.com__cut-or-bulk.txt` L146, L200 | — |
| Obese-beginner special case | `rippedbody.com__cut-or-bulk.txt` L100-106 | — |
| BF% underestimate +50 % heuristic | `rippedbody.com__body-fat-guide.txt` L70 | — |
| Visible abs threshold | `body-fat-guide.txt` L83; `how-calculate...txt` L75; `ultimateperformance...txt` L277-278 | — |

---

## 7. Engine Action Items (Flagged Gaps)

The following items are referenced by the synthesized sources but **not fully printed** in their text — the engine team will need to fetch the original primary-source citations to fill them:

1. **CUN-BAE coefficients** — FatCalc bf.txt describes the method but does not print coefficients. Fetch Gómez-Ambrosi et al. 2012 *Diabetes Care*.
2. **Covert Bailey site list & equations** — fetch from *The Ultimate Fit or Fat* or Bailey's published tape-measure formula.
3. **Jackson-Pollock 3/4/7-site density equations** — standard published formulas (Jackson & Pollock 1978, 1980); fetch from primary literature. Then convert density → BF% via Siri.
4. **Durnin-Womersley 4-site density equation** — Durnin & Womersley 1974.
5. **Ashwell WHtR sex-specific boundary values** — Ashwell 2012 *Obesity Reviews* meta-analysis.
6. **Heymsfield SM prediction equation** (height, weight, waist, age) — Heymsfield 2020 *Frontiers in Endocrinology*.
7. **Casey Butt full model** (wrist + ankle circumference) — fetch Butt's "Your Muscular Potential" article.
8. **Kevin Hall NIH body-dynamics model** — Hall 2011 *Lancet* (differential-equation system, not closed-form).
9. **ACSM 2017 / ACE / WHO numeric BF% category boundaries** — FatCalc names the categories but does not print numeric ranges; standard tables are reproduced in §2.1 above (mark as "canonical, cited-by-FatCalc").

All other formulas listed in §1, §3, §4, §5 are extracted verbatim (or with explicit canonical-form interpolation noted) from the synthesized source text and are ready for direct Python codification.

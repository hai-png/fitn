# Fitness Engine — Work Log

Project: Build a Python fitness engine that (1) assesses a user's profile,
(2) proposes a complete fitness path: nutrition + training + meal plan.

Scope locked with user:
- Tech: Python 3.11 library (pure functions, no I/O framework)
- Phase 1: Full engine (assessment + nutrition + training + meal plan)
- Input depth: Standard (age/sex/height/weight/activity/goal + BF% + measurements + training experience + schedule)
- Reference doc: Markdown
- Interface: Library only (no CLI / REST in Phase 1)
- Population: General healthy adults 18–65, omnivore
- Note: User will provide detailed exercise & meal resources LATER — training & meal modules must be framework-ready / extensible.

Source resources: 50+ URLs spanning RippedBody, MacroFactor, GymGeek, Zolthealth, GymCreek, FatCalc.

---
Task ID: 1
Agent: main
Task: Initialize project structure and worklog

Work Log:
- Created directory tree under /home/z/my-project/
- Created worklog file
- Locked user requirements (above)

Stage Summary:
- Project skeleton ready: scripts/, download/, fitness_engine/{models,assessment,nutrition,training,meal_plan,utils,tests}/, resources/{raw,synthesized}/
- Next: fetch all source URLs in parallel via web-reader skill

---
Task ID: 2-B
Agent: cluster-B-analyzer
Task: Extract every formula, threshold, decision rule, and methodology from 16 nutrition/macro source files (RippedBody + FatCalc) for codification into the Python fitness engine.

Files analyzed (16):
- rippedbody.com__nutrition-pyramid-overview.txt
- rippedbody.com__calories.txt
- rippedbody.com__macro-calculator.txt
- rippedbody.com__best-macro-ratio.txt
- rippedbody.com__how-to-count-macros.txt
- rippedbody.com__how-to-adjust-macros.txt
- rippedbody.com__how-to-adjust-macros-bulk.txt
- rippedbody.com__micros.txt
- rippedbody.com__before-you-count.txt
- rippedbody.com__keto.txt
- rippedbody.com__advice-for-vegans.txt
- fatcalc.com__macro.txt
- fatcalc.com__protein-calculator.txt
- fatcalc.com__hydration-calculator.txt
- fatcalc.com__rmr-calculator.txt
- fatcalc.com__tdee-calculator.txt

Work Log:
- Read worklog and confirmed project context (Python 3.11 fitness engine, Phase 1 full engine).
- Read all 5 FatCalc files completely (smaller, calculator-focused, formula-dense).
- Read RippedBody keto.txt, advice-for-vegans.txt, how-to-adjust-macros-bulk.txt completely (smaller).
- Used Grep to extract formula/threshold lines from large RippedBody files (calories, macro-calculator, best-macro-ratio, how-to-count-macros, how-to-adjust-macros, micros, before-you-count, nutrition-pyramid-overview); verified context with targeted Read calls.
- Compiled findings into structured Markdown report at /home/z/my-project/resources/analysis/cluster-B-nutrition-analysis.md (14 sections, ~600 lines).
- All claims attributed to source files via [filename.txt] bracket notation for traceability.

Stage Summary:
- Comprehensive extraction complete. Report covers:
  1. RMR/BMR formulas — Mifflin-St Jeor (FatCalc default), Harris-Benedict original 1919 (RippedBody default) + revised 1984, Cunningham/Katch-McArdle (LBM-based), Jackson BMI→BF% equations, McMurray population RMR reference values (kcal/kg/hr by age/sex/BMI).
  2. TDEE & activity factors — RippedBody 4-category (1.15/1.35/1.55/1.75) and 5-category (1.25/1.45/1.65/1.85/2.05) tables; FatCalc IOM DLW/EER alternative.
  3. Calorie targets — Cut: TDCI = TDEE − (BW × 0.0075 × 500) with 0.5–1% weekly rate range; Bulk: TDCI = TDEE + (BW × monthly_rate × 150) with tier-based rates (beginner 2% → advanced ≤0.5%); Maintenance/Recomp = TDEE; 3,500 kcal/lb fat, 2,500 kcal/lb muscle.
  4. Protein — RippedBody LBM-based (1.14 g/lb cut, 1.0 g/lb bulk-recomp) when BF% known; body-weight based (1.0 g/lb target cut, 0.73 g/lb bulk-recomp) when unknown; obese → 1 g/cm height; vegan-adjusted higher (1.0/1.2 g/lb); FatCalc activity tiers 0.8–2.2 g/kg + goal modifiers (+0.2 build, +0.3 lose, +0.1 endurance) + age >65 min 1.0–1.2 g/kg + pregnancy/breastfeeding +25 g.
  5. Fat — 15–25% cutting, 20–30% maintenance/bulk; absolute floor 40–60 g/day (or 0.25 g/lb); saturated <10% ceiling; 11 diet presets from FatCalc.
  6. Carbs — Fill-the-remainder rule; 2:1 carb:fat calorie slider ratio (40 g carb + 10 g fat per 250 kcal); keto ≤50 g/day; simplified counting rules (rice 70 g/100 g, etc.); fiber 14 g/1,000 kcal; alcohol = 7 kcal/g.
  7. Hydration — FatCalc multi-step: 30 mL/kg base + 300 mL male + sweat rate (300/500/800 mL/h by intensity) × climate (0.95/1.0/1.3/1.4) + 300 mL pregnant + 700 mL breastfeeding; EFSA 2.0/2.5 L, NAM 2.7/3.7 L.
  8. Micronutrients — Fat-soluble vs water-soluble; deficiency consequences (zinc/iron/calcium); fruit/veg table (2/3/4 cups by calorie tier); vegan supplement table (B12, iron, zinc, calcium, omega-3, D3, creatine) with sex-specific doses.
  9. Nutrition pyramid — #1 Calories → #2 Macros → #3 Micros → #4 Nutrient Timing → #5 Supplements; "10 Big Wins" pre-counting strategies.
  10. Macro adjustment — Cut: 5–8% reduction (~100–200 kcal); Bulk: ~5% increase (~150–200 kcal); weekly cut adjustments = delta_lb × 500; monthly bulk adjustments = delta_lb × 150; 4-week minimum data window; sudden stall = water (wait), gradual slowdown = real (adjust); whoosh phenomenon; reverse diet = use tracking data not calculator.
  11. Keto — ≤50 g carbs, ≥60% fat, 20–25% protein; 1–4 wk adaptation; 4-month systematic testing protocol (40% fat month vs 20% fat month, repeated); entry criteria (insulin resistance, PCOS, oligomenorrhea).
  12. Vegan — 70:30 pea:rice protein blend; 1.0/1.2 g/lb (not dieting/dieting); 15–25% fat with 0.25 g/lb floor; 7-nutrient supplement protocol.
  13. Source citations master index.
  14. Codification notes — Python pseudocode for formula selection logic, calorie decision tree, protein/fat/carb decision trees, hydration function, macro adjustment & redistribution functions, micronutrient targets; flagged open items (MacroFactor BMR coefficients and IOM EER coefficients not explicitly given in source files).
- Next: hand off to nutrition module implementer for Python codification.

---
Task ID: 2-D
Agent: cluster-D-analyzer
Task: Extract every formula, threshold, decision rule and methodology from 9 calculator/adaptive-TDEE source files for codification into the Python nutrition engine.

Files analyzed (all in resources/synthesized/):
1. macrofactor.com__cutting-calculator.txt
2. macrofactor.com__bulk-or-cut.txt
3. macrofactor.com__bulking-calculator.txt
4. gymgeek.com__calculators-maintenance-calories-calculator.txt
5. gymgeek.com__calculators-calorie-calculator.txt
6. gymgeek.com__calculators-adaptive-tdee-calculator.txt
7. gymgeek.com__calculators-bulking-calculator.txt
8. gymcreek.com__adaptive-tdee-calculator.txt
9. zolthealth.com__learn-what-is-adaptive-tdee.txt

Work Log:
- Read worklog.md for project context (Python 3.11, pure functions, no I/O, 18–65 omnivore adults).
- Read all 9 source files; large calorie-calculator file paginated via offset/limit reads.
- Extracted and codified the following items into a structured Markdown report at /home/z/my-project/reports/task_2D_adaptive_tdee_calculator_analysis.md:
  * Adaptive TDEE definition, two algorithm families (first-principles vs statistical-model), why static formulas fail (10–15 % error band, 200–400 kcal inter-individual variation, 15–25 % metabolic adaptation).
  * First-principles observed-TDEE identity: observed_TDEE = avg_intake − (Δweight × 3500)/N (lb) or − (Δweight × 7700)/N (kg). Statistical model = w_data·observed + (1−w_data)·Mifflin-St Jeor prior; w_data grows from 0 at n≤7 days to ~1 at n≥60 days.
  * Mifflin-St Jeor BMR formulas (full 9.99/6.25/4.92 and simplified 10/6.25/5 variants for M/F); Katch-McArdle noted as BF%-aware alternative.
  * Harris-Benedict SAF table: 1.2 / 1.375 / 1.55 / 1.725 / 1.9 with definitions and per-sex TDEE ranges.
  * Cutting tier table (% BW/week × deficit %): Very Conservative 0.10 %/<5 %, Conservative 0.25 %/5–10 %, Moderate 0.5–0.75 %/10–20 %, Slightly Aggressive 1.00 %/20–30 %, Aggressive 1.50 %>30 %; 2 lb / 1 kg hard cap; 500 kcal/day muscle-preservation threshold (Murphy & Koehler 2021).
  * Bulking tier tables (% BW/week by Beginner/Intermediate/Experienced × Conservative/Happy Medium/Aggressive/Very Aggressive) plus absolute kg/week and lb/week caps; training-age definitions (strength gain rate).
  * Bulk-or-Cut decision: BF% thresholds (cut if M>25 %, F>35 %; conservative 20/30; tolerant 30/40); default = maintenance recomp; Forbes/leanness-better-for-muscle debunked.
  * Bulking macro rules: protein 1.6 g/kg (training) / 1.2 g/kg (sedentary); high-protein 1.8/1.6 g/kg; 35 % protein cap; 30 % fat default (down to floor 0.5 g/kg); carbs 45–65 % remainder; 4/9/4 kcal/g densities.
  * GymCreek fixed ladders: cut −250/−500/−750 kcal/day; bulk +250/+500 kcal/day; ±0 maintain/recomp.
  * Macro presets: Balanced 30P/40C/30F, High Protein 40/35/25, Low Carb 35/20/45, Keto 25/5/70, High Carb 25/55/20, Standard 50/30/20, Tailored 51/30/19.
  * Convergence rules: ≥10 entries for any adaptive value; ~4 weeks for spreadsheet; 1 week for statistical model; 1–2 months until user data dominates prior; re-evaluate every 4–6 weeks; review progress 3–4 weeks; 7-day rolling average weight; outlier detection + intelligent smoothing + rolling recalculation + data-quality indicators.
  * Constants: 3500 kcal/lb, 7700 kcal/kg, 4.184 kJ/kcal, thermic effect ~10 %, +10–12 kcal/lb muscle TDEE boost, 1200 kcal women / 1500 kcal men floor, VLCD <1200 (very-low <800) medical-only, healthy BMI 18.5–24.9, 18+ age limit, lb/kg and cm/in conversions.
- Section 10 of the report lists 16 suggested pure-function signatures ready to drop into fitness_engine/nutrition/.

Stage Summary:
- Deliverable: /home/z/my-project/reports/task_2D_adaptive_tdee_calculator_analysis.md (10 sections, every claim tagged with bracketed source filename).
- Every formula, threshold, decision rule and methodology across the 9 source files is now extracted and Python-codification-ready.
- Key finding: NO source publishes the exact adaptive-TDEE closed-form equation; the first-principles identity was reconstructed as the unique solution consistent with all four adaptive-TDEE sources (zolthealth explicitly references nSuns spreadsheet, gymgeek/zolthealth describe the statistical-model blend qualitatively).
- Next (main agent): consume this report + sibling cluster reports to implement fitness_engine/nutrition/{bmr,tdee,adaptive_tdee,cutting,bulking,bulk_or_cut,maintenance}.py as pure functions with unit tests in fitness_engine/tests/.

---
Task ID: 2-A
Agent: cluster-A-analyzer
Task: Extract every formula, threshold, decision rule, and methodology from 13 body-composition / assessment source files (RippedBody ×4, UltimatePerformance ×1, FatCalc ×8) for codification into the fitness-engine assessment module.

Work Log:
- Read worklog header for project context (Python 3.11 library, standard input depth, general healthy adults 18–65).
- Read all 13 source files from /home/z/my-project/resources/synthesized/.
- Extracted formulas (US Navy BF% M/F, CUN-BAE, BMI, WHR, WHtR, ABSI, FFMI, normalized FFMI, Berkhan H−100, Devine/Robinson/Miller/Hamwi IBW, target-weight math, Mifflin-St Jeor REE, MET calorie burn).
- Extracted thresholds & categories (ACE/ACSM/WHO BF% bands, RippedBody visual ranges, UP male 8–35% scale, WHO BMI, WHO WHR cut-offs, WHtR 0.5 universal boundary, ABSI 5-band z-score risk table, SM% reference ranges by age/sex, frame-size wrist tables).
- Extracted decision logic (RippedBody cut/bulk master table, recomp eligibility, skinny-fat sub-tree, obese-beginner special case, P-ratio myth, weight-loss rate targets, +8% women rule, 10%/20% cycle boundaries, 5–10 month minimum bulk duration).
- Documented FFMI ceilings (25 natural, 27.3 documented, 28 likely; Mr. America 1939-59 historical data; Berkhan FFMI 23.8–24.2 at 5% BF).
- Flagged 9 engine-action gaps where synthesized text references a formula but does not print coefficients (CUN-BAE, Covert Bailey, Jackson-Pollock, Durnin-Womersley, Ashwell WHtR, Heymsfield SM, Casey Butt full model, Kevin Hall differential-equation model, ACSM/ACE numeric BF bands).
- Wrote full structured Markdown report to /home/z/my-project/reports/task-2A-body-composition-analysis.md (7 sections, every item prefixed with [source-file] for traceability, ready for Python codification).

Stage Summary:
- Deliverable: /home/z/my-project/reports/task-2A-body-composition-analysis.md
- Coverage: 100% of formulas/thresholds/rules explicitly printed in the 13 synthesized sources; 9 cited-but-unprinted formulas flagged for primary-source fetch in a later task.
- Next: cluster-B analyzer can begin parallel extraction on nutrition / training / meal-plan sources; engine module can start scaffolding the assessment package with the formulas catalogued here.

---
Task ID: 2-C
Agent: cluster-C-analyzer
Task: Extract every formula, threshold, decision rule, and methodology from 13 goal-setting / progress-tracking / bulking / reverse-diet / recomp / fat-loss-rate source files (RippedBody ×7, FatCalc ×5, + 1 weight-fluctuations article) for codification into the Python fitness engine.

Files analyzed (all in /home/z/my-project/resources/synthesized/):
1. rippedbody.com__goal-setting-1.txt
2. rippedbody.com__goal-setting-2.txt
3. rippedbody.com__goal-setting-3.txt
4. rippedbody.com__diet-progress-tracking.txt
5. rippedbody.com__why-my-weight-going-up-and-down-while-dieting.txt
6. rippedbody.com__initial-adjustment.txt
7. rippedbody.com__training-plateaus.txt
8. rippedbody.com__how-to-bulk.txt
9. rippedbody.com__updated-bulking-guidelines.txt
10. fatcalc.com__reverse-diet-calculator.txt
11. fatcalc.com__body-recomp-calculator.txt
12. fatcalc.com__rwl.txt  (recommended weight loss rate)
13. fatcalc.com__mfl.txt  (maximum fat loss)

Work Log:
- Read worklog header for project context (Python 3.11 library, standard input depth, general healthy adults 18–65 omnivore).
- Read all 13 source files (5 small FatCalc + 8 RippedBody files; large files used Grep + paginated Read).
- Wrote structured Markdown report to /home/z/my-project/resources/analysis/task-2C-goal-setting-and-progress-tracking.md (10 sections + 2 appendices, every claim prefixed with [source-file] for traceability, all formulas expressed Python-ready).
- Extracted and codified:
  * Goal-setting framework: 9-category RippedBody trainee taxonomy; cut/bulk/recomp/maintenance/reverse-diet goals; cut-bulk cycle boundaries (10–20% BF men; bulk start only <15%, cap at 20%, don't cut <10% before bulking; purgatory 9–15%).
  * Muscle-growth potential tables: Beginner 1.0–1.5% BW/mo, Novice 0.75–1.25%, Intermediate 0.5–0.75%, Advanced <0.5%; McDonald model (men kg/mo + women 50%); beginner surplus ~200–300 kcal/d, intermediate ~100–200, advanced slight.
  * Time-horizon: 3500-kcal rule refuted → Hall model (Lancet 2011); calorie floors 1200 W / 1500 M.
  * Body recomp: eligibility by BF% (M: >25% excellent, 15–25% good, <15% limited; F: >35% / 25–35% / <25%); calorie deficit by potential (excellent 10–20%, good 0–10%, limited → bulk/cut); protein 1.8–2.4 g/kg recomp; FFMI formulas.
  * Skinny-fat recomp specifics: 12–23% BF scaling 0–1 lb/wk; calipers useful ≤15% BF; exit to purgatory.
  * Bulking protocol: three methods (relaxed/lean/controlled); updated controlled-bulk rates by training status (2/1.5/1/0.5% BW/mo); surplus math (2500 kcal/lb muscle + 3500 kcal/lb fat; 1:1 ratio → 100 kcal/d per lb/mo; +50% NEAT buffer → 150 kcal/d per lb/mo or 330 per kg/mo); macro ratio 3:1 carb:fat when bulking; fat 20–30% of total kcal; minimum bulk duration 5–6 months; 5-week adjustment cycle; ±150 kcal/d per lb/mo deviation; 20% BF cap.
  * Cutting protocol: rate-by-BF% table (0.5–2 lb/wk); 0.5–1% BW/wk typical; fat-but-muscled 1–1.25 lb/wk; muscled-few-pounds 0.75–1.25 lb/wk; fat-and-weak 1.25–1.5 lb/wk (3–5 lb/mo net); obese cap 2 lb/wk.
  * Maximum fat loss formula (Alpert, corrected): **max_daily_deficit_kcal = body_fat_lb × 22** (original was 31); weekly max = (FM_lb × 22 × 7) / 3500; decision rule: consuming less than TDEE − max_daily_deficit forces muscle breakdown.
  * Cut adjustment formula: daily_kcal_delta = (actual_lb_per_wk − target_lb_per_wk) × 500; cut macro ratio 1:1 to 2:1 carb:fat; round to nearest 5 g.
  * Reverse diet: 3 presets (+50/+100/+150 kcal/wk → conservative/moderate/aggressive with 12–20/6–10/4–7 wk typical duration); protein 1.6 (maintain) or 2.2 (build) g/kg; slowdown if weekly gain >0.5% BW; metabolic adaptation 5–15%. Andy Morgan's counterpoint: skip reverse diet, jump straight to maintenance.
  * Progress tracking: 8 RippedBody methods (daily weight + weekly avg; 9-site weekly measurements to 0.1 cm; monthly photos; calorie adherence % = weekly_kcal_consumed / weekly_kcal_target × 100; training adherence %; sleep/stress/hunger/fatigue 0–5; key-lifts 2-week notes; detailed training log). 3 methods to avoid (BF% tools, activity trackers, mirror). 4-week trend minimum. Assessment every 2 weeks. Adherence red flag <85%.
  * Plateau detection: 7-step RippedBody troubleshooting flowchart (sleep → calories → protein → RPE → frequency → technique → joint pain); cut-stall pattern (1/3 progress / 1/3 maintain / 1/3 regress); ±20% volume adjustment.
  * Initial adjustment timing: cutting — ignore wks 1–2 (women wait 4 wks for menstrual phase); bulking — wait 6–7 weeks before adjusting; do not adjust more frequently than every 5 weeks when bulking.
  * Weight fluctuation causes: hydration, gut/bladder content, glycogen (with ~3 g water/g), salt, stress, menstrual cycle, sweat, respiration; magnitude up to ~5 lb initial dip/spike; whoosh effect 6–8 weeks; creatine water pull; women cycle-phase compare.
  * Python constants & functions appendix (constants block + 11 pure functions + 2 decision-tree sketches).
- All claims attributed via [filename.txt] bracket notation.

Stage Summary:
- Deliverable: /home/z/my-project/resources/analysis/task-2C-goal-setting-and-progress-tracking.md (10 sections + 2 appendices, every item source-tagged, Python-ready constants/functions/decision-trees).
- Coverage: 100% of formulas/thresholds/rules explicitly printed in the 13 synthesized sources. Key formula captured: corrected Alpert maximum-fat-loss = 22 kcal/lb fat/day (the core cutting-intensity cap).
- Next (main agent): consume this report alongside cluster-A/B/D reports to implement fitness_engine/{assessment, nutrition, training}/goal_setting.py, progress_tracking.py, plateau_detection.py, bulking.py, cutting.py, reverse_diet.py, recomp.py as pure functions with unit tests in fitness_engine/tests/.

---
Task ID: 2-E (final)
Agent: main
Task: Build Python fitness engine from synthesized analysis + deliver

Work Log:
- Created 4 analysis subagents in parallel (clusters A/B/C/D) — all completed and saved reports
- Synthesized 4 cluster reports (~163KB) into unified reference guide
- Built fitness_engine/ package with 5 submodules + models + utils + tests
  - models/: 5 files (profile, assessment, nutrition, training, meal)
  - assessment/: 5 files (body_composition, health_risk, muscular_potential, decision, assessor)
  - nutrition/: 8 files (rmr, tdee, calories, macros, hydration, micronutrients, adjustments, planner)
  - training/: 4 files (exercise_library, splits, progression, planner)
  - meal_plan/: 4 files (food_database, meal_templates, allocator, planner)
  - utils/: 2 files (units, __init__)
  - engine.py (top-level orchestrator)
  - tests/: 3 test files (test_assessment, test_nutrition, test_engine)
- Total: 39 Python files, ~6000 LOC
- Wrote 81 unit tests — ALL PASSING (0.25s)
- Built sample_runner.py — generates 4 demo plans (cut/bulk/recomp/maintenance) → /download/

Stage Summary:
- Engine is fully functional end-to-end:
    profile = UserProfile(...)
    assessment = assess_profile(profile)
    plan = propose_plan(profile, assessment)
- All formulas sourced from 50+ URLs with [source.txt] citations
- Training + meal plan modules are framework-ready for user's Phase-2 detailed resources
- Adaptive TDEE implemented (Bayesian blend + first-principles)
- Safety overrides (obese → cut regardless of goal; calorie floors; cut/bulk BF boundaries)
- Decision tree handles 9+ scenarios (cut/bulk/recomp/maintenance/habit-change-first/skinny-fat)
- 4 sample plans generated (143KB-173KB JSON each) showing full plan structure

Deliverables in /home/z/my-project/download/:
- fitness_engine_reference_guide.md (43KB, 18 sections)
- sample_plan_cut.json
- sample_plan_bulk.json
- sample_plan_recomp.json
- sample_plan_female_maintenance.json

Deliverables in /home/z/my-project/fitness_engine/:
- Complete Python library (39 files, 81 tests passing)
- Public API: from fitness_engine import UserProfile, assess_profile, propose_plan

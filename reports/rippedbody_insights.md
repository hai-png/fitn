# RippedBody Insights — Codified Rules for the Fitness Engine

**Source articles** (extracted plain text in `resources/synthesized/`):
1. `rippedbody.com__how-to-build-training-programs.txt` — "Guide To Program Building For Bodybuilding and Powerlifting" (Helms / Morgan / Valdez, 3rd ed., updated 2025-12-28). Cited below as **[PB]**.
2. `rippedbody.com__progression.txt` — "How to Make Progress With Your Training" (Andy Morgan, updated 2025-12-28). Cited below as **[PROG]**.

All bracketed quotes are verbatim from those files. Every rule below is followed by a `Codified:` line in plain English so it can be mapped directly to a code change.

Tables extracted: **7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 7.11, 7.12, 7.13, 7.14, 7.15 (flowchart), 7.16, 7.17, 7.18**, plus the **RIR table**, the **Linear Progression example table**, the **Novice & Intermediate Double Progression example tables**, and the **Reactive Deload Self-Assessment checklist**.

---

## 1. Program-Building Decision Order

### Rule 1.1 — The six-step pyramid order
> "Step 1: Adherence Step 2: Volume, Intensity, and Frequency Step 3: Progression Step 4: Exercise Selection Steps 5 and 6: Rest Periods and Tempo Warming Up Dual Athletes" **[PB]**

**Codified:** The architect MUST make decisions in this order:
1. **Adherence** → pick `training_days_per_week` first (driven by life schedule, not by physiology)
2. **V·I·F** → set volume, intensity, frequency together
3. **Progression** → choose scheme + rep-range-variation structure
4. **Exercise selection** → fill movement-pattern slots
5. **Rest periods**
6. **Tempo**
…then warm-up prescription layered on top.

> The current `architect.py` does not enforce this order explicitly. Decisions are entangled (volume is derived from the split, but RippedBody says frequency/split is decided first and volume is fit to it).

### Rule 1.2 — Adherence is non-negotiable; frequency is the first decision
> "Plan your workout frequency with adherence in mind… Choose a realistic number of training days that would not stress your life or schedule. This value can be anywhere from two or more days per week." **[PB]**

**Codified:** When the user is asked for `training_days_per_week`, the prompt must explain that *life schedule* — not optimization — is the right input. Two days is the floor; any value ≥2 is acceptable.

### Rule 1.3 — Three-day minimum to progress (advanced lifters)
> "at a certain point, it is challenging for most people to progress (although maintenance is certainly feasible) without training at least three times per week. For advanced lifters, a two-day schedule is rarely practical as the loads and volumes required make each workout a gruelling marathon." **[PB]**

**Codified:**
- If `training_status ∈ {INTERMEDIATE, ADVANCED}` and `training_days_per_week < 3` → emit a warning that progress will be hard / maintenance is the realistic outcome.
- If `training_status == ADVANCED` and `training_days_per_week == 2` → emit a stronger warning OR refuse to build a strength program.

---

## 2. Volume Landmarks (MRV / MAV / MEV / ML)

RippedBody does not use the MEV/MAV/MRV/ML vocabulary directly, but Tables 7.3 and 7.4 encode the same four tiers.

### Rule 2.1 — Four-tier volume model per muscle group (per week)
> **TABLE 7.3. VOLUME • INTENSITY • FREQUENCY SUMMARY OF STARTING RECOMMENDATIONS**
> Hypertrophy Volume: Minimum "4 sets/muscle/wk, increases w/training status." Maximum "~30 sets/muscle/wk." Practical "10–20 sets/muscle wk, Higher volume with specialization." **[PB]**

| Tier (mapped) | Hypertrophy sets/muscle/wk | Strength sets/lift/wk |
|---|---|---|
| MEV (Minimum Effective Volume) | 4 | 1 |
| MRV (Maximum Recoverable Volume) | ~30 (short-term) | ~5 (short-term) |
| Practical / MAV (Maximum Adaptive Volume) | 10–20 | 3–5 short-term, 5–10 long-term |

**Codified:**
- MEV_HYPERTROPHY = 4 sets/muscle/wk
- MRV_HYPERTROPHY = 30 sets/muscle/wk (hard ceiling; advanced only, short-term)
- MAV_HYPERTROPHY = 10–20 sets/muscle/wk (default range)
- MEV_STRENGTH = 1 set/lift/wk
- MRV_STRENGTH = 5 sets/lift/wk (short-term)
- MAV_STRENGTH = 3–5 short-term, 5–10 long-term

### Rule 2.2 — Volume tiers by time commitment (Table 7.4)
> **TABLE 7.4. HYPERTROPHY VOLUME TIERS BY TIME COMMITMENT, AVERAGE STIMULUS PER SET, AND TOTAL STIMULUS**

| Weekly Sets/Muscle | Time Commitment | Avg Stimulus/Set | Total Stimulus (% of max) |
|---|---|---|---|
| 4–8 | Minimal (~1–2.5 h) | Highest | Lowest (~25–45%) |
| 9–12 | Low (~3–4.5 h) | High | Modest (~45–60%) |
| 13–16 | Medium (~5–6.5 h) | Medium | Medium (~60–70%) |
| 17–20 | High (~7–8.5 h) | Low | High (~70–85%) |
| 21–30 | Very High (~9+ h) | Lowest | Highest (~85–100% if sustainable) |

**Codified:** Add a `VolumeTier` enum (`MINIMAL`, `LOW`, `MEDIUM`, `HIGH`, `VERY_HIGH`) with the set ranges above. Use it to (a) translate user time-budget into weekly sets, (b) warn if a beginner picks `VERY_HIGH`.

### Rule 2.3 — Volume tier is a *choice*, not a constant
> "For hypertrophy with minimal time, optimal might mean the lowest volume that still produces good returns. For a competitive bodybuilder, optimal might mean maximum achievable volume for the highest possible rate of muscle gain." **[PB]**

**Codified:** Volume should be a user-facing input (or derived from a time-budget question), not a hardcoded value per goal. Engine should ask "how much time can you train per week?" and map to a tier.

### Rule 2.4 — Maintenance volume ≈ ½ to ⅔ of growth volume
> "Based on what I saw during the pandemic with clients, you can probably get away with half of the training volume as long as your weight is stable (caloric maintenance) and your protein intake is kept high. Start with 2/3rds if you wish to be more prudent, and see if you can drop from there." **[PB comments]**

**Codified:** For `TrainingGoal.MAINTENANCE`, weekly sets/muscle = 0.5 × MAV (or 0.67 × MAV for a prudent start). The current `MAINTENANCE` preset in `periodization.py` does not reduce sets — it only changes rep ranges.

### Rule 2.5 — Fractional set counting (primary vs secondary)
> "For hypertrophy, sets count as 1 for primary muscle groups and 0.5 for secondary muscle groups. For strength, sets of the main lift count as 1 for that lift, and all other lifts that train any of the same muscles count as 0.5." **[PB]**
> "any movement that trains the same muscles as a main lift, but is not the main lift itself, adds 0.5 to your weekly frequency for that lift. For example, a squat session also contributes 0.5 to your weekly deadlift frequency, and vice versa." **[PB]**

**Codified:** When tallying weekly volume per muscle/lift, count:
- Hypertrophy: primary muscle = 1.0 set; secondary muscle = 0.5 set.
- Strength: main-lift sets = 1.0 toward that lift; any other lift sharing the same primary OR secondary muscle = 0.5 toward the main lift.

The exercise DB already has `muscle_groups` (primary) and `secondary_muscles`. Add a `count_sets_toward_muscle(exercise, muscle) -> float` helper.

### Rule 2.6 — 11-set per-muscle per-session cap
> "The main goal when designing your split is to avoid sessions becoming logistically impractical, overly fatiguing, demotivating, or exceeding roughly 11 sets per muscle group per session." **[PB]**
> "If performing >11 weekly sets per muscle group, increase frequency so no session exceeds 11 fractional sets per muscle group." **[PB, Table 7.3 footnote]**

**Codified:** Hard cap = 11 fractional sets per muscle group per session. If total weekly volume / current frequency > 11, the engine MUST either (a) raise frequency, or (b) switch to a split with more session types. The current engine has no such check.

---

## 3. Frequency Rules

### Rule 3.1 — Hypertrophy frequency is volume-driven (Table 7.6)
> **TABLE 7.6. FREQUENCY RECOMMENDATIONS BY VOLUME**

| Weekly Fractional Sets/Muscle | Weekly Frequency/Muscle |
|---|---|
| 4–10 | 1–2 |
| 11–20 | 2–3 |
| 21–30 | 3+ |

**Codified:** Frequency selector:
```
if weekly_sets_per_muscle <= 10:  freq = 1 or 2
elif weekly_sets_per_muscle <= 20: freq = 2 or 3
else:                              freq >= 3
```

### Rule 3.2 — Hypertrophy minimum frequency = 1×/muscle/wk
> **TABLE 7.5.** Hypertrophy: "≥1x/week per muscle group, based on volume. If you exceed ~11 fractional sets for a muscle in a session, increase frequency to distribute volume better." **[PB]**

**Codified:** Floor frequency for any hypertrophy program = 1×/muscle/wk. (Indirect fractional work from compounds may already satisfy this — see Rule 2.5.)

### Rule 3.3 — Strength frequency = 2–6×/lift/wk, spread thinly
> "Strength: 2–6x/lift/wk based on volume. Higher frequency provides some benefit. Spread sets over as many days as possible with 1–2 direct sets per main lift per session." **[PB, Table 7.3]**
> "ideally, you train each lift with a frequency of at least twice per week." **[PB]**

**Codified:**
- Strength floor = 2×/lift/wk (counting fractional overlap).
- Per-session cap on main-lift working sets = 1–2 direct sets.
- Maximum = 6×/lift/wk.

### Rule 3.4 — 90 % of lifters: 3–5 days/wk, 2–4× muscle frequency
> "For ~90% of lifters, train 3–5 days per week with a muscle/movement frequency of 2–4 times per week, as this typically strikes the best balance between stimulus and recovery." **[PB]**

**Codified:** Default recommendation engine: 3–5 days/wk, muscle freq 2–4×. If the user's choice falls outside this, show the "90% sweet spot" hint but allow override.

### Rule 3.5 — Squat and deadlift overlap counts 0.5 toward each other
> "a squat session also contributes 0.5 to your weekly deadlift frequency, and vice versa." **[PB]**
> "Anecdotally, most powerlifters find squats create less next-day discomfort and soreness than deadlifts, so our examples lean toward higher squat frequency." **[PB]**

**Codified:** When tallying strength frequency for S/B/D, treat S↔D as 0.5 overlap. Default to **higher squat frequency than deadlift** unless user opts to reverse.

---

## 4. Strength Frequency Matrix (Table 7.1)

> **TABLE 7.1. STRENGTH FREQUENCY MATRIX FOR CHOOSING SPLITS** — `S=Squat, B=Bench, D=Deadlift, "/" = same session, "," = day separator, NA = Not applicable` **[PB]**

| Days/Wk | 1.5–2 | 2 | 2–3 | 3–4 | 4–5 | 6 |
|---|---|---|---|---|---|---|
| **2** | S/B, B/D | S/B/D, S/B/D | NA | NA | NA | NA |
| **3** | S/B, B, D | NA | S/B, B/D, S/B | S/B/D, B, S/B/D, B | NA | NA |
| **4** | S, B, D, B | S/D, B, D/S, B | S/B, B, D, S/B | S/B, B/D, S/B, B/D | S/B/D, B/S, S/B/D, B/D | NA |
| **5** | S, B, D, B, Secondaries | S/D, B, D/S, B, Secondaries | S/B, B, D, S/B, Secondaries | S/B, B/D, S/B, B/D, Secondaries | S/B, B/D, S/B, B/D, S/B | NA |
| **6** | S, B, D, B, Sec, Sec | S/D, B, D/S, B, Sec, Sec | S, B, D, B, S, B | S, B, D, B, S/B, B/D | S/B/D, B, D, S/B, B/D, S/B | S/B/D, S/B, B/D, S/B/D, S/B, B/D |

**Codified:** New `STRENGTH_FREQUENCY_MATRIX` constant — a dict keyed by `(days_per_week, target_main_lift_freq)`. The architect uses the user's chosen frequency to pick a split configuration. This is materially richer than the current 8-split catalogue.

---

## 5. Hypertrophy Frequency Matrix (Table 7.2)

> **TABLE 7.2. HYPERTROPHY FREQUENCY MATRIX FOR CHOOSING SPLITS** — `NA = Not applicable` **[PB]**

| Days/Wk | 1–2 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| **2** | Upper, Lower OR Full Push, Full Pull | Full Body, Full Body | NA | NA | NA | NA |
| **3** | Lower, Upper Push, Upper Pull | Lower, Upper, Full Body OR Full Push, Full Pull, Full Body | Full Body, Full Body, Full Body | NA | NA | NA |
| **4** | Chest & Tris, Back & Bis, Shoulders, Lower | Lower, Upper, Lower, Upper OR Full Push, Full Pull, Full Push, Full Pull | Upper, Lower, Full Body, Full Body OR Full Push, Full Pull, Full Body, Full Body | Full Body, Full Body, Full Body, Full Body | NA | NA |
| **5** | Chest, Back, Lower, Shoulders, Arms | Lower, Upper Push, Upper Pull, Lower, Upper OR Lower, Upper Push, Upper Pull, Full Push, Full Pull | Lower, Upper Push, Upper Pull, Full, Full | Full Body, Full Body, Full Body, Upper, Lower OR Full Body, Full Body, Full Body, Full Push, Full Pull | Full Body, Full Body, Full Body, Full Body, Full Body | NA |
| **6** | Chest, Back, Quads & Calves, Shoulders, Arms, Glutes & Hams | Lower, Upper Push, Upper Pull, Lower, Upper Push, Upper Pull | Lower, Upper, Lower, Upper, Lower, Upper OR Full Push, Full Pull, Full Push, Full Pull, Full Push, Full Pull | Full Body, Full Body, Full Body, Lower, Upper Push, Upper Pull | Full Body, Full Body, Full Body, Full Body, Upper, Lower OR Full Body, Full Body, Full Body, Full Body, Full Push, Full Pull | Full Body, Full Body, Full Body, Full Body, Full Body, Full Body |

### Session-type descriptors (Table 7.2 footnotes)

| Session type | Best volume range | Notes |
|---|---|---|
| **Muscle Group** (1–2 muscles/session) | ~4–12 sets | Lower weekly frequency; high per-session volume. Less effective for higher weekly volumes unless combined with other types. |
| **Upper Push / Pull** | ~12–24 sets when 2×/wk | Chest+Tri+Ant Delt  /  Back+Bi+Rear Delt; pick one day for middle delts. |
| **Upper / Lower** | ~12–18 sets when 2×/wk | "Lower body sessions are disproportionately challenging." |
| **Full Body** | ~12–18 sets at 3+/wk | Strict FB limits per-session volume; can train consecutive days if RIR / length / selection are managed. |
| **Full Push / Full Pull** | wide range — low at 2×/wk, very high at 5+/wk | Non-strict FB: push day = quads+calves, pull day = glutes+hams. Good for consecutive-day training. |

**Codified:** New `HYPERTROPHY_FREQUENCY_MATRIX` dict keyed by `(days_per_week, target_muscle_freq)`. Each cell is a list of session-type labels. Session types map to volume caps per the table above. This **substantially expands** the current 8-split catalogue (which has full_body 2/3-day, upper_lower 4-day, ppl 3-day, ppl_x2 6-day, ppl_ul 5-day, body_part 5-day, push_pull 4-day). The current engine is missing: **muscle-group specialization days, full push/full pull hybrids, and the full-body-at-high-frequency options**.

### Rule 5.1 — Indirect work means true 1×/wk frequency is rare
> "Even when using classical bodybuilding splits, where you only train each muscle group once per week, because of indirect work producing fractional sets… few training splits provide a true weekly muscle group frequency of only one." **[PB]**

**Codified:** Don't refuse a bro-split on the grounds of "frequency = 1 is suboptimal" — the fractional overlap usually lifts it to 1.5–2. Just warn the user.

---

## 6. Intensity / RPE / RIR Rules

### Rule 6.1 — RIR-to-RPE conversion table
> **RIR and RIR-based RPE TABLE** **[PROG]**

| RIR | Meaning | RPE |
|---|---|---|
| 0 | Max lift, couldn't do more reps | 10 |
| 0 | No more reps, could do slightly more load | 10 |
| 1–2 | Could do 1 more rep, possibility of 2 | 8–9 |
| 2 | Could do 2 more reps | 8 |
| 2–3 | Could definitely do 2, possibly 3 | 7–8 |
| 3 | Could do 3 more reps | 7 |
| 4–6 | Could do 4 to 6 more reps | 4–6 |

**Codified:** Add a `rir_to_rpe(rir: float) -> float` helper. Note that RPE = 10 - RIR only above RIR 3; below 4 RIR the mapping is fuzzy.

### Rule 6.2 — Hypertrophy load range is huge (4–30 RM)
> **TABLE 7.3.** Hypertrophy Load: "~4–30 RM (~30-90% 1RM)." Strength Load: "1–8 RM (~80+% 1RM)." **[PB]**

**Codified:**
- HYPERTROPHY_LOAD_RANGE = (4, 30) RM  ≈  (30%, 90%) 1RM
- STRENGTH_LOAD_RANGE = (1, 8) RM  ≈  (80%, 100%) 1RM

### Rule 6.3 — Hypertrophy RIR-by-rep-range table (replaces single-RPE preset)
> **TABLE 7.3 (Hypertrophy Intensity rows):** "4–6 reps/set: 4-0 RIR… 6–8 reps/set: 3 RIR to failure… 8–12 reps/set: 2 RIR to failure… >12 reps/set: 1 RIR to failure." **[PB]**

| Reps/set | RIR target |
|---|---|
| 4–6 | 4–0 |
| 6–8 | 3 to failure (0) |
| 8–12 | 2 to failure (0) |
| >12 | 1 to failure (0) |

**Codified:** For hypertrophy, **the higher the load, the further from failure you train**. Replace the current single-float `rpe` field per (goal, category) with an RIR range that depends on rep range. The current `periodization.py` sets HYPERTROPHY COMPOUND_PRIMARY RPE=8.0 — too high for the 4–6 rep sub-range (which should be 4 RIR ≈ RPE 6).

### Rule 6.4 — Strength RIR-by-rep-range
> **TABLE 7.3 (Strength Intensity rows):** "~7–0 RIR per load/rep combination." "Load, not RIR, dictates strength. RIR is a function of load. Higher loads allow fewer reps and are inherently closer to failure." **[PB]**

**Codified:** For strength, RIR is *derived* from load, not specified. Add a function `strength_rir_for_load(load_pct_1rm) -> float` that decreases as load approaches 1RM.

### Rule 6.5 — Hypertrophy RIR by exercise type (Table 7.7) — THE KEY INTENSITY TABLE
> **TABLE 7.7. REP AND RPE/RIR RANGE COMBINATIONS FOR HYPERTROPHY BY EXERCISE TYPE**

| Exercise Type | Rep Range | RPE/RIR Range |
|---|---|---|
| Lower Free-Weight Compound (squat, deadlift, RDL) | 4–8 | 6–8 RPE / 4–2 RIR |
| Lower Machine Compound (leg press, hack squat) OR Upper Free-Weight Pressing (OHP, bench, incline DB) | 4–12 | 6–9 RPE / 4–1 RIR |
| Upper Machine Pressing (machine chest/shoulder press) OR Pulling Compound (lat pulldown, BB row, cable row) | 6–15 | 7–10 / 3–0 RIR and failure |
| Isolation (curls, tricep pushdown, calf raise, leg ext, lateral raise) | 8–20 | 8–10 / 2–0 RIR and failure |

**Codified:** Replace the current `ExerciseCategory` axis with a new **`IntensityTier`** axis that has four values: `LOWER_FREE_WEIGHT_COMPOUND`, `MACHINE_OR_UPPER_PRESS`, `MACHINE_PRESS_OR_PULL`, `ISOLATION`. Each intensity tier carries its own (rep_range, RPE_range) tuple. This is **the most important upgrade** the engine could adopt — Table 7.7 contradicts the current single-RPE-per-category model.

### Rule 6.6 — Compound vs isolation fatigue principle
> "the higher the fatigue generated by the movement, the greater the technical demand, and the greater the safety risk. Therefore, it makes more sense to train further from failure and use a higher load to ensure the set retains its full stimulus… Compound movements are generally a better vehicle for doing the portion of your volume that is lower rep and further from failure, and thus heavier. Likewise, isolation exercises and machines are better vehicles for the higher-rep, lower-load portion of your volume." **[PB]**

**Codified:** When the engine assigns RIR, the **default** should be: compounds → lower-rep, further-from-failure, heavier; isolations → higher-rep, closer-to-failure, lighter. Inverted pairings (high-rep barbell squat to failure, low-rep curl) should be flagged.

### Rule 6.7 — High-load hypertrophy needs ≥4 reps per set
> "High load effective for hypertrophy at high RIR but sets must be ≥4 reps. RIR underestimation more likely at low loads." **[PB, Table 7.3 footnote 5]**

**Codified:** Hard floor: any hypertrophy working set must be ≥4 reps. (A 3-rep set is strength territory.)

### Rule 6.8 — Don't take lower-body free-weight compounds to failure
> "while 0 RIR can be appropriate for low-rep high-load training for hypertrophy, it's not ideal for most free weight compound lower body and upper body pressing exercises for safety, or even lower compound machine exercises for fatigue management." **[PB]**

**Codified:** Cap RIR at ≥1 for `LOWER_FREE_WEIGHT_COMPOUND` and `UPPER_FREE_WEIGHT_PRESSING` (Table 7.7 categories 1 & 2). Failure (0 RIR) is reserved for machine pressing, pulling compounds, and isolation.

---

## 7. Progression Rules

### Rule 7.1 — Two progression systems (NOT three)
> "Linear Progression: When You Can Make Load Increases Every Session… Once you are no longer able to progress like this, start using Autoregulated Double Progression." **[PROG]**
> Wave loading was retired in the 3rd edition: "It's not that it's less effective, it's that it's unnecessarily complicated." **[PROG comments]**

**Codified:** The engine should expose **two** progression primitives — `LINEAR` (load added every session) and `AUTOREGULATED_DOUBLE` (load held; reps climbed; load added when top of rep range reached). The current `ProgressionScheme` enum has `LINEAR | DUP | BLOCK`. Consider renaming `DUP` → `AUTOREGULATED_DOUBLE` and replacing the day-type modifiers with the RIR-based system below. (RippedBody's "block" for strength is really a 3-phase volume→load→peak cycle, see Section 11.)

### Rule 7.2 — Linear progression: load-increment rules
> "For compound movements that use a lot of muscle, consider increasing the load by 10 lbs each session. Other exercises might need to progress in 5-lb (or 2.5-lb increments when possible)." **[PROG]**

**Codified:** Default increments:
- Compound (multi-muscle) → **10 lb ≈ 4.5 kg** per jump
- Other → **5 lb ≈ 2.25 kg** per jump
- If microplates available → **2.5 lb ≈ 1.1 kg**

The current `linear_progression_next` uses 2.5 kg uniformly — too small for compounds (will stall beginners) and the unit conversion is off.

### Rule 7.3 — Linear progression: first-week intro rule
> "To minimize unnecessary fatigue and soreness and help you get used to the new routine, consider doing one set less than prescribed for all exercises for the first week." **[PROG]**

**Codified:** In microcycle 1 of any new program (or any new exercise introduced later), reduce sets by 1 across the board. The current engine doesn't do this.

### Rule 7.4 — Linear progression: don't train to failure
> "Try not to train to failure for any of your sets. If you think your next rep will fail, stop the set, even if this means you are short of your rep target. (Avoiding failure is better for skill acquisition, which is the goal right now.)" **[PROG]**

**Codified:** During LINEAR progression, the engine should set RIR floor ≥1 and warn if user logs 0 RIR. Skill acquisition is the priority during linear.

### Rule 7.5 — Linear → autoregulated transition trigger
> "There will come a point when it is not possible to increase every session. If the set felt particularly difficult, aim to increase the weight every second session, focusing on the feeling of it being easier in the next session." **[PROG]**
> "Once you are no longer able to progress like this, start using Autoregulated Double Progression." **[PROG]**

**Codified:** Trigger to graduate from LINEAR → AUTOREGULATED_DOUBLE: **two consecutive sessions where load could not be added** (or one session where minimum reps were missed). The current `linear_progression_next` deloads 10% on a single miss — too aggressive.

### Rule 7.6 — Autoregulated Double Progression: load-selection rule
> "After warming up, select a weight you expect to land near the top of the RIR range and the middle or lower end of the rep range. For example, you might pick a weight you think you can do for 12 reps at 2 RIR — i.e., your ~14RM." **[PROG]**

**Codified:** For a target of `N–M reps at A–B RIR`, opening load = user's (M+B)RM. (Top of rep range + top of RIR range.) Engine can compute this from a 1RM estimate.

### Rule 7.7 — Autoregulated Double Progression: stop at upper RIR boundary
> "Perform the set, stopping once you hit the upper RIR boundary — in this case, 2 RIR — even if you could do more reps." **[PROG]**

**Codified:** Working sets stop at the *high* end of the RIR range (the easier end). Don't grind to failure when not prescribed.

### Rule 7.8 — Autoregulated Double Progression: load-bump trigger
> "Progress Load When Ready — When you can hit the top end of the rep range at the highest end of the RIR range (e.g., 15 reps at 2 RIR) in your first set, increase the load next session." **[PROG]**

**Codified:** Bump-load trigger = **first set** hits (top of rep range) AND (top of RIR range). Note: it's the FIRST set, not all sets. The current `linear_progression_next` requires "all sets achieved high reps" — too strict.

### Rule 7.9 — Autoregulated Double Progression: 4 % per-rep load adjustment
> "If your reps on your first set were below or above the target rep range, adjust the load on the next set, up or down, making your best guess of what load would put you in the rep range on the next set. If unsure, adjust load ~4% up or down for every rep outside the range." **[PROG]**

**Codified:** Add a `recompute_load(weight, achieved_reps, target_low, target_high) -> float` helper:
```
delta_reps = achieved_reps - target_high   # positive = too easy, negative = too hard
adjustment = 0.04 * delta_reps * sign
new_weight = weight * (1 + adjustment)
```
This is a clean numeric rule with no current equivalent in the engine.

### Rule 7.10 — Autoregulated Double Progression: tolerate fluctuation
> "Performance won't always progress linearly. Some weeks will regress slightly — that's normal. Think in terms of trends, not single sessions." **[PROG]**
> "As you train week to week, you sometimes might think you are at a higher RIR than you really are during a set, and then accidentally hit a 1 RIR on your first set when you meant to hit a 2 RIR. That's totally fine." **[PROG]**

**Codified:** A single regression session should NOT trigger a deload. Track a 3-session rolling trend. The current `ProgressionState.STALLED = "failed to add load for 2+ sessions"` is on the edge — acceptable but should be 3 sessions for autoregulated.

### Rule 7.11 — Novice vs Intermediate vs Advanced progression rates (Table 7.14)
> **TABLE 7.14. TRAINING STATUS DEFINITION AND ESTIMATED AVERAGE RATES OF PROGRESS**

| Status | Definition | Timeframe |
|---|---|---|
| Novice | Able to add load and/or reps each time a lift is repeated in the same week or from week to week | ≥6 months, can last years |
| Intermediate | Progress slows. You might add reps in the 10–20 rep range week to week, or add load in lower rep ranges month to month | Reach by year 1, may remain through years 4–5 |
| Advanced | Gains are much slower. May add a rep or two in the 10–20 rep range month to month, or small increases in reps or load in lower rep ranges over longer timeframes | Most never reach this |

**Codified:** Map the engine's `TrainingStatus` enum onto these progression expectations:
- BEGINNER/NOVICE → linear progression appropriate, expect session-to-session load adds
- INTERMEDIATE → autoregulated double progression, expect 5 sessions to add load (per Example 3 in [PROG])
- ADVANCED → autoregulated double progression, expect ~10 sessions to add load

### Rule 7.12 — Rep-range variation structures (Table 7.8)
> **TABLE 7.8. HYPERTROPHY TRAINING STRUCTURES TO ACHIEVE REP RANGE VARIATION**

| Structure | Pattern |
|---|---|
| Within-Session | Different rep ranges per lift in same session (e.g., Lower A: 4–8, 6–10, 10–15, 15–20) |
| Between-Session | Heavy day / light day within the microcycle |
| Alternating Week | Week A heavy (4–6, 6–10, 8–12); Week B light (8–12, 10–15, 15–20) |
| Alternating Mesocycle | Meso A heavy; Meso B light |

**Codified:** Add a `RepRangeVariationStrategy` enum: `WITHIN_SESSION`, `BETWEEN_SESSIONS`, `ALTERNATING_WEEK`, `ALTERNATING_MESOCYCLE`. Default = `WITHIN_SESSION` for hypertrophy. The current `DUP` day-type system is roughly equivalent to `BETWEEN_SESSIONS` but uses percentages instead of explicit rep ranges.

### Rule 7.13 — Don't spend >3 weeks outside hypertrophy rep ranges
> "you want to avoid spending too long (longer than ~3 weeks) exclusively training outside of hypertrophy guidelines" **[PROG]**

**Codified:** Hard ceiling: any contiguous block of training at <6 reps with high RIR (i.e., pure-strength work) must be ≤3 weeks long, OR must be interleaved with hypertrophy-rep work in the same session.

### Rule 7.14 — Rep-range variation is *beneficial* but no single structure is superior
> "While rep range variation beyond the 'traditional hypertrophy' range of 8–12 seems to be beneficial, no evidence indicates that any specific structure is superior to another." **[PROG]**

**Codified:** Don't over-engineer the variation strategy. Any of the four (Rule 7.12) is acceptable; let user preference / variety drive the choice.

---

## 8. Deload Rules

### Rule 8.1 — Reactive, not scheduled
> "We recommend deloads on an as-needed basis rather than as pre-planned components of all programs." **[PROG]**

**Codified:** The current engine forces `deload_week = True` on every mesocycle. **Contradiction.** Replace with: deload is a flag the user/coach triggers, OR an automatic trigger based on Rule 8.2.

### Rule 8.2 — Reactive deload self-assessment (5 questions)
> **REACTIVE DELOAD SELF-ASSESSMENT TABLE** — "After completing a week of training and days off are you: Y/N? Dreading the gym? / Sleep worse than normal? / Loads or reps at the same load, decreasing from the last training cycle? / Stress worse than normal? / Aches and pain worse than normal? — Yes to 0–1 questions: carry on. Yes to 2 or more questions: consider a deload." **[PROG]**

**Codified:** Add a `DeloadDecisionEngine` that ingests a weekly self-assessment (5 booleans) and returns `DELOAD` iff ≥2 are True. Optionally the engine can auto-track the third question (loads/reps decreasing) from the progression log.

### Rule 8.3 — Standard deload: −30 to −50 % sets, intensity unchanged
> "Therefore, don't reduce volume as much as you would in a taper (~50–80%); instead, reduce sets on all exercises by ~30–50%… Volume: Reduce sets by ~30–50% across all exercises. Intensity: Maintain normal loading and proximity to failure. Frequency: Keep the same number of sessions per week." **[PROG]**

**Codified:** Standard deload recipe:
- `sets_new = round(sets_old * uniform(0.5, 0.7))`  (i.e., drop 30–50 %)
- `reps` unchanged
- `rpe_target` unchanged
- `sessions_per_week` unchanged

The current `apply_periodization(is_deload=True)` does `sets -= 1; rpe -= 2`. **Contradiction** — RippedBody explicitly says *do not* reduce intensity.

### Rule 8.4 — Targeted deload for a single body region
> "if you feel great overall but have lingering, substantial lumbar soreness, you can do a targeted deload, keeping hack squats, leg extensions, leg curls, and hip thrusts at their normal volume, but remove deadlifts and/or back squats completely next training week." **[PROG]**

**Codified:** Support a *targeted deload* mode: pass a list of muscle groups (or exercise slugs) to suppress; everything else stays at normal volume.

### Rule 8.5 — Deload can also restructure sessions
> "if it feels like a waste of time to commute to the gym to train for 30 minutes doing half as many sets, you can restructure your training into fewer days to reduce volume… you could do one upper and one lower day, training just twice that week." **[PROG]**

**Codified:** Allow a deload-week mode that *collapses* the split (e.g., 4-day U/L → 2-day U/L) rather than reducing per-session volume.

### Rule 8.6 — Higher reps can substitute for lower load during deload
> "if you experience aches and pains that flare up with heavier loads, but not at higher reps, you could do higher reps for a week for those movements." **[PROG]**

**Codified:** Add a deload variant: `DeloadMode.HIGH_REP` — keep sets the same, but shift rep range up one tier (e.g., 4–8 → 8–12) and reduce load accordingly.

### Rule 8.7 — Pick up where you left off post-deload
> "Pick up where you left off. Note that this doesn't necessarily mean exactly the same weight and reps, as the RIR/RPE may change post-deload and you'll want to adjust accordingly." **[PROG comments]**

**Codified:** After a deload, the next session starts at the *pre-deload load*, with RIR auto-adjusted by feel. Do NOT auto-increment load immediately after a deload.

### Rule 8.8 — Calories stay the same during a deload
> "I'd keep them the same." (re: deload-week calories for bulk or cut) **[PROG comments]**

**Codified:** Nutrition planner should NOT change calorie targets during a deload week. (Documented as a check.)

---

## 9. Exercise Selection Rules

### Rule 9.1 — Six core movement patterns
> "choose 1–3 lifts for each of the six core movement patterns (Squat, Hip Hinge, Vertical Push, Vertical Pull, Horizontal Push, and Horizontal Pull)" **[PB]**

**Codified:** The engine must guarantee at least 1 and at most 3 lifts per pattern across the microcycle. The six canonical patterns are the floor of any hypertrophy program. (The current `MovementPatternSlot` set has more patterns — lunge, hip_thrust, knee_flexion, etc. — which is fine as long as the 6 core are always covered.)

### Rule 9.2 — Three mandatory exercise sub-types
> "Include: An incline press. An elbow-flared row plus a shoulder-extension–dominant row." **[PB]**
> (clarification in comments): "This simply means to perform one row with elbows high (45~90º from the body, often done with a wider grip) and another with elbows tucked closer to the body (necessitating a narrower grip)." **[PB comments]**

**Codified:** Add three hard requirements to the hypertrophy exercise selector:
1. At least one **incline press** (slot pattern `incline_push`).
2. At least one **elbow-flared row** (wide-grip, elbows 45–90°, e.g., wide-grip cable row, BB row elbows-out).
3. At least one **shoulder-extension-dominant row** (narrow grip, elbows tucked, e.g., close-grip lat pulldown, seated cable row narrow).

### Rule 9.3 — Mandatory isolation coverage
> "At least one isolation exercise each for the quads, hamstrings, biceps, triceps, middle delts, and calves." **[PB]**

**Codified:** Hypertrophy program must include ≥1 isolation lift targeting each of: `quads`, `hamstrings`, `biceps`, `triceps`, `middle_delts`, `calves`. Add a validation pass after slot-filling.

### Rule 9.4 — Movement-pattern → muscle mapping (Table 7.17)
> **TABLE 7.17. HYPERTROPHY: EXERCISES AND MUSCLE GROUPS TRAINED**

| Movement Pattern | Primary Muscles | Secondary Muscles |
|---|---|---|
| Squat (all variations, leg press, single-leg) | Quads, Glutes | Erectors (if free weights) |
| Hip Hinge (DL variations, good morning, back ext) | Glutes, Hams, Erectors | Scapular Retractors |
| Vertical Pull (chins, lat pulldown) | Lats, Scapular Depressors | Rear Delts, Bis |
| Vertical Push (OHP variations) | Anterior Delts | Triceps, Middle Delts |
| Horizontal Pull (row variations) | Lats, Scapular Retractors | Rear Delts, Bis, Middle Delts (face pull) |
| Horizontal Push (flat, incline, decline) | Chest, Anterior Delts | Tris, Middle Delts (incline) |
| Horizontal Hip Extension (hip thrust, glute bridge) | Glutes | Hams |
| Pull Over (DB, BB, cable, machine) | Lats | Chest, Rear Delts, Tris (long head) |
| Upright Row | Scapular Elevators, Middle Delts | Rear Delts, Bis |
| Fly (cable, DB, machine) | Chest, Anterior Delts | N/A |
| Isolation | Target muscle | N/A |

**Codified:** Use this table to populate `secondary_muscles` for any exercise missing it, and to drive the fractional-set counter (Rule 2.5).

### Rule 9.5 — Strength: prefer main lifts; use variations only when needed
> "Use your main lifts to achieve the target volume for those lifts unless you have a low tolerance for their total volume. In that case, select variations with high carryover based on your biomechanics, injury history, technical needs, and/or sticking points. For hypertrophy work, choose less fatiguing, higher-rep exercises that are quicker to set up and perform." **[PB, Table 7.16]**

**Codified:** Strength program defaults: main lifts (squat/bench/deadlift or sport-specific) at the prescribed volume. Variations are a fallback when the user reports low volume tolerance (tracked via the deload checklist).

### Rule 9.6 — Strength: avoid interference (scheduling rule)
> "Don't schedule heavy secondary work for the same muscle group the day before main lift training (e.g., avoid lots of quad work before squats, lots of pressing before bench)." **[PB]**

**Codified:** Add a `scheduling_interference_check` to the architect: if Day N has heavy secondary quad work and Day N+1 has a main squat session, emit a warning (or auto-swap days).

### Rule 9.7 — Beginner exercise count: fewer, not more
> "When starting out at the gym you will be tempted to see how heavy you can lift, or try every single exercise and piece of equipment in sight. These are both mistakes… Limit the number of exercises you start with. Focus on learning the correct form." **[PB comments]**

**Codified:** For `TrainingStatus.BEGINNER` and `NOVICE`, cap total distinct exercises per microcycle at ~6–8 (not 12+). For advanced, the cap can relax.

### Rule 9.8 — Selection criteria (feasibility + long-length training)
> "Following the principles of feasibility and ensuring the target muscle is both trained and challenged at long lengths" **[PB]**

**Codified:** When ranking exercise candidates, prefer (in order):
1. Feasibility (equipment available, user can perform safely)
2. The target muscle is trained at **long muscle lengths** (e.g., deep-stretch DB fly > machine fly at short length; full-ROM RDL > partial). This requires either a metadata field `long_length_emphasis: bool` or a per-pattern default.

---

## 10. Exercise Variation / Swap Rules

### Rule 10.1 — Swapping is fine if movement pattern is preserved
> "You can if you wish. They both train the chest to a similar degree (albeit without the additional triceps stimulation). So, if you love flys and they feel great, feel free to swap them in!" **[PB comments]**

**Codified:** A user-initiated swap is allowed if the replacement matches the same (pattern, primary_muscle) tuple. The engine should recompute fractional set counts after the swap and warn if the swap changes secondary-muscle coverage materially (e.g., fly → press adds triceps stimulus).

### Rule 10.2 — Swap squat+DL on the same day if too taxing
> "if you lower the loads from what you are used to, work your way up, then make sure you keep to the RPEs, you should be fine. If after trying that… then you feel the need to adjust, you can certainly do that." **[PB comments]** (in response to a user asking about pairing Squat+RDL, Deadlift+Front Squat, etc.)

**Codified:** When two heavy lower-body compounds fall on the same day (e.g., back squat + conventional deadlift), allow the user to substitute one with a close variation (front squat, RDL, hack squat, deficit DL). Provide a `close_variations(exercise_slug)` lookup.

### Rule 10.3 — Horizontal + vertical push count as ONE movement for volume
> "Horizontal/vertical push consider 1 movement or separate? — Together when it comes to counting volume." **[PB comments]**

**Codified:** For volume-counting purposes, **horizontal push + vertical push = one combined bucket**. Same for horizontal pull + vertical pull. (The MovementPatternSlot system currently treats them as separate — that's fine for slot-filling, but the volume tally should merge them.)

### Rule 10.4 — Calves can be trained every session
> "The MSP Training book describes pairing calves with quads; however, here we train calves every session to avoid needing twice as many sets to achieve the target volume." **[PB comments]**

**Codified:** Calves recover fast; treat them as a high-frequency muscle. Engine can spread calf volume across all training days rather than concentrating it.

---

## 11. Strength Block Periodization (Tables 7.11–7.13)

RippedBody's strength "block" is a 3-phase cycle (Volume → Load → Peak), NOT the current engine's `accumulation → intensification → deload/peak` abstraction.

### Rule 11.1 — Volume Phase (Table 7.11)
> Goal: Build muscle; maintain or build strength.
> Main lifts: 1–3 singles/lift/week; progress from 5 to 8 RPE (5 to 2 RIR).
> Secondary lifts: 10–20 sets/week per main-lift muscle group; mostly in the 6–20 rep range at 0–3 RIR; autoregulated double progression, primarily non-specific, low-demand exercises.
> Length: 6–12 weeks per timeline.

**Codified:**
- Phase name: `VOLUME`
- Main lifts: 1–3 singles per lift per week, RPE ramp 5→8 across the phase
- Secondary: 10–20 sets/wk per main-lift muscle group, 6–20 reps, 0–3 RIR
- Duration: 6–12 weeks

### Rule 11.2 — Load Phase (Table 7.12)
> Goal: Build strength, maintain/build muscle.
> Main lifts: 2–4 singles/lift/week; progress from 6 to 9 RPE (4 to 1 RIR). 2 back-off sets/single at 5–8 RPE (5–2 RIR); progress from 5 to 3 reps (~80–85% 1RM). Use variations if needed.
> Secondary lifts: 5–10 sets/week/main-lift muscle group, mostly 6–20 reps at 0–3 RIR; autoregulated double progression, primarily non-specific, low-demand exercises.
> Length: 4–8 weeks per timeline, gradually reduce secondary lift volume by 1–2 sets every 1–2 weeks (e.g., 10 sets in weeks 1–2, 9 sets in weeks 3–4, 8 sets in weeks 5–6, and 6 sets in weeks 7–8).

**Codified:**
- Phase name: `LOAD`
- Main lifts: 2–4 singles per lift per week, RPE ramp 6→9, plus 2 back-off sets at 5–8 RPE, 5→3 reps (~80–85 % 1RM)
- Secondary: 5–10 sets/wk per main-lift muscle, tapering −1 to −2 sets every 1–2 weeks
- Duration: 4–8 weeks

### Rule 11.3 — Peak Phase (Table 7.13)
> Goal: Peak strength, maintain muscle.
> Main lifts: 2–5 singles/each/week at 7–10 RPE (3–0 RIR); 0–3 back-off sets/single at 5–8 RPE (5–2 RIR). If 3–4 weeks, progress from 4 to 2 reps/set (~85% 1RM). Use variations if needed.
> Secondary lifts: 0–4 sets/week/main-lift muscle group, mostly 6–20 reps at 0–3 RIR; autoregulated double progression; primarily non-specific, low-demand exercises.
> Length: 2–4 weeks, 2 weeks if the volume and load phase lasted 10–12 weeks, 3 weeks if 13–15 weeks, 4 weeks if 16+ weeks. Decrease the back-off set and secondary lift volume weekly.

**Codified:**
- Phase name: `PEAK`
- Main lifts: 2–5 singles per lift per week at 7–10 RPE, 0–3 back-off sets at 5–8 RPE, 4→2 reps (~85 % 1RM)
- Secondary: 0–4 sets/wk per main-lift muscle
- Duration: scales with prior phase length:
  - prior 10–12 wks → 2-week peak
  - prior 13–15 wks → 3-week peak
  - prior 16+ wks → 4-week peak
- Back-off and secondary volume decrease weekly.

### Rule 11.4 — Replace the current BLOCK abstraction
The current `_BLOCK_PHASE_MODIFIERS` has `accumulation → intensification → deload`. The above three phases (Volume / Load / Peak) are materially different:
- Volume phase = high secondary volume + low main-lift intensity
- Load phase = ramping main-lift intensity + tapering secondary
- Peak phase = max main-lift intensity + minimal secondary

**Codified:** Add `StrengthPhase` enum {VOLUME, LOAD, PEAK} with the per-phase rules above. The BLOCK `ProgressionScheme` should produce a sequence like `[VOLUME ×6-12wk, LOAD ×4-8wk, PEAK ×2-4wk]`. Current `get_block_phases_for_program` returns `["accumulation", "intensification", "peak"]` — close but the parameters per phase differ.

---

## 12. Specialization Cycles (Advanced Hypertrophy)

### Rule 12.1 — Specialization mesocycle structure (Table 7.9)
> Balanced Phase: 8–12 weeks, 10–20 sets/wk on all muscle groups.
> Specialization Phase: 8–12 weeks, 20–30 sets/wk on 1–2 muscle groups, 5–15 on remaining.
> (Then return to Balanced.)

**Codified:** For `TrainingStatus.ADVANCED` hypertrophy, the engine should produce a 3-mesocycle program: `Balanced (8–12wk) → Specialization (8–12wk) → Balanced (8–12wk)`. The specialization mesocycle takes 1–2 `muscle_focus` entries and pushes them to 20–30 sets/wk while dropping everything else to 5–15.

### Rule 12.2 — Specialization requires frequency bump for the focus muscle
> "Higher volumes closer to maximum ED only advised for advanced lifters via specialization cycles." **[PB, Table 7.3 footnote 4]**

**Codified:** When specialization volume is ≥21 sets/wk for the focus muscle, frequency for that muscle must be ≥3×/wk (Rule 3.1).

---

## 13. Rest Period Rules

### Rule 13.1 — Rest is goal/exercise-type dependent but loosely defined
> "Ensure your rest periods are appropriate for your goals on each lift" **[PB]**

RippedBody does not give a hard rest-seconds table; they explicitly leave it to the "appropriate for your goals on each lift" principle. The current engine's preset values (60–240 s by goal/category) are reasonable but not source-supported. **Codified:** Keep current values as defaults, but expose them as user-tunable. Consider lengthening rest for `LOWER_FREE_WEIGHT_COMPOUND` (Rule 6.5) — they're the most fatiguing.

### Rule 13.2 — Warm-up set rest = 1–2 minutes
> "Ascending sets with percentage of target working weight with 1–2-minute rest between" **[PB, Table 7.18]**

**Codified:** Warm-up sets rest 60–120 s. Working-set rest is the existing preset.

### Rule 13.3 — Time-saving techniques are optional
> "Consider whether you can incorporate antagonist-paired sets, peripheral-paired sets, drop sets, or rest-pause techniques to save time. Use them only with suitable exercise combinations and if your cardiorespiratory fitness allows." **[PB]**

**Codified:** Add an optional `time_saving_technique` field on `WorkoutExercise`: `None | ANTAGONIST_PAIR | PERIPHERAL_PAIR | DROP_SET | REST_PAUSE`. Default None.

---

## 14. Tempo Rules

### Rule 14.1 — Tempo is a final-shaping variable, not a primary one
> "your tempos align with the intended training effect" **[PB]**

RippedBody gives no numeric tempo prescription (no "3-1-1-0" tables). **Codified:** Do not encode a tempo table from this source. Leave tempo as a free-text field on `WorkoutExercise` (already implicit). For weightlifting variations specifically, "controlled eccentrics" are mentioned for the 4–8 rep range.

---

## 15. Warm-Up Protocol (Table 7.18)

### Rule 15.1 — Three warm-up components: general / dynamic / specific
> **TABLE 7.18. WARM-UP SUMMARY GUIDELINES**

| Component | Description |
|---|---|
| **General** | Optional — 5 min light aerobic activity |
| **Dynamic** | Optional — 3–5 min (7–10 min if no general warm-up) of active stretching drills; gradually increase ROM and force |
| **Specific for ≤6-Rep Sets** | Ascending sets: 5–10 reps ≤40% (optional w/ general or dynamic) → 3–5 reps ~60% → 1–3 reps ~80% → 1 rep 90%. Rest 1–2 min between. |
| **Specific for ≥6-Rep Sets** | Ascending sets: 5–10 reps 40% (optional w/ general or dynamic) → 4–6 reps ~60% → 2–4 reps ~80% → 1–2 reps 85–90% (optional PAPE, use %1RM, not target weight). Rest 1–2 min between. |

**Codified:** Add a `WarmUpSetGenerator` that takes `(target_weight, target_reps)` and emits a list of warm-up sets with reps + % load. Two recipes: `LEQ_6_REP` and `GEQ_6_REP`. The current engine has no warm-up prescription at all.

### Rule 15.2 — First exercise gets more warm-up sets; subsequent get one (or none)
> "Perform more warm-up sets on the first exercises for each muscle group. Then, a single warm-up set is often all that's needed for subsequent free weight exercises for that muscle to familiarize the movement, and on machines, you may not need any more warm-up sets." **[PB]**

**Codified:** Warm-up prescription is per-muscle-group: full ascending warm-up on the first exercise of each muscle group in the session; one familiarization set (40 % × 8 reps) on subsequent free-weight exercises for the same muscle; zero warm-up sets on machine exercises for already-warmed muscles.

### Rule 15.3 — Don't conclude warm-up with static stretching
> "you can do static stretching, dynamic stretching, or foam rolling in a warm-up, so long as it doesn't conclude with long-duration static stretching" **[PB]**

**Codified:** N/A for the engine; informational.

### Rule 15.4 — PAPE protocol (optional)
> "Protocols that most consistently enhance resistance training back-off set performance consist of 1–2 sets of 1–3 reps with ~85-90% of 1RM" **[PB]**

**Codified:** Optional `PAPE` warm-up step before the working sets: 1–2 × 1–3 reps at 85–90 % 1RM. The "singles" in the Strength Progression System fill this role naturally.

### Rule 15.5 — Foam rolling duration
> "Foam rolling for ~60 s with moderate pressure can also increase ROM and, like dynamic stretching, may slightly boost performance" **[PB]**

**Codified:** If a `mobility` slot is filled with foam rolling, default duration = 60 s per muscle.

---

## 16. Dual-Athlete / Powerbuilder Rules

### Rule 16.1 — Non-competitive "powerbuilder" — use strength guidelines, higher secondary vol
> "Simply follow our strength training guidelines, using the higher end of the non-specific volumes and the lower end of the main-lift volumes." **[PB]**

**Codified:** New implicit profile `POWERBUILDER` (or a `dual_athlete` flag): strength progression + secondary volume at the upper bound of the load-phase range (10 sets rather than 5) + main-lift singles at the lower bound (2 singles rather than 4).

### Rule 16.2 — Physique athlete off-season strength: add 1–2 singles/week
> "When in bodybuilding-focused phases (either offseason or prep) with no meet within the next 3–4 months, simply add 1–2 singles per week on the main lifts for your chosen strength sport. Start some sessions by working up to a single in the 5–8 RPE range to maintain proficiency." **[PB]**

**Codified:** Hypertrophy program + `dual_athlete=True` → prepend 1–2 main-lift singles at RPE 5–8 to 1–2 sessions per week. Doesn't change the rest of the hypertrophy volume.

### Rule 16.3 — Strength athlete contest-prep physique: hypertrophy + singles
> "When you have no meets planned in the next 3–4 months and are dieting for a physique contest, shift to the Hypertrophy Progression System with several added main-lift singles." **[PB]**

**Codified:** Same as 16.2 with a calorie deficit (covered by the nutrition side).

### Rule 16.4 — 3–4 months out from a meet: switch to Strength Progression System
> "switch to the Strength Progression System with modifications: Keep hypertrophy work for all muscle groups when selecting secondary lifts… The volume phase can be shortened or skipped if you've been doing hypertrophy work on main lifts or high-transfer variations" **[PB]**

**Codified:** Auto-switch from hypertrophy+singles to Volume→Load→Peak when a meet date is set 12–16 weeks out. If the user was already doing hypertrophy with the main lifts, skip Volume phase and start at Load.

---

## 17. Other Codifiable Numerical Thresholds (consolidated)

| Threshold | Value | Source |
|---|---|---|
| Minimum training days/week | 2 | [PB] Rule 1.2 |
| Min days/week to progress (intermediate+) | 3 | [PB] Rule 1.3 |
| Hypertrophy MEV | 4 sets/muscle/wk | [PB] Table 7.3 |
| Hypertrophy MAV (practical) | 10–20 sets/muscle/wk | [PB] Table 7.3 |
| Hypertrophy MRV (short-term) | ~30 sets/muscle/wk | [PB] Table 7.3 |
| Strength MEV | 1 set/lift/wk | [PB] Table 7.3 |
| Strength MAV (short-term) | 3–5 sets/lift/wk | [PB] Table 7.3 |
| Strength MAV (long-term) | 5–10 sets/lift/wk | [PB] Table 7.3 |
| Strength MRV (short-term) | ~5 sets/lift/wk | [PB] Table 7.3 |
| Per-session cap (hypertrophy) | ~11 fractional sets/muscle | [PB] Rule 2.6 |
| Hypertrophy load range | 4–30 RM (~30–90 % 1RM) | [PB] Rule 6.2 |
| Strength load range | 1–8 RM (~80+ % 1RM) | [PB] Rule 6.2 |
| Hypertrophy rep-set floor | ≥4 reps | [PB] Rule 6.7 |
| Linear compound load jump | 10 lb ≈ 4.5 kg | [PROG] Rule 7.2 |
| Linear other-exercise jump | 5 lb ≈ 2.25 kg | [PROG] Rule 7.2 |
| Linear microplate jump | 2.5 lb ≈ 1.1 kg | [PROG] Rule 7.2 |
| First-week set reduction | −1 set all exercises | [PROG] Rule 7.3 |
| Double-progression load-bump trigger | First set hits top rep × top RIR | [PROG] Rule 7.8 |
| Per-rep load-adjustment factor | ~4 % per rep outside range | [PROG] Rule 7.9 |
| Deload volume reduction | −30 to −50 % sets | [PROG] Rule 8.3 |
| Deload intensity reduction | 0 % (maintain load + RIR) | [PROG] Rule 8.3 |
| Taper volume reduction (for contrast) | 50–80 % | [PROG] Rule 8.3 |
| Reactive deload trigger | ≥2 of 5 self-assessment questions | [PROG] Rule 8.2 |
| Pure-strength block ceiling without hypertrophy reps | 3 weeks | [PROG] Rule 7.13 |
| Foam-rolling duration | ~60 s moderate pressure | [PB] Rule 15.5 |
| Dynamic warm-up duration | 3–5 min (7–10 min if no general) | [PB] Table 7.18 |
| General warm-up duration | 5 min light aerobic | [PB] Table 7.18 |
| Warm-up set rest | 1–2 min | [PB] Table 7.18 |
| PAPE protocol | 1–2 × 1–3 reps @ 85–90 % 1RM | [PB] Rule 15.4 |
| Volume phase length (strength) | 6–12 wk | [PB] Table 7.11 |
| Load phase length (strength) | 4–8 wk | [PB] Table 7.12 |
| Peak phase length (strength) | 2–4 wk (scales with prior) | [PB] Table 7.13 |
| Specialization balanced phase | 8–12 wk @ 10–20 sets/muscle | [PB] Table 7.9 |
| Specialization focus phase | 8–12 wk @ 20–30 sets on 1–2 muscles, 5–15 on rest | [PB] Table 7.9 |
| "Sweet spot" days/week | 3–5 | [PB] Rule 3.4 |
| "Sweet spot" muscle frequency | 2–4 ×/wk | [PB] Rule 3.4 |
| Hypertrophy frequency floor | ≥1 ×/muscle/wk | [PB] Rule 3.2 |
| Strength frequency floor | 2 ×/lift/wk | [PB] Rule 3.3 |
| Strength frequency ceiling | 6 ×/lift/wk | [PB] Rule 3.3 |
| Maintenance volume | 50–67 % of MAV | [PB comments] Rule 2.4 |
| Beginner exercise cap per microcycle | ~6–8 | [PB comments] Rule 9.7 |
| Movements per pattern per microcycle | 1–3 | [PB] Rule 9.1 |
| Default squat:deadlift frequency bias | higher squat | [PB] Rule 3.5 |

---

## 18. Contradictions With the Current Engine

| # | Current behaviour | RippedBody rule | Severity |
|---|---|---|---|
| C1 | `periodization.py` sets a single RPE float per (goal, category) | RIR/RPE must be a *range* depending on rep range AND exercise intensity tier (Tables 7.3, 7.7) | **High** |
| C2 | `ExerciseCategory` axis = COMPOUND_PRIMARY / SECONDARY / ACCESSORY / ISOLATION | Table 7.7 uses 4 *intensity tiers* that don't map cleanly: LOWER_FREE_WEIGHT_COMPOUND, MACHINE_OR_UPPER_PRESS, MACHINE_PRESS_OR_PULL, ISOLATION | **High** |
| C3 | `apply_periodization(is_deload=True)` does `sets -= 1; rpe -= 2` | Deload = −30 to −50 % sets, RPE unchanged (Rule 8.3) | **High** |
| C4 | `Mesocycle.deload_week = True` is the default; every mesocycle deloads | Deloads are *reactive*, not scheduled (Rule 8.1) | **High** |
| C5 | `linear_progression_next` deloads 10 % on first missed session | Reactive deloads only after ≥2 self-assessment flags; LINEAR graduation = 2 missed sessions, then switch to AUTOREGULATED_DOUBLE (Rules 7.5, 8.2) | **High** |
| C6 | `linear_progression_next` requires all sets ≥ high reps before adding load | Autoregulated double progression triggers on **first set** hitting top rep × top RIR (Rule 7.8) | **High** |
| C7 | Increment = 2.5 kg uniformly | 10 lb compounds / 5 lb others / 2.5 lb microplate (Rule 7.2) | Medium |
| C8 | `_BLOCK_PHASE_MODIFIERS` = accumulation / intensification / deload | Strength block = Volume → Load → Peak (Tables 7.11–7.13) | **High** |
| C9 | `get_block_phases_for_program` returns `["accumulation", "intensification", "peak"]` | Should return `["volume", "load", "peak"]` with phase-specific set/rep/RPE/volume rules | Medium |
| C10 | `MAINTENANCE` preset keeps sets the same, only changes reps | Maintenance = 50–67 % of MAV sets (Rule 2.4) | Medium |
| C11 | `FAT_LOSS` preset uses 45–60 s rest "for calorie burn" | RippedBody does not endorse short-rest fat-loss training; fat loss is nutrition-driven. Rest should match hypertrophy defaults | Medium |
| C12 | No MRV / MEV / MAV volume landmarks in the data model | Tables 7.3 + 7.4 define these explicitly | **High** |
| C13 | No 11-set-per-muscle-per-session cap | Hard cap (Rule 2.6) | **High** |
| C14 | No frequency-by-volume table | Table 7.6 (Rule 3.1) | Medium |
| C15 | Split catalogue has 8 patterns; no "muscle group day", "full push", "full pull", "full body ×N" | Tables 7.1, 7.2 have ~30 split configurations | **High** |
| C16 | No fractional set counting (primary=1.0, secondary=0.5) | Required by Rules 2.5, 3.5, 9.4 | **High** |
| C17 | No warm-up set prescription at all | Table 7.18 has explicit recipes (Rule 15.1) | **High** |
| C18 | No reactive-deload self-assessment | 5-question checklist (Rule 8.2) | Medium |
| C19 | No specialization cycles | Table 7.9 (advanced hypertrophy) | Medium |
| C20 | No "incline press + elbow-flared row + shoulder-extension row" requirements | Hard requirements (Rule 9.2) | Medium |
| C21 | No mandatory isolation coverage check | Rule 9.3 | Medium |
| C22 | No interference-aware day ordering | Rule 9.6 | Medium |
| C23 | DUP uses % multipliers on rep range | RippedBody's autoregulated double progression uses RIR targets, not day types | Medium |
| C24 | Mesocycle duration fixed by `get_mesocycle_length` (4–6 wk) | Strength phases: 6–12, 4–8, 2–4 wk. Specialization: 8–12 wk. Much more varied | Medium |
| C25 | `ProgressionScheme.STALLED = "failed to add load for 2+ sessions"` | Should be 3 sessions for autoregulated; track trend not single sessions (Rule 7.10) | Low |
| C26 | Exercise selector ignores "long muscle length" criterion | Rule 9.8 | Low |
| C27 | No `close_variations()` lookup for swapping | Rule 10.2 | Low |
| C28 | Horizontal + vertical push counted as separate volumes | Rule 10.3 — merge for volume tally | Low |
| C29 | Calves treated like any other muscle | Rule 10.4 — high-frequency exception | Low |
| C30 | `training_days_per_week` lower bound = 2 with no warning | Rule 1.3 — warn at <3 for intermediate+ | Low |

---

## 19. Summary

- **Total codified rules extracted: 90+** (across Sections 1–17, plus the 30-row threshold table in Section 17 and the 30 contradictions in Section 18).
- **Total tables extracted: 18** (RippedBody's Tables 7.1–7.18, plus the RIR table, linear-progression example, novice/intermediate double-progression examples, and the reactive-deload checklist from the Progression article).
- **Two frequency matrices captured in full**: Table 7.1 (Strength, 5 days × 6 freq tiers) and Table 7.2 (Hypertrophy, 5 days × 6 freq tiers, with 5 session-type descriptors).

### Top 10 highest-impact enhancements

1. **Replace single-RPE-per-category with RIR-range-per-(rep-range, exercise-intensity-tier)** based on Tables 7.3 + 7.7. This is the single biggest correctness fix. (Contradictions C1, C2.)
2. **Add the four volume landmarks (MEV/MAV/MRV/ML)** per muscle group as first-class data, plus Table 7.4's time-budget tiers. Drive program volume from these instead of fixed presets. (C12.)
3. **Implement the 11-set-per-muscle-per-session cap** with auto-frequency-bump when exceeded. (C13, Rule 2.6.)
4. **Implement fractional set counting** (primary=1.0, secondary=0.5) so the volume tally matches RippedBody's method. (C16, Rules 2.5, 3.5, 9.4.)
5. **Replace the BLOCK abstraction with Volume → Load → Peak phases**, each with its own (main-lift singles, secondary sets, RPE ramp, duration) from Tables 7.11–7.13. (C8, C9.)
6. **Add Table 7.1 and Table 7.2 as data**, expanding the split catalogue from 8 patterns to ~30 (days × frequency) configurations including muscle-group days, full push, full pull, and high-frequency full body. (C15.)
7. **Implement Autoregulated Double Progression** with the 4 %-per-rep load adjustment, first-set bump trigger, and graduation from LINEAR after 2 missed sessions. (C5, C6, Rules 7.5–7.10.)
8. **Switch deloads from scheduled to reactive**: 5-question self-assessment → ≥2 Yes triggers deload; deload recipe = −30 to −50 % sets, intensity unchanged. (C3, C4, Rules 8.1–8.3.)
9. **Add warm-up set generation** (Table 7.18) with two recipes (≤6-rep targets vs ≥6-rep targets), per-muscle-group warm-up logic, and optional PAPE. (C17, Rule 15.1.)
10. **Add exercise-selection validators**: 6 core patterns covered, 1–3 lifts per pattern, mandatory incline press + elbow-flared row + shoulder-extension row + 6 isolation targets, and an interference-aware day-ordering check. (Rules 9.1–9.3, 9.6, C20, C21, C22.)

### Tables extracted (full text reproduced above)

- **Table 7.1** Strength Frequency Matrix (Section 4)
- **Table 7.2** Hypertrophy Frequency Matrix + 5 session-type descriptors (Section 5)
- **Table 7.3** V·I·F summary of starting recommendations (Section 2, Rule 2.1; Section 6, Rules 6.2–6.4)
- **Table 7.4** Hypertrophy volume tiers by time commitment (Rule 2.2)
- **Table 7.5** Frequency recommendations (Rule 3.2)
- **Table 7.6** Frequency recommendations by volume (Rule 3.1)
- **Table 7.7** Rep + RPE/RIR by exercise type (Rule 6.5)
- **Table 7.8** Hypertrophy training structures for rep-range variation (Rule 7.12)
- **Table 7.9** Specialization phase mesocycles (Rule 12.1)
- **Table 7.10** Example autoregulated double progression (referenced in Rule 7.8)
- **Table 7.11** Volume phase summary (Rule 11.1)
- **Table 7.12** Load phase summary (Rule 11.2)
- **Table 7.13** Peak phase summary (Rule 11.3)
- **Table 7.14** Training-status definitions + rates of progress (Rule 7.11)
- **Table 7.15** Reactive-deload self-assessment flowchart (Rule 8.2)
- **Table 7.16** Exercise-selection recommendations summary (Rules 9.5, 9.6)
- **Table 7.17** Hypertrophy: exercises and muscle groups trained (Rule 9.4)
- **Table 7.18** Warm-up summary guidelines (Rule 15.1)
- **RIR table** (Rule 6.1)
- **Linear Progression example table** (referenced in Rule 7.2)
- **Novice & Intermediate Double Progression example tables** (referenced in Rule 7.11)

### Highest-impact contradictions (recap)

The five most consequential mismatches between RippedBody and the current engine are:

1. **RIR/RPE model** — current single-float-per-category vs RippedBody's range-depending-on-rep-range-and-exercise-type (C1, C2).
2. **Deload model** — current scheduled deload with `sets-=1, rpe-=2` vs reactive deload with `sets × 0.5–0.7, rpe unchanged` (C3, C4).
3. **Progression graduation** — current 10 %-deload-on-single-miss vs RippedBody's "2 missed sessions, then switch to autoregulated double progression" (C5).
4. **Block periodization** — current `accumulation → intensification → deload/peak` vs RippedBody's `Volume → Load → Peak` with very different per-phase parameters (C8, C9).
5. **Volume model** — current engine has no MEV/MAV/MRV landmarks, no 11-set session cap, no fractional set counting, and only 8 split patterns vs the ~30 cells in Tables 7.1 + 7.2 (C12, C13, C15, C16).

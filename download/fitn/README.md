# Fitn — Flutter Mobile Fitness Companion

A mobile fitness app built around a **deterministic, physiology-grounded
engine**. The engine is the product's core value — its formulas, thresholds,
and decision trees are pinned down completely. Everything around it (UI, state,
storage, sync) is specified to a buildable level of detail.

**Stack:** Flutter 3.x + Material 3 · Riverpod 2.x · go_router 14 · Isar 4 ·
Supabase · `fitn_engine` (pure-Dart, runs in `Isolate.run`).

## What's in this repo

```
fitn/
├── fitn_engine/              # Pure-Dart engine package (the "first deliverable")
│   ├── lib/
│   │   ├── fitn_engine.dart  # public API
│   │   └── src/
│   │       ├── models/       # plain-Dart models (enums, profile, preferences, assessment, nutrition, training, meal, fitness_plan)
│   │       ├── assessment/   # body comp, health risk, muscular potential, decision tree
│   │       ├── nutrition/    # RMR, TDEE, calories, macros, hydration, micros, adjustments
│   │       ├── training/     # exercise library, periodization, selector, architect
│   │       ├── meal_plan/    # recipe loader, scorer, scaler, allocator
│   │       ├── utils/        # banker's rounding, units, enum helpers
│   │       ├── errors.dart
│   │       ├── version.dart  # "3.2.0"
│   │       └── engine_data.dart  # JSON asset loader
│   ├── assets/               # JSON data files (1,217 exercises, 8 splits, 40 patterns, ~30 foods, ~225 recipes)
│   ├── test/                 # snapshot + edge-case + allergen tests
│   └── README.md             # engine docs
├── fitn_app/                 # Flutter app
│   ├── lib/
│   │   ├── main.dart
│   │   ├── app.dart          # MaterialApp.router
│   │   ├── router.dart       # go_router config + onboarding redirect
│   │   ├── bootstrap.dart    # Supabase + engine init
│   │   ├── core/             # env, Result, extensions
│   │   ├── engine/           # engine provider + Isolate.run wrapper
│   │   ├── data/
│   │   │   ├── isar/         # collections + repositories (in-memory + SharedPreferences for skeleton)
│   │   │   ├── supabase/     # sync service (workmanager-driven background flush)
│   │   │   └── prefs/        # theme + units preferences
│   │   ├── state/            # app, plan, workout session, progress, auth notifiers
│   │   └── ui/
│   │       ├── theme/        # Material 3 dark-first
│   │       ├── widgets/      # ProgressRing, AnimatedNumber, MacroRing, Skeleton
│   │       ├── shell/        # AppShell + BottomNav (5 tabs)
│   │       ├── onboarding/   # 5-step wizard (Basics → Body → Activity → Goal → Preferences)
│   │       ├── tabs/         # Home, Workouts, Meals, Progress, Profile
│   │       ├── workout/      # full-screen set/rep/weight/RPE logger with rest timer
│   │       ├── exercise_library/  # browse all 1,217 exercises
│   │       ├── auth/         # magic-link + OAuth (Google/Apple) + callback
│   │       └── settings/     # theme, units, sync queue, danger zone
│   └── pubspec.yaml
└── supabase/
    └── schema.sql            # tables + RLS + triggers (apply via Supabase SQL editor)
```

## Quick start

### 1. Run the engine tests

```bash
cd fitn_engine
dart pub get
dart test
```

The engine is fully self-contained — no Flutter, no Supabase, no network.

### 2. Configure Supabase (optional — app runs without it)

1. Create a project at [supabase.com](https://supabase.com).
2. Apply `supabase/schema.sql` via the SQL editor.
3. Enable Email auth (magic-link) + Google + Apple OAuth in Auth settings.
4. Set redirect URL: `com.fitn.app://auth/callback`.
5. Put your project URL + anon key in `fitn_app/lib/core/env.dart` (or pass as
   `--dart-define=SUPABASE_URL=... --dart-define=SUPABASE_ANON_KEY=...`).

> **Note:** The anon key is safe to ship in the app — it's protected by RLS
> policies. The app runs fine without Supabase configured; it just won't sync
> across devices.

### 3. Run the Flutter app

```bash
cd fitn_app
flutter pub get
flutter run --flavor dev   # or: flutter run -d chrome
```

For iOS/Android deep links, add the `com.fitn.app` URL scheme:
- **iOS:** `Info.plist` → `CFBundleURLSchemes` includes `com.fitn.app`.
- **Android:** `AndroidManifest.xml` → `<intent-filter>` with
  `android:scheme="com.fitn.app"`.

## What the app does

1. **Onboards in 5 steps** — minimal friction, sensible defaults, optional
   fields never block.
2. **Generates a plan in <500 ms** — engine runs in an isolate, no spinner
   anxiety.
3. **Works offline** — the plan, exercise library, and recipe database live
   on-device. Sync is a background concern.
4. **Logs workouts** — sets, reps, weight, RPE, rest timer. Daily-use loop.
5. **Tracks progress** — weight log, intake log, workout history, volume
   trends. Engine accepts weight/intake logs as inputs for adaptive TDEE.
6. **Syncs across devices** — sign in, pick up where you left up on another
   phone.
7. **Regenerates gracefully** — when the user's body changes, the plan updates
   without losing history.

## Engine highlights

The engine is the differentiator. It's **deterministic** (same inputs → byte-
identical output) and **grounded in published physiology**:

| Sub-system | Formulas / Sources |
| ---------- | ------------------ |
| Body fat % | User-provided → US Navy circumference (Hodgdon-Beckett 1984) → CUN-BAE |
| FFMI | Kouri 1995 (natural ceiling 25.0, attainable 27.3, likely max 28.0) |
| Health risk | WHR, WHtR, ABSI (NHANES z-scores), IBW (Devine/Robinson/Miller/Hamwi) |
| RMR | Mifflin-St Jeor (default), Katch-McArdle (when BF% known) |
| TDEE | RippedBody activity factors + adaptive TDEE from logs |
| Volume landmarks | MEV/MAV/MRV/ML for 22 muscles (RippedBody) |
| Muscle-gain rates | Lyle McDonald monthly table (×0.5 for women) |
| Decision tree | Sex-specific boundaries + first-match-wins (cut/bulk/recomp/maintenance/reverse-diet) |

**Critical implementation rules** (spec §11):
1. Banker's rounding everywhere (except rep-range math = round-half-up).
2. Vegetarian → vegan recipe mapping (no separate vegetarian tag in DB).
3. Plant-qualifier suppression for allergens (`coconut milk` ≠ dairy).
4. `proposePlan` throws `PartialAssessmentError` if `isPartial == true`.
5. Diet-type protein boosts before rounding: vegan ×1.20, vegetarian ×1.10.
6. 2-meal plans skip breakfast (LUNCH + DINNER 50/50).
7. 5-meal plans interleave snacks (BREAKFAST, SNACK, LUNCH, SNACK, DINNER).
8. Adaptive TDEE requires equal-length logs (skip otherwise).
9. `WEEKS_PER_MONTH = 4.348` (not 4.345).
10. CUN-BAE coefficient is `1.0689` (not the published-paper typo 1.39).
11. Cut rate cap = 1.0% BW/week (even "very_aggressive").
12. Calorie floor 1200 (F) / 1500 (M), applied after deficit computation.
13. Reverse-diet detection requires 30+ days of intake logs.

## Engine data files

The engine loads JSON data from `fitn_engine/assets/` at construction:

| File | Purpose | Count |
| ---- | ------- | ----- |
| `all_exercises.json` | Exercise library | 1,217 |
| `split_designs.json` | Workout split designs | 8 |
| `movement_patterns.json` | Movement-pattern specs | 40 |
| `food_database.json` | Food items for macro-gap fillers | ~30 |
| `recipe_database.json` | Curated recipes (`is_curated=true`) | 12 |
| `recipe_database_uncurated.json` | Uncurated recipes (IDs prefixed `U` on collision) | 197 |
| `pre_post_workout_recipes.json` | Pre/post-workout recipes (4 diets × 2 types × 2 kcal bins) | 16 |

**Note on recipe counts:** The uploaded `recipe_database_uncurated.json`
contains 197 recipes (not the ~305 the spec mentioned). The engine tolerates
whatever count is present — it loads everything and deduplicates by ID. The
`recipe_database.json` (curated) is a small 12-recipe subset synthesized for
this build; in production it would contain the full 79 curated recipes per
spec §9.4.

## Build & deploy

```bash
# Development
flutter run --flavor dev

# Production
flutter build ipa --release            # iOS
flutter build apk --release            # Android
flutter build appbundle --release      # Android (Play Store)
```

### CI/CD (suggested GitHub Actions)
- On PR: `flutter test`, `dart analyze`, `dart format --set-exit-if-changed`,
  `build_runner` (ensure generated files up to date).
- On main: build IPA + APK, upload to TestFlight + Play internal testing.
- Nightly: run snapshot tests to catch regressions.

## What's deferred (spec §12)

- Marketplace / commerce
- Realtime cross-device sync (pull-on-foreground + push-on-write is sufficient
  for launch)
- Social features (sharing, leaderboards)
- Custom exercise / recipe creation (engine uses fixed libraries)
- Keto / paleo diet support (engine doesn't model them)
- Wear OS / watchOS companion
- Apple Health / Google Fit sync
- Adaptive plan adjustments UI (`recommendCutAdjustment` /
  `recommendBulkAdjustment` are implemented in the engine; wire into UI when
  the user has 3+ weeks of weight logs)

## License

Proprietary. See LICENSE.

---

*Built per the Fitn Flutter App Specification v3.2.0.*

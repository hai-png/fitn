# Fitn — Flutter Mobile Fitness Companion

A mobile fitness app built around a **deterministic, physiology-grounded
engine**. The engine is the product's core value — its formulas, thresholds,
and decision trees are pinned down completely. The UI integrates the FitLife Hub
design language with full feature parity to the reference React app.

**Stack:** Flutter 3.x · Riverpod 2.x · go_router 14 · `fitn_engine` (pure-Dart,
runs in `Isolate.run`) · Supabase (auth/sync, optional) · `google_fonts` ·
`fl_chart` · `lucide_icons`.

## Repo structure

```
fitn/
├── fitn_engine/              # Pure-Dart engine package (v3.2.0)
│   ├── lib/
│   │   ├── fitn_engine.dart  # public API barrel
│   │   └── src/
│   │       ├── models/       # enums, profile, preferences, assessment, nutrition, training, meal, fitness_plan
│   │       ├── assessment/   # body comp, health risk, muscular potential, decision tree
│   │       ├── nutrition/    # RMR, TDEE, calories, macros, hydration, micros, adjustments
│   │       ├── training/     # exercise library, periodization, selector, architect
│   │       ├── meal_plan/    # recipe loader, scorer, allocator, allergen constants
│   │       ├── utils/        # banker's rounding, units, enum helpers
│   │       ├── errors.dart
│   │       ├── version.dart  # "3.2.0"
│   │       └── engine_data.dart  # JSON asset loader
│   ├── assets/               # 1,217 exercises, 8 splits, 40 patterns, ~30 foods, ~225 recipes
│   ├── test/                 # 21 snapshot + edge-case + allergen tests
│   └── README.md             # engine docs
├── fitn_app/                 # Flutter app (FitLife Hub design)
│   ├── lib/                  # see fitn_app/README.md for full tree
│   │   ├── core/             # env, result, extensions
│   │   ├── data/             # analytics engine, catalog, domain types, isar, supabase, prefs
│   │   ├── engine/           # engine provider + exercise/recipe data providers
│   │   ├── state/            # Riverpod notifiers (app, workout session, auth)
│   │   └── ui/               # theme, shell, onboarding, 5 tabs, workout, library, auth, settings
│   ├── web/                  # web index.html
│   ├── linux/                # Linux desktop config
│   ├── test/                 # widget smoke test
│   └── README.md             # app docs
└── supabase/
    └── schema.sql            # 5 RLS-protected tables + triggers
```

## Quick start

### 1. Run the engine tests

```bash
cd fitn_engine
dart pub get
dart test    # 21 tests — all must pass
```

### 2. Run the Flutter app

```bash
cd fitn_app
flutter pub get
flutter run                    # dev (web/desktop/mobile)
flutter build web --release    # web build
```

The app runs without Supabase (sync is a no-op). To enable cross-device sync,
set `SUPABASE_URL` / `SUPABASE_ANON_KEY` in `fitn_app/lib/core/env.dart` and
apply `supabase/schema.sql` via the Supabase SQL editor.

## Feature summary (5 tabs)

| Tab | Features |
|-----|----------|
| **Training** | Weekly timeline tracker, day selector, exercise cards with sets/reps/rest/RPE, inline rest timer, program preset selector (5 presets), custom split builder (uses 1,217-exercise DB), video tutorial player modal |
| **Meals Prep** | Meal delivery ordering with day/meals-per-day configurator, auto-generated plan (cycles through ~225 engine recipes filtered by diet + allergens), per-meal swap modal, cart with loyalty discount + delivery fee, checkout flow |
| **Logs** | 4 sub-tabs: **Metrics** (core metrics, rolling 7/30/365-day trends, training focus splits, weight log chart, water log, workout history, lifetime volume tier), **Muscles** (volume zones, balance analysis, interactive body map), **Exercises** (PRs via Epley 1RM, progression analysis, custom set logger using 1,217-exercise DB), **Visuals** (flex/share cards) |
| **Store** | Product grid (apparel/equipment/supplements/accessories), category filter, search, sort, cart drawer, checkout |
| **Profile** | User bio + metrics grid + allergen warning, nutrition blueprint with macro visualizer bars, hydration + timeline summary, paid orders history, plan history with restore, account section (sign in/out), reset assessment |

## Engine data (all loaded from JSON assets)

| File | Count |
|------|-------|
| `all_exercises.json` | 1,217 exercises (759 YouTube + 443 Vimeo + 15 no video) |
| `split_designs.json` | 8 workout split designs |
| `movement_patterns.json` | 40 movement-pattern specs |
| `food_database.json` | ~30 food items for macro-gap fillers |
| `recipe_database.json` | 12 curated recipes |
| `recipe_database_uncurated.json` | 197 uncurated recipes |
| `pre_post_workout_recipes.json` | 16 pre/post-workout recipes |

The app uses these databases via Riverpod providers — no hardcoded exercise or
recipe lists.

## Design system

- **Colors**: `#1A1A1A` ink, `#F9F8F6` cream, `#E63946` red accent, `#EFECE6`
  warm cream outer
- **Typography**: Inter (sans), JetBrains Mono (stats/numbers), Playfair Display
  (italic headlines) — via `google_fonts`
- **Patterns**: Sharp corners (BorderRadius.zero), uppercase tracking-widest
  micro-labels, phone mockup frame on desktop

## Branches

- `main` — original Python `fitness_engine` (the engine audit work)
- `feat/audit-and-feature-parity` — Flutter app + Dart engine (active development)

# Fitn App — Flutter Mobile Fitness Companion

The Flutter frontend for **Fitn**, a mobile fitness companion app built around
a deterministic, physiology-grounded engine. This app integrates the FitLife Hub
design language (cream/ink/red-accent, sharp corners, Playfair Display italic
headlines) with the full feature set of the reference React app.

## Architecture

```
lib/
├── main.dart                    # Entry point — ProviderScope + AppBootstrap
├── app.dart                     # MaterialApp.router (FitnTheme)
├── router.dart                  # go_router config + onboarding redirect
├── bootstrap.dart               # Supabase + engine data init
├── core/
│   ├── env.dart                 # Supabase URL/anon key
│   ├── result.dart              # Result<T> sealed class
│   └── extensions.dart          # DateTime/num helpers
├── data/
│   ├── analytics_engine.dart    # Epley 1RM, rolling trends, PRs, muscle zones
│   ├── catalog.dart             # Marketplace products (commerce)
│   ├── domain_types.dart        # MealProduct, CartItem, Order, ExerciseLog, etc.
│   ├── workout_templates.dart   # Program presets (5 pre-built programs)
│   ├── isar/
│   │   ├── collections/         # ProfileRecord, PlanRecord, WorkoutLogRecord, etc.
│   │   └── repositories/        # In-memory + SharedPreferences persistence
│   ├── supabase/sync/           # Background sync (workmanager)
│   └── prefs/                   # Theme + units preferences
├── engine/
│   └── engine_provider.dart     # Engine FutureProvider + exercise/recipe data providers
├── state/
│   └── app_state.dart           # AppState + AppNotifier + WorkoutSession + Auth
└── ui/
    ├── theme/fitn_design.dart   # FitnColors, FitnText, FitnTheme, FitnCard
    ├── shell/app_shell.dart     # Phone mockup frame + 5-tab bottom nav
    ├── onboarding/              # 4-step wizard (basics → goal → gym finder → diet)
    ├── tabs/
    │   ├── training_tab.dart    # Program timeline + day selector + exercise cards + split builder
    │   ├── meals_tab.dart       # Meal delivery ordering (engine recipes + cart + checkout)
    │   ├── progress_tab.dart    # 4 sub-tabs: metrics / muscles / exercises / visuals
    │   ├── marketplace_tab.dart # Product store + cart drawer + checkout
    │   └── profile_tab.dart     # Bio + nutrition blueprint + orders + plan history
    ├── workout/                 # Full-screen set/rep/weight/RPE logger + rest timer
    ├── exercise_library/        # Browse all 1,217 exercises
    ├── auth/                    # Magic-link + OAuth (Google/Apple)
    └── settings/                # Theme, units, sync, danger zone
```

## Key design decisions

- **Engine-driven data**: The app pulls exercises (1,217) and recipes (~225)
  from the `fitn_engine` package via Riverpod providers — no hardcoded lists.
- **FitLife Hub design**: Cream background (#F9F8F6), ink text (#1A1A1A), red
  accent (#E63946). Sharp corners everywhere. Inter (sans) + JetBrains Mono
  (stats) + Playfair Display (italic headlines) via `google_fonts`.
- **Phone mockup frame**: On desktop, the app renders in a centered 410px-wide
  phone frame with a status bar (time/wifi/battery).
- **5 tabs**: Training, Meals Prep, Logs, Store, Profile (matches reference app).

## Running

```bash
cd fitn_app
flutter pub get
flutter run                    # dev
flutter build web --release    # web build
flutter build apk --release    # Android
flutter build ipa --release    # iOS
```

The app runs without Supabase configured (sync is a no-op). To enable
cross-device sync, set `SUPABASE_URL` and `SUPABASE_ANON_KEY` in
`lib/core/env.dart` and apply `supabase/schema.sql`.

## Dependencies

Key packages: `flutter_riverpod` (state), `go_router` (navigation),
`fitn_engine` (engine, local path dep), `fl_chart` (charts),
`google_fonts` (typography), `lucide_icons` (icons), `supabase_flutter` (auth/
sync), `shared_preferences` (local persistence).

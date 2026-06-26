# fitn Mobile App — Comprehensive Build Plan

> Version: 1.0 | Date: 2026-06-27 | Target: iOS 16+ / Android 13+
> Engine: `fitn` v3.1.5 (deterministic Python fitness engine)

## 1. Executive summary

This plan details how to wrap the existing `fitn` Python engine in a production-grade cross-platform mobile app. The core engine stays in Python (zero third-party runtime deps, deterministic, ~1s per plan); the mobile app is a thin UI layer that calls the engine via a local embedded runtime or a lightweight backend.

**Recommended stack**: React Native (Expo) + Python backend (FastAPI) OR Kivy/Nui for fully-offline embedded Python. We recommend the **React Native + FastAPI** approach for best UX, app-store acceptance, and team scalability.

**Timeline**: 16 weeks (4 months) from zero to App Store + Play Store submission, with a 6-week MVP milestone.

**Budget estimate**: $180K–$280K (2-3 engineers × 4 months + design + infra), or ~$40K solo with a 6-month timeline.

---

## 2. Architecture decision

### Option A: React Native + FastAPI backend (RECOMMENDED)

```
┌─────────────────────────────────────────────────────┐
│  Mobile App (React Native / Expo)                   │
│  ┌───────────────────────────────────────────────┐  │
│  │  UI Layer (screens, navigation, state)        │  │
│  │  State: Zustand/Redux + AsyncStorage          │  │
│  │  Offline: SQLite (watermelondb) + queue       │  │
│  └──────────────────┬────────────────────────────┘  │
│                     │ HTTPS (REST/JSON)              │
│  ┌──────────────────▼────────────────────────────┐  │
│  │  API Client (axios + retry + auth)            │  │
│  └──────────────────┬────────────────────────────┘  │
└─────────────────────┼───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│  Backend (FastAPI on Python 3.12)                    │
│  ┌───────────────────────────────────────────────┐  │
│  │  REST API: /assess, /plan, /adapt             │  │
│  │  Auth: JWT + refresh tokens                   │  │
│  │  Rate limiting: 100 req/min/user              │  │
│  └──────────────────┬────────────────────────────┘  │
│  ┌──────────────────▼────────────────────────────┐  │
│  │  fitn engine (existing Python package)        │  │
│  │  - assess_profile(), propose_plan()           │  │
│  │  - No changes to engine code                  │  │
│  └──────────────────┬────────────────────────────┘  │
│  ┌──────────────────▼────────────────────────────┐  │
│  │  PostgreSQL (users, plans, logs)              │  │
│  │  Redis (cache, rate limit, sessions)          │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Pros**: Best UX, native performance, app-store friendly, team-scalable, offline-capable, easy A/B testing.
**Cons**: Requires backend infra, two codebases (RN + Python), network dependency for plan generation.

### Option B: Embedded Python (Kivy / BeeWare / chaquopy)

```
┌─────────────────────────────────────────────────────┐
│  Mobile App (Kivy or BeeWare)                       │
│  ┌───────────────────────────────────────────────┐  │
│  │  UI Layer (KivyMD widgets)                    │  │
│  └──────────────────┬────────────────────────────┘  │
│  ┌──────────────────▼────────────────────────────┐  │
│  │  Embedded Python runtime (chaquopy/Pyodide)   │  │
│  │  fitn engine runs locally on-device           │  │
│  └──────────────────┬────────────────────────────┘  │
│  ┌──────────────────▼────────────────────────────┐  │
│  │  SQLite (local user data + plans)             │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Pros**: Fully offline, no backend, lower infra cost.
**Cons**: Worse UX (Kivy is not native-feeling), larger APK/IPA (50-80MB Python runtime), harder app-store review, slower iteration, no analytics/A/B testing.

### Option C: React Native + on-device Python via Pyodide (experimental)

Hybrid: React Native UI + Pyodide (WebAssembly Python) running fitn in a JS worker. Promising but immature — Pyodide's WASM bundle is ~10MB and startup is 2-3s. Worth experimenting with for v2.

### Decision: **Option A**

Rationale: fitn is a planning engine, not a real-time widget. A 1-second API call is acceptable UX. The backend gives us analytics, A/B testing, and the ability to update the engine without app-store resubmission. React Native gives us native UX with a single codebase for iOS + Android.

---

## 3. Feature roadmap

### MVP (Weeks 1-6) — "Generate a plan"

| Feature | Description | Priority |
|---|---|---|
| Onboarding | 6-screen wizard: age, sex, height, weight, activity, goal, training days, equipment | P0 |
| Assessment | Display BF%, BMI, FFMI, health risk, recommended strategy | P0 |
| Plan generation | Call `/plan` endpoint; show loading state; display nutrition + training + meal plan summary | P0 |
| Nutrition view | TDEE, target calories, macros (P/C/F), hydration, fiber, timeline | P0 |
| Training view | Split type, mesocycles, workouts (exercises with sets/reps/RPE) | P0 |
| Meal plan view | 7-day meal plan with recipe names, macros per meal, weekly summary | P0 |
| Save plan | Persist to SQLite + backend; offline access | P0 |
| Auth | Email/password + Apple Sign In + Google Sign In | P0 |

### v1.0 (Weeks 7-12) — "Use the plan daily"

| Feature | Description | Priority |
|---|---|---|
| Daily log | Log weight, calories, workouts completed; track streaks | P0 |
| Workout player | Step-through mode: current exercise, sets completed, RPE entry, rest timer | P0 |
| Meal swap | Tap a meal → see top 5 alternatives (v3.1.5 feature) → swap with one tap | P0 |
| Recipe detail | Full ingredients, instructions, nutrition, image, selection reason | P0 |
| Progress charts | Weight trend, BF% estimate, workout volume, calorie adherence | P1 |
| Adapt plan | Re-assess every 2 weeks; auto-adjust calories based on weight trend | P1 |
| Push notifications | Workout reminders, meal prep reminders, weekly check-in | P1 |
| Profile edit | Change goal, activity, equipment; regenerate plan | P1 |

### v1.5 (Weeks 13-16) — "Polish & differentiate"

| Feature | Description | Priority |
|---|---|---|
| Apple Health / Google Fit | Sync weight, workouts, calories burned | P1 |
| Social | Share plan progress; friend leaderboards (opt-in) | P2 |
| Premium tier | Recipe DB access (500+ recipes), custom splits, advanced analytics | P2 |
| Widget | iOS home screen widget: today's workout / calorie target | P2 |
| Apple Watch / Wear OS | Workout timer, set counter, heart rate | P2 |
| Multi-language | English, Amharic (Ethiopian cuisine focus), Spanish, Portuguese | P2 |

### v2.0 (post-launch) — "AI coach"

| Feature | Description | Priority |
|---|---|---|
| LLM coach | Chat-based Q&A: "Why is my protein 180g?", "Can I swap chicken for tofu?" | P2 |
| Photo food logging | Snap a meal → vision model estimates macros | P2 |
| Adaptive TDEE | Use the v3.1.2 `update_tdee_with_logs` with real weight/intake logs | P2 |
| Barcode scanner | Scan food barcodes → log calories instantly | P3 |

---

## 4. Technical architecture

### 4.1 Backend (FastAPI)

```
backend/
├── app/
│   ├── main.py              # FastAPI app, CORS, middleware
│   ├── api/
│   │   ├── auth.py          # /auth/register, /auth/login, /auth/refresh
│   │   ├── assess.py        # POST /assess → AssessmentResult
│   │   ├── plan.py          # POST /plan → FitnessPlan
│   │   ├── adapt.py         # POST /adapt (re-assess with new logs)
│   │   ├── user.py          # GET/PUT /user (profile)
│   │   └── logs.py          # POST /logs (weight, intake, workouts)
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/
│   │   ├── fitn_service.py  # Wraps fitn engine calls
│   │   ├── auth_service.py  # JWT, password hashing
│   │   └── cache_service.py # Redis caching
│   └── config.py            # env vars, DB URL, Redis URL
├── tests/
├── requirements.txt
└── Dockerfile
```

**Key endpoints**:

| Method | Path | Body | Response | Notes |
|---|---|---|---|---|
| POST | `/auth/register` | `{email, password}` | `{user_id, token}` | bcrypt + JWT |
| POST | `/auth/login` | `{email, password}` | `{user_id, token, refresh}` | |
| POST | `/assess` | `UserProfile` | `AssessmentResult` | calls `assess_profile()` |
| POST | `/plan` | `{profile, assessment, preferences}` | `FitnessPlan` | calls `propose_plan()` |
| POST | `/adapt` | `{user_id, weight_log, intake_log}` | `{new_tdee, new_targets}` | calls `update_tdee_with_logs()` |
| GET | `/user` | — | `UserProfile` | |
| PUT | `/user` | `UserProfile` | `{updated: true}` | |
| POST | `/logs/weight` | `[{date, weight_kg}]` | `{saved: n}` | |
| POST | `/logs/intake` | `[{date, kcal}]` | `{saved: n}` | |
| GET | `/recipes` | `?diet=&meal_type=&cuisine=` | `[Recipe]` | paginated |

**Caching**: Assessment + plan results cached by `hash(UserProfile + PlanPreferences)` in Redis (TTL 24h). Identical profiles get instant results.

**Rate limiting**: 100 req/min/user. Plan generation is CPU-bound (~1s); protect against abuse.

### 4.2 Mobile app (React Native / Expo)

```
mobile/
├── app/                     # Expo Router file-based routing
│   ├── (auth)/
│   │   ├── login.tsx
│   │   └── register.tsx
│   ├── (tabs)/
│   │   ├── index.tsx        # Home: today's summary
│   │   ├── nutrition.tsx    # Macros, hydration, timeline
│   │   ├── training.tsx     # Workouts, exercise list
│   │   ├── meals.tsx        # 7-day meal plan
│   │   └── profile.tsx      # Settings, edit profile
│   ├── onboarding/
│   │   ├── step-1-basics.tsx
│   │   ├── step-2-activity.tsx
│   │   ├── step-3-goal.tsx
│   │   └── step-4-summary.tsx
│   ├── workout-player.tsx   # Full-screen workout mode
│   ├── recipe-detail.tsx    # Recipe + ingredients + swap
│   └── progress.tsx         # Charts
├── components/
│   ├── ui/                  # Buttons, cards, inputs (shadcn-inspired)
│   ├── charts/              # Weight trend, macro donut, volume bar
│   └── workout/             # SetRow, RestTimer, ExerciseCard
├── stores/                  # Zustand stores
│   ├── authStore.ts
│   ├── profileStore.ts
│   ├── planStore.ts
│   └── logStore.ts
├── services/
│   ├── api.ts               # axios client + interceptors
│   ├── storage.ts           # AsyncStorage + SQLite wrappers
│   └── notifications.ts     # push notification scheduling
├── hooks/
│   ├── usePlan.ts           # fetch + cache plan
│   ├── useOfflineQueue.ts   # queue mutations when offline
│   └── useStreak.ts         # daily log streak tracking
├── lib/
│   ├── types.ts             # TypeScript types matching backend schemas
│   ├── constants.ts         # meal types, diet tags, goals
│   └── format.ts            # kcal, g, date formatters
└── assets/
    ├── images/
    └── fonts/
```

**State management**: Zustand (simpler than Redux, excellent TS support). Persist to AsyncStorage.

**Offline-first**: SQLite via `expo-sqlite`. Queue mutations when offline; sync when online. Plans cached locally so the app works fully offline after first generation.

**Navigation**: Expo Router (file-based, like Next.js). Tab navigator for main screens + stack for detail screens.

**Styling**: NativeWind (Tailwind for React Native) + shadcn-inspired component library. Dark mode first.

### 4.3 Database schema (PostgreSQL)

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User profiles (versioned — keep history)
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    profile_data JSONB NOT NULL,  -- full UserProfile dict
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Assessments + plans (versioned)
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    profile_id UUID REFERENCES user_profiles(id),
    result JSONB NOT NULL,  -- AssessmentResult
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    assessment_id UUID REFERENCES assessments(id),
    preferences JSONB NOT NULL,
    plan JSONB NOT NULL,  -- FitnessPlan
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Daily logs
CREATE TABLE weight_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    date DATE NOT NULL,
    weight_kg FLOAT NOT NULL,
    UNIQUE(user_id, date)
);

CREATE TABLE intake_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    date DATE NOT NULL,
    kcal INT NOT NULL,
    protein_g FLOAT, carb_g FLOAT, fat_g FLOAT,
    UNIQUE(user_id, date)
);

CREATE TABLE workout_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    date DATE NOT NULL,
    workout_data JSONB NOT NULL,  -- completed exercises, sets, RPE
    duration_min INT,
    UNIQUE(user_id, date)
);

-- Indexes
CREATE INDEX idx_plans_user_active ON plans(user_id) WHERE is_active = TRUE;
CREATE INDEX idx_weight_logs_user_date ON weight_logs(user_id, date DESC);
```

---

## 5. Development phases

### Phase 1: Foundation (Weeks 1-2)

**Backend**:
- Set up FastAPI project with Docker, PostgreSQL, Redis
- Implement `/auth/register`, `/auth/login`, `/auth/refresh` (JWT + bcrypt)
- Wrap `fitn` engine in `fitn_service.py` with `/assess` and `/plan` endpoints
- Write integration tests (pytest + httpx)

**Mobile**:
- Initialize Expo project with TypeScript + Tailwind
- Set up navigation (Expo Router) with auth flow
- Build login + register screens
- Implement API client with auth interceptor + token refresh

**Deliverable**: User can register, log in, and see a placeholder home screen.

### Phase 2: MVP core (Weeks 3-4)

**Backend**:
- Implement `/user` GET/PUT (profile CRUD)
- Add Redis caching for assessments + plans
- Rate limiting middleware

**Mobile**:
- Build onboarding wizard (4 steps → UserProfile)
- Build home screen: assessment summary + "Generate Plan" button
- Build plan display: nutrition / training / meals tabs
- Zustand stores: auth, profile, plan
- SQLite offline cache for plans

**Deliverable**: User can onboard, generate a plan, and view it offline. **This is the MVP milestone.**

### Phase 3: Daily use (Weeks 5-8)

**Backend**:
- Implement `/logs/weight`, `/logs/intake`, `/logs/workout`
- Implement `/adapt` (re-assess with logs → new TDEE + targets)

**Mobile**:
- Daily log screen: weight + calories + workout checkbox
- Workout player: step-through exercises, set tracker, rest timer, RPE entry
- Meal detail: ingredients, instructions, "swap" button
- Meal swap: show top 5 alternatives (v3.1.5), tap to swap
- Progress charts: weight trend, calorie adherence, workout volume
- Push notifications: workout reminder, daily log reminder

**Deliverable**: User can use the app daily for workouts + logging.

### Phase 4: Polish (Weeks 9-12)

**Backend**:
- Apple Health / Google Fit sync endpoints
- Analytics events (mixpanel/posthog)
- A/B testing infra (feature flags)

**Mobile**:
- Apple Health / Google Fit integration (read weight + write workouts)
- Dark mode + dynamic type
- App store screenshots + metadata
- Beta testing via TestFlight + Play Internal Testing
- Crash reporting (Sentry)
- Performance optimization (startup < 2s, plan gen < 1.5s)

**Deliverable**: App store-ready build submitted for review.

### Phase 5: Launch + iterate (Weeks 13-16)

- App store review (1-2 weeks)
- Marketing site (Next.js landing page)
- Onboarding A/B test (2 variants)
- Bug fix sprints based on beta feedback
- v1.5 feature work begins (social, premium tier, widgets)

**Deliverable**: App live on App Store + Play Store. v1.5 roadmap locked.

---

## 6. UI/UX design

### 6.1 Design system

- **Colors**: Dark-first. Primary: `#10b981` (emerald, health/fitness vibe). Background: `#0a0a0a`. Card: `#171717`.
- **Typography**: Inter (body) + Inter Display (headings). Dynamic Type support.
- **Spacing**: 4/8/12/16/24/32 px scale.
- **Components**: shadcn-inspired — Card, Button (primary/secondary/ghost), Input, Select, Sheet (bottom sheet), Toast.
- **Iconography**: Lucide icons (consistent with shadcn).
- **Charts**: Victory Native (React Native chart library) — weight line chart, macro donut, volume bar chart.

### 6.2 Key screens

**Onboarding (4 steps)**:
- Step 1: "Tell us about you" — age, sex, height, weight (slider + input)
- Step 2: "Your activity" — activity level (5 cards), training days (2-6 picker), equipment (3 cards)
- Step 3: "Your goal" — fat_loss / muscle_gain / recomp / maintenance / strength (5 cards with icons)
- Step 4: Summary → "Generate my plan" CTA

**Home (today's view)**:
- Top: "Good morning, [name]" + date
- Card 1: Today's calorie target + consumed (donut chart)
- Card 2: Today's workout (or "Rest day — focus on recovery")
- Card 3: Macro progress (P/C/F bars)
- Card 4: Weight trend (7-day sparkline)
- Bottom: Tab bar (Home / Nutrition / Training / Meals / Profile)

**Workout player**:
- Full-screen, immersive
- Top: workout name + day number + progress (3/8 exercises)
- Center: current exercise card — name, sets×reps, RPE target, image/video
- Set tracker: rows of [set #] [reps achieved] [RPE] [checkmark]
- Rest timer: circular countdown between sets
- Bottom: "Next exercise" / "Skip" / "Finish workout"

**Meal plan (7-day)**:
- Horizontal swipeable day selector (Mon-Sun)
- Vertical list of meals for selected day
- Each meal: name, kcal, macros, recipe image thumbnail
- Tap meal → recipe detail (ingredients, instructions, swap button)
- "Swap" button → bottom sheet with top 5 alternatives + similarity scores

**Recipe detail**:
- Hero image
- Title + cuisine + diet tags
- "Why this recipe?" → selection_reason (v3.1.5)
- Nutrition: kcal, P/C/F/fiber per serving
- Ingredients list (with serving size)
- Instructions (numbered)
- "Swap this recipe" → alternatives sheet
- "Add to shopping list" button

---

## 7. Data flow

### 7.1 Plan generation flow

```
User completes onboarding
  → mobile validates UserProfile
  → POST /plan {profile, assessment, preferences}
  → backend calls fitn.propose_plan()
  → ~1 second
  → backend caches result in Redis (key = hash(profile+prefs))
  → backend saves to PostgreSQL (plans table)
  → returns FitnessPlan JSON
  → mobile saves to SQLite (offline cache)
  → mobile navigates to home screen
```

### 7.2 Daily logging flow

```
User logs weight (e.g. 81.5 kg)
  → mobile saves to SQLite immediately
  → mobile queues sync if offline
  → POST /logs/weight {date, weight_kg}
  → backend saves to weight_logs table
  → if 7+ days of logs: trigger /adapt
  → /adapt calls fitn.update_tdee_with_logs()
  → if TDEE shifted >5%: push notification "Your plan has been updated"
  → mobile fetches new active plan
```

### 7.3 Offline flow

```
User opens app (no network)
  → mobile reads last-known plan from SQLite
  → shows offline banner ("You're offline — showing last plan")
  → user can log weight/workouts (queued)
  → user can view recipes (cached)
  → user CANNOT generate new plan (requires backend)
  → when online: sync queue + fetch latest plan
```

---

## 8. Testing strategy

### 8.1 Backend tests

- **Unit tests**: `fitn_service` wrappers, auth logic, caching. Target 90% coverage (matches engine).
- **Integration tests**: Each endpoint with real PostgreSQL + Redis (testcontainers).
- **Load tests**: k6 scripts — 1000 concurrent plan generations, p95 < 2s.
- **Security tests**: OWASP top 10 scan (ZAP), JWT tampering, SQL injection.

### 8.2 Mobile tests

- **Unit tests**: Jest + React Native Testing Library. Test stores, hooks, formatters.
- **Component tests**: Snapshot + interaction tests for each component.
- **E2E tests**: Detox (iOS + Android) — full onboarding → plan generation → daily log flow.
- **Device tests**: Test on iPhone SE (smallest), iPhone 15 Pro, Pixel 7, Galaxy S23, iPad mini.

### 8.3 Engine tests (existing)

The `fitn` engine already has 1272 tests at 90% coverage. The mobile app's `fitn_service` wrapper adds a thin layer that:
- Validates input JSON matches `UserProfile` schema
- Calls `assess_profile()` / `propose_plan()` / `update_tdee_with_logs()`
- Validates output JSON matches `AssessmentResult` / `FitnessPlan` / `TDEEResult` schema

Wrapper tests focus on serialization round-trips, not engine logic (already covered).

---

## 9. Deployment & infrastructure

### 9.1 Backend deployment

- **Host**: Fly.io or Railway (containerized FastAPI). Choose Fly.io for multi-region.
- **Database**: Neon (serverless PostgreSQL) — generous free tier, branching for staging.
- **Cache**: Upstash (serverless Redis) — pay per request.
- **CDN**: Cloudflare (recipe images, app icons).
- **Monitoring**: Sentry (errors) + Grafana Cloud (metrics) + Logtail (logs).

**Cost estimate** (1000 users):
- Fly.io: 2 × shared-cpu-1x (256MB) = $4/mo
- Neon: free tier (0.5GB) → $19/mo at scale
- Upstash: free tier (10K cmds/day) → $10/mo at scale
- Sentry: free tier (5K errors/mo) → $26/mo at scale
- **Total**: ~$60/mo at 1000 users, ~$200/mo at 10K users

### 9.2 Mobile deployment

- **iOS**: App Store Connect + TestFlight. $99/yr Apple Developer Program.
- **Android**: Play Console. $25 one-time fee. Internal testing → closed testing → production.
- **OTA updates**: Expo Updates (push JS bundle updates without app-store resubmission).
- **Code signing**: Fastlane Match (shared signing certificates).

### 9.3 CI/CD

```
GitHub Actions:
  backend-ci:
    - on: push to main, PR
    - run: pytest --cov, ruff, mypy
    - build: Docker image → ghcr.io
  backend-deploy:
    - on: tag v*.*.*
    - fly deploy --image ghcr.io/...:sha
  mobile-ci:
    - on: push to main, PR
    - run: jest, eslint, tsc
    - build: eas build --platform ios+android
  mobile-deploy:
    - on: tag v*.*.*
    - fastlane beta (TestFlight + Play Internal)
```

---

## 10. Monetization

### Free tier
- Full assessment + plan generation
- 7-day meal plan with 79 curated recipes
- Daily logging (weight, calories, workouts)
- Progress charts (30-day history)

### Premium tier ($9.99/mo or $79/yr)
- 500+ recipe database (uncurated pool + future additions)
- Custom training splits (muscle focus, custom exercise selection)
- Advanced analytics (12-month trends, volume landmarks, MRV warnings)
- Adaptive TDEE with weight/intake logs (v3.1.2 feature)
- Apple Health / Google Fit sync
- Priority plan generation (skip queue during peak)
- LLM coach (v2.0 feature)

**Revenue projection** (conservative):
- 10K free users → 3% conversion → 300 paid → $2,700/mo
- 50K free users → 3% conversion → 1500 paid → $13,500/mo
- Break-even at ~200 paid users ($1,800/mo vs ~$200/mo infra)

---

## 11. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| App store rejection (Guideline 1.4.1 — safety) | Medium | High | Add medical disclaimer; remove any "medical advice" language; submit for pre-review |
| Engine too slow for real-time UX | Low | Medium | Cache aggressively; show loading animation; 1s is acceptable |
| Recipe DB copyright issues | Medium | High | All recipes sourced from public sites (Trifecta, MuscleAndStrength, EthiopianFood.org); add attribution in recipe detail |
| User data breach | Low | Critical | bcrypt passwords, JWT short TTL, no PII in logs, GDPR-compliant deletion endpoint |
| Backend downtime | Medium | High | Multi-region Fly.io deploy; health checks; auto-restart; status page |
| Offline sync conflicts | Medium | Medium | Last-write-wins for logs; plans are immutable (new version replaces old) |
| Apple/Google API changes | Low | Medium | Use Expo (abstracts native APIs); pin SDK versions; test before upgrade |
| User churn (boredom) | High | Medium | Push notifications, streaks, weekly check-ins, social features (v1.5) |

---

## 12. Success metrics

### North star metric
**Weekly active plan-viewers** (% of users who view their plan ≥1× per week). Target: 40%+ at 30 days, 25%+ at 90 days.

### Supporting metrics

| Metric | Target (30d) | Target (90d) |
|---|---|---|
| Onboarding completion | 70% | 75% |
| Plan generation | 60% of onboarded | 65% |
| Daily log retention (D1) | 50% | 55% |
| Daily log retention (D7) | 30% | 35% |
| Daily log retention (D30) | 15% | 20% |
| Workout completion | 2.5 workouts/wk | 3 workouts/wk |
| Meal swap usage | 20% of meals | 25% |
| Crash-free sessions | 99.5% | 99.8% |
| App store rating | 4.3+ | 4.5+ |

---

## 13. Team & roles

### Lean team (MVP → v1.0)

| Role | FTE | Responsibilities |
|---|---|---|
| Tech lead / full-stack | 1.0 | Backend + mobile architecture, code review, deployment |
| Mobile engineer | 1.0 | React Native screens, state, offline, push notifications |
| Designer | 0.5 | UI/UX, design system, app store assets |
| Product manager | 0.3 | Roadmap, user research, analytics, app store listing |

### Extended team (v1.5+)

| Role | FTE | When |
|---|---|---|
| Backend engineer | 1.0 | v1.5 (social, premium tier) |
| QA engineer | 0.5 | v1.0 launch |
| Data scientist | 0.3 | v2.0 (adaptive TDEE, LLM coach) |
| Marketing | 0.5 | Post-launch |

---

## 14. Legal & compliance

- **Privacy policy**: Required by App Store + Play Store. Template: Termly or iubenda.
- **Terms of service**: Limit liability; no medical advice disclaimer.
- **GDPR**: Data export endpoint (`GET /user/data`); deletion endpoint (`DELETE /user`).
- **CCPA**: "Do not sell my info" link (we don't sell data, but include for compliance).
- **Apple App Tracking Transparency (ATT)**: If we add analytics/tracking, request permission.
- **Health data**: Apple Health / Google Fit data stays on-device unless user explicitly syncs.

---

## 15. Next actions

1. **Week 0 (this week)**: Validate this plan with stakeholders. Set up GitHub repo structure (`fitn-app/mobile`, `fitn-app/backend`). Buy Apple Developer Program + Play Console.
2. **Week 1**: Backend foundation (FastAPI + Docker + PostgreSQL + Redis + auth). Mobile foundation (Expo + navigation + auth screens).
3. **Week 2**: First end-to-end: user registers → onboards → generates plan → sees it on home screen.
4. **Week 6**: MVP internal demo. Start TestFlight beta with 10 testers.
5. **Week 12**: Submit to App Store + Play Store.
6. **Week 16**: Public launch.

---

## Appendix A: fitn engine API surface

The mobile app uses these public APIs from the `fitn` engine:

```python
from fitness_engine import (
    UserProfile, PlanPreferences, assess_profile, propose_plan,
)
from fitness_engine.nutrition.tdee import update_tdee_with_logs
from fitness_engine.meal_plan.recipe_loader import recipes_by_filters

# Assessment
assessment = assess_profile(profile)

# Plan generation
plan = propose_plan(profile, assessment, preferences)

# Adaptive TDEE (v3.1.2)
new_tdee = update_tdee_with_logs(
    tdee=prior_tdee,
    avg_intake_kcal=avg_intake,
    weight_start_kg=weight_log[0],
    weight_end_kg=weight_log[-1],
    n_days=len(weight_log),
)

# Recipe browsing
recipes = recipes_by_filters(
    meal_type="breakfast",
    diet_type="OMNI",
    cuisine="ethiopian",
    exclude_ids=used_today,
)
```

All inputs/outputs are JSON-serializable via `to_dict()` methods, making them trivial to pass over HTTP.

## Appendix B: Existing test coverage

The `fitn` engine ships with 1272 tests at 90% coverage. The mobile app inherits this coverage for free — no need to re-test engine logic. The backend `fitn_service` wrapper adds ~50 tests for serialization + endpoint behavior.

## Appendix C: Recipe DB ready for mobile

The v3.1.5 recipe DB includes:
- 79 curated recipes + 305 uncurated (schema B, engine-ready)
- `selection_reason` per recipe (v3.1.5 Task 3) — surfaces in UI as "Why this recipe?"
- `top_alternatives` per recipe (v3.1.5 Task 3) — powers the "swap" feature
- `allergens` extracted from ingredients — powers allergen filtering
- `goal_fit` derived from macros — powers "recipes for cutting/bulking"
- `protein_density` + `calorie_density` — powers recipe sorting
- Ethiopian cultural flags (`fasting_yetsom`, `injera_accompaniment`)

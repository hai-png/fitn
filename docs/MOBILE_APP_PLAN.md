# fitn — All-in-One Mobile Fitness App Plan

> **Value proposition**: Making fitness easy, convenient, and everything you need in one place.
>
> **Three propositions**:
> 1. **Exercise plan** — free for every user (assessment + personalized training plan)
> 2. **Meal plan** — paid delivered meal service (chef-prepared meals matching your macros, delivered to your door)
> 3. **Marketplace** — supplements, equipment, wearables, and fitness services from vetted partners
>
> **Monetization**: Free users get assessment + training plan forever. Paid subscribers get delivered meals + marketplace discounts + premium features.

---

## 1. Executive summary

**fitn** is an all-in-one mobile fitness app that eliminates the friction between knowing what to do and actually doing it. Most fitness apps stop at "here's your plan" — fitn goes further by delivering the actual food to your door and curating everything else you need (supplements, equipment, coaching) in a built-in marketplace.

**Why this wins**:
- **Convenience**: Users don't have to meal-prep, grocery-shop, or research supplements. The app handles the entire fitness lifestyle.
- **Accountability**: Delivered meals remove the #1 reason people fail diets — they don't have the right food available.
- **Revenue diversity**: Subscription (meals) + transaction (marketplace) + freemium (training plans) = 3 revenue streams from one user.

**Tech foundation**: The existing `fitn` Python engine (v3.1.5, 1272 tests, 90% coverage, deterministic) powers the assessment + training plan + meal plan generation. The mobile app wraps this in a React Native shell with a FastAPI backend, adding meal-delivery logistics and a marketplace layer on top.

**Timeline**: 20 weeks (5 months) to launch, with an 8-week MVP (free training plan only).

**Budget**: $300K–$450K (3-4 engineers + designer + ops + meal-delivery infrastructure).

---

## 2. The three propositions

### Proposition 1: Exercise plan (FREE — every user)

**What users get**:
- 6-screen onboarding assessment (age, sex, height, weight, activity, goal, training days, equipment)
- Body composition analysis (BF%, BMI, FFMI, health risk score)
- Personalized training plan (split design, periodization, exercise selection, volume landmarks)
- Daily workout player with set/rep/RPE tracking, rest timer, progression logic
- Adaptive re-assessment every 2-4 weeks based on logged progress

**Why it's free**: The training plan is the hook. It demonstrates the engine's intelligence, builds trust, and creates the user base for the paid meal delivery + marketplace. The marginal cost of generating a training plan is ~$0 (1 second of CPU time).

**Engine integration**: Directly calls `assess_profile()` + `propose_plan()` from the `fitn` engine. No new engine code needed — the existing API is production-ready.

### Proposition 2: Meal plan — delivered (PAID subscription)

**What users get**:
- Personalized macro targets (calories, protein, carb, fat, fiber, hydration) computed by the `fitn` engine
- Chef-prepared meals matching their exact macros, delivered daily or weekly
- 7-day rotating menu with cuisine preferences (Ethiopian, American, Mexican, Italian, Thai, Mediterranean, Indian, Japanese, Korean, Chinese)
- Allergen filtering (dairy, eggs, gluten, nuts, peanuts, soy, shellfish, fish, sesame)
- Portion-controlled meals that hit macro targets within ±5%
- "Swap this meal" feature powered by the recipe DB's `top_alternatives` (v3.1.5)
- Delivery tracking (real-time ETA, temperature-controlled packaging)

**Subscription tiers**:
| Tier | Price | Meals/wk | Delivery |
|---|---|---|---|
| Starter | $89/wk | 7 (lunch + dinner, 5 days) | Weekly |
| Standard | $149/wk | 14 (breakfast + lunch + dinner, 5 days) | Twice/week |
| Full | $219/wk | 21 (all meals, 7 days) | Daily (AM) |
| Custom | $269/wk | 21 + 2 snacks + pre/post workout | Daily (AM + PM) |

**Why it works**: The `fitn` engine already generates precise macro targets and 7-day meal plans with recipe scaling. The delivery layer is a logistics + kitchen partnership problem, not an engine problem. The engine's output (macros per meal, recipe IDs, ingredient lists) becomes the kitchen's production spec.

**Kitchen model** (choose one):
- **Option A — Ghost kitchen partnership**: Partner with a cloud-kitchen operator (e.g. Kitchen United, Zuul) in each launch city. They cook to our specs, we handle the app + delivery.
- **Option B — White-label meal prep**: Partner with an existing meal-prep company (e.g. Factor, Freshly, Trifecta) — they already have the kitchen + delivery infra. We provide the macro-precise recipes; they produce + deliver.
- **Option C — In-house kitchen**: Build our own commissary kitchen. Highest margin, highest capex, slowest to scale.

**Recommendation**: Start with Option B (white-label) for launch, transition to Option A (ghost kitchen) at 1000+ subscribers, consider Option C at 5000+ subscribers in a single city.

### Proposition 3: Marketplace (transaction-based)

**What users get**:
- Curated fitness products: supplements (protein powder, creatine, vitamins), equipment (resistance bands, dumbbells, yoga mats), wearables (smart scales, heart rate monitors), apparel
- Services: 1-on-1 coaching sessions, physical therapy consultations, massage therapy, cryotherapy
- "Engine-recommended" badges: products that match the user's plan (e.g. "Your plan recommends 180g protein/day — here's a whey protein that fits")
- Subscribe & save for recurring items (supplements)
- Partner discounts for app subscribers

**Revenue model**:
- Product sales: 15-25% margin on wholesale
- Service bookings: 10-15% commission
- "Featured" placements: CPM-based advertising for brands

**Why it works**: The `fitn` engine knows exactly what the user needs (macros, training equipment, recovery tools). The marketplace turns that knowledge into targeted product recommendations — the highest-converting form of e-commerce.

---

## 3. Architecture

### 3.1 System overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Mobile App (React Native / Expo)                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Three tabs: Train | Eat | Shop                            │ │
│  │  + Home (daily summary) + Profile                          │ │
│  └─────────────────┬──────────────────────────────────────────┘ │
│                    │ HTTPS (REST/JSON)                            │
│  ┌─────────────────▼──────────────────────────────────────────┐ │
│  │  API Client (offline-capable, JWT auth)                    │ │
│  └─────────────────┬──────────────────────────────────────────┘ │
└────────────────────┼─────────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────────┐
│  Backend (FastAPI + PostgreSQL + Redis)                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  API Gateway: /auth /assess /plan /meals /marketplace      │ │
│  └─────────────────┬──────────────────────────────────────────┘ │
│  ┌─────────────────▼──────────────────────────────────────────┐ │
│  │  fitn Engine (existing Python package)                     │ │
│  │  assess_profile() → propose_plan() → meal plan + macros    │ │
│  └─────────────────┬──────────────────────────────────────────┘ │
│  ┌─────────────────▼──────────────────────────────────────────┐ │
│  │  Meal Delivery Service                                     │ │
│  │  - Kitchen order routing (API to partner kitchen)          │ │
│  │  - Delivery scheduling (API to delivery partner)           │ │
│  │  - Subscription management (Stripe Billing)                │ │
│  └─────────────────┬──────────────────────────────────────────┘ │
│  ┌─────────────────▼──────────────────────────────────────────┐ │
│  │  Marketplace Service                                       │ │
│  │  - Product catalog (Shopify-style)                         │ │
│  │  - Order management (Stripe + fulfillment partner)         │ │
│  │  - Inventory sync (partner APIs)                           │ │
│  └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐         ┌──────────────────────┐
│  Kitchen Partner │         │  Fulfillment Partner  │
│  (white-label    │         │  (ShipBob / ShipRush) │
│   meal prep)     │         │  for marketplace      │
└─────────────────┘         └──────────────────────┘
         │
         ▼
┌─────────────────┐
│  Delivery Partner │
│  (DoorDash Drive  │
│   / Uber Freight) │
└─────────────────┘
```

### 3.2 Backend services

```
backend/
├── app/
│   ├── main.py                    # FastAPI app, CORS, middleware
│   ├── api/
│   │   ├── auth.py                # /auth/register, /auth/login
│   │   ├── assess.py              # POST /assess → AssessmentResult
│   │   ├── plan.py                # POST /plan → FitnessPlan (training + macros)
│   │   ├── meals/
│   │   │   ├── subscribe.py       # POST /meals/subscribe (Stripe checkout)
│   │   │   ├── menu.py            # GET /meals/menu (this week's menu)
│   │   │   ├── swap.py            # POST /meals/swap (replace a meal)
│   │   │   ├── delivery.py        # GET /meals/delivery (tracking)
│   │   │   └── pause.py           # POST /meals/pause (vacation hold)
│   │   ├── marketplace/
│   │   │   ├── catalog.py         # GET /marketplace/products
│   │   │   ├── cart.py            # POST /marketplace/cart
│   │   │   ├── checkout.py        # POST /marketplace/checkout (Stripe)
│   │   │   └── orders.py          # GET /marketplace/orders
│   │   ├── user.py                # GET/PUT /user
│   │   └── logs.py                # POST /logs (weight, workouts)
│   ├── services/
│   │   ├── fitn_service.py        # Wraps fitn engine
│   │   ├── meal_service.py        # Kitchen order routing + delivery scheduling
│   │   ├── marketplace_service.py # Product catalog + order management
│   │   ├── stripe_service.py      # Payments + subscriptions
│   │   └── notification_service.py # Push + email notifications
│   └── config.py
├── tests/
└── Dockerfile
```

### 3.3 Mobile app structure

```
mobile/
├── app/                           # Expo Router
│   ├── (auth)/
│   │   ├── login.tsx
│   │   └── register.tsx
│   ├── (tabs)/
│   │   ├── index.tsx              # Home: daily summary
│   │   ├── train.tsx              # Exercise plan + workout player
│   │   ├── eat.tsx                # Meal delivery + menu
│   │   ├── shop.tsx               # Marketplace
│   │   └── profile.tsx            # Settings + subscription
│   ├── onboarding/                # 4-step assessment wizard
│   ├── workout-player.tsx         # Full-screen workout mode
│   ├── meal-detail.tsx            # Meal nutrition + swap
│   ├── checkout.tsx               # Marketplace + subscription checkout
│   └── delivery-tracking.tsx      # Real-time meal delivery map
├── components/
│   ├── ui/                        # shadcn-inspired components
│   ├── workout/                   # SetRow, RestTimer, ExerciseCard
│   ├── meal/                      # MealCard, MacroRing, SwapSheet
│   └── marketplace/               # ProductCard, CartBar, ReviewStars
├── stores/                        # Zustand (auth, profile, plan, cart)
├── services/                      # API client + Stripe + offline
└── assets/
```

---

## 4. Feature roadmap

### Phase 1: MVP — Free training plan (Weeks 1-8)

**Goal**: Launch with the free exercise plan to build a user base.

| Feature | Description |
|---|---|
| Onboarding | 4-step assessment wizard → UserProfile |
| Assessment display | BF%, BMI, FFMI, health risk, recommended strategy |
| Training plan | Split design, 7-day workout schedule, exercise list |
| Workout player | Set/rep/RPE tracking, rest timer, progression |
| Daily log | Weight + workout completion tracking |
| Auth | Email + Apple/Google Sign In |
| Offline | Plans cached in SQLite; logs queued when offline |

**Deliverable**: App on App Store + Play Store with the free training plan. No payment, no meals, no marketplace yet.

### Phase 2: Meal delivery launch (Weeks 9-16)

**Goal**: Add the paid meal subscription in one launch city.

| Feature | Description |
|---|---|
| Stripe integration | Subscription billing (Starter/Standard/Full/Custom tiers) |
| Meal plan generation | fitn engine generates macros → kitchen gets production spec |
| Kitchen partner API | Send daily order list to white-label meal prep partner |
| Delivery scheduling | Route orders to delivery partner (DoorDash Drive / Uber Freight) |
| Menu display | 7-day rotating menu with cuisine + allergen filters |
| Meal swap | Tap a meal → see top 5 alternatives → swap |
| Delivery tracking | Real-time map (embedded DoorDash/Uber tracker) |
| Subscription management | Pause, resume, change tier, cancel |
| Push notifications | "Your meals are out for delivery" |

**Deliverable**: Paid meal subscription live in 1 city (e.g. Addis Ababa or a US metro). ~50 beta subscribers.

### Phase 3: Marketplace (Weeks 17-20)

**Goal**: Add the marketplace as the third revenue stream.

| Feature | Description |
|---|---|
| Product catalog | 200+ SKUs (supplements, equipment, wearables, apparel) |
| Engine recommendations | "Based on your plan, you need X" product suggestions |
| Cart + checkout | Stripe checkout with Apple Pay / Google Pay |
| Fulfillment | ShipBob integration (they handle warehousing + shipping) |
| Order tracking | Shipment tracking via ShipBob API |
| Reviews | Star ratings + text reviews on products |
| Subscribe & save | Recurring supplement deliveries (e.g. monthly protein powder) |

**Deliverable**: Marketplace live with 200+ products. Full 3-proposition app.

### Phase 4: Scale (Weeks 21+)

- Expand meal delivery to 5 cities
- Add services marketplace (coaching, PT, massage)
- Apple Watch / Wear OS app
- Social features (share workouts, friend leaderboards)
- LLM coach (chat-based Q&A)

---

## 5. Revenue model

### 5.1 Revenue streams

| Stream | Pricing | Margin | Target at Year 1 |
|---|---|---|---|
| Meal subscription | $89–$269/wk | 25-35% (after food + delivery cost) | 500 subscribers → $1.5M ARR |
| Marketplace products | $10–$500/item | 15-25% | 2000 orders/mo → $400K/yr |
| Marketplace services | $50–$200/session | 10-15% commission | 500 bookings/mo → $300K/yr |
| Premium app features | $9.99/mo | 90%+ (software) | 2000 subscribers → $240K/yr |

### 5.2 Unit economics (meal subscription)

| Item | Cost |
|---|---|
| Food cost (ingredients) | $35/wk (Standard tier) |
| Kitchen labor + overhead | $25/wk |
| Packaging | $8/wk |
| Delivery | $15/wk |
| **Total COGS** | **$83/wk** |
| **Revenue** | **$149/wk** (Standard tier) |
| **Gross margin** | **$66/wk (44%)** |
| CAC (customer acquisition) | ~$200 |
| **Payback period** | ~3 weeks |

### 5.3 Free-tier economics

The free training plan costs ~$0.01/user/month in compute (FastAPI + PostgreSQL + Redis). At 50K free users, that's $500/month — negligible. The free tier is justified by conversion: if 2% of free users convert to meal subscribers, 50K free users → 1000 subscribers → $1.5M+ ARR.

---

## 6. UI/UX — three-tab navigation

### 6.1 Tab structure

```
┌─────────────────────────────────────┐
│           [Home]                    │  ← daily summary (default)
├────────┬────────┬────────┬─────────┤
│ Train  │  Eat   │  Shop  │ Profile │
├────────┴────────┴────────┴─────────┤
│                                     │
│  [Tab content]                      │
│                                     │
└─────────────────────────────────────┘
```

### 6.2 Home screen

```
┌─────────────────────────────────────┐
│ Good morning, Abebe 👋              │
│ Wednesday, June 27                  │
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ Today's Workout                  │ │
│ │ Upper A — 4 exercises            │ │
│ │ [▶ Start Workout]                │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ Today's Meals (delivered)        │ │
│ │ 🍳 Breakfast — 520 kcal ✓        │ │
│ │ 🥗 Lunch — 650 kcal (12pm)       │ │
│ │ 🍲 Dinner — 700 kcal (6pm)       │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ Macros (1,870 / 2,200 kcal)      │ │
│ │ P: 145g ████████░░  C: 180g ████ │ │
│ │ F: 65g ██████░░░░  Fiber: 38g ██ │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ Recommended for you              │ │
│ │ 🛒 Whey Protein — $39.99         │ │
│ │ (Your plan needs 180g protein/d) │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 6.3 Train tab

- Current mesocycle overview (week 2 of 5, deload next week)
- 7-day workout schedule (today highlighted)
- Tap a workout → workout player (full-screen, immersive)
- Progress charts: volume per muscle, weight lifted over time
- "Adapt plan" button: re-assess based on logged progress

### 6.4 Eat tab

- **Free users**: See macro targets + recipe suggestions (cook yourself)
- **Paid subscribers**: See this week's delivered menu + delivery tracking
- Meal swap: tap any meal → bottom sheet with top 5 alternatives + similarity scores
- "Pause delivery" for vacations
- "Change tier" (Starter → Standard → Full)

### 6.5 Shop tab

- "Engine-recommended" carousel (products matched to your plan)
- Browse by category: Supplements / Equipment / Wearables / Apparel / Services
- Search + filter
- Product detail: images, description, reviews, "Add to cart"
- Cart bar at bottom: item count + total + checkout button
- Order history + tracking

---

## 7. Meal delivery operations

### 7.1 Daily flow

```
4:00 AM  — fitn engine generates tomorrow's meal plan for each subscriber
5:00 AM  — Backend sends production orders to kitchen partner API
          (each order: user_id, delivery_address, meal_specs with macros)
6:00 AM  — Kitchen partner confirms orders, begins cooking
10:00 AM — Meals packed, labeled with user name + delivery address
11:00 AM — Delivery partner picks up from kitchen
11:30 AM — Delivery partner routes to subscribers
12:00 PM — Subscribers receive "Your meal is arriving" push notification
12:15 PM — Meals delivered; subscriber confirms in app
```

### 7.2 Kitchen partner API

```python
# POST /api/kitchen/orders
{
  "delivery_date": "2026-06-28",
  "orders": [
    {
      "user_id": "usr_abc123",
      "delivery_address": "123 Bole Rd, Addis Ababa",
      "delivery_window": "11am-1pm",
      "meals": [
        {
          "meal_type": "breakfast",
          "recipe_id": "R042",
          "recipe_name": "Chechebsa",
          "target_kcal": 520,
          "target_protein_g": 35,
          "target_carb_g": 60,
          "target_fat_g": 18,
          "allergens_to_avoid": ["dairy"],
          "cuisine": "ethiopian"
        },
        // ... lunch, dinner
      ]
    },
    // ... more users
  ]
}
```

### 7.3 Quality assurance

- Every meal is weighed + photographed before delivery
- Macro accuracy verified by kitchen partner (±5% tolerance)
- Temperature logged during transit (cold chain for perishables)
- Subscriber rates each meal (1-5 stars); ratings below 4 trigger kitchen review
- Weekly menu rotation (no recipe repeated within 3 days per user)

---

## 8. Marketplace operations

### 8.1 Product sourcing

- **Supplements**: Direct wholesale accounts with manufacturers (Optimum Nutrition, MyProtein, etc.)
- **Equipment**: Drop-ship from fitness equipment distributors
- **Wearables**: Authorized reseller agreements (Withings, Garmin, Polar)
- **Services**: Partner network of certified trainers, PTs, massage therapists

### 8.2 Engine-powered recommendations

The `fitn` engine knows:
- User's macro targets → recommend appropriate protein powder, creatine, vitamins
- User's equipment access → recommend home gym equipment if "bodyweight_only"
- User's training status → recommend intermediate/advanced equipment as they progress
- User's goal → recommend cutting/bulking-specific supplements

Example recommendation logic:
```python
def recommend_products(user_profile, plan):
    recs = []
    # Protein powder if protein target > 150g/day
    if plan.nutrition.macros.protein_g > 150:
        recs.append({"product": "whey_protein_2kg", "reason": "Your plan targets 180g protein/day"})
    # Creatine for muscle_gain/strength goals
    if user_profile.primary_goal in ("muscle_gain", "strength"):
        recs.append({"product": "creatine_500g", "reason": "Creatine supports strength goals"})
    # Home equipment if bodyweight_only
    if user_profile.equipment_access == "bodyweight_only":
        recs.append({"product": "resistance_bands_set", "reason": "Upgrade your home workouts"})
    return recs
```

### 8.3 Fulfillment

- Physical products: ShipBob (3PL) handles warehousing + shipping
- Digital products (coaching plans): Instant in-app delivery
- Services: Booking confirmation + calendar sync

---

## 9. Development phases & timeline

### Phase 1: MVP (Weeks 1-8) — Free training plan

| Week | Backend | Mobile | Infra |
|---|---|---|---|
| 1-2 | FastAPI + Docker + PostgreSQL + auth | Expo + navigation + auth screens | Fly.io + Neon + Upstash setup |
| 3-4 | /assess + /plan endpoints + fitn_service | Onboarding wizard (4 steps) | Sentry + Grafana |
| 5-6 | /logs endpoints + caching | Home + Train tab + workout player | CI/CD (GitHub Actions) |
| 7-8 | Polish + rate limiting | Profile + progress charts + offline | TestFlight beta |

**MVP deliverable**: Free app on App Store + Play Store. Users can onboard, get a training plan, log workouts.

### Phase 2: Meal delivery (Weeks 9-16)

| Week | Backend | Mobile | Operations |
|---|---|---|---|
| 9-10 | Stripe Billing + meal_service | Eat tab + subscription flow | Sign kitchen partner |
| 11-12 | Kitchen partner API + delivery scheduling | Menu display + meal swap | First test orders |
| 13-14 | Delivery tracking integration | Delivery tracking map | QA kitchen + delivery |
| 15-16 | Subscription management | Pause/resume/change tier | Soft launch (50 users) |

**Phase 2 deliverable**: Paid meal subscription live in 1 city.

### Phase 3: Marketplace (Weeks 17-20)

| Week | Backend | Mobile | Operations |
|---|---|---|---|
| 17-18 | Marketplace catalog + Stripe checkout | Shop tab + product detail | Source 200+ SKUs |
| 19-20 | ShipBob integration + order tracking | Cart + checkout + order history | Launch marketplace |

**Phase 3 deliverable**: Full 3-proposition app. All revenue streams active.

### Phase 4: Scale (Weeks 21+)

- Expand to 5 cities (meal delivery)
- Add services marketplace
- Apple Watch app
- Social features
- LLM coach

---

## 10. Team & budget

### 10.1 Team (Phases 1-3)

| Role | FTE | Salary (annualized) |
|---|---|---|
| Tech lead / full-stack | 1.0 | $140K |
| Backend engineer | 1.0 | $120K |
| Mobile engineer (React Native) | 1.0 | $130K |
| Designer (UI/UX) | 0.5 | $60K |
| Operations lead (meal delivery) | 0.5 | $55K |
| Product manager | 0.3 | $45K |

**Total payroll (5 months)**: ~$275K

### 10.2 Other costs

| Item | Cost (5 months) |
|---|---|
| Infrastructure (Fly.io + Neon + Redis + Sentry) | $5K |
| Stripe fees (2.9% + $0.30/transaction) | ~$15K (at $500K GMV) |
| Kitchen partner (food + labor, 50 subscribers × 20 weeks) | $83K |
| Delivery partner (50 subscribers × 20 weeks) | $30K |
| ShipBob (marketplace fulfillment) | $5K |
| App store fees | $0.1K |
| Marketing (launch) | $30K |
| Legal + compliance | $10K |

**Total Phase 1-3 budget**: ~$450K

### 10.3 Break-even

At 500 meal subscribers (Standard tier, $149/wk):
- Revenue: $500 × $149 × 52 = $3.87M/yr
- COGS (44%): $1.70M
- Gross profit: $2.17M
- Operating costs (team + infra): ~$1.2M/yr
- **Break-even at ~350 subscribers**

---

## 11. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Kitchen partner can't scale | Medium | High | Multi-partner strategy; in-house kitchen at scale |
| Meal delivery logistics failure | Medium | Critical | Use established delivery partners (DoorDash/Uber); temperature monitoring |
| Food safety incident | Low | Critical | Kitchen partner carries liability insurance; HACCP certification required; recall protocol |
| User churn (meals too repetitive) | High | Medium | 79 curated recipes + 305 uncurated pool; weekly menu rotation; swap feature |
| Marketplace low conversion | Medium | Medium | Engine-powered recommendations; limited-time discounts; free shipping threshold |
| Stripe account hold | Low | High | Diversified payment processors (Stripe + Adyen backup); reserve fund |
| Cold chain failure | Low | High | Temperature sensors in packaging; delivery partner SLA; refund policy |
| Regulatory (food licensing) | Medium | High | Partner with licensed kitchens; obtain food handler permits per city |

---

## 12. Success metrics

### North star
**Weekly active meal subscribers** — subscribers who receive ≥4 meals/week. Target: 80%+ at 30 days, 70%+ at 90 days.

### Phase 1 (free training plan)
| Metric | 30-day target | 90-day target |
|---|---|---|
| App downloads | 10K | 50K |
| Onboarding completion | 70% | 75% |
| D7 retention | 30% | 35% |
| D30 retention | 15% | 20% |
| Crash-free sessions | 99.5% | 99.8% |

### Phase 2 (meal delivery)
| Metric | 30-day target | 90-day target |
|---|---|---|
| Free → paid conversion | 3% | 5% |
| Subscriber D30 retention | 70% | 75% |
| Meal satisfaction (4+ stars) | 80% | 85% |
| Delivery on-time rate | 90% | 95% |
| Macro accuracy (±5%) | 90% | 95% |

### Phase 3 (marketplace)
| Metric | 30-day target | 90-day target |
|---|---|---|
| Marketplace conversion (visit → buy) | 5% | 8% |
| Average order value | $45 | $55 |
| Repeat purchase rate | 25% | 35% |
| Engine-recommended CTR | 15% | 20% |

---

## 13. Legal & compliance

- **Food safety**: Kitchen partner must have local food service license + HACCP certification. We carry product liability insurance ($2M coverage).
- **Payment processing**: PCI DSS compliance via Stripe (we never touch card data).
- **Privacy**: GDPR + CCPA compliant. Data export + deletion endpoints. No PII in logs.
- **Health data**: Apple Health / Google Fit data stays on-device. No health data sold to third parties.
- **Subscription terms**: Clear cancellation policy (cancel anytime, no penalty). Auto-renewal disclosure per App Store guidelines.
- **Marketplace**: Return policy (30-day for products, 24-hour cancellation for services). Vendor agreements with quality SLAs.

---

## 14. Next actions

1. **Week 0**: Sign kitchen partner LOI. Set up Stripe account. File food service permits for launch city.
2. **Week 1**: Backend foundation (auth + assess + plan). Mobile foundation (Expo + navigation).
3. **Week 4**: First end-to-end: user onboards → gets training plan → sees it on home screen.
4. **Week 8**: MVP submitted to App Store + Play Store (free training plan only).
5. **Week 12**: Kitchen partner integration complete. First test meal delivery.
6. **Week 16**: Soft launch meal delivery (50 beta subscribers in 1 city).
7. **Week 20**: Marketplace launch. Full 3-proposition app live.

---

## Appendix A: fitn engine integration

The mobile app uses these `fitn` engine APIs:

```python
# Free tier — assessment + training plan
from fitness_engine import UserProfile, PlanPreferences, assess_profile, propose_plan

assessment = assess_profile(profile)
plan = propose_plan(profile, assessment, preferences)
# plan.training → training plan for the Train tab
# plan.nutrition → macro targets for meal plan generation

# Paid tier — meal plan generation (sent to kitchen partner)
# plan.meal → 7-day meal plan with recipes + macros per meal
# Each meal has: recipe_id, target_kcal, target_protein_g, etc.
# This becomes the kitchen's production spec.

# Adaptive re-assessment (every 2-4 weeks)
from fitness_engine.nutrition.tdee import update_tdee_with_logs
new_tdee = update_tdee_with_logs(tdee, avg_intake, weight_start, weight_end, n_days)
```

## Appendix B: Recipe DB readiness

The v3.1.5 recipe DB (79 curated + 305 uncurated recipes) includes:
- `selection_reason` per recipe — powers "Why this meal?" in the Eat tab
- `top_alternatives` per recipe — powers the meal swap feature
- `allergens` extracted from ingredients — powers allergen filtering
- `goal_fit` tags — powers "meals for cutting/bulking"
- `protein_density` + `calorie_density` — powers menu optimization
- Ethiopian cultural flags — powers the Ethiopian cuisine specialization
- Schema-B format (engine-ready, no transformation needed)

## Appendix C: Test coverage

The `fitn` engine ships with 1272 tests at 90% coverage. The mobile app's backend wrapper adds ~100 tests for API endpoints, Stripe integration, kitchen partner routing, and marketplace checkout. The mobile app adds Jest unit tests + Detox E2E tests.

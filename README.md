# fitn

> Deterministic, dependency-free Python fitness engine: assessment + nutrition + training + meal planning.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-444%20passing-green.svg)](#testing)

`fitn` produces a unified `FitnessPlan` (nutrition + training + meal plan) from a
`UserProfile`. It is **fully deterministic** (no `random`, no `datetime.now`,
zero third-party runtime dependencies) and runs in <1 second per plan.

## Quickstart

```python
from fitness_engine import UserProfile, assess_profile, propose_plan, PlanPreferences

profile = UserProfile(
    age=30, sex="male", height_cm=178, weight_kg=82,
    activity_level="moderate",
    training_status="intermediate",
    primary_goal="fat_loss",
    training_days_per_week=4,
)

assessment = assess_profile(profile)
plan = propose_plan(profile, assessment, PlanPreferences(
    meal_frequency=4,
    include_pre_post_workout=True,
    cuisine_preference="ethiopian",
    allergens_to_avoid=["dairy"],
))

print(plan.summary)
# === Fitness Plan Summary ===
# User: MALE, 30y, 178cm, 82.0kg
# Assessment: BF=18.5% (FITNESS), BMI=25.9, FFMI=21.4
# Strategy: CUT
# ...

# Serialize
import json
print(json.dumps(plan.to_dict(), indent=2, default=str))
```

## Installation

```bash
# From source
git clone https://github.com/hai-png/fitn.git
cd fitn
pip install -e ".[dev]"
```

## Architecture

```
UserProfile
    ↓
assess_profile(profile)  →  AssessmentResult
    ↓
propose_plan(profile, assessment, preferences?)  →  FitnessPlan
    ├── build_nutrition_plan  (RMR, TDEE, calories, macros, hydration, micros)
    ├── build_training_plan   (split, periodization, exercise selection, volume)
    └── build_meal_plan       (recipe scoring, scaling, swaps, pre/post workout)
```

### Domain coverage

| Subsystem | Capabilities |
|---|---|
| **Assessment** | Navy / Jackson / Boer / BMI body-fat methods; ABSI / WHR / WHtR health-risk; FFMI muscular potential; cut/bulk/recomp decision |
| **Nutrition** | Mifflin-St Jeor / Katch-McArdle / Harris-Benedict RMR; adaptive TDEE; cut/bulk/recomp calorie targets; RippedBody macro splits; hydration; micronutrients; plateau detection; reverse dieting |
| **Training** | 8 split designs (full-body, UL, PPL, body-part); linear / DUP / block periodization; RP-sourced volume landmarks; RIR/RPE intensity model; exercise categorization (compound/accessory/isolation) |
| **Meal plan** | Recipe database with allergen filtering; word-boundary ingredient matching; pre/post-workout slots with daily-macro preservation; recipe scaling + fillers; swap system respecting allergens |

## Testing

```bash
pytest                       # full suite (444 tests, ~4s)
pytest -m "not integration"  # fast subset
pytest --cov=fitness_engine  # with coverage report
```

## Documentation

- [`reports/meal_planning/DESIGN.md`](reports/meal_planning/DESIGN.md) — meal planner design
- [`reports/meal_planning/coverage_analysis.md`](reports/meal_planning/coverage_analysis.md) — recipe coverage
- [`reports/rippedbody_insights.md`](reports/rippedbody_insights.md) — domain sources
- [`reports/CLEANUP_PLAN.md`](reports/CLEANUP_PLAN.md) — historical cleanup log

## License

[MIT](LICENSE)

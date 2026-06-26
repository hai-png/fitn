# fitn

> Deterministic, dependency-free Python fitness engine: assessment + nutrition + training + meal planning.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-557%20passing-green.svg)](#testing)
[![Coverage](https://img.shields.io/badge/coverage-90%25-green.svg)](#testing)

`fitn` produces a unified `FitnessPlan` (nutrition + training + meal plan) from a
`UserProfile`. It is **fully deterministic** (no `random`, no `datetime.now`,
zero third-party runtime dependencies) and runs in ~1 second per plan.

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
pytest                       # full suite (557 tests, ~100s)
pytest -m "not integration"  # same — no test carries the integration marker yet
pytest --cov=fitness_engine  # with coverage report (90%+)
```

## Documentation

- [`ANALYSIS.md`](ANALYSIS.md) — critical analysis report + systematic fixes (v3.1.1)
- [`reports/meal_planning/DESIGN.md`](reports/meal_planning/DESIGN.md) — meal planner design
- [`reports/meal_planning/coverage_analysis.md`](reports/meal_planning/coverage_analysis.md) — recipe coverage
- [`reports/rippedbody_insights.md`](reports/rippedbody_insights.md) — domain sources
- [`reports/CLEANUP_PLAN.md`](reports/CLEANUP_PLAN.md) — historical cleanup log

## Known limitations

- **ABSI z-score** uses 10-year age bands (acknowledged simplification of the
  NHANES 5-year bands; up to ~0.3 SD of error at age-band boundaries). Not for
  clinical decisions.
- **Health-risk aggregator** weights (ABSI=0.5, WHR=0.3, WHtR=0.2) are
  heuristic, reflecting relative predictive strength from source papers but
  not formally validated as a composite score.
- **CUN-BAE** BF% formula uses a modified coefficient (1.0689 instead of
  10.689) because the originally-published coefficient produces
  physiologically impossible values (>200% BF for BMI=25). See
  `assessment/body_composition.py` docstring for verification data points.
- **Adaptive TDEE** functions are public but not wired into the pipeline
  (`UserProfile.weight_log_kg` is stubbed out). Use `update_tdee_with_logs`
  directly if you have intake/weight logs.
- **Reverse diet** function is public but not wired into `propose_plan` —
  call `reverse_diet_plan` directly for transition phases.

## License

[MIT](LICENSE)

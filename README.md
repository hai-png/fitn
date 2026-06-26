# fitn

> Deterministic, dependency-free Python fitness engine: assessment + nutrition + training + meal planning.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-1272%20passing-green.svg)](#testing)
[![Coverage](https://img.shields.io/badge/coverage-90%25-green.svg)](#testing)

`fitn` produces a unified `FitnessPlan` (nutrition + training + meal plan) from a
`UserProfile`. It is **fully deterministic** (no `random`, no `datetime.now`,
zero third-party runtime dependencies) and runs in ~1 second per plan.

## Quickstart

```python
from fitness_engine import UserProfile, assess_profile, propose_plan, PlanPreferences

profile = UserProfile(
    age=30, sex="male", height_cm=178, weight_kg=82,
    activity_level="lightly_active",
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
pytest                       # full suite (1272 tests, ~25s)
pytest -m "not integration"  # same — no test carries the integration marker yet
pytest --cov=fitness_engine  # with coverage report (90%+)
```

## Documentation

### Audit reports (`docs/audit_reports/`)
- [`ANALYSIS_v3.1.4.md`](docs/audit_reports/ANALYSIS_v3.1.4.md) — latest critical analysis report + systematic fixes (v3.1.4)
- [`REAUDIT_v3.1.3.md`](docs/audit_reports/REAUDIT_v3.1.3.md) — re-audit report (v3.1.3)
- [`ANALYSIS_v3.1.1.md`](docs/audit_reports/ANALYSIS_v3.1.1.md) — original critical analysis report + systematic fixes (v3.1.1)
- [`CURATE_CRITIQUE.md`](docs/audit_reports/CURATE_CRITIQUE.md) — recipe curation script critique (v3.1.4)

### Design & analysis (`reports/`)
- [`reports/meal_planning/DESIGN.md`](reports/meal_planning/DESIGN.md) — meal planner design
- [`reports/meal_planning/coverage_analysis.md`](reports/meal_planning/coverage_analysis.md) — recipe coverage
- [`reports/rippedbody_insights.md`](reports/rippedbody_insights.md) — domain sources
- [`reports/CLEANUP_PLAN.md`](reports/CLEANUP_PLAN.md) — historical cleanup log

### Mobile app plan (`docs/`)
- [`docs/MOBILE_APP_PLAN.md`](docs/MOBILE_APP_PLAN.md) — comprehensive plan for building a mobile app (v3.1.5)

## Scripts (`scripts/`)

| Script | Purpose |
|---|---|
| `curate_recipe_db.py` | Build the curated recipe database from the raw uploaded JSON (v3.1.4). Replaces the legacy `curate_recipes.py`. |
| `backfill_overviews.py` | Backfill missing `overview` fields in `all_exercises.json` with metadata-derived placeholders (v3.1.2). Idempotent. |
| `recipe_curator.py` | One-time analysis script: produces `reports/meal_planning/coverage_analysis.{json,md}` showing recipe DB coverage gaps. |
| `sample_runner.py` | Demo runner — generates 6 sample plans (cut/bulk/recomp × 3 equipment tiers) into `download/`. |

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

## License

[MIT](LICENSE)

# Phase-6: Information Flow Cleanup + File Tidying

## 1. Current Information Flow Issues

### 1.1 The flow is correct but parameter passing is inconsistent

```
UserProfile → assess_profile() → AssessmentResult
                                       ↓
                                       + → propose_plan()
                                       ↓
                       ┌───────────────┼───────────────┐
                       ↓               ↓               ↓
              build_nutrition   build_training   build_meal_plan
                  _plan()          _plan()            ()
                       ↓               ↓               ↓
                NutritionPlan   TrainingPlan       MealPlan
                       └───────────────┼───────────────┘
                                       ↓
                                  FitnessPlan
```

**Issue**: `propose_plan()` accepts 13 parameters, many of which are passed
straight through to one of the three sub-planners. This is a "god function"
smell. Better: group related parameters into a single `PlanPreferences`
dataclass that flows through the system.

### 1.2 Legacy/versioned files to remove

| File | Status | Action |
|---|---|---|
| `meal_plan/allocator.py` | Legacy Phase-2 allocator (kept "for backward compat") | **Delete** — replaced by `allocator_v2.py` |
| `meal_plan/allocator_v2.py` | Current clean implementation | **Rename → `allocator.py`** |
| `meal_plan/planner.py` | Shim that re-exports from `planner_v2.py` | **Delete** — replaced by `planner_v2.py` |
| `meal_plan/planner_v2.py` | Current clean implementation | **Rename → `planner.py`** |
| `training/planner.py` | Shim that re-exports from `architect.py` | **Delete** |
| `training/splits.py` | Shim with `select_split`/`select_progression` | **Delete** (logic in `architect.py` + `exercise_selector.py`) |
| `scripts/extract_text.py` | Phase-1 scraping script | **Delete** |
| `scripts/fetch_resources.py` | Phase-1 scraping script | **Delete** |
| `scripts/fetch_resources_retry.py` | Phase-1 scraping script | **Delete** |
| `CRITICAL_ANALYSIS.md` | Phase-2 analysis (superseded by reports/) | **Delete** |
| `download/README.md` | Stale Phase-1 doc | **Delete** |
| `download/fitness_engine_reference_guide.md` | Stale Phase-1 doc | **Delete** |

### 1.3 Test files with phase suffixes

| File | Rename to |
|---|---|
| `tests/test_phase2.py` | `tests/test_recipes_and_exercises.py` |
| `tests/test_phase3.py` | `tests/test_training_architect.py` |
| `tests/test_phase4.py` | `tests/test_rippedbody_enhancements.py` |
| `tests/test_phase5.py` | `tests/test_meal_planning.py` |
| `tests/test_engine.py` | (keep — integration tests) |
| `tests/test_assessment.py` | (keep) |
| `tests/test_nutrition.py` | (keep) |

### 1.4 Module `__init__.py` exports are bloated

Several `__init__.py` files export 50+ symbols. This makes the public API
unclear. We'll trim each to the *intended* public API (≤20 symbols).

---

## 2. Cleanup Plan

### Step 1: Delete legacy files
- `meal_plan/allocator.py` (will be replaced by renamed `allocator_v2.py`)
- `meal_plan/planner.py` (will be replaced by renamed `planner_v2.py`)
- `training/planner.py` (shim)
- `training/splits.py` (shim)
- `scripts/extract_text.py`, `scripts/fetch_resources.py`, `scripts/fetch_resources_retry.py`
- `CRITICAL_ANALYSIS.md`
- `download/README.md`, `download/fitness_engine_reference_guide.md`

### Step 2: Rename v2 files to canonical names
- `meal_plan/allocator_v2.py` → `meal_plan/allocator.py`
- `meal_plan/planner_v2.py` → `meal_plan/planner.py`

### Step 3: Rename test files to functional names
- `tests/test_phase2.py` → `tests/test_recipes_and_exercises.py`
- `tests/test_phase3.py` → `tests/test_training_architect.py`
- `tests/test_phase4.py` → `tests/test_rippedbody_enhancements.py`
- `tests/test_phase5.py` → `tests/test_meal_planning.py`

### Step 4: Introduce `PlanPreferences` dataclass
Group the 8 "preference" parameters of `propose_plan()` into a single
dataclass so the signature becomes:

```python
def propose_plan(
    profile: UserProfile,
    assessment: AssessmentResult,
    preferences: PlanPreferences | None = None,
) -> FitnessPlan:
```

`PlanPreferences` contains:
- `meal_frequency: int = 3`
- `exercise_hours_per_day: float = 1.0`
- `exercise_intensity: str = "moderate"`
- `climate: str = "temperate"`
- `in_active_deficit: bool = False`
- `weight_reduced_pct: float = 0.0`
- `plan_type: PlanType | None = None`
- `muscle_focus: list[str] | None = None`
- `program_duration_weeks: int | None = None`
- `cuisine_preference: str | None = None`
- `allergens_to_avoid: list[str] | None = None`
- `excluded_ingredients: list[str] | None = None`
- `include_pre_post_workout: bool = False`

Backward compat: keep the old flat signature working by detecting if
`preferences` is None and falling back to the old kwargs (deprecated).

### Step 5: Update `__init__.py` exports
Trim each module's `__all__` to the intended public API.

### Step 6: Update `engine.py` to use the clean flow
- Accept `PlanPreferences` (or flat kwargs for backward compat)
- Pass preferences through to sub-planners cleanly
- Improve summary formatting

### Step 7: Update all imports + tests
- Replace `from .planner_v2 import` → `from .planner import`
- Replace `from .allocator_v2 import` → `from .allocator import`
- Remove references to deleted shims
- Update test imports for renamed files

### Step 8: Run full test suite + regenerate sample plans
- All 285 tests must pass
- 6 sample plans regenerated
- No references to deleted files anywhere

---

## 3. Acceptance Criteria

- [ ] No file with `_v2` suffix exists
- [ ] No file with `phase` in its name (except in worklog.md history)
- [ ] No shim files (planner.py that just re-exports)
- [ ] `propose_plan()` accepts a single `PlanPreferences` (or flat kwargs for compat)
- [ ] All 285+ tests pass
- [ ] Sample plans regenerate successfully
- [ ] No import errors anywhere in the codebase

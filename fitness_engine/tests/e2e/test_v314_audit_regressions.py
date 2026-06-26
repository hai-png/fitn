"""
v3.1.4 audit-recommended regression tests.

These tests cover the 5 test-gap categories identified at the end of
ANALYSIS_v3.1.4.md. Each would have caught one or more of the v3.1.4
CRITICAL/HIGH defects earlier in the development cycle:

  1. Cardio/plyo classification — would have caught C3 (85 misclassified
     non-Strength exercises).
  2. Selector experience-level assertions — would have caught C2
     (INTERMEDIATE users getting ADVANCED Olympic lifts).
  3. Hydration invariant (sum(components) == water_liters_per_day) — would
     have caught HIGH-1 (climate delta double-counted) and HIGH-2
     (hyponatremia clamp didn't update components).
  4. Calorie-delta invariant (base_tdee + delta == target across all
     strategies) — would have caught HIGH-3 (negative rate_pct producing
     surplus labeled DEFICIT).
  5. DB slug audit (every slug in _COMPOUND_PRIMARY_SLUGS exists in DB with
     expected name) — would have caught C1 (bent-over-row slug regression).
"""
from __future__ import annotations

import math

import pytest

from fitness_engine import (
    PlanPreferences,
    UserProfile,
    assess_profile,
    propose_plan,
)
from fitness_engine.models.profile import (
    ActivityLevel,
    Climate,
    DietType,
    EquipmentAccess,
    ExerciseIntensity,
    PrimaryGoal,
    Sex,
    TrainingStatus,
)
from fitness_engine.models.training import ExerciseCategory, TrainingGoal
from fitness_engine.nutrition.calories import (
    bulk_target_calories,
    compute_calorie_targets,
    cut_target_calories,
    maintenance_target_calories,
    recomp_target_calories,
)
from fitness_engine.nutrition.hydration import compute_hydration
from fitness_engine.training.exercise_categorization import get_movement_pattern
from fitness_engine.training.exercise_loader import (
    _COMPOUND_PRIMARY_SLUGS,
    get_exercise_by_slug,
    load_exercises,
)
from fitness_engine.training.exercise_selector import select_exercise_for_slot
from fitness_engine.training.split_designs import ALL_SPLITS


# ============================================================
# Test 1: Cardio / plyometric classification
#
# C3 regression: previously 85 of 129 non-Strength exercises were
# mis-bucketed as strength patterns (e.g. "concept-2-rowing-machine" →
# horizontal_pull). This test iterates the full exercise DB and asserts
# that every exercise with a non-Strength exercise_type gets a non-strength
# pattern (cardio or mobility).
# ============================================================

def test_every_conditioning_exercise_gets_cardio_pattern():
    """All 39 Conditioning exercises must have pattern == 'cardio'."""
    db = load_exercises()
    conditioning = [e for e in db if e.exercise_type == "Conditioning"]
    assert len(conditioning) >= 30, f"Expected ≥30 Conditioning exercises, got {len(conditioning)}"
    wrong = [e for e in conditioning if get_movement_pattern(e) != "cardio"]
    assert not wrong, (
        f"{len(wrong)} Conditioning exercises misclassified: "
        f"{[(e.name, get_movement_pattern(e)) for e in wrong[:5]]}"
    )


def test_every_plyometrics_exercise_gets_cardio_pattern():
    """All Plyometrics exercises must have pattern == 'cardio'.

    Pre-v3.1.4: ALL 33 Plyometrics were misclassified as strength patterns
    (e.g. 'Standing Medicine Ball Chest Throw' → horizontal_pull) because
    keyword matching ran before exercise_type checks.
    """
    db = load_exercises()
    plyo = [e for e in db if e.exercise_type == "Plyometrics"]
    assert len(plyo) >= 25, f"Expected ≥25 Plyometrics exercises, got {len(plyo)}"
    wrong = [e for e in plyo if get_movement_pattern(e) != "cardio"]
    assert not wrong, (
        f"{len(wrong)} Plyometrics exercises misclassified: "
        f"{[(e.name, get_movement_pattern(e)) for e in wrong[:5]]}"
    )


def test_every_warmup_activation_smr_gets_mobility_pattern():
    """Warmup / Activation / SMR / Stretching exercises must have pattern == 'mobility'."""
    db = load_exercises()
    non_strength_non_cardio = [
        e for e in db
        if e.exercise_type in {"Warmup", "Activation", "SMR", "Stretching"}
    ]
    assert len(non_strength_non_cardio) >= 50
    wrong = [e for e in non_strength_non_cardio if get_movement_pattern(e) != "mobility"]
    assert not wrong, (
        f"{len(wrong)} mobility exercises misclassified: "
        f"{[(e.name, get_movement_pattern(e)) for e in wrong[:5]]}"
    )


def test_plyometrics_get_cardio_category():
    """All Plyometrics exercises must have ExerciseCategory.CARDIO (so the
    selector filters them out of strength slots)."""
    db = load_exercises()
    plyo = [e for e in db if e.exercise_type == "Plyometrics"]
    wrong = [e for e in plyo if e.category != ExerciseCategory.CARDIO]
    assert not wrong, (
        f"{len(wrong)} Plyometrics exercises not categorized as CARDIO: "
        f"{[(e.name, e.category) for e in wrong[:5]]}"
    )


# ============================================================
# Test 2: Selector experience-level assertions
#
# C2 regression: INTERMEDIATE users got ADVANCED exercises (Snatch Grip
# Deadlift, etc.) because the sort key anchored on the cap (max allowed
# rank) rather than the user's own level.
# ============================================================

# Standard full-gym equipment set used across all selector tests.
_FULL_GYM = {
    "barbell", "dumbbell", "cable", "machine", "bodyweight",
    "kettlebell", "band", "ez_bar", "trap_bar", "bands",
}


def _slots_for_pattern(pattern: str):
    """Yield (split, template, slot) tuples for every slot with the given pattern."""
    for split in ALL_SPLITS:
        for tmpl in split.templates:
            for slot in tmpl.slots:
                if slot.pattern == pattern:
                    yield split, tmpl, slot


@pytest.mark.parametrize("status", [
    TrainingStatus.BEGINNER,
    TrainingStatus.NOVICE,
    TrainingStatus.INTERMEDIATE,
    TrainingStatus.ADVANCED,
])
@pytest.mark.parametrize("pattern", [
    "hinge", "squat", "horizontal_push", "horizontal_pull",
    "vertical_push", "vertical_pull",
])
def test_selector_returns_exercise_at_or_below_user_level(status, pattern):
    """For every (status × pattern) combination, the selected exercise must
    not exceed the user's allowed experience cap.

    C2 regression: INTERMEDIATE users (cap=2) were getting ADVANCED exercises
    (rank 2) preferred over Intermediate ones (rank 1, distance 1). The cap
    is still respected, but the SORT preferred the wrong rank.
    """
    cap = {TrainingStatus.BEGINNER: 0, TrainingStatus.NOVICE: 1,
           TrainingStatus.INTERMEDIATE: 2, TrainingStatus.ADVANCED: 2}[status]
    rank_map = {"Beginner": 0, "Intermediate": 1, "Advanced": 2}
    for _split, _tmpl, slot in _slots_for_pattern(pattern):
        ex = select_exercise_for_slot(slot, _FULL_GYM, status, set())
        if ex is None:
            continue  # some slots have no candidates for some equipment sets
        if ex.experience_level is None:
            continue  # missing metadata — treated as Intermediate by selector
        ex_rank = rank_map.get(ex.experience_level.value, 1)
        assert ex_rank <= cap, (
            f"{status.value} user (cap={cap}) got {ex.name} "
            f"(experience={ex.experience_level.value}, rank={ex_rank}) "
            f"for slot {slot.name} ({pattern}) — exceeds cap"
        )


def test_intermediate_users_get_intermediate_exercises_not_advanced():
    """Smoke test for the specific C2 regression: an INTERMEDIATE user on the
    4-day upper_lower split should NOT get 'Snatch Grip Deadlift' (Advanced)
    for the hinge slot. They should get an Intermediate-ranked hinge."""
    hinge_slots = []
    for split in ALL_SPLITS:
        if split.days_per_week == 4 and split.split_type.value == "upper_lower":
            for tmpl in split.templates:
                for slot in tmpl.slots:
                    if slot.pattern == "hinge":
                        hinge_slots.append(slot)
    assert hinge_slots, "Test setup failed: no hinge slots in 4-day upper_lower split"

    for slot in hinge_slots:
        ex = select_exercise_for_slot(slot, _FULL_GYM, TrainingStatus.INTERMEDIATE, set())
        assert ex is not None, f"No exercise selected for hinge slot {slot.name}"
        # Snatch Grip Deadlift was the C2 regression symptom — never again.
        assert "snatch" not in ex.name.lower(), (
            f"INTERMEDIATE user got '{ex.name}' for {slot.name} — Olympic lifts "
            f"are Advanced and should not be preferred for Intermediate users."
        )


# ============================================================
# Test 3: Hydration invariant — sum(components) == water_liters_per_day
#
# HIGH-1 regression: climate delta was double-counted (sum > water).
# HIGH-2 regression: hyponatremia clamp didn't update components (sum > water).
# ============================================================

def _profile(**kw) -> UserProfile:
    defaults = dict(
        age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        training_status=TrainingStatus.INTERMEDIATE,
        primary_goal=PrimaryGoal.MAINTENANCE,
        training_days_per_week=4,
        equipment_access=EquipmentAccess.FULL_GYM,
    )
    defaults.update(kw)
    return UserProfile(**defaults)


@pytest.mark.parametrize("sex", [Sex.MALE, Sex.FEMALE])
@pytest.mark.parametrize("weight_kg", [50.0, 75.0, 100.0, 120.0])
@pytest.mark.parametrize("hours", [0.0, 0.5, 1.0, 2.0, 3.0, 4.0])
@pytest.mark.parametrize("intensity", [
    ExerciseIntensity.LIGHT, ExerciseIntensity.MODERATE, ExerciseIntensity.INTENSE,
])
@pytest.mark.parametrize("climate", [
    Climate.COLD, Climate.TEMPERATE, Climate.HOT, Climate.HOT_HUMID,
])
def test_hydration_components_sum_to_water_liters_per_day(
    sex, weight_kg, hours, intensity, climate,
):
    """sum(components.values()) must equal water_liters_per_day across all
    (sex × weight × hours × intensity × climate) combinations.

    Catches:
      - HIGH-1: climate delta double-counted (sum was 0.48L > water)
      - HIGH-2: clamp didn't update components (sum was 0.96L > water)
    """
    profile = _profile(sex=sex, weight_kg=weight_kg)
    h = compute_hydration(
        profile,
        exercise_hours_per_day=hours,
        exercise_intensity=intensity,
        climate=climate,
    )
    components_sum = sum(h.components.values())
    # Allow 0.05 L rounding tolerance (each component is round(..., 2)).
    assert abs(components_sum - h.water_liters_per_day) <= 0.05, (
        f"sum(components)={components_sum:.3f} != water={h.water_liters_per_day:.3f} "
        f"for sex={sex.value}, weight={weight_kg}kg, hours={hours}, "
        f"intensity={intensity.value}, climate={climate.value}\n"
        f"components={h.components}"
    )


def test_hydration_clamp_preserves_components_invariant():
    """Specifically test the hyponatremia clamp path: a 100kg male doing 4h
    intense exercise in temperate climate produces >5L pre-clamp, so the
    clamp engages. After clamping, sum(components) must still equal 5.0L."""
    profile = _profile(sex=Sex.MALE, weight_kg=100.0)
    h = compute_hydration(
        profile,
        exercise_hours_per_day=4.0,
        exercise_intensity=ExerciseIntensity.INTENSE,
        climate=Climate.TEMPERATE,
    )
    assert h.water_liters_per_day == 5.0, (
        f"Test setup: expected clamp to engage at 5.0L, got {h.water_liters_per_day}"
    )
    components_sum = sum(h.components.values())
    assert abs(components_sum - 5.0) <= 0.05, (
        f"Clamp broke the invariant: sum(components)={components_sum:.3f} != 5.0"
    )


# ============================================================
# Test 4: Calorie-delta invariant — base_tdee + delta == target
#
# HIGH-3 regression: negative rate_pct produced surplus labeled DEFICIT,
# with base_tdee + delta != target (target was +4510 over base).
# ============================================================

def _calorie_profile(**kw) -> UserProfile:
    defaults = dict(
        age=30, sex=Sex.MALE, height_cm=178, weight_kg=82, body_fat_pct=18,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        training_status=TrainingStatus.INTERMEDIATE,
        primary_goal=PrimaryGoal.MAINTENANCE,
        training_days_per_week=4,
        equipment_access=EquipmentAccess.FULL_GYM,
    )
    defaults.update(kw)
    return UserProfile(**defaults)


@pytest.mark.parametrize("tdee", [1500.0, 2000.0, 2500.0, 3000.0, 3500.0])
@pytest.mark.parametrize("sex", [Sex.MALE, Sex.FEMALE])
def test_cut_calorie_delta_invariant(tdee, sex):
    """For cuts: base_tdee + calorie_delta == target_calories (±1 kcal rounding)."""
    profile = _calorie_profile(sex=sex)
    cals = cut_target_calories(profile, tdee_kcal=tdee)
    assert abs(cals.base_tdee_kcal + cals.calorie_delta_kcal - cals.target_calories_kcal) <= 1.0, (
        f"CUT: base({cals.base_tdee_kcal}) + delta({cals.calorie_delta_kcal}) "
        f"!= target({cals.target_calories_kcal}) for tdee={tdee}"
    )
    assert cals.target_calories_kcal > 0


@pytest.mark.parametrize("tdee", [1500.0, 2000.0, 2500.0, 3000.0, 3500.0])
def test_bulk_calorie_delta_invariant(tdee):
    """For bulks: base_tdee + calorie_delta == target_calories."""
    profile = _calorie_profile()
    cals = bulk_target_calories(profile, tdee_kcal=tdee)
    assert abs(cals.base_tdee_kcal + cals.calorie_delta_kcal - cals.target_calories_kcal) <= 1.0


@pytest.mark.parametrize("tdee", [1500.0, 2000.0, 2500.0, 3000.0])
def test_maintenance_calorie_delta_invariant(tdee):
    """For maintenance: base + 0 == target (delta must be 0)."""
    cals = maintenance_target_calories(tdee)
    assert cals.calorie_delta_kcal == 0.0
    assert cals.base_tdee_kcal == cals.target_calories_kcal


@pytest.mark.parametrize("bf_pct", [10.0, 15.0, 20.0, 25.0, 30.0, 35.0])
@pytest.mark.parametrize("tdee", [1500.0, 2000.0, 2500.0, 3000.0])
def test_recomp_calorie_delta_invariant(bf_pct, tdee):
    """For recomp: base_tdee + calorie_delta == target_calories."""
    profile = _calorie_profile(body_fat_pct=bf_pct)
    cals = recomp_target_calories(profile, tdee_kcal=tdee, body_fat_pct=bf_pct)
    assert abs(cals.base_tdee_kcal + cals.calorie_delta_kcal - cals.target_calories_kcal) <= 1.0


def test_cut_rejects_negative_rate_pct():
    """HIGH-3 regression: negative rate_pct must raise ValueError, not silently
    produce a surplus labeled DEFICIT."""
    profile = _calorie_profile()
    with pytest.raises(ValueError, match="rate_pct must be positive"):
        cut_target_calories(profile, tdee_kcal=2500, rate_pct=-0.05)


def test_cut_rejects_zero_rate_pct():
    """A zero rate_pct is also nonsensical for a cut — should raise."""
    profile = _calorie_profile()
    with pytest.raises(ValueError, match="rate_pct must be positive"):
        cut_target_calories(profile, tdee_kcal=2500, rate_pct=0.0)


def test_bulk_rejects_negative_rate_pct():
    """Symmetric guard on bulk: negative rate must raise."""
    profile = _calorie_profile()
    with pytest.raises(ValueError, match="rate_pct_monthly must be non-negative"):
        bulk_target_calories(profile, tdee_kcal=2500, rate_pct_monthly=-0.05)


@pytest.mark.parametrize("tdee", [1500.0, 2000.0, 2500.0, 3000.0])
def test_floor_engagement_preserves_invariant(tdee):
    """When the calorie floor engages (sub-floor target), the delta must
    still equal target - base."""
    # Small female + aggressive cut → floor will engage.
    profile = _calorie_profile(
        sex=Sex.FEMALE, weight_kg=50.0, body_fat_pct=15.0,
        activity_level=ActivityLevel.SEDENTARY,
    )
    cals = cut_target_calories(profile, tdee_kcal=tdee)
    assert cals.target_calories_kcal > 0
    assert abs(cals.base_tdee_kcal + cals.calorie_delta_kcal - cals.target_calories_kcal) <= 1.0


# ============================================================
# Test 5: DB slug audit
#
# C1 regression: 'bent-over-row' was used in _COMPOUND_PRIMARY_SLUGS but
# actually points to T-Bar Row in the DB, not the Barbell Bent-Over Row.
# ============================================================

def test_every_compound_primary_slug_exists_in_db():
    """Every slug in _COMPOUND_PRIMARY_SLUGS must resolve to an exercise in
    the loaded DB. Catches typos and stale slugs (C1 regression: 'bent-over-row'
    was a valid DB slug but pointed to the wrong exercise)."""
    db = load_exercises()
    db_slugs = {e.slug for e in db if e.slug}
    missing = [s for s in _COMPOUND_PRIMARY_SLUGS if s not in db_slugs]
    assert not missing, (
        f"{len(missing)} _COMPOUND_PRIMARY_SLUGS not found in DB: {missing[:5]}"
    )


def test_no_compound_primary_slug_points_to_machine_or_isolation_exercise():
    """Slugs in _COMPOUND_PRIMARY_SLUGS must point to compound barbell/dumbbell
    exercises, NOT to machine/cable/isolation variants. Catches C1 (where
    'bent-over-row' pointed to T-Bar Row, a machine exercise).

    Note: some exercises are legitimately machine-only (Hack Squat, Leg Press,
    Hip Thrust on machine) — those are listed in _LEGITIMATE_MACHINE_SLUGS.
    The test only flags slugs that DON'T explicitly name the machine variant
    AND aren't in the legitimate list.
    """
    # Exercises that are genuinely machine-only by nature — no barbell
    # equivalent exists in the DB. These are accepted as compound primary
    # because they're the canonical mass-builder for their movement pattern.
    _LEGITIMATE_MACHINE_SLUGS = {
        "hack-squat",        # Hack Squat is a specific machine
        "leg-press",         # Leg Press is machine-only
        "leg-extension",     # isolation, but listed for quad slot
        "hip-thrust",        # often machine-assisted
        "machine-hip-thrust",
        "glute-drive",       # machine
        "pit-shark-belt-squat",  # machine
        "hip-thrust-machine",
    }

    bad_machine_keywords = {"t-bar", "smith"}
    for slug in _COMPOUND_PRIMARY_SLUGS:
        ex = get_exercise_by_slug(slug)
        assert ex is not None, f"Slug {slug!r} not found in DB"
        # Skip explicitly-named machine/cable variants — they're intentional.
        if any(kw in slug for kw in ("t-bar", "machine", "cable", "smith")):
            continue
        # Skip known-legitimate machine exercises.
        if slug in _LEGITIMATE_MACHINE_SLUGS:
            continue
        # For everything else, flag if the equipment contains 't-bar' or
        # 'smith' (the C1 regression symptom — a free-weight slug pointing
        # to a machine exercise).
        equipment_lower = (ex.equipment or "").lower()
        for kw in bad_machine_keywords:
            if kw in equipment_lower:
                pytest.fail(
                    f"Slug {slug!r} -> {ex.name!r} has equipment={ex.equipment!r} "
                    f"(contains {kw!r}). This looks like the C1 'bent-over-row' "
                    f"regression where a free-weight slug points to a machine exercise."
                )


def test_bent_over_barbell_row_is_compound_primary():
    """Direct regression test for C1: the Barbell Bent-Over Row slug must be
    'bent-over-barbell-row' (not 'bent-over-row' which points to T-Bar Row)."""
    assert "bent-over-barbell-row" in _COMPOUND_PRIMARY_SLUGS, (
        "C1 regression: 'bent-over-barbell-row' must be in _COMPOUND_PRIMARY_SLUGS"
    )
    bb_row = get_exercise_by_slug("bent-over-barbell-row")
    assert bb_row is not None, "bent-over-barbell-row slug not found in DB"
    assert "bent over row" in bb_row.name.lower() or "barbell" in bb_row.name.lower(), (
        f"bent-over-barbell-row slug -> {bb_row.name!r} — expected a barbell row"
    )
    # And 'bent-over-row' must NOT be in the primary list (it's T-Bar Row).
    assert "bent-over-row" not in _COMPOUND_PRIMARY_SLUGS, (
        "C1 regression: 'bent-over-row' should not be in _COMPOUND_PRIMARY_SLUGS "
        "(it points to T-Bar Row, a machine exercise)"
    )

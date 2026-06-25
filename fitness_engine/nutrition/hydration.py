"""
Hydration calculations.

Source: fatcalc.com__hydration-calculator (multi-step formula)
"""
from __future__ import annotations

# Phase-6 cleanup: hoisted from inside ``compute_hydration`` (was a deferred
# import for no reason — ``warnings`` has no circular dependency here).
import warnings

from ..models.profile import UserProfile, Sex, ExerciseIntensity, Climate
from ..models.nutrition import HydrationTarget


# === Constants ===
BASE_ML_PER_KG = 30                    # 30 mL/kg
SEX_ADD_ML = {Sex.MALE: 300, Sex.FEMALE: 0}
# Phase-6 fix: dict keys now use the ExerciseIntensity enum members directly
# (was raw strings, which bypassed the type system despite the dedicated enum).
SWEAT_RATE_ML_PER_HR = {
    ExerciseIntensity.LIGHT: 300,
    ExerciseIntensity.MODERATE: 500,
    ExerciseIntensity.INTENSE: 800,
}
# Phase-6 fix: dict keys now use the Climate enum members directly.
CLIMATE_MULTIPLIER = {
    Climate.COLD: 0.95,                  # <20°C — 5% reduction
    Climate.TEMPERATE: 1.0,             # 20-25°C baseline
    Climate.HOT: 1.3,                   # >25°C +30%
    Climate.HOT_HUMID: 1.4,             # >25°C + high humidity +40%
}
PREGNANCY_ADD_ML = 300
BREASTFEEDING_ADD_ML = 700

# Phase-6 fix: soft upper ceiling on daily water intake to flag
# exercise-driven prescriptions that risk hyponatremia. A 100kg male doing 4h
# intense exercise in hot_humid climate can hit ~9.1 L/day, which exceeds the
# ~1.5 L/h kidney clearance ceiling. We clamp the recommendation at this value
# and add a warning note rather than silently emitting an unsafe prescription.
HYDRATION_SOFT_CEILING_L = 5.0

# EFSA / NAM reference values
EFSA_AI = {Sex.FEMALE: 2.0, Sex.MALE: 2.5}    # L/day
NAM_AI = {Sex.FEMALE: 2.7, Sex.MALE: 3.7}     # L/day


def compute_hydration(
    profile: UserProfile,
    exercise_hours_per_day: float = 1.0,
    exercise_intensity: str | "ExerciseIntensity" = "moderate",
    climate: str | "Climate" = "temperate",
    pregnant: bool = False,
    breastfeeding: bool = False,
) -> HydrationTarget:
    """
    Multi-step hydration formula (FatCalc).

    1. Base = weight_kg × 0.030 L
    2. Sex adjustment: +0.3 L if male
    3. Exercise sweat: hours × sweat_rate (L/h)
    4. Climate multiplier applied to total
    5. Pregnancy: +0.3 L
    6. Breastfeeding: +0.7 L

    Tier 3.31 fix: exercise_intensity and climate now accept the ExerciseIntensity
    / Climate enums (or strings for backward compat). Unknown values fall back to
    defaults with a logged warning (previously silent fallback).

    Returns HydrationTarget.
    """
    # Tier 3.31 fix: coerce enums to their string values for dict lookup.
    # Phase-6 fix: now that the dicts are keyed by enum members, we keep the
    # enum form for lookup (strings are coerced to enum values for back-compat).
    if isinstance(exercise_intensity, str):
        try:
            exercise_intensity = ExerciseIntensity(exercise_intensity)
        except ValueError:
            exercise_intensity = None
    if isinstance(climate, str):
        try:
            climate = Climate(climate)
        except ValueError:
            climate = None
    # Validate against known values; fall back to defaults on unknown inputs.
    if exercise_intensity not in SWEAT_RATE_ML_PER_HR:
        # Phase-6 cleanup: ``import warnings`` hoisted to module top.
        warnings.warn(
            f"Unknown exercise_intensity '{exercise_intensity}' — falling back to 'moderate'. "
            f"Valid values: {[e.value for e in ExerciseIntensity]} or ExerciseIntensity enum.",
            stacklevel=2,
        )
        exercise_intensity = ExerciseIntensity.MODERATE
    if climate not in CLIMATE_MULTIPLIER:
        warnings.warn(
            f"Unknown climate '{climate}' — falling back to 'temperate'. "
            f"Valid values: {[c.value for c in Climate]} or Climate enum.",
            stacklevel=2,
        )
        climate = Climate.TEMPERATE

    # Step 1
    water = profile.weight_kg * (BASE_ML_PER_KG / 1000)   # liters
    components = {"base (30 mL/kg)": round(water, 2)}

    # Step 2
    sex_add = SEX_ADD_ML[profile.sex] / 1000
    water += sex_add
    if sex_add > 0:
        components["sex (+male)"] = round(sex_add, 2)

    # Step 3
    sweat = SWEAT_RATE_ML_PER_HR.get(exercise_intensity, 500) / 1000
    exercise_add = exercise_hours_per_day * sweat
    water += exercise_add
    components[f"exercise ({exercise_intensity.value}, {exercise_hours_per_day}h)"] = round(exercise_add, 2)

    # Step 4
    mult = CLIMATE_MULTIPLIER.get(climate, 1.0)
    pre_climate = water
    water *= mult
    if mult != 1.0:
        components[f"climate ({climate.value}, ×{mult})"] = round(water - pre_climate, 2)

    # Step 5
    if pregnant:
        water += PREGNANCY_ADD_ML / 1000
        components["pregnancy"] = round(PREGNANCY_ADD_ML / 1000, 2)

    # Step 6
    if breastfeeding:
        water += BREASTFEEDING_ADD_ML / 1000
        components["breastfeeding"] = round(BREASTFEEDING_ADD_ML / 1000, 2)

    # Phase-6 fix: soft ceiling on daily water intake. Above 5 L/day the risk
    # of exercise-associated hyponatremia (EAH) rises sharply; we clamp the
    # prescription and surface a warning note rather than silently emitting an
    # unsafe value.
    clamped = False
    if water > HYDRATION_SOFT_CEILING_L:
        clamped = True
        original = water
        water = HYDRATION_SOFT_CEILING_L
        components[f"hyponatremia cap (was {original:.2f} L)"] = round(water - original, 2)

    notes = [
        f"EFSA AI ({profile.sex.value}): {EFSA_AI[profile.sex]} L/day",
        f"NAM AI ({profile.sex.value}): {NAM_AI[profile.sex]} L/day",
        "Target urine color: pale yellow (lemonade).",
        "~20% of daily fluid intake typically comes from food.",
    ]
    if clamped:
        notes.append(
            f"Phase-6 fix: prescription clamped to {HYDRATION_SOFT_CEILING_L:.1f} L/day "
            f"(original {original:.2f} L exceeded the soft hyponatremia ceiling). "
            "Spread intake across the day; do not exceed ~1.0-1.5 L/h during exercise."
        )

    return HydrationTarget(
        water_liters_per_day=round(water, 2),
        components={k: v for k, v in components.items() if v != 0},
        notes=notes,
    )


__all__ = [
    "BASE_ML_PER_KG", "SEX_ADD_ML", "SWEAT_RATE_ML_PER_HR",
    "CLIMATE_MULTIPLIER", "PREGNANCY_ADD_ML", "BREASTFEEDING_ADD_ML",
    "EFSA_AI", "NAM_AI", "HYDRATION_SOFT_CEILING_L",
    "compute_hydration",
]

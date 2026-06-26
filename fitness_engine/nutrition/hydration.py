"""
Hydration calculations.

Source: fatcalc.com__hydration-calculator (multi-step formula)
"""
from __future__ import annotations

import warnings

from ..models.nutrition import HydrationTarget
from ..models.profile import Climate, ExerciseIntensity, Sex, UserProfile

# === Constants ===
BASE_ML_PER_KG = 30                    # 30 mL/kg
SEX_ADD_ML = {Sex.MALE: 300, Sex.FEMALE: 0}
# dict keys use the ExerciseIntensity enum members directly.
SWEAT_RATE_ML_PER_HR = {
    ExerciseIntensity.LIGHT: 300,
    ExerciseIntensity.MODERATE: 500,
    ExerciseIntensity.INTENSE: 800,
}
# dict keys use the Climate enum members directly.
CLIMATE_MULTIPLIER = {
    Climate.COLD: 0.95,                  # <20°C — 5% reduction
    Climate.TEMPERATE: 1.0,             # 20-25°C baseline
    Climate.HOT: 1.3,                   # >25°C +30%
    Climate.HOT_HUMID: 1.4,             # >25°C + high humidity +40%
}
PREGNANCY_ADD_ML = 300
BREASTFEEDING_ADD_ML = 700

# soft upper ceiling on daily water intake to flag
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
    exercise_intensity: str | ExerciseIntensity = "moderate",
    climate: str | Climate = "temperate",
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
    # strings coerced to enum values for back-compat (dicts keyed by enum
    # members). Preserve the original user-supplied value for the warning
    # message.
    original_intensity = exercise_intensity
    original_climate = climate
    # MEDIUM-severity fix: case-insensitive coercion. Previously
    # `ExerciseIntensity("Moderate")` (capitalized) would raise ValueError,
    # silently falling back to MODERATE — but only after warning the user
    # about an "unknown" value they had clearly specified. Now we lowercase
    # first so "Moderate" / "MODERATE" / "moderate" all work.
    if isinstance(exercise_intensity, str):
        try:
            exercise_intensity = ExerciseIntensity(exercise_intensity.lower())
        except ValueError:
            exercise_intensity = None
    if isinstance(climate, str):
        try:
            climate = Climate(climate.lower())
        except ValueError:
            climate = None
    # Validate against known values; fall back to defaults on unknown inputs.
    if exercise_intensity not in SWEAT_RATE_ML_PER_HR:
        warnings.warn(
            f"Unknown exercise_intensity '{original_intensity}' — falling back to 'moderate'. "
            f"Valid values: {[e.value for e in ExerciseIntensity]} or ExerciseIntensity enum.",
            stacklevel=2,
        )
        exercise_intensity = ExerciseIntensity.MODERATE
    if climate not in CLIMATE_MULTIPLIER:
        warnings.warn(
            f"Unknown climate '{original_climate}' — falling back to 'temperate'. "
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
    # HIGH-severity fix: previously the climate multiplier was applied to the
    # TOTAL water (base + sex + exercise), but the cited source
    # (fatcalc.com__hydration-calculator.txt) describes the multipliers as
    # affecting sweat losses specifically — "Reduced sweat losses in cool
    # environments", "Significantly increased sweat losses", "Maximum sweat
    # production as humidity impairs evaporative cooling". Baseline metabolic
    # water needs don't increase 30% just because it's hot. Now: apply the
    # multiplier only to the exercise/sweat component, then add back to base.
    # Concrete impact for 100 kg male, 2h intense exercise, hot climate:
    #   was: (3.0 + 0.3 + 1.6) × 1.3 = 6.37 L
    #   now: 3.0 + 0.3 + (1.6 × 1.3) = 5.38 L  (saves ~1 L/day overestimation)
    mult = CLIMATE_MULTIPLIER.get(climate, 1.0)
    if mult != 1.0 and exercise_add > 0:
        # Undo the un-multiplied exercise_add we already added, then add back
        # the climate-scaled version.
        water -= exercise_add
        climate_adjusted_exercise = exercise_add * mult
        water += climate_adjusted_exercise
        components[f"climate ({climate.value}, ×{mult} on sweat)"] = round(
            climate_adjusted_exercise - exercise_add, 2
        )
        # Update the displayed exercise component to reflect the actual sweat
        # volume (was the pre-climate amount; now includes climate adjustment).
        components[f"exercise ({exercise_intensity.value}, {exercise_hours_per_day}h, climate-adj)"] = round(
            climate_adjusted_exercise, 2
        )
        # Remove the un-adjusted exercise key we added in Step 3.
        components.pop(f"exercise ({exercise_intensity.value}, {exercise_hours_per_day}h)", None)

    # Step 5
    # MEDIUM-severity fix: validate biological plausibility. A male user with
    # pregnant=True would silently get +0.3 L added — a domain-correctness gap.
    if pregnant and profile.sex == Sex.MALE:
        raise ValueError(
            "pregnant=True is biologically impossible for Sex.MALE — check the input."
        )
    if breastfeeding and profile.sex == Sex.MALE:
        raise ValueError(
            "breastfeeding=True is biologically impossible for Sex.MALE — check the input."
        )
    if pregnant:
        water += PREGNANCY_ADD_ML / 1000
        components["pregnancy"] = round(PREGNANCY_ADD_ML / 1000, 2)

    # Step 6
    if breastfeeding:
        water += BREASTFEEDING_ADD_ML / 1000
        components["breastfeeding"] = round(BREASTFEEDING_ADD_ML / 1000, 2)

    # soft ceiling on daily water intake. Above 5 L/day the risk
    # of exercise-associated hyponatremia (EAH) rises sharply; we clamp the
    # prescription and surface a warning note rather than silently emitting an
    # unsafe value.
    clamped = False
    if water > HYDRATION_SOFT_CEILING_L:
        clamped = True
        original = water
        water = HYDRATION_SOFT_CEILING_L
        # MEDIUM-severity fix: previously added a NEGATIVE entry to components
        # (water - original is negative after clamping), making the sum of
        # components no longer equal water_liters_per_day. Now we keep the
        # clamp info in `notes` only — components stay as a true additive
        # decomposition of the final water_liters_per_day.

    notes = [
        f"EFSA AI ({profile.sex.value}): {EFSA_AI[profile.sex]} L/day",
        f"NAM AI ({profile.sex.value}): {NAM_AI[profile.sex]} L/day",
        "Target urine color: pale yellow (lemonade).",
        "~20% of daily fluid intake typically comes from food.",
    ]
    if clamped:
        notes.append(
            f"⚠ Prescription clamped to {HYDRATION_SOFT_CEILING_L:.1f} L/day "
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

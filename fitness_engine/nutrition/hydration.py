"""
Hydration calculations.

Source: fatcalc.com__hydration-calculator (multi-step formula)
"""
from __future__ import annotations

from ..models.profile import UserProfile, Sex
from ..models.nutrition import HydrationTarget


# === Constants ===
BASE_ML_PER_KG = 30                    # 30 mL/kg
SEX_ADD_ML = {Sex.MALE: 300, Sex.FEMALE: 0}
SWEAT_RATE_ML_PER_HR = {
    "light": 300,
    "moderate": 500,
    "intense": 800,
}
CLIMATE_MULTIPLIER = {
    "cold": 0.95,                       # <20°C — 5% reduction
    "temperate": 1.0,                   # 20-25°C baseline
    "hot": 1.3,                         # >25°C +30%
    "hot_humid": 1.4,                   # >25°C + high humidity +40%
}
PREGNANCY_ADD_ML = 300
BREASTFEEDING_ADD_ML = 700

# EFSA / NAM reference values
EFSA_AI = {Sex.FEMALE: 2.0, Sex.MALE: 2.5}    # L/day
NAM_AI = {Sex.FEMALE: 2.7, Sex.MALE: 3.7}     # L/day


def compute_hydration(
    profile: UserProfile,
    exercise_hours_per_day: float = 1.0,
    exercise_intensity: str = "moderate",
    climate: str = "temperate",
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

    Returns HydrationTarget.
    """
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
    components[f"exercise ({exercise_intensity}, {exercise_hours_per_day}h)"] = round(exercise_add, 2)

    # Step 4
    mult = CLIMATE_MULTIPLIER.get(climate, 1.0)
    pre_climate = water
    water *= mult
    if mult != 1.0:
        components[f"climate ({climate}, ×{mult})"] = round(water - pre_climate, 2)

    # Step 5
    if pregnant:
        water += PREGNANCY_ADD_ML / 1000
        components["pregnancy"] = round(PREGNANCY_ADD_ML / 1000, 2)

    # Step 6
    if breastfeeding:
        water += BREASTFEEDING_ADD_ML / 1000
        components["breastfeeding"] = round(BREASTFEEDING_ADD_ML / 1000, 2)

    notes = [
        f"EFSA AI ({profile.sex.value}): {EFSA_AI[profile.sex]} L/day",
        f"NAM AI ({profile.sex.value}): {NAM_AI[profile.sex]} L/day",
        "Target urine color: pale yellow (lemonade).",
        "~20% of daily fluid intake typically comes from food.",
    ]

    return HydrationTarget(
        water_liters_per_day=round(water, 2),
        components={k: v for k, v in components.items() if v != 0},
        notes=notes,
    )


__all__ = [
    "BASE_ML_PER_KG", "SEX_ADD_ML", "SWEAT_RATE_ML_PER_HR",
    "CLIMATE_MULTIPLIER", "PREGNANCY_ADD_ML", "BREASTFEEDING_ADD_ML",
    "EFSA_AI", "NAM_AI",
    "compute_hydration",
]

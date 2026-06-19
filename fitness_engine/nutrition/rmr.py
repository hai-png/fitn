"""
Resting Metabolic Rate (RMR) formulas.

Sources:
- Mifflin-St Jeor (1990): fatcalc.com__rmr-calculator, gymgeek.com__calculators-calorie-calculator
- Harris-Benedict original (1919): rippedbody.com__calories
- Harris-Benedict revised (1984): fatcalc.com__rmr-calculator
- Cunningham / Katch-McArdle (1991): fatcalc.com__rmr-calculator
- Metabolic adaptation: rippedbody.com__macro-calculator
"""
from __future__ import annotations

from ..models.profile import UserProfile, Sex
from ..models.nutrition import RMRResult, RMRFormula


def rmr_mifflin_st_jeor(profile: UserProfile) -> float:
    """
    Mifflin-St Jeor (1990) — DEFAULT for general population.

    Men:   RMR = 9.99 × weight_kg + 6.25 × height_cm − 4.92 × age + 5
    Women: RMR = 9.99 × weight_kg + 6.25 × height_cm − 4.92 × age − 161
    """
    base = 9.99 * profile.weight_kg + 6.25 * profile.height_cm - 4.92 * profile.age
    if profile.sex == Sex.MALE:
        return base + 5
    return base - 161


def rmr_harris_benedict_original(profile: UserProfile) -> float:
    """
    Harris-Benedict original (1919) — RippedBody's preferred.

    Men:   BMR = 66 + 13.7 × weight_kg + 5 × height_cm − 6.8 × age
    Women: BMR = 655 + 9.6 × weight_kg + 1.8 × height_cm − 4.7 × age
    """
    if profile.sex == Sex.MALE:
        return 66 + 13.7 * profile.weight_kg + 5 * profile.height_cm - 6.8 * profile.age
    return 655 + 9.6 * profile.weight_kg + 1.8 * profile.height_cm - 4.7 * profile.age


def rmr_harris_benedict_revised(profile: UserProfile) -> float:
    """
    Harris-Benedict revised (1984, Roza & Shizgal).
    """
    if profile.sex == Sex.MALE:
        return (13.397 * profile.weight_kg + 4.799 * profile.height_cm
                - 5.677 * profile.age + 88.362)
    return (9.247 * profile.weight_kg + 3.098 * profile.height_cm
            - 4.330 * profile.age + 447.593)


def rmr_cunningham(profile: UserProfile, body_fat_pct: float) -> float:
    """
    Cunningham (1991) / "Katch-McArdle" — body-composition-aware.
    RMR = 370 + 21.6 × LBM_kg

    Use when BF% is known and user is athletic / muscular.
    """
    lbm = profile.weight_kg * (1 - body_fat_pct / 100)
    return 370 + 21.6 * lbm


def select_rmr_formula(profile: UserProfile) -> RMRFormula:
    """
    Select RMR formula based on data availability.

    - If BF% known: Cunningham (best for athletic/muscular)
    - Else: Mifflin-St Jeor (general-population default)
    """
    if profile.body_fat_pct is not None:
        return RMRFormula.CUNNINGHAM
    return RMRFormula.MIFFLIN_ST_JEOR


def compute_rmr(
    profile: UserProfile,
    body_fat_pct: float | None = None,
    in_active_deficit: bool = False,
    weight_reduced_pct: float = 0.0,
) -> RMRResult:
    """
    Compute RMR with metabolic adaptations applied.

    Adaptations (RippedBody):
      - In active deficit: -5%
      - >10% below all-time high body weight: -3%
      Both apply multiplicatively.

    Args:
      profile: user profile
      body_fat_pct: BF% (use computed value from assessment)
      in_active_deficit: True if user is currently in a cutting phase
      weight_reduced_pct: 0-1, fraction below all-time high body weight
    """
    formula = select_rmr_formula(profile)

    if formula == RMRFormula.CUNNINGHAM and body_fat_pct is not None:
        base_rmr = rmr_cunningham(profile, body_fat_pct)
    elif formula == RMRFormula.MIFFLIN_ST_JEOR:
        base_rmr = rmr_mifflin_st_jeor(profile)
    elif formula == RMRFormula.HARRIS_BENEDICT_ORIG:
        base_rmr = rmr_harris_benedict_original(profile)
    else:
        base_rmr = rmr_mifflin_st_jeor(profile)
        formula = RMRFormula.MIFFLIN_ST_JEOR

    # Apply adaptations
    notes: list[str] = [f"Base RMR ({formula.value}): {base_rmr:.0f} kcal"]
    adaptation_factor = 1.0
    weight_reduced_factor = 1.0

    if in_active_deficit:
        adaptation_factor = 0.95
        notes.append("Metabolic adaptation: -5% (active deficit).")

    if weight_reduced_pct > 0.10:
        weight_reduced_factor = 0.97
        notes.append(
            f"Weight-reduced state: -3% ({weight_reduced_pct*100:.0f}% "
            "below all-time high)."
        )

    adjusted_rmr = base_rmr * adaptation_factor * weight_reduced_factor

    return RMRResult(
        formula=formula,
        base_rmr_kcal=round(base_rmr, 1),
        metabolic_adaptation_factor=adaptation_factor,
        weight_reduced_factor=weight_reduced_factor,
        adjusted_rmr_kcal=round(adjusted_rmr, 1),
        notes=notes,
    )


__all__ = [
    "rmr_mifflin_st_jeor", "rmr_harris_benedict_original",
    "rmr_harris_benedict_revised", "rmr_cunningham",
    "select_rmr_formula", "compute_rmr",
]

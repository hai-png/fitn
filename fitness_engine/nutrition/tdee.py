"""
TDEE (Total Daily Energy Expenditure) and Adaptive TDEE.

Sources:
- Activity multipliers (RippedBody 5-cat): rippedbody.com__macro-calculator
- Activity multipliers (Harris-Benedict SAF): fatcalc.com__tdee-calculator
- Adaptive TDEE first-principles: gymcreek.com__adaptive-tdee-calculator,
  zolthealth.com__learn-what-is-adaptive-tdee, gymgeek.com__calculators-adaptive-tdee-calculator
- Statistical-model adaptive TDEE: gymgeek.com__calculators-adaptive-tdee-calculator
"""
from __future__ import annotations

from typing import Optional

from ..models.profile import UserProfile, ActivityLevel
from ..models.nutrition import RMRResult, TDEEResult


# === Activity multipliers (RippedBody 5-category — DEFAULT) ===
ACTIVITY_FACTORS_RIPPEDBODY = {
    ActivityLevel.SEDENTARY:         1.25,
    ActivityLevel.MOSTLY_SEDENTARY:  1.45,
    ActivityLevel.LIGHTLY_ACTIVE:    1.65,
    ActivityLevel.ACTIVE:            1.85,
    ActivityLevel.HIGHLY_ACTIVE:     2.05,
}

# === Harris-Benedict SAF (alternative) ===
ACTIVITY_FACTORS_HARRIS_BENEDICT = {
    ActivityLevel.SEDENTARY:         1.20,
    ActivityLevel.MOSTLY_SEDENTARY:  1.375,
    ActivityLevel.LIGHTLY_ACTIVE:    1.55,
    ActivityLevel.ACTIVE:            1.725,
    ActivityLevel.HIGHLY_ACTIVE:     1.90,
}


def activity_factor(profile: UserProfile) -> float:
    """Get activity multiplier for the user's level (RippedBody default)."""
    return ACTIVITY_FACTORS_RIPPEDBODY[profile.activity_level]


def compute_tdee(rmr: RMRResult, profile: UserProfile) -> TDEEResult:
    """
    Compute TDEE = RMR × activity_factor.

    If intake/weight logs are available, also compute adaptive TDEE.
    """
    factor = activity_factor(profile)
    tdee = rmr.adjusted_rmr_kcal * factor

    notes = [
        f"RMR (adjusted): {rmr.adjusted_rmr_kcal:.0f} kcal",
        f"Activity factor: {factor} ({profile.activity_level.value})",
        f"TDEE = RMR × {factor} = {tdee:.0f} kcal",
    ]

    return TDEEResult(
        rmr_kcal=rmr.adjusted_rmr_kcal,
        activity_factor=factor,
        tdee_kcal=round(tdee, 1),
        adaptive_tdee_kcal=None,
        final_tdee_kcal=round(tdee, 1),
        notes=notes,
    )


# === Adaptive TDEE ===

def observed_tdee_first_principles(
    avg_intake_kcal: float,
    weight_start_kg: float,
    weight_end_kg: float,
    n_days: int,
) -> float:
    """
    First-principles observed-TDEE identity (nSuns / Reddit formulation).

    observed_TDEE = avg_intake − (Δweight_kg × 7700) / N_days

    Source: gymcreek.com__adaptive-tdee-calculator,
            zolthealth.com__learn-what-is-adaptive-tdee

    Args:
      avg_intake_kcal: average daily calorie intake over the window
      weight_start_kg: body weight at start of window
      weight_end_kg: body weight at end of window
      n_days: number of days in the window

    Phase-6 fix: validates n_days >= 1 to prevent ZeroDivisionError.
    """
    if n_days < 1:
        raise ValueError(f"n_days must be >= 1, got {n_days}")
    delta_weight = weight_end_kg - weight_start_kg
    return avg_intake_kcal - (delta_weight * 7700.0) / n_days


def adaptive_weight_data(n_days: int) -> float:
    """
    Bayesian blend weight for statistical-model adaptive TDEE.

    - 0–7 days of data: pure prior (Mifflin-St Jeor)
    - 8–60 days: linear ramp from 0 → 1
    - >60 days: pure observed TDEE

    Source: gymgeek.com__calculators-adaptive-tdee-calculator (mechanism
    described; formula reconstructed as the unique solution consistent
    with all source claims).
    """
    if n_days <= 7:
        return 0.0
    if n_days >= 60:
        return 1.0
    return (n_days - 7) / 53.0


def adaptive_tdee(
    prior_tdee: float,
    avg_intake_kcal: float,
    weight_start_kg: float,
    weight_end_kg: float,
    n_days: int,
) -> float:
    """
    Statistical-model adaptive TDEE (Bayesian blend).

    adaptive_TDEE = w_data × observed_TDEE + (1 − w_data) × prior_TDEE

    Source: gymgeek.com__calculators-adaptive-tdee-calculator,
            zolthealth.com__learn-what-is-adaptive-tdee
    """
    if n_days < 1:
        return prior_tdee
    w = adaptive_weight_data(n_days)
    observed = observed_tdee_first_principles(
        avg_intake_kcal, weight_start_kg, weight_end_kg, n_days
    )
    return w * observed + (1 - w) * prior_tdee


def update_tdee_with_logs(
    tdee: TDEEResult,
    avg_intake_kcal: float,
    weight_start_kg: float,
    weight_end_kg: float,
    n_days: int,
) -> TDEEResult:
    """Update a TDEEResult with adaptive TDEE from logged intake + weight."""
    if n_days < 1:
        return tdee
    adaptive = adaptive_tdee(
        prior_tdee=tdee.tdee_kcal,
        avg_intake_kcal=avg_intake_kcal,
        weight_start_kg=weight_start_kg,
        weight_end_kg=weight_end_kg,
        n_days=n_days,
    )
    tdee.adaptive_tdee_kcal = round(adaptive, 1)
    tdee.final_tdee_kcal = round(adaptive, 1)
    tdee.notes.append(
        f"Adaptive TDEE ({n_days}d, w_data={adaptive_weight_data(n_days):.2f}): "
        f"{adaptive:.0f} kcal"
    )
    return tdee


__all__ = [
    "ACTIVITY_FACTORS_RIPPEDBODY", "ACTIVITY_FACTORS_HARRIS_BENEDICT",
    "activity_factor", "compute_tdee",
    "observed_tdee_first_principles", "adaptive_weight_data", "adaptive_tdee",
    "update_tdee_with_logs",
]

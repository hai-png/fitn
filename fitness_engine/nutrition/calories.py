"""
Calorie target calculations for cut / bulk / maintenance / recomp / reverse diet.

Sources:
- Cut/bulk formulas: rippedbody.com__calories, rippedbody.com__macro-calculator
- Cut rate tiers: macrofactor.com__cutting-calculator
- Bulk rate tiers & caps: macrofactor.com__bulking-calculator
- Bulk rates by training status: rippedbody.com__updated-bulking-guidelines
- Calorie floors: fatcalc.com__bwp, gymgeek.com__calculators-calorie-calculator
- Reverse diet: fatcalc.com__reverse-diet-calculator
"""
from __future__ import annotations

import math

from ..models.profile import (
    UserProfile, Sex, TrainingStatus, PrimaryGoal, CutRateTier, BulkAggressiveness,
)
from ..models.assessment import RecommendedStrategy
from ..models.nutrition import CalorieTargets, CalorieStrategy
from ..utils.units import kg_to_lb, lb_to_kg
# Phase-6 cleanup: hoisted from inside ``recomp_target_calories`` (was a
# deferred import to avoid a circular dependency at module load time, but
# ``assessment.decision`` only imports constants and ``Sex`` is already at top).
from ..assessment.decision import CUT_BULK_BOUNDARIES


# === Energy constants ===
KCAL_PER_LB_FAT = 3500
KCAL_PER_KG_FAT = 7700
KCAL_PER_LB_MUSCLE = 2500
SURPLUS_KCAL_PER_LB_PER_MONTH = 150    # daily kcal/lb of monthly gain (bulk w/ +50% NEAT buffer)
SURPLUS_KCAL_PER_KG_PER_MONTH = 330    # daily kcal/kg of monthly gain
DEFICIT_KCAL_PER_LB_PER_WEEK = 500
DEFICIT_KCAL_PER_KG_PER_WEEK = 1100

# === Calorie floors ===
MIN_CALORIES = {Sex.FEMALE: 1200, Sex.MALE: 1500}

# === Hard caps ===
# RED-S protection: 1.0 % BW/week is the documented ceiling for women in
# active deficit (amenorrhea / bone loss risk above this). 1.5 % is unsafe
# and has been removed.
MAX_WEEKLY_LOSS_PCT = 0.010   # 1.0 % BW/week

# === Cut rate tiers (MacroFactor) ===
# VERY_AGGRESSIVE is clipped to MAX_WEEKLY_LOSS_PCT (1.0 %) at runtime;
# the tier is retained for API compatibility but its effective rate is capped.
CUT_RATE_TIERS = {
    CutRateTier.VERY_CONSERVATIVE: 0.0010,   # 0.10 % BW/week
    CutRateTier.CONSERVATIVE:      0.0025,   # 0.25 %
    CutRateTier.MODERATE:          0.0075,   # 0.75 %
    CutRateTier.AGGRESSIVE:        0.0100,   # 1.00 % (= safety cap)
    CutRateTier.VERY_AGGRESSIVE:   0.0100,   # clipped to 1.00 %
}
DEFAULT_CUT_RATE_PCT = 0.0075   # 0.75 % BW/week
SWEET_SPOT_CUT_RATE_PCT = 0.005  # 0.50 %

# === Bulk rate by training status (monthly % BW) ===
BULK_RATE_BY_STATUS = {
    TrainingStatus.BEGINNER:     0.020,    # 2.0 % BW/month
    TrainingStatus.NOVICE:       0.015,    # 1.5 %
    TrainingStatus.INTERMEDIATE: 0.010,    # 1.0 %
    TrainingStatus.ADVANCED:     0.005,    # 0.5 %
}

# === Bulk weekly rate tiers (MacroFactor — % BW/week) ===
BULK_WEEKLY_RATE_TIERS = {
    # (beginner, intermediate, experienced)
    BulkAggressiveness.CONSERVATIVE:    (0.0020, 0.0015, 0.0010),
    BulkAggressiveness.HAPPY_MEDIUM:    (0.0050, 0.00325, 0.0015),  # DEFAULT
    BulkAggressiveness.AGGRESSIVE:      (0.0080, 0.00575, 0.0035),
    BulkAggressiveness.VERY_AGGRESSIVE: (0.0100, 0.00800, 0.0060),
}

# === Reverse diet presets ===
REVERSE_DIET_WEEKLY_INCREMENT = {
    "conservative": 50,
    "moderate": 100,
    "aggressive": 150,
}
REVERSE_DIET_RED_FLAG_WEEKLY_GAIN_PCT = 0.005


# === Helpers ===
# Phase-6: removed duplicated _lb_to_kg / _kg_to_lb — use utils.units instead.


def _apply_calorie_floor(calories: float, sex: Sex) -> tuple[float, bool, int]:
    """Apply minimum calorie floor; return (final, applied, floor)."""
    floor = MIN_CALORIES[sex]
    if calories < floor:
        return float(floor), True, floor
    return calories, False, floor


def cut_target_calories(
    profile: UserProfile,
    tdee_kcal: float,
    rate_pct: float | None = None,
) -> CalorieTargets:
    """
    Compute cut calorie target.

    TDCI_cut = TDEE − (weight_kg × weekly_rate × 1100)
    """
    # Select rate
    if rate_pct is None:
        if profile.cut_rate_tier is not None:
            rate_pct = CUT_RATE_TIERS[profile.cut_rate_tier]
        else:
            # Default: scale down for leaner users.
            # Tier 2.14 fix: use `is not None` instead of falsy check (was
            # `if profile.body_fat_pct else 25` which silently used 25 when
            # body_fat_pct=0). Also use the exported DEFAULT_CUT_RATE_PCT
            # constant instead of the magic 25 when BF% is genuinely unknown.
            bf_pct = profile.body_fat_pct if profile.body_fat_pct is not None else None
            if bf_pct is None:
                # Unknown BF% — use the MODERATE default (0.75% for men, 0.5% for women
                # would be asymmetric; DEFAULT_CUT_RATE_PCT = 0.0075 is the documented
                # moderate tier and applies to both sexes).
                rate_pct = DEFAULT_CUT_RATE_PCT
            else:
                # Phase-6 fix: previously these inline thresholds hardcoded
                # 0.005/0.0075/0.010 instead of referencing SWEET_SPOT_CUT_RATE_PCT /
                # DEFAULT_CUT_RATE_PCT / MAX_WEEKLY_LOSS_PCT. Now we use the exported
                # constants as the single source of truth (so future changes to the
                # constants propagate here automatically).
                if profile.sex == Sex.MALE:
                    if bf_pct >= 25:
                        rate_pct = MAX_WEEKLY_LOSS_PCT       # 1.0 % — obese, max safe rate
                    elif bf_pct >= 20:
                        rate_pct = DEFAULT_CUT_RATE_PCT      # 0.75 % — moderate
                    elif bf_pct >= 15:
                        rate_pct = SWEET_SPOT_CUT_RATE_PCT   # 0.5 % — sweet spot
                    else:
                        rate_pct = SWEET_SPOT_CUT_RATE_PCT   # ≤0.5 % for lean
                else:
                    if bf_pct >= 35:
                        rate_pct = MAX_WEEKLY_LOSS_PCT
                    elif bf_pct >= 28:
                        rate_pct = DEFAULT_CUT_RATE_PCT
                    elif bf_pct >= 22:
                        rate_pct = SWEET_SPOT_CUT_RATE_PCT
                    else:
                        rate_pct = SWEET_SPOT_CUT_RATE_PCT

    # Enforce hard cap (>= so the VERY_AGGRESSIVE tier is also clipped)
    capped = rate_pct >= MAX_WEEKLY_LOSS_PCT
    if capped:
        # Tier 2.14 fix: warn the user when their requested rate is clipped
        original_rate = rate_pct
        rate_pct = MAX_WEEKLY_LOSS_PCT
        # Note added below after we compute the target
        cap_warning = (
            f"⚠ Requested cut rate {original_rate*100:.2f}% clipped to safety "
            f"cap {MAX_WEEKLY_LOSS_PCT*100:.2f}% BW/week."
        )
    else:
        cap_warning = None

    weekly_loss_kg = profile.weight_kg * rate_pct
    weekly_loss_lb = kg_to_lb(weekly_loss_kg)
    daily_deficit_kcal = weekly_loss_kg * DEFICIT_KCAL_PER_KG_PER_WEEK
    target = tdee_kcal - daily_deficit_kcal

    # Apply floor
    target, floor_applied, floor = _apply_calorie_floor(target, profile.sex)

    rate_label = f"{rate_pct*100:.2f}% BW/week ≈ {weekly_loss_kg:.2f} kg/wk"

    notes = [
        f"Cut rate: {rate_label}",
        f"Daily deficit: {daily_deficit_kcal:.0f} kcal",
        f"Target = TDEE ({tdee_kcal:.0f}) − deficit ({daily_deficit_kcal:.0f}) "
        f"= {target:.0f} kcal",
    ]
    if cap_warning:
        notes.append(cap_warning)
    if floor_applied:
        notes.append(
            f"⚠ Calorie floor applied: {floor} kcal ({profile.sex.value} minimum). "
            "Increase activity instead of cutting further."
        )

    return CalorieTargets(
        strategy=CalorieStrategy.DEFICIT,
        base_tdee_kcal=round(tdee_kcal, 1),
        rate_pct=rate_pct,
        rate_label=rate_label,
        calorie_delta_kcal=round(-daily_deficit_kcal, 1),
        target_calories_kcal=round(target, 1),
        calorie_floor_applied=floor_applied,
        floor_kcal=floor,
        notes=notes,
    )


def bulk_target_calories(
    profile: UserProfile,
    tdee_kcal: float,
    rate_pct_monthly: float | None = None,
) -> CalorieTargets:
    """
    Compute bulk calorie target.

    TDCI_bulk = TDEE + (weight_kg × monthly_rate × 330)

    Tier 2.15 fix: `profile.bulk_aggressiveness` is now honored (previously
    the user-facing setting was silently ignored — the rate was always
    `BULK_RATE_BY_STATUS[training_status]`). When `bulk_aggressiveness` is
    set, we use `BULK_WEEKLY_RATE_TIERS[aggressiveness][status_idx]` and
    convert the weekly rate to a monthly rate (×4.345). When not set, we
    fall back to the legacy `BULK_RATE_BY_STATUS` table.
    """
    if rate_pct_monthly is None:
        # Tier 2.15 fix: honor bulk_aggressiveness if the user set it.
        if profile.bulk_aggressiveness is not None:
            # Map TrainingStatus to the tier index (beginner=0, novice=0, intermediate=1, advanced=2).
            # Novice uses the beginner tier (closest match in the MacroFactor table).
            status_idx_map = {
                TrainingStatus.BEGINNER: 0,
                TrainingStatus.NOVICE: 0,
                TrainingStatus.INTERMEDIATE: 1,
                TrainingStatus.ADVANCED: 2,
            }
            status_idx = status_idx_map.get(profile.training_status, 1)
            weekly_rate = BULK_WEEKLY_RATE_TIERS[profile.bulk_aggressiveness][status_idx]
            # Convert weekly % to monthly % (avg 4.345 weeks/month)
            WEEKS_PER_MONTH = 4.348  # 365.25/12/7
            rate_pct_monthly = weekly_rate * WEEKS_PER_MONTH
        else:
            rate_pct_monthly = BULK_RATE_BY_STATUS[profile.training_status]

    monthly_gain_kg = profile.weight_kg * rate_pct_monthly
    daily_surplus_kcal = monthly_gain_kg * SURPLUS_KCAL_PER_KG_PER_MONTH
    target = tdee_kcal + daily_surplus_kcal

    # Floors don't apply to bulking; no upper cap on surplus in Phase-1
    aggressiveness_label = (
        f", aggressiveness={profile.bulk_aggressiveness.value}"
        if profile.bulk_aggressiveness is not None
        else ""
    )
    rate_label = (
        f"{rate_pct_monthly*100:.2f}% BW/month ≈ {monthly_gain_kg:.2f} kg/mo "
        f"({profile.training_status.value}{aggressiveness_label})"
    )

    notes = [
        f"Bulk rate: {rate_label}",
        f"Daily surplus: {daily_surplus_kcal:.0f} kcal "
        "(includes +50% NEAT-compensation buffer)",
        f"Target = TDEE ({tdee_kcal:.0f}) + surplus ({daily_surplus_kcal:.0f}) "
        f"= {target:.0f} kcal",
    ]

    return CalorieTargets(
        strategy=CalorieStrategy.SURPLUS,
        base_tdee_kcal=round(tdee_kcal, 1),
        rate_pct=rate_pct_monthly,
        rate_label=rate_label,
        calorie_delta_kcal=round(daily_surplus_kcal, 1),
        target_calories_kcal=round(target, 1),
        calorie_floor_applied=False,
        floor_kcal=None,
        notes=notes,
    )


def maintenance_target_calories(tdee_kcal: float) -> CalorieTargets:
    """Maintenance: TDCI = TDEE."""
    return CalorieTargets(
        strategy=CalorieStrategy.MAINTENANCE,
        base_tdee_kcal=round(tdee_kcal, 1),
        rate_pct=0.0,
        rate_label="maintenance (no surplus/deficit)",
        calorie_delta_kcal=0.0,
        target_calories_kcal=round(tdee_kcal, 1),
        calorie_floor_applied=False,
        floor_kcal=None,
        notes=[f"Target = TDEE = {tdee_kcal:.0f} kcal"],
    )


def recomp_target_calories(
    profile: UserProfile,
    tdee_kcal: float,
    body_fat_pct: float,
) -> CalorieTargets:
    """
    Recomp calorie target based on BF% (FatCalc / McDonald model).

    - High recomp potential (BF% ≥ recomp_excellent): 10-20% deficit
    - Moderate recomp potential: 0-10% deficit
    """
    # Phase-6 cleanup: ``CUT_BULK_BOUNDARIES`` is now imported at module top;
    # ``Sex`` is already in the top-level ``from ..models.profile import ...``.
    b = CUT_BULK_BOUNDARIES[profile.sex]

    if body_fat_pct >= b["recomp_excellent"]:
        deficit_pct = 0.15   # 15 % deficit (mid of 10-20%)
        label = "high (10-20% deficit)"
    elif body_fat_pct >= b["recomp_good_lo"]:
        deficit_pct = 0.05   # 5 % deficit (mid of 0-10%)
        label = "moderate (0-10% deficit)"
    else:
        # Limited recomp — shouldn't reach here, but handle gracefully
        deficit_pct = 0.0
        label = "limited (use bulk/cut instead)"

    deficit_kcal = tdee_kcal * deficit_pct
    target = tdee_kcal - deficit_kcal
    target, floor_applied, floor = _apply_calorie_floor(target, profile.sex)

    notes = [
        f"Recomp potential: {label}",
        f"BF%={body_fat_pct:.1f}",
        f"Target = TDEE × (1 − {deficit_pct:.0%}) = {target:.0f} kcal",
    ]

    return CalorieTargets(
        strategy=CalorieStrategy.RECOMP,
        base_tdee_kcal=round(tdee_kcal, 1),
        rate_pct=deficit_pct,
        rate_label=label,
        calorie_delta_kcal=round(-deficit_kcal, 1),
        target_calories_kcal=round(target, 1),
        calorie_floor_applied=floor_applied,
        floor_kcal=floor,
        notes=notes,
    )


def reverse_diet_plan(
    current_calories: float,
    target_calories: float,
    aggressiveness: str = "moderate",
) -> tuple[list[float], CalorieTargets]:
    """
    Reverse-diet weekly plan.

    Returns (list of weekly calorie targets, CalorieTargets for first week).
    """
    increment = REVERSE_DIET_WEEKLY_INCREMENT[aggressiveness]
    delta = target_calories - current_calories
    if delta <= 0:
        # Already at or above target — just return target
        return [target_calories], CalorieTargets(
            strategy=CalorieStrategy.REVERSE_DIET,
            base_tdee_kcal=target_calories,
            rate_pct=0.0,
            rate_label="already at target",
            calorie_delta_kcal=0.0,
            target_calories_kcal=round(target_calories, 1),
            notes=["Already at or above target — no reverse diet needed."],
        )

    # Phase-6 fix: replace fragile float-modulo expression
    #   `int(delta / increment) + (1 if delta % increment else 0)`
    # with math.ceil which is the documented intent (round up to cover any
    # remainder). Float modulo can produce surprising results due to FP error.
    weeks_needed = max(1, math.ceil(delta / increment))
    weekly_targets = []
    for w in range(weeks_needed):
        target = min(current_calories + (w + 1) * increment, target_calories)
        weekly_targets.append(round(target, 1))

    notes = [
        f"Reverse diet ({aggressiveness}): +{increment} kcal/week",
        f"Duration: ~{weeks_needed} weeks to reach {target_calories:.0f} kcal",
        f"Weekly targets: {weekly_targets[:4]}{'...' if len(weekly_targets) > 4 else ''}",
        f"⚠ Red flag: weekly weight gain > 0.5% BW → slow down.",
    ]

    return weekly_targets, CalorieTargets(
        strategy=CalorieStrategy.REVERSE_DIET,
        base_tdee_kcal=current_calories,
        # Tier 4.49 fix: rate_pct and calorie_delta_kcal now use consistent
        # semantics with other strategies. rate_pct = weekly increment as a
        # fraction of current intake (was increment/7, dimensionally wrong).
        # calorie_delta_kcal = DAILY delta (increment/7), matching the
        # documented "daily delta" field semantics (was weekly increment).
        rate_pct=increment / current_calories if current_calories > 0 else 0.0,
        rate_label=f"+{increment} kcal/week ({aggressiveness})",
        calorie_delta_kcal=round(increment / 7.0, 1),  # daily delta
        target_calories_kcal=weekly_targets[0],
        notes=notes,
    )


def compute_calorie_targets(
    profile: UserProfile,
    tdee_kcal: float,
    strategy: RecommendedStrategy,
    body_fat_pct: float,
    in_active_deficit: bool = False,  # Phase-6 fix: kept for API compat but ignored (see planner.py)
) -> CalorieTargets:
    """Compute calorie targets based on the recommended strategy.

    Phase-6 fix: the `in_active_deficit` parameter is accepted for backward
    API compatibility but is NOT used by this function — the strategy +
    profile already encode everything needed. The single source of truth for
    "is the user currently in a deficit" now lives in the planner (derived
    from strategy); see nutrition/planner.py for the consolidation.

    Phase-6 cleanup: DEPRECATION — ``in_active_deficit`` will be removed in a
    future major version. New callers should omit it. Existing callers that
    still pass it (e.g. ``nutrition/planner.py``) are tolerated but the value
    is discarded silently.
    """
    if strategy == RecommendedStrategy.CUT:
        return cut_target_calories(profile, tdee_kcal)
    elif strategy == RecommendedStrategy.BULK:
        return bulk_target_calories(profile, tdee_kcal)
    elif strategy == RecommendedStrategy.RECOMP:
        return recomp_target_calories(profile, tdee_kcal, body_fat_pct)
    elif strategy == RecommendedStrategy.MAINTENANCE:
        return maintenance_target_calories(tdee_kcal)
    elif strategy == RecommendedStrategy.HABIT_CHANGE_FIRST:
        # For habit-change-first: target = maintenance (no aggressive deficit)
        return maintenance_target_calories(tdee_kcal)
    else:
        return maintenance_target_calories(tdee_kcal)


__all__ = [
    "KCAL_PER_LB_FAT", "KCAL_PER_KG_FAT", "KCAL_PER_LB_MUSCLE",
    "SURPLUS_KCAL_PER_LB_PER_MONTH", "SURPLUS_KCAL_PER_KG_PER_MONTH",
    "DEFICIT_KCAL_PER_LB_PER_WEEK", "DEFICIT_KCAL_PER_KG_PER_WEEK",
    "MIN_CALORIES", "MAX_WEEKLY_LOSS_PCT",
    "CUT_RATE_TIERS", "DEFAULT_CUT_RATE_PCT", "SWEET_SPOT_CUT_RATE_PCT",
    "BULK_RATE_BY_STATUS", "BULK_WEEKLY_RATE_TIERS",
    "REVERSE_DIET_WEEKLY_INCREMENT", "REVERSE_DIET_RED_FLAG_WEEKLY_GAIN_PCT",
    "cut_target_calories", "bulk_target_calories",
    "maintenance_target_calories", "recomp_target_calories",
    "reverse_diet_plan", "compute_calorie_targets",
]

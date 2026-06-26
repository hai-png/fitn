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

# top-level import: ``assessment.decision`` only imports constants, so this is safe.
from ..assessment.decision import CUT_BULK_BOUNDARIES
from ..models.assessment import RecommendedStrategy
from ..models.nutrition import CalorieStrategy, CalorieTargets
from ..models.profile import (
    BulkAggressiveness,
    CutRateTier,
    Sex,
    TrainingStatus,
    UserProfile,
)
from ..utils.units import WEEKS_PER_MONTH

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
# active deficit (amenorrhea / bone loss risk above this).
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

# BF% thresholds for the cut-rate ladder, hoisted to a
# module-level constant. Lower BF% → smaller cut rate (leaner users should cut
# slower to preserve LBM). The 4 buckets per sex map (in descending threshold
# order) to (MAX_WEEKLY_LOSS_PCT, DEFAULT_CUT_RATE_PCT, SWEET_SPOT_CUT_RATE_PCT,
# SWEET_SPOT_CUT_RATE_PCT) — the final fallback (leaner than all thresholds)
# is also the sweet spot.
CUT_RATE_BF_THRESHOLDS: dict[Sex, list[float]] = {
    Sex.MALE:   [25, 20, 15],
    Sex.FEMALE: [35, 28, 22],
}
# Cut rates corresponding to each threshold tier (and the below-all-thresholds
# fallback). Indexed by position relative to CUT_RATE_BF_THRESHOLDS[sex].
_CUT_RATES_BY_TIER: list[float] = [
    MAX_WEEKLY_LOSS_PCT,      # >= thresholds[0]: obese, max safe rate
    DEFAULT_CUT_RATE_PCT,     # >= thresholds[1]: moderate
    SWEET_SPOT_CUT_RATE_PCT,  # >= thresholds[2]: sweet spot
    SWEET_SPOT_CUT_RATE_PCT,  # below thresholds[2]: lean — sweet spot
]


def _select_cut_rate_by_bf(sex: Sex, bf_pct: float) -> float:
    """Pick the weekly cut rate based on body-fat % and sex.

    Uses ``CUT_RATE_BF_THRESHOLDS[sex]`` (a descending list of BF% thresholds)
    and the corresponding rates in ``_CUT_RATES_BY_TIER``. The first threshold
    the user's BF% meets (or exceeds) determines the rate; users below all
    thresholds get the leanest (SWEET_SPOT) rate.
    """
    thresholds = CUT_RATE_BF_THRESHOLDS[sex]
    for i, threshold in enumerate(thresholds):
        if bf_pct >= threshold:
            return _CUT_RATES_BY_TIER[i]
    return _CUT_RATES_BY_TIER[-1]

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
            # MEDIUM-severity cleanup: previously this used a tautological
            # expression `bf_pct = profile.body_fat_pct if ... is not None else None`
            # which is equivalent to just `profile.body_fat_pct`. Simplified.
            bf_pct = profile.body_fat_pct
            if bf_pct is None:
                # Unknown BF% — use the MODERATE default (0.75% for men, 0.5% for women
                # would be asymmetric; DEFAULT_CUT_RATE_PCT = 0.0075 is the documented
                # moderate tier and applies to both sexes).
                rate_pct = DEFAULT_CUT_RATE_PCT
            else:
                # BF%-ladder lookup via ``_select_cut_rate_by_bf`` (thresholds
                # in ``CUT_RATE_BF_THRESHOLDS``).
                rate_pct = _select_cut_rate_by_bf(profile.sex, bf_pct)

    # Enforce hard cap. Use strict `>` so the AGGRESSIVE tier (which exactly
    # equals MAX_WEEKLY_LOSS_PCT = 0.010) is NOT clipped — only requests that
    # EXCEED the cap are.
    capped = rate_pct > MAX_WEEKLY_LOSS_PCT
    if capped:
        # warn the user when their requested rate is clipped
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
    daily_deficit_kcal = weekly_loss_kg * DEFICIT_KCAL_PER_KG_PER_WEEK
    pre_floor_target = tdee_kcal - daily_deficit_kcal

    # Apply floor
    target, floor_applied, floor = _apply_calorie_floor(pre_floor_target, profile.sex)

    # CRITICAL FIX: recompute the deficit AFTER clamping so that
    # `base_tdee_kcal + calorie_delta_kcal == target_calories_kcal`. Previously
    # `calorie_delta_kcal` was the pre-clamp deficit, leading to field
    # inconsistency (e.g. TDEE 1500 + delta -660 = 840 ≠ target 1200 when the
    # 1200-kcal floor engaged). Now delta is derived from the FINAL target.
    actual_delta_kcal = target - tdee_kcal

    rate_label = f"{rate_pct*100:.2f}% BW/week ≈ {weekly_loss_kg:.2f} kg/wk"

    notes = [
        f"Cut rate: {rate_label}",
        f"Daily deficit: {daily_deficit_kcal:.0f} kcal",
        # CRITICAL FIX: show the pre-clamp arithmetic, then a separate line if
        # the floor engaged. Previously the note computed `target` AFTER
        # clamping, producing arithmetically-wrong strings like
        # "1500 − 660 = 1200" (should be 840, then clamped to 1200).
        f"Target = TDEE ({tdee_kcal:.0f}) − deficit ({daily_deficit_kcal:.0f}) "
        f"= {pre_floor_target:.0f} kcal",
    ]
    if cap_warning:
        notes.append(cap_warning)
    if floor_applied:
        notes.append(
            f"⚠ Calorie floor applied: pre-floor target {pre_floor_target:.0f} kcal "
            f"raised to {floor} kcal ({profile.sex.value} minimum). "
            "Increase activity instead of cutting further. "
            f"Effective daily deficit: {-actual_delta_kcal:.0f} kcal."
        )

    return CalorieTargets(
        strategy=CalorieStrategy.DEFICIT,
        base_tdee_kcal=round(tdee_kcal, 1),
        rate_pct=rate_pct,
        rate_label=rate_label,
        calorie_delta_kcal=round(actual_delta_kcal, 1),
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
        # honor bulk_aggressiveness if the user set it.
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
            # Convert weekly % to monthly % (avg 4.348 weeks/month)
            rate_pct_monthly = weekly_rate * WEEKS_PER_MONTH
        else:
            rate_pct_monthly = BULK_RATE_BY_STATUS[profile.training_status]

    monthly_gain_kg = profile.weight_kg * rate_pct_monthly
    daily_surplus_kcal = monthly_gain_kg * SURPLUS_KCAL_PER_KG_PER_MONTH
    target = tdee_kcal + daily_surplus_kcal

    # Floors don't apply to bulking; no upper cap on surplus.
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
    pre_floor_target = tdee_kcal - deficit_kcal
    target, floor_applied, floor = _apply_calorie_floor(pre_floor_target, profile.sex)

    # CRITICAL FIX: derive delta from FINAL target so
    # `base_tdee_kcal + calorie_delta_kcal == target_calories_kcal`.
    actual_delta_kcal = target - tdee_kcal

    notes = [
        f"Recomp potential: {label}",
        f"BF%={body_fat_pct:.1f}",
        f"Target = TDEE × (1 − {deficit_pct:.0%}) = {pre_floor_target:.0f} kcal",
    ]
    if floor_applied:
        notes.append(
            f"⚠ Calorie floor applied: pre-floor target {pre_floor_target:.0f} kcal "
            f"raised to {floor} kcal ({profile.sex.value} minimum). "
            f"Effective daily deficit: {-actual_delta_kcal:.0f} kcal."
        )

    return CalorieTargets(
        strategy=CalorieStrategy.RECOMP,
        base_tdee_kcal=round(tdee_kcal, 1),
        rate_pct=deficit_pct,
        rate_label=label,
        calorie_delta_kcal=round(actual_delta_kcal, 1),
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

    # math.ceil is the documented intent (round up to cover any remainder).
    # Float modulo can produce surprising results due to FP error.
    weeks_needed = max(1, math.ceil(delta / increment))
    weekly_targets = []
    for w in range(weeks_needed):
        target = min(current_calories + (w + 1) * increment, target_calories)
        weekly_targets.append(round(target, 1))

    notes = [
        f"Reverse diet ({aggressiveness}): +{increment} kcal/week",
        f"Duration: ~{weeks_needed} weeks to reach {target_calories:.0f} kcal",
        f"Weekly targets: {weekly_targets[:4]}{'...' if len(weekly_targets) > 4 else ''}",
        "⚠ Red flag: weekly weight gain > 0.5% BW → slow down.",
    ]

    return weekly_targets, CalorieTargets(
        strategy=CalorieStrategy.REVERSE_DIET,
        base_tdee_kcal=current_calories,
        # rate_pct = weekly increment as a fraction of current intake.
        # calorie_delta_kcal = DAILY delta (increment/7), matching the
        # documented "daily delta" field semantics.
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
) -> CalorieTargets:
    """Compute calorie targets based on the recommended strategy."""
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
    "CUT_RATE_BF_THRESHOLDS",
    "BULK_RATE_BY_STATUS", "BULK_WEEKLY_RATE_TIERS",
    "REVERSE_DIET_WEEKLY_INCREMENT", "REVERSE_DIET_RED_FLAG_WEEKLY_GAIN_PCT",
    "cut_target_calories", "bulk_target_calories",
    "maintenance_target_calories", "recomp_target_calories",
    "reverse_diet_plan", "compute_calorie_targets",
]

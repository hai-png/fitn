"""
Macro adjustment protocol — for ongoing plan tuning based on progress data.

Sources:
- Cut troubleshooting: rippedbody.com__how-to-adjust-macros
- Bulk troubleshooting: rippedbody.com__how-to-adjust-macros-bulk
- Adjustment math: rippedbody.com__macro-calculator
- Initial adjustment timing: rippedbody.com__initial-adjustment
- Stalls & whooshes: rippedbody.com__calories
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from ..models.assessment import RecommendedStrategy
from ..models.nutrition import MacroSplit, CalorieTargets
from .calories import (
    DEFICIT_KCAL_PER_LB_PER_WEEK, DEFICIT_KCAL_PER_KG_PER_WEEK,
    SURPLUS_KCAL_PER_LB_PER_MONTH, SURPLUS_KCAL_PER_KG_PER_MONTH,
)
from .macros import cut_macro_adjustment, bulk_macro_adjustment
# use shared unit conversion helper.
# (target - actual) is in kg/wk (or kg/mo); kg_to_lb converts to lb/wk (or lb/mo).
from ..utils.units import kg_to_lb


class PlateauType(str, Enum):
    NONE = "none"
    SUDDEN_STALL = "sudden_stall"           # water retention — wait
    GRADUAL_SLOWDOWN = "gradual_slowdown"   # real adaptation — adjust
    WHOOSH = "whoosh"                        # sudden drop — no action needed
    WEIGHT_GAIN = "weight_gain"              # gaining weight during a cut


# plateau detection thresholds as named constants.
_STALL_THRESHOLD_FRACTION = 0.003   # |delta| < 0.3% of body weight → flat
_WHOOSH_THRESHOLD_FRACTION = 0.015  # delta > 1.5% of body weight → whoosh

# Decision table for detect_plateau: ordered (condition_fn, plateau_type) tuples.
# First match wins. The condition_fn signature is (deltas, last_3, body_weight_kg).
# Order: recent signals (weight gain, sudden stall, gradual slowdown) BEFORE the
# historical whoosh check — a historical whoosh shouldn't mask a current gaining
# streak or stall.
_PLATEAU_RULES: list[tuple[Callable[[list[float], list[float], float], bool], PlateauType]] = [
    (lambda deltas, last_3, bw: all(d < 0 for d in last_3),
     PlateauType.WEIGHT_GAIN),
    (lambda deltas, last_3, bw: all(abs(d) < bw * _STALL_THRESHOLD_FRACTION for d in last_3),
     PlateauType.SUDDEN_STALL),
    (lambda deltas, last_3, bw: all(d > 0 for d in last_3) and last_3[0] > last_3[1] > last_3[2],
     PlateauType.GRADUAL_SLOWDOWN),
    (lambda deltas, last_3, bw: any(d > bw * _WHOOSH_THRESHOLD_FRACTION for d in last_3),
     PlateauType.WHOOSH),
]


@dataclass
class AdjustmentRecommendation:
    """Recommended macro/calorie adjustment based on progress data."""
    plateau_type: PlateauType
    action: str                              # "wait", "adjust_calories", "lifestyle_fix"
    calorie_delta_kcal: float = 0.0
    carb_g_delta: float = 0.0
    fat_g_delta: float = 0.0
    protein_g_delta: float = 0.0
    reasoning: str = ""
    troubleshooting_steps: list[str] = field(default_factory=list)


def detect_plateau(
    weekly_weight_log_kg: list[float],
    body_weight_kg: float,
) -> PlateauType:
    """
    Detect plateau type from weekly weight log.

    Phase-6 fix: clarifying the docstring to match the actual implementation:
      - Sudden stall: last 3 weekly deltas ALL have |delta| < 0.3% of body
        weight (i.e. weight is essentially flat for 3 consecutive weeks).
        Previously the docstring said "within ±0.3% of prior avg" which
        suggested a comparison to the prior moving average — the code does
        not compute a moving average; it checks absolute weekly deltas
        against a fixed 0.3%-of-BW threshold.
      - Gradual slowdown: rate of loss decelerating week-over-week (last 3
        deltas all positive AND monotonically decreasing in magnitude).
      - Whoosh: any single week delta > 1.5% of body weight (absolute).
        Phase-6 fix: restricted to the LAST 3 weeks only — previously scanned
        the entire log, so a whoosh at week 2 masked all subsequent plateaus.
      - Weight gain: last 3 weekly deltas all negative (weight went up).
      - None: insufficient data (< 3 weeks) or normal progress.

    Phase-6 consolidation: refactored from 4 sequential `if` blocks to a
    decision table (`_PLATEAU_RULES`) — first matching condition wins.
    Behavior is identical to the prior sequential form.
    """
    if len(weekly_weight_log_kg) < 3:
        return PlateauType.NONE

    deltas = [
        weekly_weight_log_kg[i] - weekly_weight_log_kg[i + 1]
        for i in range(len(weekly_weight_log_kg) - 1)
    ]
    last_3 = deltas[-3:]

    for condition_fn, plateau_type in _PLATEAU_RULES:
        if condition_fn(deltas, last_3, body_weight_kg):
            return plateau_type

    return PlateauType.NONE


def recommend_cut_adjustment(
    weekly_weight_log_kg: list[float],
    target_weekly_rate_pct: float,
    body_weight_kg: float,
    week_number: int,
) -> AdjustmentRecommendation:
    """
    Recommend cut-phase adjustment based on progress.

    Rules (RippedBody):
      - Weeks 1-2: ignore (water shifts)
      - Weeks 3+: assess plateau
      - Sudden stall: wait (water retention)
      - Gradual slowdown: 5-8% calorie reduction (~100-200 kcal)
      - Adjustment math: 0.5 lb off target × 500 kcal = 250 kcal adjustment
    """
    # Compute observed vs target rate
    if len(weekly_weight_log_kg) >= 2:
        n_weeks = len(weekly_weight_log_kg) - 1
        actual_loss = weekly_weight_log_kg[0] - weekly_weight_log_kg[-1]
        actual_weekly_rate = actual_loss / n_weeks if n_weeks > 0 else 0
        target_weekly_loss = body_weight_kg * target_weekly_rate_pct
        delta_off_target_lb = kg_to_lb(target_weekly_loss - actual_weekly_rate)
    else:
        delta_off_target_lb = 0
        actual_weekly_rate = 0

    plateau = detect_plateau(weekly_weight_log_kg, body_weight_kg)

    # Troubleshooting checklist (RippedBody order)
    troubleshooting = [
        "1. Adherence check — solid week incl. weekend.",
        "2. Tracking accuracy — log everything 2 weeks.",
        "3. Hunger management — swap liquid kcal, cut sugary foods, more veg.",
        "4. Food environment — control surroundings.",
        "5. Sleep quality — poor sleep mimics stress + water retention.",
        "6. Stress management.",
        "7. Activity / NEAT — set min 5,000 steps/day.",
        "8. Cardio (before calorie reduction): low-impact, <50% of lifting time.",
        "9. Calorie reduction (LAST): -5-8% total intake (~100-200 kcal).",
    ]

    if week_number < 3:
        return AdjustmentRecommendation(
            plateau_type=PlateauType.NONE,
            action="wait",
            reasoning=(
                f"Week {week_number}: ignore weeks 1-2 (water/gut/glycogen shifts). "
                "Wait until week 3+ before judging progress."
            ),
            troubleshooting_steps=troubleshooting,
        )

    if plateau == PlateauType.SUDDEN_STALL:
        return AdjustmentRecommendation(
            plateau_type=plateau,
            action="wait",
            reasoning=(
                "Sudden stall detected (3+ weeks within ±0.3% BW). "
                "Water retention is masking fat loss — wait minimum 4 more weeks "
                "before adjusting. Cortisol/stress/sleep are common causes."
            ),
            troubleshooting_steps=troubleshooting,
        )

    if plateau == PlateauType.WHOOSH:
        return AdjustmentRecommendation(
            plateau_type=plateau,
            action="wait",
            reasoning=(
                "Whoosh detected (sudden multi-kg drop after stall). "
                "Water release — no adjustment needed."
            ),
            troubleshooting_steps=troubleshooting,
        )

    # weight gain during a cut — strong signal of adherence issue
    # or miscalculated TDEE. Do NOT reduce calories further; instead surface
    # the troubleshooting checklist prominently.
    if plateau == PlateauType.WEIGHT_GAIN:
        return AdjustmentRecommendation(
            plateau_type=plateau,
            action="lifestyle_fix",
            reasoning=(
                "Weight GAIN detected during cut (3+ weeks of weight increase). "
                "Do NOT reduce calories further — this is almost always an adherence "
                "or tracking issue, not a metabolism problem. Work through the "
                "troubleshooting checklist before any calorie change."
            ),
            troubleshooting_steps=troubleshooting,
        )

    if plateau == PlateauType.GRADUAL_SLOWDOWN or abs(delta_off_target_lb) > 0.25:
        # Adjustment math.
        # delta_off_target_lb > 0 means losing too slowly -> need to DECREASE intake.
        # delta_off_target_lb < 0 means losing too fast  -> need to INCREASE intake.
        # cut_macro_adjustment interprets its argument as:
        #   negative kcal delta -> reduce carbs/fat (a cut)
        #   positive kcal delta -> add carbs/fat (an increase)
        # So we pass -calorie_delta (sign-flipped relative to off-target direction).
        calorie_delta = delta_off_target_lb * DEFICIT_KCAL_PER_LB_PER_WEEK
        adjustment_kcal = -calorie_delta  # negate: too slow -> cut; too fast -> increase
        carb_g, fat_g, expl = cut_macro_adjustment(adjustment_kcal)
        return AdjustmentRecommendation(
            plateau_type=plateau,
            action="adjust_calories",
            calorie_delta_kcal=adjustment_kcal,
            carb_g_delta=carb_g,
            fat_g_delta=fat_g,
            protein_g_delta=0.0,
            reasoning=(
                f"Off-target by {delta_off_target_lb:+.2f} lb/week. "
                f"Adjustment: {expl}. "
                f"Apply troubleshooting steps 1-8 first; calorie reduction is last resort."
            ),
            troubleshooting_steps=troubleshooting,
        )

    return AdjustmentRecommendation(
        plateau_type=PlateauType.NONE,
        action="wait",
        reasoning=(
            f"Progress on-track. Actual: {actual_weekly_rate:.2f} kg/wk, "
            f"target: {body_weight_kg * target_weekly_rate_pct:.2f} kg/wk. "
            "No adjustment needed."
        ),
        troubleshooting_steps=troubleshooting,
    )


def recommend_bulk_adjustment(
    monthly_weight_log_kg: list[float],
    target_monthly_rate_pct: float,
    body_weight_kg: float,
    week_number: int,
) -> AdjustmentRecommendation:
    """
    Recommend bulk-phase adjustment.

    Rules (RippedBody):
      - Weeks 1-6: wait (WGG regain + adaptation)
      - Weeks 7+: assess
      - Off-target by 1 lb/month × 150 kcal = adjustment
    """
    troubleshooting = [
        "1. Feeling too full? Swap whole food for liquid kcal; eat faster; higher meal freq.",
        "2. Revisit 'why' — bulking is a chore for hard gainers.",
        "3. Manage stress.",
        "4. Sleep.",
        "5. Activity level increase — wait to see effect before proactively bumping.",
        "6. Calorie increase (LAST): +5% (~150-200 kcal).",
    ]

    if week_number < 6:
        return AdjustmentRecommendation(
            plateau_type=PlateauType.NONE,
            action="wait",
            reasoning=(
                f"Week {week_number}: wait until week 6-7 before assessing bulk progress. "
                "First weeks include WGG (water/gut/glycogen) regain which obscures true gain."
            ),
            troubleshooting_steps=troubleshooting,
        )

    # Compute observed vs target monthly gain
    if len(monthly_weight_log_kg) >= 2:
        n_months = len(monthly_weight_log_kg) - 1
        actual_gain = monthly_weight_log_kg[-1] - monthly_weight_log_kg[0]
        actual_monthly_rate = actual_gain / n_months if n_months > 0 else 0
        target_monthly_gain = body_weight_kg * target_monthly_rate_pct
        delta_off_target_lb = kg_to_lb(target_monthly_gain - actual_monthly_rate)
    else:
        delta_off_target_lb = 0
        actual_monthly_rate = 0

    if abs(delta_off_target_lb) > 0.5:
        # delta_off_target_lb > 0 means gaining too slowly -> increase intake (positive delta).
        # delta_off_target_lb < 0 means gaining too fast  -> decrease intake (negative delta).
        # Pass the signed calorie_delta straight through; bulk_macro_adjustment
        # handles the sign correctly (positive delta -> positive g-deltas).
        calorie_delta = delta_off_target_lb * SURPLUS_KCAL_PER_LB_PER_MONTH
        carb_g, fat_g, expl = bulk_macro_adjustment(calorie_delta)
        return AdjustmentRecommendation(
            plateau_type=PlateauType.NONE,
            action="adjust_calories",
            calorie_delta_kcal=calorie_delta,
            carb_g_delta=carb_g,
            fat_g_delta=fat_g,
            protein_g_delta=0.0,
            reasoning=(
                f"Off-target by {delta_off_target_lb:+.2f} lb/month. "
                f"Adjustment: {expl}. "
                "Apply troubleshooting steps 1-5 first; calorie increase is last resort."
            ),
            troubleshooting_steps=troubleshooting,
        )

    return AdjustmentRecommendation(
        plateau_type=PlateauType.NONE,
        action="wait",
        reasoning=(
            f"Progress on-track. Actual: {actual_monthly_rate:.2f} kg/mo, "
            f"target: {body_weight_kg * target_monthly_rate_pct:.2f} kg/mo. "
            "No adjustment needed."
        ),
        troubleshooting_steps=troubleshooting,
    )


__all__ = [
    "PlateauType", "AdjustmentRecommendation",
    "detect_plateau", "recommend_cut_adjustment", "recommend_bulk_adjustment",
]

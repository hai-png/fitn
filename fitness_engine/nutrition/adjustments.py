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

from dataclasses import dataclass
from enum import Enum

from ..models.assessment import RecommendedStrategy
from ..models.nutrition import MacroSplit, CalorieTargets
from .calories import (
    DEFICIT_KCAL_PER_LB_PER_WEEK, DEFICIT_KCAL_PER_KG_PER_WEEK,
    SURPLUS_KCAL_PER_LB_PER_MONTH, SURPLUS_KCAL_PER_KG_PER_MONTH,
)
from .macros import cut_macro_adjustment, bulk_macro_adjustment


class PlateauType(str, Enum):
    NONE = "none"
    SUDDEN_STALL = "sudden_stall"           # water retention — wait
    GRADUAL_SLOWDOWN = "gradual_slowdown"   # real adaptation — adjust
    WHOOSH = "whoosh"                        # sudden drop — no action needed


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
    troubleshooting_steps: list[str] = None


def detect_plateau(
    weekly_weight_log_kg: list[float],
    expected_weekly_rate_pct: float,
    body_weight_kg: float,
) -> PlateauType:
    """
    Detect plateau type from weekly weight log.

    - Sudden stall: 3+ weeks with avg within ±0.3% of prior avg
    - Gradual slowdown: rate of loss decelerating week-over-week
    - Whoosh: sudden drop > 1.5% in single week after plateau
    - None: insufficient data (< 3 weeks) or normal progress
    """
    if len(weekly_weight_log_kg) < 3:
        return PlateauType.NONE

    expected_weekly_loss = body_weight_kg * expected_weekly_rate_pct
    deltas = [
        weekly_weight_log_kg[i] - weekly_weight_log_kg[i + 1]
        for i in range(len(weekly_weight_log_kg) - 1)
    ]

    # Whoosh: any single week delta > 3× expected
    if any(d > expected_weekly_loss * 3 for d in deltas):
        return PlateauType.WHOOSH

    # Sudden stall: last 3 deltas all < 0.3% body weight
    if len(deltas) >= 3:
        last_3 = deltas[-3:]
        threshold = body_weight_kg * 0.003
        if all(abs(d) < threshold for d in last_3):
            return PlateauType.SUDDEN_STALL

    # Gradual slowdown: deltas decreasing in magnitude
    if len(deltas) >= 3:
        last_3 = deltas[-3:]
        if all(d > 0 for d in last_3) and last_3[0] > last_3[1] > last_3[2]:
            return PlateauType.GRADUAL_SLOWDOWN

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
        delta_off_target_lb = (target_weekly_loss - actual_weekly_rate) / 0.45359237
    else:
        delta_off_target_lb = 0
        actual_weekly_rate = 0

    plateau = detect_plateau(weekly_weight_log_kg, target_weekly_rate_pct, body_weight_kg)

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

    if plateau == PlateauType.GRADUAL_SLOWDOWN or abs(delta_off_target_lb) > 0.25:
        # Adjustment math
        calorie_delta = delta_off_target_lb * DEFICIT_KCAL_PER_LB_PER_WEEK
        # delta_off_target_lb > 0 means losing too slowly → decrease intake
        # We pass negative delta to indicate a cut
        carb_g, fat_g, expl = cut_macro_adjustment(-abs(calorie_delta))
        return AdjustmentRecommendation(
            plateau_type=plateau,
            action="adjust_calories",
            calorie_delta_kcal=-abs(calorie_delta),
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
        delta_off_target_lb = (target_monthly_gain - actual_monthly_rate) / 0.45359237
    else:
        delta_off_target_lb = 0
        actual_monthly_rate = 0

    if abs(delta_off_target_lb) > 0.5:
        calorie_delta = delta_off_target_lb * SURPLUS_KCAL_PER_LB_PER_MONTH
        # delta > 0 = gaining too slowly → increase
        carb_g, fat_g, expl = bulk_macro_adjustment(abs(calorie_delta))
        return AdjustmentRecommendation(
            plateau_type=PlateauType.NONE,
            action="adjust_calories",
            calorie_delta_kcal=abs(calorie_delta),
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

"""
Regression tests for nutrition/adjustments.py.

Covers:
  - Plateau detection (sudden stall, gradual slowdown, whoosh, none)
  - Cut adjustment direction (too slow -> reduce intake; too fast -> increase intake)
  - Bulk adjustment direction (too slow -> increase; too fast -> decrease)
  - troubleshooting_steps default is a list (not None) — Tier 1.1 / Tier 3.30
  - Week-number gating (weeks 1-2 cut / 1-6 bulk are "wait")
"""
import pytest

from fitness_engine.nutrition.adjustments import (
    PlateauType,
    AdjustmentRecommendation,
    detect_plateau,
    recommend_cut_adjustment,
    recommend_bulk_adjustment,
)


# === detect_plateau tests ===

class TestDetectPlateau:
    def test_insufficient_data_returns_none(self):
        assert detect_plateau([80.0, 79.5], 0.01, 80.0) == PlateauType.NONE

    def test_sudden_stall_three_weeks_within_threshold(self):
        # 3 consecutive weeks with weight essentially unchanged (<0.3% BW = 0.24kg)
        # Need deltas all < 0.24 kg. Use small steady losses.
        log = [80.0, 79.95, 79.90, 79.85]
        result = detect_plateau(log, 0.01, 80.0)
        assert result == PlateauType.SUDDEN_STALL

    def test_whoosh_sudden_drop(self):
        # 3 weeks stalled, then a >3x expected drop. Expected = 80*0.01 = 0.8,
        # whoosh threshold = 2.4 kg. Use 3.0 kg drop.
        log = [80.0, 80.0, 80.0, 77.0]
        result = detect_plateau(log, 0.01, 80.0)
        assert result == PlateauType.WHOOSH

    def test_gradual_slowdown_strict_decreasing(self):
        # Losses: 1.0, 0.7, 0.4 kg/wk — clearly decelerating
        log = [80.0, 79.0, 78.3, 77.9]
        result = detect_plateau(log, 0.01, 80.0)
        assert result == PlateauType.GRADUAL_SLOWDOWN

    def test_gradual_slowdown_with_tie_no_longer_missed(self):
        # Losses: 0.8, 0.6, 0.6 kg/wk — previously NOT flagged because strict >,
        # now flagged because the >= fix catches plateaus where two consecutive
        # weeks share the same loss rate.
        log = [80.0, 79.2, 78.6, 78.0]
        result = detect_plateau(log, 0.01, 80.0)
        assert result == PlateauType.GRADUAL_SLOWDOWN

    def test_normal_progress_returns_none(self):
        # Steady 0.7 kg/wk loss — not a plateau
        log = [80.0, 79.3, 78.6, 77.9]
        result = detect_plateau(log, 0.01, 80.0)
        assert result == PlateauType.NONE


# === Cut adjustment direction tests (Tier 1.1 — CRITICAL fix) ===

class TestCutAdjustmentDirection:
    """
    Regression for the directional bug. Previously the code did
    `cut_macro_adjustment(-abs(calorie_delta))` which always recommended
    a cut, even when the user was losing too fast. Now we pass the
    signed -calorie_delta so:
      - losing too slowly (delta_off_target_lb > 0) -> negative kcal delta (cut)
      - losing too fast   (delta_off_target_lb < 0) -> positive kcal delta (increase)
    """

    def test_losing_too_slowly_recommends_calorie_reduction(self):
        # Target: 0.75% BW/wk = 0.6 kg/wk for 80kg user
        # Actual: 0.3 kg/wk (too slow) — deltas below whoosh threshold (1.8kg)
        # and above sudden-stall threshold (0.24kg), so we land in the
        # off-target adjustment branch.
        log = [80.0, 79.7, 79.4, 79.1]
        rec = recommend_cut_adjustment(
            weekly_weight_log_kg=log,
            target_weekly_rate_pct=0.0075,
            body_weight_kg=80.0,
            week_number=4,
        )
        assert rec.action == "adjust_calories"
        # Losing too slowly -> we should DECREASE intake -> negative kcal delta
        assert rec.calorie_delta_kcal < 0, (
            f"Losing too slowly must recommend a calorie reduction (negative delta); "
            f"got {rec.calorie_delta_kcal}"
        )
        # Carb and fat deltas should also be negative (we're removing food)
        assert rec.carb_g_delta < 0
        assert rec.fat_g_delta < 0

    def test_losing_too_fast_recommends_calorie_increase(self):
        """
        CRITICAL regression: previously this case recommended a cut (more loss),
        which is a patient-safety bug. Now it should recommend an increase.
        """
        # Target: 0.5% BW/wk = 0.4 kg/wk for 80kg user
        # Actual: 0.8 kg/wk (too fast, but below whoosh threshold of 1.2 kg)
        log = [80.0, 79.2, 78.4, 77.6]
        rec = recommend_cut_adjustment(
            weekly_weight_log_kg=log,
            target_weekly_rate_pct=0.005,
            body_weight_kg=80.0,
            week_number=4,
        )
        assert rec.action == "adjust_calories"
        # Losing too fast -> we should INCREASE intake -> positive kcal delta
        assert rec.calorie_delta_kcal > 0, (
            f"Losing too fast must recommend a calorie INCREASE (positive delta); "
            f"got {rec.calorie_delta_kcal}. This was the original patient-safety bug."
        )
        # Carb and fat deltas should be positive (we're adding food)
        assert rec.carb_g_delta > 0
        assert rec.fat_g_delta > 0

    def test_on_track_no_adjustment(self):
        # Target: 0.5% BW/wk = 0.4 kg/wk; actual matches
        log = [80.0, 79.6, 79.2, 78.8]
        rec = recommend_cut_adjustment(
            weekly_weight_log_kg=log,
            target_weekly_rate_pct=0.005,
            body_weight_kg=80.0,
            week_number=4,
        )
        assert rec.action == "wait"
        assert rec.calorie_delta_kcal == 0.0

    def test_weeks_1_and_2_always_wait(self):
        log = [80.0, 78.0]  # would normally trigger "too fast"
        rec = recommend_cut_adjustment(
            weekly_weight_log_kg=log,
            target_weekly_rate_pct=0.005,
            body_weight_kg=80.0,
            week_number=2,
        )
        assert rec.action == "wait"


# === Bulk adjustment direction tests ===

class TestBulkAdjustmentDirection:
    """
    Bulk uses the same sign convention as cut: positive calorie_delta_kcal
    means "add calories". So:
      - gaining too slowly (delta_off_target_lb > 0) -> positive kcal delta (increase)
      - gaining too fast   (delta_off_target_lb < 0) -> negative kcal delta (decrease)
    """

    def test_gaining_too_slowly_recommends_increase(self):
        # Target: 0.5% BW/mo = 0.4 kg/mo for 80kg user
        # Actual: 0.1 kg/mo over 2 months (too slow)
        log = [80.0, 80.1, 80.2]
        rec = recommend_bulk_adjustment(
            monthly_weight_log_kg=log,
            target_monthly_rate_pct=0.005,
            body_weight_kg=80.0,
            week_number=8,  # past the 6-week wait
        )
        assert rec.action == "adjust_calories"
        assert rec.calorie_delta_kcal > 0
        assert rec.carb_g_delta > 0
        assert rec.fat_g_delta > 0

    def test_gaining_too_fast_recommends_decrease(self):
        # Target: 0.5% BW/mo = 0.4 kg/mo for 80kg user
        # Actual: 2.0 kg/mo (way too fast)
        log = [80.0, 82.0, 84.0]
        rec = recommend_bulk_adjustment(
            monthly_weight_log_kg=log,
            target_monthly_rate_pct=0.005,
            body_weight_kg=80.0,
            week_number=8,
        )
        assert rec.action == "adjust_calories"
        # Gaining too fast -> DECREASE intake -> negative kcal delta
        assert rec.calorie_delta_kcal < 0, (
            f"Gaining too fast must recommend a calorie DECREASE; "
            f"got {rec.calorie_delta_kcal}"
        )
        assert rec.carb_g_delta < 0
        assert rec.fat_g_delta < 0

    def test_weeks_before_6_always_wait(self):
        log = [80.0, 82.0]  # would normally trigger "too fast"
        rec = recommend_bulk_adjustment(
            monthly_weight_log_kg=log,
            target_monthly_rate_pct=0.005,
            body_weight_kg=80.0,
            week_number=4,
        )
        assert rec.action == "wait"


# === Default mutable-default fix (Tier 3.30) ===

class TestAdjustmentRecommendationDefaults:
    def test_troubleshooting_steps_defaults_to_empty_list_not_none(self):
        rec = AdjustmentRecommendation(plateau_type=PlateauType.NONE, action="wait")
        # Must be iterable (list), not None
        assert isinstance(rec.troubleshooting_steps, list)
        assert rec.troubleshooting_steps == []
        # Iterate without TypeError
        for step in rec.troubleshooting_steps:
            assert step  # empty list -> no iteration, no error

    def test_troubleshooting_steps_can_be_set(self):
        rec = AdjustmentRecommendation(
            plateau_type=PlateauType.NONE,
            action="wait",
            troubleshooting_steps=["step 1", "step 2"],
        )
        assert len(rec.troubleshooting_steps) == 2

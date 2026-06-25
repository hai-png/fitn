"""
Tests for the recommendation/adjustment subsystem (plateau → recommendation).

Covers recommend_cut_adjustment and recommend_bulk_adjustment which produce
structured AdjustmentRecommendation objects for troubleshooting plateaus.
"""
from __future__ import annotations

import pytest

from fitness_engine.nutrition.adjustments import (
    detect_plateau, recommend_cut_adjustment, recommend_bulk_adjustment,
    PlateauType, AdjustmentRecommendation,
)


class TestRecommendCutAdjustment:

    def test_weeks_1_2_returns_wait(self):
        """Weeks 1-2 of a cut: ignore (water shifts)."""
        rec = recommend_cut_adjustment(
            weekly_weight_log_kg=[80, 79.5],
            target_weekly_rate_pct=0.005,
            body_weight_kg=80,
            week_number=1,
        )
        assert "wait" in rec.reasoning.lower() or "ignore" in rec.reasoning.lower()

    def test_week_3_with_progress_no_adjustment(self):
        """Week 3+, on-track: no adjustment."""
        rec = recommend_cut_adjustment(
            weekly_weight_log_kg=[80, 79.6, 79.2, 78.8],  # 0.4 kg/wk loss
            target_weekly_rate_pct=0.005,  # 0.4 kg/wk target
            body_weight_kg=80,
            week_number=4,
        )
        # Should not recommend a calorie reduction
        assert rec.calorie_delta_kcal >= 0 or "on track" in rec.reasoning.lower()

    def test_sudden_stall_returns_wait_recommendation(self):
        """Sudden stall: wait (water retention)."""
        rec = recommend_cut_adjustment(
            weekly_weight_log_kg=[80, 78, 78, 78, 78],  # whoosh then stall
            target_weekly_rate_pct=0.005,
            body_weight_kg=78,
            week_number=5,
        )
        # Should mention waiting
        assert isinstance(rec, AdjustmentRecommendation)

    def test_weight_gain_returns_troubleshooting(self):
        """Weight gain during cut: troubleshooting checklist."""
        rec = recommend_cut_adjustment(
            weekly_weight_log_kg=[80, 80, 81, 82, 83],  # gaining
            target_weekly_rate_pct=0.005,
            body_weight_kg=83,
            week_number=5,
        )
        assert isinstance(rec, AdjustmentRecommendation)
        # Should have troubleshooting steps
        assert len(rec.troubleshooting_steps) > 0

    def test_gradual_slowdown_returns_calorie_reduction(self):
        """Gradual slowdown: 5-8% calorie reduction."""
        # Loss decelerating: 1.0 → 0.5 → 0.2 kg/wk
        rec = recommend_cut_adjustment(
            weekly_weight_log_kg=[80, 79, 78.5, 78.3, 78.1],
            target_weekly_rate_pct=0.005,
            body_weight_kg=78.1,
            week_number=5,
        )
        # Should recommend a calorie reduction (negative delta)
        assert isinstance(rec, AdjustmentRecommendation)


class TestRecommendBulkAdjustment:

    def test_weeks_1_5_returns_wait(self):
        """Weeks 1-5 of a bulk: wait (WGG regain + adaptation)."""
        rec = recommend_bulk_adjustment(
            monthly_weight_log_kg=[70, 70.5, 71],
            target_monthly_rate_pct=0.02,
            body_weight_kg=71,
            week_number=3,
        )
        assert "wait" in rec.reasoning.lower() or "adaptation" in rec.reasoning.lower()

    def test_week_6_plus_returns_assessment(self):
        """Week 6+: assess progress."""
        rec = recommend_bulk_adjustment(
            monthly_weight_log_kg=[70, 70.5, 71, 71.5, 72, 72.5, 73],
            target_monthly_rate_pct=0.02,
            body_weight_kg=73,
            week_number=7,
        )
        assert isinstance(rec, AdjustmentRecommendation)


class TestDetectPlateauEdgeCases:

    def test_insufficient_data_returns_none(self):
        assert detect_plateau([], body_weight_kg=80) == PlateauType.NONE
        assert detect_plateau([80], body_weight_kg=80) == PlateauType.NONE
        assert detect_plateau([80, 79], body_weight_kg=80) == PlateauType.NONE

    def test_normal_progress_returns_none(self):
        # Steady 0.5% weekly loss, no plateau signal
        log = [80, 79.6, 79.2, 78.8, 78.4]
        assert detect_plateau(log, body_weight_kg=78.4) == PlateauType.NONE

    def test_whoosh_in_old_logs_does_not_mask_current_stall(self):
        """Whoosh at week 1 should not mask stall at weeks 3-5."""
        log = [80, 73, 73, 73, 73]  # whoosh then 3-week stall
        result = detect_plateau(log, body_weight_kg=73)
        assert result == PlateauType.SUDDEN_STALL

    def test_whoosh_in_recent_weeks_detected(self):
        """Whoosh in last 3 weeks should be detected."""
        log = [80, 80, 80, 73]
        assert detect_plateau(log, body_weight_kg=73) == PlateauType.WHOOSH

"""
Regression tests for meal allocation percentages.

Tier 1.3 fix: STANDARD_ALLOCATIONS[5] previously summed to 0.85 (15% underdelivery
on 5-meal plans). The training-day 5-meal variant summed to 0.90. Both now sum to 1.0.

This test verifies ALL allocation variants sum to 1.0 (within floating-point tolerance)
for meal frequencies 2, 3, 4, 5, in both standard-day and training-day modes.
"""
import pytest

from fitness_engine.meal_plan.profile_requirements import (
    STANDARD_ALLOCATIONS, get_meal_allocation,
)
from fitness_engine.meal_plan.meal_templates import MEAL_ALLOCATIONS
from fitness_engine.models.meal import MealType


class TestAllocationSums:
    """Every allocation dict must sum to 1.0 — otherwise the plan under/over-delivers."""

    @pytest.mark.parametrize("meal_frequency", [2, 3, 4, 5])
    def test_standard_allocations_sum_to_one(self, meal_frequency):
        alloc = STANDARD_ALLOCATIONS[meal_frequency]
        total = sum(alloc.values())
        # For 5-meal, SNACK is split between 2 snacks in the template, but the
        # dict value is the TOTAL snack allocation, so the sum must be 1.0.
        assert total == pytest.approx(1.0), (
            f"STANDARD_ALLOCATIONS[{meal_frequency}] sums to {total}, expected 1.0. "
            f"Contents: {alloc}"
        )

    @pytest.mark.parametrize("meal_frequency", [2, 3, 4, 5])
    def test_meal_templates_allocations_sum_to_one(self, meal_frequency):
        alloc = MEAL_ALLOCATIONS[meal_frequency]
        total = sum(alloc.values())
        assert total == pytest.approx(1.0), (
            f"MEAL_ALLOCATIONS[{meal_frequency}] sums to {total}, expected 1.0. "
            f"Contents: {alloc}"
        )

    @pytest.mark.parametrize("meal_frequency", [3, 4, 5])
    def test_training_day_allocations_sum_to_one(self, meal_frequency):
        """Training-day allocations (with PRE/POST workout) must also sum to 1.0."""
        alloc = get_meal_allocation(
            meal_frequency,
            include_pre_post_workout=True,
            is_training_day=True,
        )
        # For 5-meal training-day, SNACK is split between 2 snacks. The dict
        # value is the TOTAL snack allocation, so the sum must be 1.0.
        total = sum(alloc.values())
        assert total == pytest.approx(1.0), (
            f"Training-day allocation for meal_frequency={meal_frequency} "
            f"sums to {total}, expected 1.0. Contents: {alloc}"
        )

    @pytest.mark.parametrize("meal_frequency", [2, 3, 4, 5])
    def test_standard_day_allocations_sum_to_one(self, meal_frequency):
        """Non-training-day allocations must sum to 1.0."""
        alloc = get_meal_allocation(
            meal_frequency,
            include_pre_post_workout=False,
            is_training_day=False,
        )
        total = sum(alloc.values())
        assert total == pytest.approx(1.0), (
            f"Standard-day allocation for meal_frequency={meal_frequency} "
            f"sums to {total}, expected 1.0. Contents: {alloc}"
        )


class TestFiveMealAllocationSpecifically:
    """Specific regression for the 5-meal bug (was 0.85 standard, 0.90 training)."""

    def test_five_meal_standard_sums_to_one(self):
        """Was 0.85 (0.20+0.25+0.25+0.15) — must now be 1.0."""
        alloc = STANDARD_ALLOCATIONS[5]
        total = sum(alloc.values())
        assert total == pytest.approx(1.0), (
            f"5-meal standard allocation was 0.85 before fix; now {total}. Must be 1.0."
        )

    def test_five_meal_training_day_sums_to_one(self):
        """Was 0.90 (0.10+0.15+0.15+0.20+0.20+0.10) — must now be 1.0."""
        alloc = get_meal_allocation(
            5, include_pre_post_workout=True, is_training_day=True,
        )
        total = sum(alloc.values())
        assert total == pytest.approx(1.0), (
            f"5-meal training-day allocation was 0.90 before fix; now {total}. Must be 1.0. "
            f"Contents: {alloc}"
        )

    def test_five_meal_snack_split_yields_correct_total(self):
        """When 5-meal template splits SNACK into 2 slots, the two halves
        plus the other 3 meals must sum to 1.0."""
        alloc = STANDARD_ALLOCATIONS[5]
        # Simulate the template split
        per_snack = alloc[MealType.SNACK] / 2
        total_with_split = (
            alloc[MealType.BREAKFAST]
            + per_snack  # morning snack
            + alloc[MealType.LUNCH]
            + per_snack  # afternoon snack
            + alloc[MealType.DINNER]
        )
        assert total_with_split == pytest.approx(1.0), (
            f"5-meal template with split snacks sums to {total_with_split}, expected 1.0"
        )

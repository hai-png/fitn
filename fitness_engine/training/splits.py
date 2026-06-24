"""
Workout split selection — backward-compat shim.

The new split definitions live in split_designs.py as declarative data.
This module re-exports the helpers that other modules still import.
"""
from __future__ import annotations

from ..models.profile import EquipmentAccess
from ..models.training import SplitType
from .exercise_selector import get_equipment_allowed_set
from .split_designs import ALL_SPLITS, get_splits_for_days, get_split


def select_split(training_days_per_week: int) -> SplitType:
    """
    Select a workout split based on training days per week.

    DEPRECATED: use architect._pick_split() for richer selection logic
    that considers experience + goal. This function is kept for any
    downstream code that calls it directly.
    """
    if training_days_per_week <= 3:
        return SplitType.FULL_BODY
    elif training_days_per_week == 4:
        return SplitType.UPPER_LOWER
    elif training_days_per_week == 5:
        return SplitType.PUSH_PULL_LEGS_UPPER_LOWER
    else:  # 6
        return SplitType.PPL_X2


def select_progression(training_status) -> str:
    """Map training status to progression scheme name."""
    from ..models.profile import TrainingStatus
    return {
        TrainingStatus.BEGINNER: "linear",
        TrainingStatus.NOVICE: "linear",
        TrainingStatus.INTERMEDIATE: "dup",
        TrainingStatus.ADVANCED: "block",
    }.get(training_status, "linear")


def filter_exercises_by_equipment(exercises: list, equipment_access: EquipmentAccess) -> list:
    """
    Filter exercises by equipment access — kept for backward compat.

    New code should use exercise_selector.select_exercise_for_slot which
    applies the filter inline during slot filling.
    """
    allowed = get_equipment_allowed_set(equipment_access)
    return [ex for ex in exercises if ex.equipment in allowed]


__all__ = [
    "select_split", "select_progression",
    "filter_exercises_by_equipment",
]

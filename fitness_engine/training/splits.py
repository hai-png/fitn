"""
Workout split selection logic.

Phase-1 implements 4 default split patterns. Future versions will support
custom splits from the user-supplied exercise resources.
"""
from __future__ import annotations

from ..models.profile import UserProfile, EquipmentAccess
from ..models.training import SplitType


def select_split(training_days_per_week: int) -> SplitType:
    """
    Select a workout split based on training days per week.

    Days → Split mapping:
      2-3  → Full Body (3x/week alternate days)
      4    → Upper/Lower (2x cycle)
      5    → Push/Pull/Legs/Upper/Lower
      6    → Push/Pull/Legs ×2
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
    """
    Select progression scheme based on training status.

    - Beginner → Linear progression (add load weekly)
    - Novice → Linear (slow) or DUP
    - Intermediate → Daily Undulating Periodization (DUP)
    - Advanced → Block periodization
    """
    from ..models.profile import TrainingStatus
    if training_status == TrainingStatus.BEGINNER:
        return "linear"
    elif training_status == TrainingStatus.NOVICE:
        return "linear"     # still linear, but with smaller jumps
    elif training_status == TrainingStatus.INTERMEDIATE:
        return "dup"
    else:  # ADVANCED
        return "block"


def filter_exercises_by_equipment(
    exercises: list, equipment_access: EquipmentAccess
) -> list:
    """
    Filter the exercise library based on equipment access.

    - full_gym: all exercises
    - home_gym: barbell, dumbbell, kettlebell, bodyweight (no machine/cable)
    - bodyweight_only: bodyweight only
    """
    if equipment_access == EquipmentAccess.FULL_GYM:
        return exercises

    if equipment_access == EquipmentAccess.HOME_GYM:
        allowed = {"barbell", "dumbbell", "kettlebell", "bodyweight"}
        return [ex for ex in exercises if ex.equipment in allowed]

    # bodyweight_only
    return [ex for ex in exercises if ex.equipment == "bodyweight"]


__all__ = [
    "select_split", "select_progression",
    "filter_exercises_by_equipment",
]

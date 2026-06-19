"""Training module — exercise library, splits, progression, plan generation."""
from .exercise_library import (
    EXERCISES, EXERCISE_INDEX,
    get_exercise, exercises_by_muscle, exercises_by_category, exercises_by_equipment,
)
from .splits import select_split, select_progression, filter_exercises_by_equipment
from .progression import (
    ProgressionState, ProgressionEntry,
    linear_progression_next, dup_next,
)
from .planner import build_training_plan

__all__ = [
    # Library
    "EXERCISES", "EXERCISE_INDEX",
    "get_exercise", "exercises_by_muscle", "exercises_by_category",
    "exercises_by_equipment",
    # Splits
    "select_split", "select_progression", "filter_exercises_by_equipment",
    # Progression
    "ProgressionState", "ProgressionEntry",
    "linear_progression_next", "dup_next",
    # Planner
    "build_training_plan",
]

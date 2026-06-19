"""
Training plan data models.

Phase-1: framework-ready. Ships with a minimal but functional periodized plan
structure. The user will supply detailed exercise resources later — the
exercise library registry is designed for extension.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class SplitType(str, Enum):
    FULL_BODY = "full_body"             # 3 d/wk, every-other-day
    UPPER_LOWER = "upper_lower"         # 4 d/wk, 2x cycle
    PPL = "ppl"                          # push/pull/legs, 3 d/wk
    PPL_X2 = "ppl_x2"                   # 6 d/wk
    PUSH_PULL_LEGS_UPPER_LOWER = "pplul"  # 5 d/wk


class ProgressionScheme(str, Enum):
    LINEAR = "linear"                    # beginners: add load weekly
    DUP = "dup"                          # daily undulating periodization (intermediate)
    BLOCK = "block"                      # block periodization (advanced)


class ExerciseCategory(str, Enum):
    COMPOUND_PRIMARY = "compound_primary"
    COMPOUND_SECONDARY = "compound_secondary"
    ACCESSORY = "accessory"
    ISOLATION = "isolation"
    CARDIO = "cardio"
    MOBILITY = "mobility"


@dataclass
class Exercise:
    name: str
    category: ExerciseCategory
    muscle_groups: list[str]
    equipment: str
    default_sets: int
    default_reps: str                    # e.g., "5-8", "8-12", "12-15"
    default_rest_sec: int
    notes: str = ""


@dataclass
class WorkoutExercise:
    exercise: Exercise
    sets: int
    reps: str                            # "5-8" or specific like "5"
    rest_sec: int
    rpe_target: Optional[float] = None   # rate of perceived exertion (1-10)
    notes: str = ""


@dataclass
class Workout:
    """A single training session."""
    day_number: int                      # 1, 2, 3, ... within the microcycle
    name: str                            # e.g., "Upper A", "Lower A", "Push"
    focus: str                           # e.g., "Strength + Hypertrophy"
    exercises: list[WorkoutExercise] = field(default_factory=list)
    estimated_duration_min: int = 60
    notes: str = ""


@dataclass
class Microcycle:
    """One week of training (or one repeatable block of N days)."""
    name: str                            # e.g., "Week 1"
    workouts: list[Workout] = field(default_factory=list)
    rest_days: list[int] = field(default_factory=list)  # day numbers (1-indexed)


@dataclass
class Mesocycle:
    """A 4-8 week training block with a single progression scheme."""
    name: str                            # e.g., "Block 1: Accumulation"
    duration_weeks: int                  # 4-8
    progression: ProgressionScheme
    microcycles: list[Microcycle] = field(default_factory=list)
    deload_week: bool = True             # include a deload at the end
    notes: str = ""


@dataclass
class TrainingPlan:
    """Top-level training plan output."""
    split_type: SplitType
    training_days_per_week: int
    progression: ProgressionScheme
    mesocycles: list[Mesocycle] = field(default_factory=list)
    weekly_volume_summary: dict = field(default_factory=dict)  # muscle_group -> sets/wk
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        def _convert(obj):
            if isinstance(obj, Enum):
                return obj.value
            if hasattr(obj, "__dataclass_fields__"):
                return {k: _convert(v) for k, v in asdict(obj).items()}
            if isinstance(obj, list):
                return [_convert(x) for x in obj]
            if isinstance(obj, dict):
                return {k: _convert(v) for k, v in obj.items()}
            return obj
        return _convert(self)


__all__ = [
    "SplitType",
    "ProgressionScheme",
    "ExerciseCategory",
    "Exercise",
    "WorkoutExercise",
    "Workout",
    "Microcycle",
    "Mesocycle",
    "TrainingPlan",
]

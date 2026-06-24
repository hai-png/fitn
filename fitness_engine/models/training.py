"""
Training plan data models — Phase-3 clean rewrite.

The training system now supports TWO plan shapes:
  - STANDARD: an ongoing rotation of N workouts (no defined end date)
  - PROGRAM:  a time-bound block with mesocycles + deload weeks

Both shapes share the same data model (TrainingPlan with mesocycles) so
downstream serialization doesn't need to branch.

Phase-3 also introduces:
  - PlanType (STANDARD | PROGRAM)
  - TrainingGoal (STRENGTH | HYPERTROPHY | GENERAL_FITNESS | FAT_LOSS | MUSCLE_GAIN | RECOMP | MAINTENANCE)
  - SplitPattern (replaces the old SplitType; kept the latter as alias for backward compat)
  - PeriodizationScheme (LINEAR | DUP | BLOCK)
  - MovementPatternSlot + WorkoutTemplate + SplitDesign (in split_designs.py)
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


# === Plan shape ===

class PlanType(str, Enum):
    """Two output shapes the architect can produce."""
    STANDARD = "standard"   # ongoing rotation — repeat N workouts indefinitely
    PROGRAM = "program"     # time-bound — 1+ mesocycles with deload weeks


# === Training goal (rep-scheme focus, derived from PrimaryGoal + user choice) ===

class TrainingGoal(str, Enum):
    """Drives rep ranges, RPE targets, rest intervals, and exercise selection."""
    STRENGTH = "strength"             # 3-6 reps, RPE 8-9, 3-5 min rest
    HYPERTROPHY = "hypertrophy"       # 6-12 reps, RPE 7-8, 60-90s rest
    GENERAL_FITNESS = "general_fitness"  # 8-15 reps, RPE 6-7, 60s rest
    FAT_LOSS = "fat_loss"             # 6-15 reps, RPE 7, 45-60s rest (preserve muscle)
    MUSCLE_GAIN = "muscle_gain"       # same as hypertrophy but with bulk calories
    RECOMP = "recomp"                 # same as hypertrophy
    MAINTENANCE = "maintenance"       # 8-12 reps, RPE 6-7, 60-90s rest


# === Split patterns ===

class SplitType(str, Enum):
    """Backward-compat name (Phase-2)."""
    FULL_BODY = "full_body"                 # 2-3 d/wk
    UPPER_LOWER = "upper_lower"             # 4 d/wk
    PPL = "ppl"                              # 3 d/wk (push/pull/legs)
    PPL_X2 = "ppl_x2"                        # 6 d/wk
    PUSH_PULL_LEGS_UPPER_LOWER = "pplul"     # 5 d/wk
    BODY_PART = "body_part"                  # 4-5 d/wk (one muscle per day)
    PUSH_PULL = "push_pull"                  # 2-4 d/wk


# Alias for new code (cleaner name)
SplitPattern = SplitType


# === Periodization ===

class ProgressionScheme(str, Enum):
    """How load progresses session-to-session."""
    LINEAR = "linear"     # beginners: add load weekly
    DUP = "dup"           # intermediate: daily undulating (heavy/mod/light)
    BLOCK = "block"       # advanced: accumulation → intensification → deload


# === Exercise categories ===

class ExerciseCategory(str, Enum):
    """Derived from new DB's mechanics + force_type + exercise_type."""
    COMPOUND_PRIMARY = "compound_primary"
    COMPOUND_SECONDARY = "compound_secondary"
    ACCESSORY = "accessory"
    ISOLATION = "isolation"                # alias for ACCESSORY (kept for backward-compat)
    CARDIO = "cardio"
    MOBILITY = "mobility"


class ExperienceLevel(str, Enum):
    """Match the new exercise DB's experience_level field."""
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


# === Exercise + WorkoutExercise ===

@dataclass
class Exercise:
    """
    A single exercise entry from the loaded JSON database.
    Rich metadata: instructions, tips, video URL, experience level, etc.
    """
    # === Identity (required) ===
    name: str
    category: ExerciseCategory
    muscle_groups: list[str]
    equipment: str                            # normalized lowercase: "barbell", "dumbbell", etc.
    default_sets: int
    default_reps: str
    default_rest_sec: int
    notes: str = ""

    # === Rich metadata (populated by loader) ===
    slug: Optional[str] = None
    source_url: Optional[str] = None
    video_url: Optional[str] = None
    video_id: Optional[str] = None
    video_thumbnail: Optional[str] = None
    views: Optional[str] = None

    instructions: list[str] = field(default_factory=list)
    tips: list[str] = field(default_factory=list)
    overview: Optional[str] = None

    secondary_muscles: list[str] = field(default_factory=list)
    experience_level: Optional[ExperienceLevel] = None
    force_type: Optional[str] = None
    mechanics: Optional[str] = None
    exercise_type: Optional[str] = None

    @property
    def all_muscle_groups(self) -> list[str]:
        """Union of primary + secondary muscle groups (deduped)."""
        seen = set()
        out = []
        for m in self.muscle_groups + self.secondary_muscles:
            key = m.lower()
            if key not in seen:
                seen.add(key)
                out.append(m)
        return out


@dataclass
class WorkoutExercise:
    """A specific exercise prescription within a workout."""
    exercise: Exercise
    sets: int
    reps: str
    rest_sec: int
    rpe_target: Optional[float] = None
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "exercise": {
                "name": self.exercise.name,
                "slug": self.exercise.slug,
                "category": self.exercise.category.value,
                "muscle_groups": self.exercise.muscle_groups,
                "secondary_muscles": self.exercise.secondary_muscles,
                "equipment": self.exercise.equipment,
                "experience_level": (
                    self.exercise.experience_level.value
                    if self.exercise.experience_level else None
                ),
                "force_type": self.exercise.force_type,
                "mechanics": self.exercise.mechanics,
                "instructions": self.exercise.instructions,
                "tips": self.exercise.tips,
                "overview": self.exercise.overview,
                "video_url": self.exercise.video_url,
                "video_thumbnail": self.exercise.video_thumbnail,
                "source_url": self.exercise.source_url,
            },
            "sets": self.sets,
            "reps": self.reps,
            "rest_sec": self.rest_sec,
            "rpe_target": self.rpe_target,
            "notes": self.notes,
        }


@dataclass
class Workout:
    """A single training session."""
    day_number: int                      # 1-indexed within the microcycle
    name: str                            # e.g., "Upper A", "Lower A", "Push"
    focus: str                           # e.g., "Strength + Hypertrophy"
    exercises: list[WorkoutExercise] = field(default_factory=list)
    estimated_duration_min: int = 60
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "day_number": self.day_number,
            "name": self.name,
            "focus": self.focus,
            "exercises": [we.to_dict() for we in self.exercises],
            "estimated_duration_min": self.estimated_duration_min,
            "notes": self.notes,
        }


@dataclass
class Microcycle:
    """One week of training (or one repeatable block of N days)."""
    name: str                            # e.g., "Week 1"
    workouts: list[Workout] = field(default_factory=list)
    rest_days: list[int] = field(default_factory=list)
    is_deload: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "workouts": [w.to_dict() for w in self.workouts],
            "rest_days": self.rest_days,
            "is_deload": self.is_deload,
        }


@dataclass
class Mesocycle:
    """A 3-8 week training block with a single periodization scheme."""
    name: str                            # e.g., "Block 1: Accumulation"
    duration_weeks: int
    progression: ProgressionScheme
    microcycles: list[Microcycle] = field(default_factory=list)
    deload_week: bool = True
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "duration_weeks": self.duration_weeks,
            "progression": self.progression.value,
            "microcycles": [m.to_dict() for m in self.microcycles],
            "deload_week": self.deload_week,
            "notes": self.notes,
        }


@dataclass
class TrainingPlan:
    """
    Top-level training plan output — works for both STANDARD and PROGRAM shapes.

    For STANDARD plans: mesocycles has 1 entry with 1 microcycle that the user
    repeats indefinitely. total_duration_weeks = 0.

    For PROGRAM plans: mesocycles has 1+ entries; total_duration_weeks is the
    sum of all mesocycle durations.
    """
    plan_type: PlanType
    goal: TrainingGoal
    split_type: SplitType
    training_days_per_week: int
    progression: ProgressionScheme
    mesocycles: list[Mesocycle] = field(default_factory=list)
    total_duration_weeks: int = 0           # 0 for STANDARD, N for PROGRAM
    muscle_focus: list[str] = field(default_factory=list)
    weekly_volume_summary: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "plan_type": self.plan_type.value,
            "goal": self.goal.value,
            "split_type": self.split_type.value,
            "training_days_per_week": self.training_days_per_week,
            "progression": self.progression.value,
            "mesocycles": [m.to_dict() for m in self.mesocycles],
            "total_duration_weeks": self.total_duration_weeks,
            "muscle_focus": list(self.muscle_focus),
            "weekly_volume_summary": dict(self.weekly_volume_summary),
            "notes": list(self.notes),
        }
        return d


__all__ = [
    "PlanType",
    "TrainingGoal",
    "SplitType",
    "SplitPattern",
    "ProgressionScheme",
    "ExerciseCategory",
    "ExperienceLevel",
    "Exercise",
    "WorkoutExercise",
    "Workout",
    "Microcycle",
    "Mesocycle",
    "TrainingPlan",
]

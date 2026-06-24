"""
Training module — Phase-3 clean architecture.

Public API:
  - build_training_plan(profile, assessment, plan_type?, muscle_focus?, duration?)
  - PlanType, TrainingGoal, SplitType, ProgressionScheme
  - All split designs + exercise library + progression helpers

The architect (architect.py) is the single entry point for plan
construction. It composes:
  - split_designs.py    (declarative split templates)
  - exercise_selector.py (fills templates with exercises from the JSON DB)
  - periodization.py    (applies reps/rest/RPE based on goal + progression)
"""
from ..models.training import (
    PlanType, TrainingGoal,
    SplitType, SplitPattern,
    ProgressionScheme,
    ExerciseCategory, ExperienceLevel,
    Exercise, WorkoutExercise, Workout, Microcycle, Mesocycle, TrainingPlan,
)
from .exercise_library import (
    EXERCISES, EXERCISE_INDEX, EXERCISE_SLUG_INDEX,
    PHASE1_TO_PHASE2_SLUG_MAP,
    get_exercise, get_exercise_by_phase1_name,
    exercises_by_muscle, exercises_by_category,
    exercises_by_equipment, exercises_by_experience,
    exercises_by_force_type,
)
from .exercise_loader import (
    load_exercises,
    get_exercise_by_slug,
    get_exercise_by_name,
    normalize_equipment,
    normalize_muscle,
    derive_category,
)
from .exercise_selector import (
    select_exercise_for_slot,
    get_equipment_allowed_set,
)
from .split_designs import (
    MovementPatternSlot, WorkoutTemplate, SplitDesign,
    ALL_SPLITS, get_splits_for_days, get_split,
    FULL_BODY_2DAY, FULL_BODY_3DAY,
    UPPER_LOWER_4DAY,
    PPL_3DAY, PPL_X2_6DAY, PPL_UL_5DAY,
    BODY_PART_5DAY, PUSH_PULL_4DAY,
)
from .periodization import (
    apply_periodization,
    get_mesocycle_length,
    get_program_duration_weeks,
    get_block_phases_for_program,
)
from .progression import (
    ProgressionState, ProgressionEntry,
    linear_progression_next, dup_next,
)
from .architect import build_training_plan

# Backward-compat: planner.py is now a shim but still importable
from .splits import select_split, select_progression, filter_exercises_by_equipment

__all__ = [
    # Models
    "PlanType", "TrainingGoal",
    "SplitType", "SplitPattern",
    "ProgressionScheme",
    "ExerciseCategory", "ExperienceLevel",
    "Exercise", "WorkoutExercise", "Workout", "Microcycle", "Mesocycle", "TrainingPlan",
    # Exercise library
    "EXERCISES", "EXERCISE_INDEX", "EXERCISE_SLUG_INDEX",
    "PHASE1_TO_PHASE2_SLUG_MAP",
    "get_exercise", "get_exercise_by_phase1_name",
    "exercises_by_muscle", "exercises_by_category",
    "exercises_by_equipment", "exercises_by_experience",
    "exercises_by_force_type",
    # Loader
    "load_exercises", "get_exercise_by_slug", "get_exercise_by_name",
    "normalize_equipment", "normalize_muscle", "derive_category",
    # Selector
    "select_exercise_for_slot", "get_equipment_allowed_set",
    # Split designs
    "MovementPatternSlot", "WorkoutTemplate", "SplitDesign",
    "ALL_SPLITS", "get_splits_for_days", "get_split",
    "FULL_BODY_2DAY", "FULL_BODY_3DAY",
    "UPPER_LOWER_4DAY",
    "PPL_3DAY", "PPL_X2_6DAY", "PPL_UL_5DAY",
    "BODY_PART_5DAY", "PUSH_PULL_4DAY",
    # Periodization
    "apply_periodization",
    "get_mesocycle_length",
    "get_program_duration_weeks",
    "get_block_phases_for_program",
    # Progression
    "ProgressionState", "ProgressionEntry",
    "linear_progression_next", "dup_next",
    # Architect (main entry point)
    "build_training_plan",
    # Backward-compat
    "select_split", "select_progression", "filter_exercises_by_equipment",
]

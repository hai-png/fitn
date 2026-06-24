"""
Training module — Phase-4 clean architecture with RippedBody-informed enhancements.

Public API:
  - build_training_plan(profile, assessment, plan_type?, muscle_focus?, duration?)
  - PlanType, TrainingGoal, SplitType, ProgressionScheme
  - All split designs + exercise library + progression helpers

Phase-4 additions:
  - exercise_categorization: 24 movement patterns + swap system + environment preferences
  - volume_landmarks: MEV/MAV/MRV/ML + fractional counting + 11-set cap + VolumeTier
  - intensity_model: RIR ranges per (rep range × intensity tier) + warm-up generator + reactive deload

The architect (architect.py) is the single entry point for plan construction.
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
from .exercise_categorization import (
    PatternFamily,
    MovementPatternSpec,
    ExerciseCategoryInfo,
    MOVEMENT_PATTERNS,
    categorize_exercise,
    get_movement_pattern,
    get_pattern_family,
    get_volume_family,
    get_environment_preferred_equipment,
    get_swappable_exercises,
)
from .volume_landmarks import (
    VolumeTier,
    TIER_SET_RANGES,
    TIER_HOURS_RANGES,
    MuscleVolumeLandmarks,
    DEFAULT_MUSCLE_LANDMARKS,
    get_muscle_landmarks,
    StrengthLiftLandmarks,
    STRENGTH_LIFT_LANDMARKS,
    get_recommended_frequency,
    PER_SESSION_SET_CAP,
    check_session_volume_cap,
    count_sets_toward_muscle,
    compute_weekly_volume_per_muscle,
    compute_session_volume_per_muscle,
    get_recommended_weekly_sets,
    validate_weekly_volume,
    SpecializationConfig,
    SPECIALIZATION_BALANCED,
    SPECIALIZATION_FOCUS,
    get_specialization_program,
)
from .intensity_model import (
    ExerciseIntensityTier,
    get_exercise_intensity_tier,
    RIR_TABLE,
    get_rir_range,
    rir_to_rpe,
    rpe_to_rir,
    WarmUpSet,
    WARMUP_LEQ_6_REP,
    WARMUP_GEQ_6_REP,
    generate_warmup_sets,
    generate_warmup_for_workout,
    REACTIVE_DELOAD_QUESTIONS,
    should_deload,
    apply_deload,
    StrengthPhase,
    StrengthPhaseSpec,
    STRENGTH_PHASE_SPECS,
    get_peak_phase_duration,
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
    # Phase-4: Categorization + swap system
    "PatternFamily", "MovementPatternSpec", "ExerciseCategoryInfo",
    "MOVEMENT_PATTERNS",
    "categorize_exercise", "get_movement_pattern", "get_pattern_family",
    "get_volume_family", "get_environment_preferred_equipment",
    "get_swappable_exercises",
    # Phase-4: Volume landmarks
    "VolumeTier", "TIER_SET_RANGES", "TIER_HOURS_RANGES",
    "MuscleVolumeLandmarks", "DEFAULT_MUSCLE_LANDMARKS", "get_muscle_landmarks",
    "StrengthLiftLandmarks", "STRENGTH_LIFT_LANDMARKS",
    "get_recommended_frequency", "PER_SESSION_SET_CAP",
    "check_session_volume_cap", "count_sets_toward_muscle",
    "compute_weekly_volume_per_muscle", "compute_session_volume_per_muscle",
    "get_recommended_weekly_sets", "validate_weekly_volume",
    "SpecializationConfig", "SPECIALIZATION_BALANCED", "SPECIALIZATION_FOCUS",
    "get_specialization_program",
    # Phase-4: Intensity model + warm-up + reactive deload
    "ExerciseIntensityTier", "get_exercise_intensity_tier",
    "RIR_TABLE", "get_rir_range", "rir_to_rpe", "rpe_to_rir",
    "WarmUpSet", "WARMUP_LEQ_6_REP", "WARMUP_GEQ_6_REP",
    "generate_warmup_sets", "generate_warmup_for_workout",
    "REACTIVE_DELOAD_QUESTIONS", "should_deload", "apply_deload",
    "StrengthPhase", "StrengthPhaseSpec", "STRENGTH_PHASE_SPECS",
    "get_peak_phase_duration",
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

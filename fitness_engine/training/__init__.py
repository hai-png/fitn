"""
Training module — clean architecture with RippedBody-informed enhancements.

Public API:
  - build_training_plan(profile, assessment, plan_type?, muscle_focus?, duration?) → TrainingPlan
  - PlanType, TrainingGoal, SplitType, ProgressionScheme
  - All split designs + exercise library + progression helpers

Modules:
  - architect: top-level orchestrator (the single entry point)
  - split_designs: 8 declarative split patterns
  - exercise_selector: 6-tier fallback slot filler
  - exercise_categorization: 24 movement patterns + swap system
  - exercise_library: loads 1,217 exercises from JSON
  - exercise_loader: JSON loading + normalization
  - periodization: rep/RPE/rest rules per goal × progression
  - intensity_model: RIR ranges + warm-up generator + reactive deload
  - volume_landmarks: MEV/MAV/MRV/ML + fractional counting + 11-set cap
  - progression: linear + DUP progression helpers
"""
from ..models.training import (
    Exercise,
    ExerciseCategory,
    ExperienceLevel,
    Mesocycle,
    Microcycle,
    PlanType,
    ProgressionScheme,
    SplitType,
    TrainingGoal,
    TrainingPlan,
    Workout,
    WorkoutExercise,
)
from .architect import build_training_plan
from .exercise_categorization import (
    MOVEMENT_PATTERNS,
    ExerciseCategoryInfo,
    MovementPatternSpec,
    PatternFamily,
    categorize_exercise,
    get_environment_preferred_equipment,
    get_movement_pattern,
    get_pattern_family,
    get_swappable_exercises,
)
from .exercise_library import (
    EXERCISE_INDEX,
    EXERCISE_SLUG_INDEX,
    EXERCISES,
    PHASE1_TO_PHASE2_SLUG_MAP,
    exercises_by_category,
    exercises_by_equipment,
    exercises_by_experience,
    exercises_by_force_type,
    exercises_by_muscle,
    get_exercise,
    get_exercise_by_phase1_name,
)
from .exercise_loader import (
    derive_category,
    get_exercise_by_name,
    get_exercise_by_slug,
    load_exercises,
    normalize_equipment,
    normalize_muscle,
)
from .exercise_selector import (
    get_equipment_allowed_set,
    select_exercise_for_slot,
)
from .intensity_model import (
    REACTIVE_DELOAD_QUESTIONS,
    RIR_TABLE,
    STRENGTH_PHASE_SPECS,
    WARMUP_GEQ_6_REP,
    WARMUP_LEQ_6_REP,
    ExerciseIntensityTier,
    StrengthPhase,
    StrengthPhaseSpec,
    WarmUpSet,
    generate_warmup_for_workout,
    generate_warmup_sets,
    get_exercise_intensity_tier,
    get_rir_range,
    rir_to_rpe,
    rpe_to_rir,
    should_deload,
)
from .periodization import (
    apply_periodization,
    get_block_phases_for_program,
    get_mesocycle_length,
    get_program_duration_weeks,
)
from .progression import (
    ProgressionEntry,
    ProgressionState,
    dup_next,
    linear_progression_next,
)
from .split_designs import (
    ALL_SPLITS,
    BODY_PART_5DAY,
    FULL_BODY_2DAY,
    FULL_BODY_3DAY,
    PPL_3DAY,
    PPL_UL_5DAY,
    PPL_X2_6DAY,
    PUSH_PULL_4DAY,
    UPPER_LOWER_4DAY,
    MovementPatternSlot,
    SplitDesign,
    WorkoutTemplate,
    get_split,
    get_splits_for_days,
)
from .volume_landmarks import (
    DEFAULT_MUSCLE_LANDMARKS,
    PER_SESSION_SET_CAP,
    SPECIALIZATION_BALANCED,
    SPECIALIZATION_FOCUS,
    STRENGTH_LIFT_LANDMARKS,
    TIER_HOURS_RANGES,
    TIER_SET_RANGES,
    MuscleVolumeLandmarks,
    SpecializationConfig,
    StrengthLiftLandmarks,
    VolumeTier,
    check_session_volume_cap,
    compute_session_volume_per_muscle,
    compute_weekly_volume_per_muscle,
    count_sets_toward_muscle,
    get_muscle_landmarks,
    get_recommended_frequency,
    get_recommended_weekly_sets,
    validate_weekly_volume,
)

__all__ = [
    # Models
    "PlanType", "TrainingGoal",
    "SplitType",
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
    # Categorization + swap system
    "PatternFamily", "MovementPatternSpec", "ExerciseCategoryInfo",
    "MOVEMENT_PATTERNS",
    "categorize_exercise", "get_movement_pattern", "get_pattern_family",
    "get_environment_preferred_equipment",
    "get_swappable_exercises",
    # Volume landmarks
    "VolumeTier", "TIER_SET_RANGES", "TIER_HOURS_RANGES",
    "MuscleVolumeLandmarks", "DEFAULT_MUSCLE_LANDMARKS", "get_muscle_landmarks",
    "StrengthLiftLandmarks", "STRENGTH_LIFT_LANDMARKS",
    "get_recommended_frequency", "PER_SESSION_SET_CAP",
    "check_session_volume_cap", "count_sets_toward_muscle",
    "compute_weekly_volume_per_muscle", "compute_session_volume_per_muscle",
    "get_recommended_weekly_sets", "validate_weekly_volume",
    "SpecializationConfig", "SPECIALIZATION_BALANCED", "SPECIALIZATION_FOCUS",
    # Intensity model + warm-up + reactive deload
    "ExerciseIntensityTier", "get_exercise_intensity_tier",
    "RIR_TABLE", "get_rir_range", "rir_to_rpe", "rpe_to_rir",
    "WarmUpSet", "WARMUP_LEQ_6_REP", "WARMUP_GEQ_6_REP",
    "generate_warmup_sets", "generate_warmup_for_workout",
    "REACTIVE_DELOAD_QUESTIONS", "should_deload",
    "StrengthPhase", "StrengthPhaseSpec", "STRENGTH_PHASE_SPECS",
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
]

"""
Volume landmarks — Phase-4 (RippedBody-informed).

Codifies RippedBody's volume model:
  - MEV (Minimum Effective Volume): floor sets/muscle/wk for growth
  - MAV (Maximum Adaptive Volume): practical growth range
  - MRV (Maximum Recoverable Volume): hard ceiling
  - ML  (Maintenance Level): volume needed to maintain muscle

Plus:
  - VolumeTier enum (Table 7.4): MINIMAL / LOW / MEDIUM / HIGH / VERY_HIGH
  - Frequency recommendation by volume (Table 7.6)
  - 11-set per-muscle per-session cap (Rule 2.6)
  - Fractional set counting (Rule 2.5): primary=1.0, secondary=0.5
  - Maintenance volume = 0.5–0.67 × MAV (Rule 2.4)
  - Specialization cycles (Table 7.9): balanced → focus → balanced

Source: /home/z/my-project/fitn/reports/rippedbody_insights.md
        Section 2 (Volume Landmarks), Section 3 (Frequency), Section 12 (Specialization)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ..models.training import Exercise, ExerciseCategory, TrainingGoal
from ..models.profile import TrainingStatus
from .exercise_categorization import get_movement_pattern, get_pattern_family, PatternFamily


# === Volume tiers (Table 7.4) ===

class VolumeTier(str, Enum):
    """Time-budget-based volume tiers."""
    MINIMAL = "minimal"        # 4-8 sets/muscle/wk, ~1-2.5h
    LOW = "low"                 # 9-12 sets/muscle/wk, ~3-4.5h
    MEDIUM = "medium"           # 13-16 sets/muscle/wk, ~5-6.5h
    HIGH = "high"               # 17-20 sets/muscle/wk, ~7-8.5h
    VERY_HIGH = "very_high"    # 21-30 sets/muscle/wk, ~9+h


TIER_SET_RANGES: dict[VolumeTier, tuple[int, int]] = {
    VolumeTier.MINIMAL:   (4, 8),
    VolumeTier.LOW:       (9, 12),
    VolumeTier.MEDIUM:    (13, 16),
    VolumeTier.HIGH:      (17, 20),
    VolumeTier.VERY_HIGH: (21, 30),
}

TIER_HOURS_RANGES: dict[VolumeTier, tuple[float, float]] = {
    VolumeTier.MINIMAL:   (1.0, 2.5),
    VolumeTier.LOW:       (3.0, 4.5),
    VolumeTier.MEDIUM:    (5.0, 6.5),
    VolumeTier.HIGH:      (7.0, 8.5),
    VolumeTier.VERY_HIGH: (9.0, 12.0),
}


# === Per-muscle volume landmarks (Table 7.3) ===

@dataclass
class MuscleVolumeLandmarks:
    """Volume landmarks for a single muscle group (sets per week)."""
    muscle: str
    mev: int               # Minimum Effective Volume (floor for growth)
    mav_lo: int            # Maximum Adaptive Volume lower bound
    mav_hi: int            # Maximum Adaptive Volume upper bound
    mrv: int               # Maximum Recoverable Volume (hard ceiling)
    ml: int                # Maintenance Level


# Default landmarks per muscle (RippedBody Table 7.3 + community consensus)
# Values are sets per week (fractional counting applied).
DEFAULT_MUSCLE_LANDMARKS: dict[str, MuscleVolumeLandmarks] = {
    "chest":          MuscleVolumeLandmarks("chest",          4, 10, 20, 30, 6),
    "back":           MuscleVolumeLandmarks("back",           4, 10, 20, 30, 6),
    "upper_back":     MuscleVolumeLandmarks("upper_back",     4, 10, 20, 30, 6),
    "lats":           MuscleVolumeLandmarks("lats",           4, 10, 20, 30, 6),
    "quads":          MuscleVolumeLandmarks("quads",          4,  8, 16, 25, 5),
    "hamstrings":     MuscleVolumeLandmarks("hamstrings",     4,  8, 16, 25, 5),
    "glutes":         MuscleVolumeLandmarks("glutes",         4,  8, 16, 25, 5),
    "shoulders":      MuscleVolumeLandmarks("shoulders",      4,  8, 16, 25, 5),
    "triceps":        MuscleVolumeLandmarks("triceps",        3,  6, 12, 20, 4),
    "biceps":         MuscleVolumeLandmarks("biceps",         3,  6, 12, 20, 4),
    "calves":         MuscleVolumeLandmarks("calves",         4,  8, 16, 25, 5),
    "abs":            MuscleVolumeLandmarks("abs",            3,  6, 12, 20, 4),
    "obliques":       MuscleVolumeLandmarks("obliques",       3,  6, 12, 20, 4),
    "forearms":       MuscleVolumeLandmarks("forearms",       3,  4,  8, 15, 3),
    "traps":          MuscleVolumeLandmarks("traps",          3,  6, 12, 20, 4),
    "lower_back":     MuscleVolumeLandmarks("lower_back",     3,  4,  8, 15, 3),
}


def get_muscle_landmarks(muscle: str) -> MuscleVolumeLandmarks:
    """Get volume landmarks for a muscle (with fallback for unknown muscles)."""
    muscle_lower = muscle.lower()
    if muscle_lower in DEFAULT_MUSCLE_LANDMARKS:
        return DEFAULT_MUSCLE_LANDMARKS[muscle_lower]
    # Default: medium-volume landmarks
    return MuscleVolumeLandmarks(muscle_lower, 4, 8, 16, 25, 5)


# === Strength volume landmarks (per main lift, not per muscle) ===

@dataclass
class StrengthLiftLandmarks:
    """Volume landmarks for a strength main lift (sets per week)."""
    lift: str
    mev: int               # 1 set/lift/wk
    mav_lo: int            # 3 short-term, 5 long-term
    mav_hi: int            # 5 short-term, 10 long-term
    mrv: int               # ~5 short-term
    ml: int


STRENGTH_LIFT_LANDMARKS: dict[str, StrengthLiftLandmarks] = {
    # Tier 2.24 fix: MRV must be >= MAV_hi (Maximum Recoverable Volume must
    # be >= upper bound of Maximum Adaptive Volume). Previously MRV=5 < MAV_hi=10,
    # which is mathematically incoherent (you can't recover from less volume
    # than the upper bound of what's adaptive). Now MRV = MAV_hi + 2.
    "squat":       StrengthLiftLandmarks("squat",       1, 3, 10, 12, 2),
    "bench":       StrengthLiftLandmarks("bench",       1, 3, 10, 12, 2),
    "deadlift":    StrengthLiftLandmarks("deadlift",    1, 3, 10, 12, 2),
    "overhead":    StrengthLiftLandmarks("overhead",    1, 3, 10, 12, 2),
}


# === Frequency recommendation by volume (Table 7.6) ===

def get_recommended_frequency(weekly_sets_per_muscle: int, is_strength: bool = False) -> int:
    """
    Get recommended weekly frequency for a muscle group based on volume.

    RippedBody Table 7.6:
      - 4-10 sets/muscle/wk → 1-2x frequency
      - 11-20 sets/muscle/wk → 2-3x frequency
      - 21-30 sets/muscle/wk → 3+x frequency

    For strength (Rule 3.3): floor = 2x/lift/wk, ceiling = 6x.
    """
    if is_strength:
        if weekly_sets_per_muscle <= 3:
            return 2
        elif weekly_sets_per_muscle <= 5:
            return 3
        else:
            return 4

    if weekly_sets_per_muscle <= 10:
        return 2
    elif weekly_sets_per_muscle <= 20:
        return 3
    else:
        return 4


# === 11-set per-session cap (Rule 2.6) ===

PER_SESSION_SET_CAP = 11


def check_session_volume_cap(
    session_sets_per_muscle: dict[str, float],
) -> list[str]:
    """
    Check if any muscle exceeds 11 fractional sets in a single session.

    Returns list of warning messages for muscles that exceed the cap.
    """
    warnings: list[str] = []
    for muscle, sets in session_sets_per_muscle.items():
        if sets > PER_SESSION_SET_CAP:
            warnings.append(
                f"⚠ {muscle} = {sets:.1f} sets in this session "
                f"(exceeds {PER_SESSION_SET_CAP}-set cap). "
                "Increase weekly frequency to distribute volume."
            )
    return warnings


# === Fractional set counting (Rule 2.5) ===

def count_sets_toward_muscle(
    exercise: Exercise,
    muscle: str,
    sets: int,
    is_strength: bool = False,
) -> float:
    """
    Count how many sets an exercise contributes toward a target muscle.

    RippedBody Rule 2.5:
      - Hypertrophy: primary muscle = 1.0 set; secondary muscle = 0.5 set.
      - Strength: main-lift sets = 1.0; any other lift sharing muscles = 0.5.

    Args:
      exercise: the exercise being counted
      muscle: target muscle (normalized lowercase)
      sets: number of hard sets performed
      is_strength: if True, use strength counting rules

    Returns: fractional set count (e.g. 4.0 or 2.0)
    """
    muscle_lower = muscle.lower()
    primary_muscles = [m.lower() for m in exercise.muscle_groups]
    secondary_muscles = [m.lower() for m in exercise.secondary_muscles]

    if muscle_lower in primary_muscles:
        return float(sets)
    elif muscle_lower in secondary_muscles:
        return sets * 0.5
    elif is_strength:
        # For strength: any lift sharing ANY muscle with the main lift = 0.5
        # (the main lift's muscles are the union of primary + secondary)
        return sets * 0.5
    return 0.0


def compute_weekly_volume_per_muscle(
    workouts: list,
    is_strength: bool = False,
) -> dict[str, float]:
    """
    Compute weekly volume per muscle group across all workouts in a microcycle.

    Uses fractional counting (Rule 2.5). Merges push/pull volumes per
    Rule 10.3 (horizontal + vertical = combined).

    Args:
      workouts: list of Workout objects
      is_strength: if True, use strength counting rules

    Returns dict: {muscle: fractional_sets_per_week}
    """
    volume: dict[str, float] = {}
    for w in workouts:
        for we in w.exercises:
            ex = we.exercise
            for muscle in ex.muscle_groups:
                muscle_lower = muscle.lower()
                volume[muscle_lower] = volume.get(muscle_lower, 0) + we.sets
            for muscle in ex.secondary_muscles:
                muscle_lower = muscle.lower()
                if muscle_lower not in [m.lower() for m in ex.muscle_groups]:
                    volume[muscle_lower] = volume.get(muscle_lower, 0) + we.sets * 0.5

    # Merge push/pull families per Rule 10.3
    # horizontal_push + vertical_push → combined "push" volume already counted
    # (we count by muscle, not by pattern, so this is automatically handled)
    return volume


def compute_session_volume_per_muscle(workout) -> dict[str, float]:
    """
    Compute per-muscle volume for a single workout session.

    Used to check the 11-set cap.
    """
    volume: dict[str, float] = {}
    for we in workout.exercises:
        ex = we.exercise
        for muscle in ex.muscle_groups:
            muscle_lower = muscle.lower()
            volume[muscle_lower] = volume.get(muscle_lower, 0) + we.sets
        for muscle in ex.secondary_muscles:
            muscle_lower = muscle.lower()
            if muscle_lower not in [m.lower() for m in ex.muscle_groups]:
                volume[muscle_lower] = volume.get(muscle_lower, 0) + we.sets * 0.5
    return volume


# === Volume recommendation by goal + tier + experience ===

def get_recommended_weekly_sets(
    muscle: str,
    goal: TrainingGoal,
    experience: TrainingStatus,
    tier: VolumeTier = VolumeTier.MEDIUM,
) -> int:
    """
    Get recommended weekly sets for a muscle based on goal + experience + tier.

    Combines RippedBody's volume landmarks (Table 7.3) with the
    time-budget tiers (Table 7.4).

    Logic:
      1. Get the muscle's MAV range from DEFAULT_MUSCLE_LANDMARKS
      2. Adjust by tier (MINIMAL → MAV_lo; VERY_HIGH → MAV_hi)
      3. Adjust by goal:
         - MAINTENANCE → 0.5–0.67 × MAV (Rule 2.4)
         - FAT_LOSS → 0.8 × MAV (preserve muscle)
         - STRENGTH → 0.7 × MAV (focus on main lifts, less accessory)
      4. Adjust by experience:
         - BEGINNER → MAV_lo × 0.8
         - NOVICE → MAV_lo
         - INTERMEDIATE → MAV midpoint
         - ADVANCED → MAV_hi
    """
    landmarks = get_muscle_landmarks(muscle)
    mav_lo, mav_hi = landmarks.mav_lo, landmarks.mav_hi

    # Tier adjustment
    tier_lo, tier_hi = TIER_SET_RANGES[tier]
    tier_multiplier = (tier_lo + tier_hi) / (mav_lo + mav_hi) if (mav_lo + mav_hi) > 0 else 1.0
    tier_multiplier = max(0.5, min(1.5, tier_multiplier))

    # Goal adjustment
    goal_multiplier = {
        TrainingGoal.HYPERTROPHY: 1.0,
        TrainingGoal.MUSCLE_GAIN: 1.0,
        TrainingGoal.RECOMP: 0.9,
        TrainingGoal.STRENGTH: 0.7,
        TrainingGoal.FAT_LOSS: 0.8,
        TrainingGoal.MAINTENANCE: 0.6,
        TrainingGoal.GENERAL_FITNESS: 0.7,
    }.get(goal, 0.8)

    # Experience adjustment
    exp_multiplier = {
        TrainingStatus.BEGINNER: 0.7,
        TrainingStatus.NOVICE: 0.85,
        TrainingStatus.INTERMEDIATE: 1.0,
        TrainingStatus.ADVANCED: 1.1,
    }.get(experience, 0.85)

    # Base MAV midpoint
    mav_mid = (mav_lo + mav_hi) / 2
    recommended = mav_mid * tier_multiplier * goal_multiplier * exp_multiplier
    return max(landmarks.mev, round(recommended))


# === Volume validation ===

def validate_weekly_volume(
    weekly_volume: dict[str, float],
    goal: TrainingGoal,
    experience: TrainingStatus,
    tier: VolumeTier = VolumeTier.MEDIUM,
) -> list[str]:
    """
    Validate weekly volume against RippedBody landmarks.

    Returns list of warning messages for muscles that are below MEV,
    above MRV, or otherwise outside the recommended range.
    """
    warnings: list[str] = []

    for muscle, sets in weekly_volume.items():
        landmarks = get_muscle_landmarks(muscle)
        recommended = get_recommended_weekly_sets(muscle, goal, experience, tier)

        if sets < landmarks.mev:
            warnings.append(
                f"⚠ {muscle} = {sets:.0f} sets/wk (below MEV of {landmarks.mev}). "
                "Insufficient stimulus for growth."
            )
        elif sets < recommended * 0.7:
            warnings.append(
                f"⚠ {muscle} = {sets:.0f} sets/wk (below recommended {recommended}). "
                "May limit progress."
            )
        elif sets > landmarks.mrv:
            warnings.append(
                f"⚠ {muscle} = {sets:.0f} sets/wk (above MRV of {landmarks.mrv}). "
                "Recovery likely compromised."
            )
        elif sets > recommended * 1.3:
            warnings.append(
                f"⚠ {muscle} = {sets:.0f} sets/wk (above recommended {recommended}). "
                "Consider reducing volume."
            )

    return warnings


# === Specialization cycles (Table 7.9) ===

@dataclass
class SpecializationConfig:
    """Configuration for a specialization mesocycle."""
    phase: str                          # "balanced" or "specialization"
    duration_weeks: tuple[int, int]     # (min, max)
    focus_muscles_sets: tuple[int, int]  # sets/wk for focus muscles
    other_muscles_sets: tuple[int, int]  # sets/wk for non-focus muscles


SPECIALIZATION_BALANCED = SpecializationConfig(
    phase="balanced",
    duration_weeks=(8, 12),
    focus_muscles_sets=(10, 20),
    other_muscles_sets=(10, 20),
)

SPECIALIZATION_FOCUS = SpecializationConfig(
    phase="specialization",
    duration_weeks=(8, 12),
    focus_muscles_sets=(20, 30),
    other_muscles_sets=(5, 15),
)


def get_specialization_program(
    focus_muscles: list[str],
) -> list[SpecializationConfig]:
    """
    Get the 3-mesocycle specialization program for advanced hypertrophy.

    Returns: [Balanced (8-12wk), Specialization (8-12wk), Balanced (8-12wk)]
    """
    return [
        SPECIALIZATION_BALANCED,
        SPECIALIZATION_FOCUS,
        SPECIALIZATION_BALANCED,
    ]


__all__ = [
    "VolumeTier",
    "TIER_SET_RANGES",
    "TIER_HOURS_RANGES",
    "MuscleVolumeLandmarks",
    "DEFAULT_MUSCLE_LANDMARKS",
    "get_muscle_landmarks",
    "StrengthLiftLandmarks",
    "STRENGTH_LIFT_LANDMARKS",
    "get_recommended_frequency",
    "PER_SESSION_SET_CAP",
    "check_session_volume_cap",
    "count_sets_toward_muscle",
    "compute_weekly_volume_per_muscle",
    "compute_session_volume_per_muscle",
    "get_recommended_weekly_sets",
    "validate_weekly_volume",
    "SpecializationConfig",
    "SPECIALIZATION_BALANCED",
    "SPECIALIZATION_FOCUS",
    "get_specialization_program",
]

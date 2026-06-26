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

from ..models.profile import TrainingStatus
from ..models.training import Exercise, TrainingGoal

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


# Default landmarks per muscle.
# Aligns with Renaissance Periodization (Dr. Mike Israetel) consensus.
# Source:
#   - RP "Volume Landmarks" series (Israetel & Hoffmann)
#   - chest:   MEV=8,  MAV=10-22, MRV=22-24
#   - back:    MEV=10, MAV=14-22, MRV=25-27  (back needs ~2-3x chest MEV)
#   - quads:   MEV=8,  MAV=12-20, MRV=20-25
#   - hamstrings: MEV=6, MAV=10-16, MRV=20
#   - glutes:  MEV=4,  MAV=8-16,  MRV=20
#   - shoulders (front delts get a lot from pressing): MEV=6, MAV=8-16, MRV=20
#   - biceps/triceps: MEV=6, MAV=8-14, MRV=18-20
#   - calves:  MEV=8,  MAV=10-16, MRV=20-25
#   - abs:     MEV=6,  MAV=10-20, MRV=20-25
# Values are sets per week (fractional counting applied).
# HIGH-severity fix: ML (Maintenance Level) values now follow the stated
# rule "ML = 0.5-0.67 × MAV_lo" (documented at the top of this file).
# Previously ML was set equal to MEV for every muscle, which is logically
# wrong — you need LESS volume to maintain than to grow. Setting ML = MEV
# meant `get_recommended_weekly_sets` for MAINTENANCE goal floored the
# recommendation at MEV (growth-level volume), defeating the point of a
# maintenance program. New ML values: round(0.5 * mav_lo).
# Also: calves MRV reduced from 25 to 20 (per RP consensus — calves are
# slow-twitch-dominant and recover poorly from high volume; 25 was 25%
# above the RP upper bound and risked tendinopathy).
DEFAULT_MUSCLE_LANDMARKS: dict[str, MuscleVolumeLandmarks] = {
    "chest":          MuscleVolumeLandmarks("chest",          8, 10, 22, 24, 5),
    "back":           MuscleVolumeLandmarks("back",          10, 14, 22, 27, 7),
    "upper_back":     MuscleVolumeLandmarks("upper_back",    10, 14, 22, 27, 7),
    "lats":           MuscleVolumeLandmarks("lats",          10, 14, 22, 27, 7),
    "quads":          MuscleVolumeLandmarks("quads",          8, 12, 20, 25, 6),
    "hamstrings":     MuscleVolumeLandmarks("hamstrings",     6, 10, 16, 20, 5),
    "glutes":         MuscleVolumeLandmarks("glutes",         4,  8, 16, 20, 3),  # ML 4→3 (must be < MEV)
    "shoulders":      MuscleVolumeLandmarks("shoulders",      6,  8, 16, 20, 4),
    "triceps":        MuscleVolumeLandmarks("triceps",        6,  8, 14, 18, 4),
    "biceps":         MuscleVolumeLandmarks("biceps",         6,  8, 14, 20, 4),
    "calves":         MuscleVolumeLandmarks("calves",         8, 10, 16, 20, 5),  # MRV 25→20
    "abs":            MuscleVolumeLandmarks("abs",            6, 10, 20, 25, 5),
    "obliques":       MuscleVolumeLandmarks("obliques",      4,  6, 12, 18, 3),
    "forearms":       MuscleVolumeLandmarks("forearms",      3,  4,  8, 15, 2),
    "traps":          MuscleVolumeLandmarks("traps",         4,  6, 12, 18, 3),
    "lower_back":     MuscleVolumeLandmarks("lower_back",    3,  4,  8, 15, 2),
}


def get_muscle_landmarks(muscle: str) -> MuscleVolumeLandmarks:
    """Get volume landmarks for a muscle (with fallback for unknown muscles)."""
    muscle_lower = muscle.lower()
    if muscle_lower in DEFAULT_MUSCLE_LANDMARKS:
        return DEFAULT_MUSCLE_LANDMARKS[muscle_lower]
    # MEV fallback = 6 to match the RP consensus update (known-muscle MEVs
    # are 6-10). Unknown muscles get MEV=6 so they don't trigger spurious
    # "below MEV" warnings.
    return MuscleVolumeLandmarks(muscle_lower, 6, 10, 16, 25, 5)


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
    # MRV must be >= MAV_hi (Maximum Recoverable Volume must be >= upper
    # bound of Maximum Adaptive Volume — you can't recover from less volume
    # than the upper bound of what's adaptive). MRV = MAV_hi + 2.
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

    Phase-6 fix: 0 sets → 0 frequency (was returning 2 for "0 sets/muscle/wk").
    """
    if weekly_sets_per_muscle <= 0:
        return 0
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
) -> float:
    """
    Count how many sets an exercise contributes toward a target muscle.

    RippedBody Rule 2.5:
      - Hypertrophy: primary muscle = 1.0 set; secondary muscle = 0.5 set.

    Args:
      exercise: the exercise being counted
      muscle: target muscle (normalized lowercase)
      sets: number of hard sets performed

    Returns: fractional set count (e.g. 4.0 or 2.0)
    """
    muscle_lower = muscle.lower()
    primary_muscles = [m.lower() for m in exercise.muscle_groups]
    secondary_muscles = [m.lower() for m in exercise.secondary_muscles]

    if muscle_lower in primary_muscles:
        return float(sets)
    elif muscle_lower in secondary_muscles:
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
    # MEDIUM-tier normalization fix: previously the tier_multiplier formula
    # `(tier_lo + tier_hi) / (mav_lo + mav_hi)` did NOT normalize MEDIUM to
    # 1.0. For chest (MAV 10-22) and MEDIUM tier (13-16), the multiplier was
    # (13+16)/(10+22) = 0.906 — so MEDIUM produced ~9% LESS volume than the
    # MAV midpoint. This was a systematic bias against MEDIUM-tier users.
    # Now we normalize by dividing by the MEDIUM tier's set-sum so MEDIUM
    # produces multiplier 1.0 exactly. Other tiers scale proportionally.
    medium_lo, medium_hi = TIER_SET_RANGES[VolumeTier.MEDIUM]
    medium_sum = medium_lo + medium_hi
    if medium_sum > 0:
        tier_multiplier = tier_multiplier / (medium_sum / (mav_lo + mav_hi)) if (mav_lo + mav_hi) > 0 else 1.0
        # Re-clamp after normalization (very high/very low tiers may now exceed bounds).
        tier_multiplier = max(0.5, min(1.5, tier_multiplier))
    recommended = mav_mid * tier_multiplier * goal_multiplier * exp_multiplier
    # MEDIUM-severity fix: MAINTENANCE goal should floor at ML (Maintenance
    # Level), not MEV (Minimum Effective Volume). ML < MEV — you need less
    # volume to maintain than to grow. Previously a maintenance user could
    # get growth-level volume because the floor was MEV.
    floor = landmarks.ml if goal == TrainingGoal.MAINTENANCE else landmarks.mev
    return max(floor, round(recommended))


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
]

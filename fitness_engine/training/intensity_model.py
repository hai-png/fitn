"""
RIR-based intensity model + warm-up generator + reactive deload.

Phase-4 (RippedBody-informed).

Replaces the single-RPE-per-category model with:
  - RIR (Reps In Reserve) ranges per (rep range × exercise intensity tier)
  - Exercise intensity tiers (Table 7.7):
      LOWER_FREE_WEIGHT_COMPOUND  (squat, deadlift, RDL, lunge, OHP, bench, row)
      MACHINE_OR_UPPER_PRESS      (leg press, machine press, machine row, push-up)
      MACHINE_PRESS_OR_PULL       (cable press, cable row, pulldown, dip)
      ISOLATION                   (curls, extensions, raises, flyes, calves)

  - Warm-up set generator (Table 7.18):
      LEQ_6_REP recipe  (for sets of ≤6 reps)
      GEQ_6_REP recipe  (for sets of ≥6 reps)

  - Reactive deload (Rule 8.1–8.3):
      5-question self-assessment → ≥2 Yes triggers deload
      Deload recipe: -30 to -50% sets, intensity unchanged

Source: /home/z/my-project/fitn/reports/rippedbody_insights.md
        Section 6 (RIR), Section 8 (Deload), Section 15 (Warm-up)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ..models.training import Exercise, ExerciseCategory, Workout, WorkoutExercise
from .exercise_categorization import get_movement_pattern


# === Exercise intensity tiers (Table 7.7) ===

class ExerciseIntensityTier(str, Enum):
    """RippedBody's 4 intensity tiers for RIR prescription."""
    LOWER_FREE_WEIGHT_COMPOUND = "lower_free_weight_compound"
    MACHINE_OR_UPPER_PRESS = "machine_or_upper_press"
    MACHINE_PRESS_OR_PULL = "machine_press_or_pull"
    ISOLATION = "isolation"


# === Tier detection ===

def get_exercise_intensity_tier(exercise: Exercise) -> ExerciseIntensityTier:
    """
    Determine the exercise intensity tier (Table 7.7).

    Rules:
      - LOWER_FREE_WEIGHT_COMPOUND: barbell squats, deadlifts, RDLs, lunges,
        OHP, bench press, bent-over rows (free-weight compound)
      - MACHINE_OR_UPPER_PRESS: machine leg press, machine chest press,
        machine shoulder press, push-ups
      - MACHINE_PRESS_OR_PULL: cable press, cable row, pulldown, dip
      - ISOLATION: curls, extensions, raises, flyes, calf raises, core
    """
    pattern = get_movement_pattern(exercise)
    equipment = exercise.equipment.lower()
    mechanics = (exercise.mechanics or "").lower()
    category = exercise.category

    # Isolation patterns
    isolation_patterns = {
        "knee_flexion", "knee_extension", "ankle_plantarflexion",
        "elbow_flexion", "elbow_extension", "lateral_raise",
        "rear_delt", "front_raise", "chest_fly", "hammer_curl",
        "preacher_curl", "overhead_tricep", "tricep_dip",
        "core_anti_extension", "core_anti_rotation", "core_flexion",
        "hip_flexion",
    }
    if pattern in isolation_patterns or category == ExerciseCategory.ACCESSORY:
        return ExerciseIntensityTier.ISOLATION

    # Free-weight compounds (LOWER_FREE_WEIGHT_COMPOUND)
    free_weight_compound_patterns = {
        "squat", "front_squat", "hinge", "romanian_deadlift",
        "lunge", "single_leg", "hip_thrust",
        "horizontal_push", "vertical_push",
        "horizontal_pull", "pendlay_row", "vertical_pull",
    }
    if (pattern in free_weight_compound_patterns
            and equipment in {"barbell", "dumbbell", "kettlebell", "trap_bar", "bodyweight"}
            and mechanics == "compound"):
        return ExerciseIntensityTier.LOWER_FREE_WEIGHT_COMPOUND

    # Machine compounds (MACHINE_OR_UPPER_PRESS)
    if equipment == "machine" and pattern in {
        "leg_press", "horizontal_push", "vertical_push", "incline_push",
    }:
        return ExerciseIntensityTier.MACHINE_OR_UPPER_PRESS

    # Push-up (bodyweight compound push)
    if pattern == "push_up":
        return ExerciseIntensityTier.MACHINE_OR_UPPER_PRESS

    # Cable / machine press or pull
    if equipment in {"cable", "machine"} and pattern in {
        "horizontal_pull", "chest_supported_row", "seated_row",
        "vertical_pull",
    }:
        return ExerciseIntensityTier.MACHINE_PRESS_OR_PULL

    # Dips
    if pattern == "chest_dip":
        return ExerciseIntensityTier.MACHINE_PRESS_OR_PULL

    # Default: isolation
    return ExerciseIntensityTier.ISOLATION


# === RIR table (Table 7.7) ===
# RIR targets by (rep range, intensity tier)
# Format: {tier: {(rep_lo, rep_hi): (rir_lo, rir_hi)}}

RIR_TABLE: dict[ExerciseIntensityTier, dict[tuple[int, int], tuple[int, int]]] = {
    ExerciseIntensityTier.LOWER_FREE_WEIGHT_COMPOUND: {
        (1, 3):  (0, 1),    # very heavy: 0-1 RIR
        (4, 6):  (1, 3),    # heavy: 1-3 RIR
        (7, 10): (2, 4),    # moderate: 2-4 RIR
        (11, 20): (3, 5),   # light: 3-5 RIR
    },
    ExerciseIntensityTier.MACHINE_OR_UPPER_PRESS: {
        (1, 3):  (0, 2),
        (4, 6):  (1, 3),
        (7, 10): (2, 4),
        (11, 20): (3, 5),
    },
    ExerciseIntensityTier.MACHINE_PRESS_OR_PULL: {
        (1, 3):  (1, 3),
        (4, 6):  (2, 4),
        (7, 10): (2, 4),
        (11, 20): (3, 5),
    },
    ExerciseIntensityTier.ISOLATION: {
        (1, 3):  (1, 3),    # rarely done at 1-3 reps, but if so
        (4, 6):  (2, 4),
        (7, 10): (2, 4),
        (11, 20): (3, 5),
        (21, 50): (4, 6),   # very high rep: 4-6 RIR
    },
}


def get_rir_range(
    exercise: Exercise,
    reps_lo: int,
    reps_hi: int,
) -> tuple[int, int]:
    """
    Get the RIR range for an exercise at a given rep range.

    Uses the exercise's intensity tier + the rep range to look up
    the appropriate RIR range from RIR_TABLE.

    Returns (rir_lo, rir_hi) tuple.
    """
    tier = get_exercise_intensity_tier(exercise)
    tier_table = RIR_TABLE.get(tier, RIR_TABLE[ExerciseIntensityTier.ISOLATION])

    # Find the rep range that contains reps_hi (the top of the target range)
    for (lo, hi), rir_range in tier_table.items():
        if lo <= reps_hi <= hi:
            return rir_range

    # Fallback: use the highest rep range
    last_range = list(tier_table.values())[-1]
    return last_range


def rir_to_rpe(rir: int, reps: int) -> float:
    """
    Convert RIR to RPE.

    RPE = 10 - RIR (standard conversion).

    Tier 5.65 fix: removed the `reps > 12 → cap RPE at 8` logic. The original
    rationale ("high-rep sets feel harder than RPE suggests") was backwards —
    capping at 8 systematically under-reports intensity for high-rep sets
    taken to failure. A 20-rep squat set at RIR 0 is RPE 10, not RPE 8.
    RIR-based RPE is unreliable above ~12 reps (cardio-respiratory failure
    vs. muscular failure), but the fix is to document that caveat, not to
    silently cap. Now we return the true RPE = 10 - RIR for all rep ranges.
    """
    rpe = 10.0 - rir
    return max(4.0, min(10.0, rpe))


def rpe_to_rir(rpe: float, reps: int) -> int:
    """Convert RPE to RIR.

    Tier 5.65 fix: removed the high-rep cap (was min(rpe, 8.0) for reps > 12)
    for the same reason as rir_to_rpe — it under-reported intensity.
    """
    return max(0, int(round(10 - rpe)))


# === Warm-up set generator (Table 7.18) ===

@dataclass
class WarmUpSet:
    """A single warm-up set."""
    set_number: int
    reps: str
    percentage_1rm: float       # 0.0-1.0
    rest_sec: int = 90


# Two recipes from Table 7.18
WARMUP_LEQ_6_REP = [
    # For target sets of ≤6 reps
    WarmUpSet(1, "5-10", 0.40, 90),    # optional, 40% 1RM
    WarmUpSet(2, "3-5",  0.60, 90),    # 60% 1RM
    WarmUpSet(3, "1-3",  0.80, 90),    # 80% 1RM
    WarmUpSet(4, "1",    0.90, 90),    # 90% 1RM
]

WARMUP_GEQ_6_REP = [
    # For target sets of ≥6 reps
    WarmUpSet(1, "5-10", 0.40, 90),    # optional, 40% 1RM
    WarmUpSet(2, "4-6",  0.60, 90),    # 60% 1RM
    WarmUpSet(3, "2-4",  0.80, 90),    # 80% 1RM
    WarmUpSet(4, "1-2",  0.875, 90),   # 85-90% 1RM (optional PAPE)
]


def generate_warmup_sets(
    target_reps: int,
    include_optional: bool = True,
) -> list[WarmUpSet]:
    """
    Generate warm-up sets for a working set with the given target reps.

    Uses LEQ_6_REP recipe for targets ≤6 reps, GEQ_6_REP for ≥6 reps.
    The first set (40% 1RM) is optional — included only if include_optional=True.
    """
    recipe = WARMUP_LEQ_6_REP if target_reps <= 6 else WARMUP_GEQ_6_REP
    if not include_optional:
        # Skip the first (40%) set
        recipe = recipe[1:]
    return list(recipe)


def generate_warmup_for_workout(workout: Workout) -> dict[str, list[WarmUpSet]]:
    """
    Generate warm-up sets for the first exercise of each muscle group in a workout.

    RippedBody Rule 15.2:
      - Full ascending warm-up on the first exercise of each muscle group
      - One familiarization set on subsequent free-weight exercises
      - Zero warm-up on machine exercises for already-warmed muscles
    """
    warmup_map: dict[str, list[WarmUpSet]] = {}
    seen_muscles: set[str] = set()

    for we in workout.exercises:
        ex = we.exercise
        primary_muscle = ex.muscle_groups[0].lower() if ex.muscle_groups else "unknown"

        if primary_muscle in seen_muscles:
            continue  # already warmed
        seen_muscles.add(primary_muscle)

        # Parse target reps
        try:
            reps_lo, reps_hi = (int(x) for x in we.reps.split("-"))
            target_reps = reps_hi
        except (ValueError, AttributeError):
            target_reps = 8  # default

        warmup_map[ex.name] = generate_warmup_sets(target_reps, include_optional=True)

    return warmup_map


# === Reactive deload (Rule 8.1–8.3) ===

# 5-question self-assessment (Rule 8.2)
REACTIVE_DELOAD_QUESTIONS = [
    "Are you dreading going to the gym?",
    "Are your lifts going backward or stagnating for 2+ weeks?",
    "Are you experiencing unusual joint pain or persistent muscle soreness?",
    "Are you sleeping poorly or feeling chronically fatigued?",
    "Has your motivation dropped significantly compared to baseline?",
]


def should_deload(answers: list[bool]) -> bool:
    """
    Determine if a deload is needed based on the 5-question self-assessment.

    Rule 8.2: ≥2 "Yes" answers → deload.
    """
    return sum(1 for a in answers if a) >= 2


def apply_deload(workout: Workout, volume_reduction_pct: float = 0.4) -> Workout:
    """
    Apply a reactive deload to a workout.

    Rule 8.3:
      - Reduce volume by 30-50% (default 40%)
      - Maintain intensity (RPE/RIR unchanged)
      - Maintain exercise selection

    Args:
      workout: the workout to deload
      volume_reduction_pct: fraction of sets to remove (0.3-0.5)

    Returns new Workout with reduced sets (mutates exercises in place).
    """
    for we in workout.exercises:
        # Round to nearest int, minimum 2 sets
        new_sets = max(2, round(we.sets * (1 - volume_reduction_pct)))
        we.sets = new_sets
        if "deload" not in (we.notes or "").lower():
            we.notes = (we.notes or "") + " [deload: -40% volume, intensity maintained]"
    if "Deload" not in workout.name:
        workout.name = workout.name + " (Deload)"
    workout.notes = (workout.notes or "") + " Reactive deload: -40% sets, RPE unchanged."
    return workout


# === Strength block phases (Tables 7.11–7.13) ===

class StrengthPhase(str, Enum):
    """RippedBody's 3 strength block phases."""
    VOLUME = "volume"        # Build muscle; maintain/build strength
    LOAD = "load"            # Build strength; maintain/build muscle
    PEAK = "peak"            # Peak strength; maintain muscle


@dataclass
class StrengthPhaseSpec:
    """Specification for a strength block phase."""
    phase: StrengthPhase
    duration_weeks: tuple[int, int]
    main_lift_singles_per_week: tuple[int, int]    # (min, max)
    main_lift_rpe_range: tuple[float, float]       # (start_rpe, end_rpe)
    main_lift_rir_range: tuple[int, int]           # (start_rir, end_rir)
    backoff_sets_per_single: tuple[int, int]
    backoff_rpe_range: tuple[float, float]
    backoff_reps: tuple[int, int]
    secondary_sets_per_week: tuple[int, int]
    secondary_reps: tuple[int, int]
    secondary_rir: tuple[int, int]
    description: str


STRENGTH_PHASE_SPECS: dict[StrengthPhase, StrengthPhaseSpec] = {
    StrengthPhase.VOLUME: StrengthPhaseSpec(
        phase=StrengthPhase.VOLUME,
        duration_weeks=(6, 12),
        main_lift_singles_per_week=(1, 3),
        main_lift_rpe_range=(5.0, 8.0),
        main_lift_rir_range=(5, 2),
        backoff_sets_per_single=(0, 0),  # no back-off in volume phase
        backoff_rpe_range=(0, 0),
        backoff_reps=(0, 0),
        secondary_sets_per_week=(10, 20),
        secondary_reps=(6, 20),
        secondary_rir=(0, 3),
        description="Build muscle; maintain or build strength. "
                    "1-3 singles/lift/wk at RPE 5→8, 10-20 secondary sets at 0-3 RIR.",
    ),
    StrengthPhase.LOAD: StrengthPhaseSpec(
        phase=StrengthPhase.LOAD,
        duration_weeks=(4, 8),
        main_lift_singles_per_week=(2, 4),
        main_lift_rpe_range=(6.0, 9.0),
        main_lift_rir_range=(4, 1),
        backoff_sets_per_single=(2, 2),  # 2 back-off sets per single
        backoff_rpe_range=(5.0, 8.0),
        backoff_reps=(5, 3),  # progress from 5 to 3 reps (~80-85% 1RM)
        secondary_sets_per_week=(5, 10),
        secondary_reps=(6, 20),
        secondary_rir=(0, 3),
        description="Build strength; maintain/build muscle. "
                    "2-4 singles/lift/wk at RPE 6→9, 2 back-off sets at 5-8 RPE, "
                    "5-10 secondary sets tapering -1 to -2 sets every 1-2 weeks.",
    ),
    StrengthPhase.PEAK: StrengthPhaseSpec(
        phase=StrengthPhase.PEAK,
        duration_weeks=(2, 4),
        main_lift_singles_per_week=(2, 5),
        main_lift_rpe_range=(7.0, 10.0),
        main_lift_rir_range=(3, 0),
        backoff_sets_per_single=(0, 3),
        backoff_rpe_range=(5.0, 8.0),
        backoff_reps=(4, 2),  # progress from 4 to 2 reps (~85% 1RM)
        secondary_sets_per_week=(0, 4),
        secondary_reps=(6, 20),
        secondary_rir=(0, 3),
        description="Peak strength; maintain muscle. "
                    "2-5 singles/lift/wk at RPE 7→10, 0-3 back-off sets at 5-8 RPE, "
                    "0-4 secondary sets. Decrease back-off + secondary weekly.",
    ),
}


def get_peak_phase_duration(prior_phase_weeks: int) -> int:
    """
    Get the peak phase duration based on prior phase length.

    Rule 11.3:
      - prior 10-12 wks → 2-week peak
      - prior 13-15 wks → 3-week peak
      - prior 16+ wks → 4-week peak
    """
    if prior_phase_weeks <= 12:
        return 2
    elif prior_phase_weeks <= 15:
        return 3
    else:
        return 4


__all__ = [
    "ExerciseIntensityTier",
    "get_exercise_intensity_tier",
    "RIR_TABLE",
    "get_rir_range",
    "rir_to_rpe",
    "rpe_to_rir",
    "WarmUpSet",
    "WARMUP_LEQ_6_REP",
    "WARMUP_GEQ_6_REP",
    "generate_warmup_sets",
    "generate_warmup_for_workout",
    "REACTIVE_DELOAD_QUESTIONS",
    "should_deload",
    "apply_deload",
    "StrengthPhase",
    "StrengthPhaseSpec",
    "STRENGTH_PHASE_SPECS",
    "get_peak_phase_duration",
]

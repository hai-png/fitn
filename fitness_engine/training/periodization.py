"""
Periodization — applies rep / rest / RPE targets based on TrainingGoal
and ProgressionScheme.

This module is the single source of truth for "how many reps should a
compound primary get on a heavy hypertrophy day?" etc.

Three layering axes:
  1. TrainingGoal → base rep/rest/RPE per category
  2. ProgressionScheme → modifies by day_type (heavy/moderate/light)
  3. Deload week → reduces volume by ~40% (drop 1 set per exercise)

Outputs are applied to WorkoutExercise objects (sets, reps, rest_sec, rpe_target).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..models.training import (
    ExerciseCategory,
    ProgressionScheme,
    TrainingGoal,
    Workout,
    WorkoutExercise,
)
# Phase-6 cleanup: hoisted from inside ``apply_periodization`` (per-exercise
# loop) and from ``get_mesocycle_length`` / ``get_program_duration_weeks``.
from .intensity_model import get_rir_range, rir_to_rpe
from ..models.profile import TrainingStatus


# === Goal-based presets (rep / rest / RPE per category) ===

@dataclass
class Preset:
    reps: str
    rest_sec: int
    rpe: float


# Default presets per (goal, category)
_GOAL_PRESETS: dict[TrainingGoal, dict[ExerciseCategory, Preset]] = {
    TrainingGoal.STRENGTH: {
        ExerciseCategory.COMPOUND_PRIMARY:   Preset("3-6",   240, 8.5),
        ExerciseCategory.COMPOUND_SECONDARY: Preset("5-8",   180, 8.0),
        ExerciseCategory.ACCESSORY:           Preset("8-12",  90, 7.0),
        ExerciseCategory.ISOLATION:           Preset("10-15", 60, 6.5),
        ExerciseCategory.CARDIO:              Preset("20-45 min", 0, 5.0),
        ExerciseCategory.MOBILITY:            Preset("30-60 sec", 30, 4.0),
    },
    TrainingGoal.HYPERTROPHY: {
        ExerciseCategory.COMPOUND_PRIMARY:   Preset("5-8",   180, 8.0),
        ExerciseCategory.COMPOUND_SECONDARY: Preset("8-12",  120, 7.0),
        ExerciseCategory.ACCESSORY:           Preset("10-15", 60, 6.0),
        ExerciseCategory.ISOLATION:           Preset("12-15", 60, 6.0),
        ExerciseCategory.CARDIO:              Preset("20-30 min", 0, 5.0),
        ExerciseCategory.MOBILITY:            Preset("30-60 sec", 30, 4.0),
    },
    TrainingGoal.MUSCLE_GAIN: {  # same as hypertrophy
        ExerciseCategory.COMPOUND_PRIMARY:   Preset("5-8",   180, 8.0),
        ExerciseCategory.COMPOUND_SECONDARY: Preset("8-12",  120, 7.0),
        ExerciseCategory.ACCESSORY:           Preset("10-15", 60, 6.0),
        ExerciseCategory.ISOLATION:           Preset("12-15", 60, 6.0),
        ExerciseCategory.CARDIO:              Preset("20-30 min", 0, 5.0),
        ExerciseCategory.MOBILITY:            Preset("30-60 sec", 30, 4.0),
    },
    TrainingGoal.RECOMP: {  # same as hypertrophy
        ExerciseCategory.COMPOUND_PRIMARY:   Preset("5-8",   180, 8.0),
        ExerciseCategory.COMPOUND_SECONDARY: Preset("8-12",  120, 7.0),
        ExerciseCategory.ACCESSORY:           Preset("10-15", 60, 6.0),
        ExerciseCategory.ISOLATION:           Preset("12-15", 60, 6.0),
        ExerciseCategory.CARDIO:              Preset("20-30 min", 0, 5.0),
        ExerciseCategory.MOBILITY:            Preset("30-60 sec", 30, 4.0),
    },
    TrainingGoal.FAT_LOSS: {  # hypertrophy-ish with shorter rest for calorie burn
        ExerciseCategory.COMPOUND_PRIMARY:   Preset("6-10",  120, 7.5),
        ExerciseCategory.COMPOUND_SECONDARY: Preset("8-12",   90, 7.0),
        ExerciseCategory.ACCESSORY:           Preset("12-20", 45, 6.0),
        ExerciseCategory.ISOLATION:           Preset("12-20", 45, 6.0),
        ExerciseCategory.CARDIO:              Preset("20-45 min", 0, 5.0),
        ExerciseCategory.MOBILITY:            Preset("30-60 sec", 30, 4.0),
    },
    TrainingGoal.GENERAL_FITNESS: {
        ExerciseCategory.COMPOUND_PRIMARY:   Preset("8-12",  120, 7.0),
        ExerciseCategory.COMPOUND_SECONDARY: Preset("10-15",  90, 6.5),
        ExerciseCategory.ACCESSORY:           Preset("12-20", 60, 6.0),
        ExerciseCategory.ISOLATION:           Preset("12-20", 60, 5.5),
        ExerciseCategory.CARDIO:              Preset("20-45 min", 0, 5.0),
        ExerciseCategory.MOBILITY:            Preset("30-60 sec", 30, 4.0),
    },
    TrainingGoal.MAINTENANCE: {
        ExerciseCategory.COMPOUND_PRIMARY:   Preset("6-10",  150, 7.0),
        ExerciseCategory.COMPOUND_SECONDARY: Preset("8-12",  120, 6.5),
        ExerciseCategory.ACCESSORY:           Preset("10-15", 60, 6.0),
        ExerciseCategory.ISOLATION:           Preset("12-15", 60, 5.5),
        ExerciseCategory.CARDIO:              Preset("20-30 min", 0, 5.0),
        ExerciseCategory.MOBILITY:            Preset("30-60 sec", 30, 4.0),
    },
}


# === DUP day-type modifiers ===
# Daily Undulating Periodization rotates heavy/moderate/light days.
# Modifiers are applied on top of the goal-based preset.

_DUP_DAY_MODIFIERS: dict[str, dict[str, float]] = {
    # day_type → {reps multiplier (lower bound, upper bound), rpe_delta, rest_multiplier}
    "heavy":    {"reps_lo_mult": 0.5, "reps_hi_mult": 0.7, "rpe_delta": +0.5, "rest_mult": 1.5},
    "moderate": {"reps_lo_mult": 1.0, "reps_hi_mult": 1.0, "rpe_delta":  0.0, "rest_mult": 1.0},
    "light":    {"reps_lo_mult": 1.5, "reps_hi_mult": 1.8, "rpe_delta": -1.0, "rest_mult": 0.6},
}


def _modify_reps_for_dup(base_reps: str, day_type: str) -> str:
    """Apply DUP day-type modifier to a rep range like '5-8'."""
    if day_type not in _DUP_DAY_MODIFIERS or "-" not in base_reps:
        return base_reps
    try:
        lo, hi = (int(x) for x in base_reps.split("-"))
    except ValueError:
        return base_reps
    mod = _DUP_DAY_MODIFIERS[day_type]
    new_lo = max(1, round(lo * mod["reps_lo_mult"]))
    new_hi = max(new_lo + 1, round(hi * mod["reps_hi_mult"]))
    return f"{new_lo}-{new_hi}"


def _modify_rpe_for_dup(base_rpe: float, day_type: str) -> float:
    if day_type not in _DUP_DAY_MODIFIERS:
        return base_rpe
    delta = _DUP_DAY_MODIFIERS[day_type]["rpe_delta"]
    return max(4.0, min(10.0, base_rpe + delta))


def _modify_rest_for_dup(base_rest: int, day_type: str) -> int:
    if day_type not in _DUP_DAY_MODIFIERS:
        return base_rest
    mult = _DUP_DAY_MODIFIERS[day_type]["rest_mult"]
    return max(30, round(base_rest * mult))


# === Block periodization phase modifiers ===
# Block periodization has 3 phases: accumulation → intensification → deload/peak
# The architect decides which mesocycle is in which phase, then applies these.

_BLOCK_PHASE_MODIFIERS: dict[str, dict] = {
    "accumulation":  {"reps_mult": 1.2, "sets_delta": +1, "rpe_delta": -0.5},  # more volume, lower intensity
    "intensification": {"reps_mult": 0.6, "sets_delta": -1, "rpe_delta": +1.0},  # less volume, higher intensity
    "deload":        {"reps_mult": 1.0, "sets_delta": -1, "rpe_delta": -2.0},  # deload week
}


# === Main application function ===

def apply_periodization(
    workout: Workout,
    goal: TrainingGoal,
    progression: ProgressionScheme,
    day_type: str | None = None,
    block_phase: str | None = None,
    is_deload: bool = False,
) -> Workout:
    """
    Apply periodization rules to every exercise in a workout.

    Mutates the workout's exercises in-place: sets, reps, rest_sec, rpe_target.

    Layering:
      1. Base preset (from goal + exercise category)
      2. DUP day-type modifier (if progression == DUP and day_type is set)
      3. Block phase modifier (if progression == BLOCK and block_phase is set)
      4. Deload week volume reduction (if is_deload)

    Returns the same workout (for chaining).
    """
    presets = _GOAL_PRESETS.get(goal, _GOAL_PRESETS[TrainingGoal.HYPERTROPHY])

    for we in workout.exercises:
        category = we.exercise.category
        preset = presets.get(category, presets[ExerciseCategory.ACCESSORY])

        reps = preset.reps
        rest = preset.rest_sec
        rpe = preset.rpe
        sets = we.sets  # start from slot's default

        # Layer 2: DUP day-type modifier
        if progression == ProgressionScheme.DUP and day_type:
            reps = _modify_reps_for_dup(reps, day_type)
            rpe = _modify_rpe_for_dup(rpe, day_type)
            rest = _modify_rest_for_dup(rest, day_type)

        # Layer 3: Block phase modifier
        if progression == ProgressionScheme.BLOCK and block_phase:
            mod = _BLOCK_PHASE_MODIFIERS.get(block_phase)
            if mod:
                # Apply reps multiplier
                if "-" in reps:
                    try:
                        lo, hi = (int(x) for x in reps.split("-"))
                        lo = max(1, round(lo * mod["reps_mult"]))
                        hi = max(lo + 1, round(hi * mod["reps_mult"]))
                        reps = f"{lo}-{hi}"
                    except ValueError:
                        pass
                sets = max(2, sets + mod["sets_delta"])
                rpe = max(4.0, min(10.0, rpe + mod["rpe_delta"]))

        # Layer 4: Deload week — reduce VOLUME, MAINTAIN INTENSITY.
        # Phase-6 fix: previously this was a flat `sets - 1` which netted to 0
        # change inside an accumulation mesocycle (block +1, deload -1 = 0).
        # Now we apply a multiplicative -40% volume reduction (RippedBody
        # Rule 8.3 spec, intensity_model.apply_deload recipe) computed from
        # the post-block-modifier value. RPE is unchanged (intensity maintained).
        if is_deload:
            sets = max(2, round(sets * 0.6))
            # rpe unchanged — intensity maintained per RippedBody deload protocol

        # Layer 5 (Phase-6 fix): RIR clamp — moved AFTER DUP/block/deload
        # modifications so it operates on the FINAL rep range. Previously
        # the clamp used the preset reps (e.g. "5-8") and then DUP transformed
        # reps to "3-6" for heavy days, leaving RPE clamped against the wrong
        # rep range (RPE 6-8 instead of the correct RPE 7-9 for 3-6 reps on
        # a heavy compound).
        try:
            # Phase-6 cleanup: ``get_rir_range`` / ``rir_to_rpe`` now imported
            # at module top.
            # Parse the FINAL rep range (post-DUP, post-block) for the clamp.
            if "-" in reps and not reps.endswith("min") and not reps.endswith("sec"):
                parts = reps.split("-")
                reps_lo = int(parts[0])
                reps_hi = int(parts[-1])
                rir_lo, rir_hi = get_rir_range(we.exercise, reps_lo, reps_hi)
                # Convert RIR range to RPE range (RPE = 10 - RIR)
                rir_based_rpe_hi = rir_to_rpe(rir_lo, reps_hi)
                rir_based_rpe_lo = rir_to_rpe(rir_hi, reps_hi)
                # Clamp the (possibly DUP-/block-modified) RPE to the RIR-based
                # range so heavy compounds aren't prescribed above RPE 9.
                if rpe > rir_based_rpe_hi:
                    rpe = rir_based_rpe_hi
                elif rpe < rir_based_rpe_lo:
                    rpe = rir_based_rpe_lo
        except (ValueError, TypeError):
            # If RIR lookup fails (e.g. cardio/mobility reps), keep preset RPE.
            # Phase-6: narrowed from bare `Exception` to avoid masking real bugs.
            pass

        we.reps = reps
        we.rest_sec = rest
        we.rpe_target = round(rpe, 1)
        we.sets = sets

    return workout


# === Mesocycle / program duration rules ===

def get_mesocycle_length(experience) -> int:
    """Return the recommended mesocycle length (in weeks, including deload)."""
    # Phase-6 cleanup: ``TrainingStatus`` now imported at module top.
    return {
        TrainingStatus.BEGINNER: 4,        # 3 acc + 1 deload
        TrainingStatus.NOVICE: 4,          # 3 acc + 1 deload
        TrainingStatus.INTERMEDIATE: 5,    # 4 acc + 1 deload (DUP)
        TrainingStatus.ADVANCED: 6,        # 5 acc + 1 deload (block)
    }.get(experience, 4)


def get_program_duration_weeks(
    experience,
    goal: TrainingGoal,
) -> int:
    """
    Return the total program duration in weeks.

    Beginner:     4-8 weeks (1-2 mesocycles)
    Novice:       8-12 weeks (2 mesocycles)
    Intermediate: 10-12 weeks (2 mesocycles)
    Advanced:     12-16 weeks (2-3 mesocycles — block periodization)
    """
    # Phase-6 cleanup: ``TrainingStatus`` now imported at module top.
    base = {
        TrainingStatus.BEGINNER: 4,        # 1 mesocycle
        TrainingStatus.NOVICE: 8,          # 2 mesocycles
        TrainingStatus.INTERMEDIATE: 10,   # 2 mesocycles
        TrainingStatus.ADVANCED: 12,       # 2 mesocycles (block)
    }.get(experience, 8)

    # Strength programs run longer (more mesocycles for peak)
    if goal == TrainingGoal.STRENGTH and experience in (TrainingStatus.INTERMEDIATE, TrainingStatus.ADVANCED):
        base = max(base, 12)

    return base


def get_block_phases_for_program(
    num_mesocycles: int,
) -> list[str]:
    """
    Return the block-phase labels for each mesocycle in a BLOCK-periodized program.

    For 1 mesocycle: ['accumulation']
    For 2 mesocycles: ['accumulation', 'intensification']
    For 3 mesocycles: ['accumulation', 'intensification', 'peak']
    """
    if num_mesocycles <= 1:
        return ["accumulation"]
    if num_mesocycles == 2:
        return ["accumulation", "intensification"]
    return ["accumulation", "intensification", "peak"]


__all__ = [
    "Preset",
    "apply_periodization",
    "get_mesocycle_length",
    "get_program_duration_weeks",
    "get_block_phases_for_program",
]

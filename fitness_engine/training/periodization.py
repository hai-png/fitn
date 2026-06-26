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

from ..models.profile import TrainingStatus
from ..models.training import (
    ExerciseCategory,
    ProgressionScheme,
    TrainingGoal,
    Workout,
)
from .intensity_model import get_rir_range, rir_to_rpe

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
        ExerciseCategory.CARDIO:              Preset("20-45 min", 0, 5.0),
        ExerciseCategory.MOBILITY:            Preset("30-60 sec", 30, 4.0),
    },
    TrainingGoal.HYPERTROPHY: {
        ExerciseCategory.COMPOUND_PRIMARY:   Preset("5-8",   180, 8.0),
        ExerciseCategory.COMPOUND_SECONDARY: Preset("8-12",  120, 7.0),
        ExerciseCategory.ACCESSORY:           Preset("10-15", 60, 6.0),
        ExerciseCategory.CARDIO:              Preset("20-30 min", 0, 5.0),
        ExerciseCategory.MOBILITY:            Preset("30-60 sec", 30, 4.0),
    },
    TrainingGoal.MUSCLE_GAIN: {  # same as hypertrophy
        ExerciseCategory.COMPOUND_PRIMARY:   Preset("5-8",   180, 8.0),
        ExerciseCategory.COMPOUND_SECONDARY: Preset("8-12",  120, 7.0),
        ExerciseCategory.ACCESSORY:           Preset("10-15", 60, 6.0),
        ExerciseCategory.CARDIO:              Preset("20-30 min", 0, 5.0),
        ExerciseCategory.MOBILITY:            Preset("30-60 sec", 30, 4.0),
    },
    TrainingGoal.RECOMP: {  # same as hypertrophy
        ExerciseCategory.COMPOUND_PRIMARY:   Preset("5-8",   180, 8.0),
        ExerciseCategory.COMPOUND_SECONDARY: Preset("8-12",  120, 7.0),
        ExerciseCategory.ACCESSORY:           Preset("10-15", 60, 6.0),
        ExerciseCategory.CARDIO:              Preset("20-30 min", 0, 5.0),
        ExerciseCategory.MOBILITY:            Preset("30-60 sec", 30, 4.0),
    },
    TrainingGoal.FAT_LOSS: {  # hypertrophy-ish with shorter rest for calorie burn
        ExerciseCategory.COMPOUND_PRIMARY:   Preset("6-10",  120, 7.5),
        ExerciseCategory.COMPOUND_SECONDARY: Preset("8-12",   90, 7.0),
        ExerciseCategory.ACCESSORY:           Preset("12-20", 45, 6.0),
        ExerciseCategory.CARDIO:              Preset("20-45 min", 0, 5.0),
        ExerciseCategory.MOBILITY:            Preset("30-60 sec", 30, 4.0),
    },
    TrainingGoal.GENERAL_FITNESS: {
        ExerciseCategory.COMPOUND_PRIMARY:   Preset("8-12",  120, 7.0),
        ExerciseCategory.COMPOUND_SECONDARY: Preset("10-15",  90, 6.5),
        ExerciseCategory.ACCESSORY:           Preset("12-20", 60, 6.0),
        ExerciseCategory.CARDIO:              Preset("20-45 min", 0, 5.0),
        ExerciseCategory.MOBILITY:            Preset("30-60 sec", 30, 4.0),
    },
    TrainingGoal.MAINTENANCE: {
        ExerciseCategory.COMPOUND_PRIMARY:   Preset("6-10",  150, 7.0),
        ExerciseCategory.COMPOUND_SECONDARY: Preset("8-12",  120, 6.5),
        ExerciseCategory.ACCESSORY:           Preset("10-15", 60, 6.0),
        ExerciseCategory.CARDIO:              Preset("20-30 min", 0, 5.0),
        ExerciseCategory.MOBILITY:            Preset("30-60 sec", 30, 4.0),
    },
}


# === DUP day-type modifiers ===
# Daily Undulating Periodization rotates heavy/moderate/light days.
# Modifiers are applied on top of the goal-based preset.
#
# CRITICAL FIX: the previous multipliers (`heavy: 0.5/0.7`) were applied
# uniformly across all goals. For HYPERTROPHY (base preset "5-8"), heavy day
# produced reps `round(5*0.5)=2` to `round(8*0.7)=6` → "2-6" — that is a
# STRENGTH rep range, not hypertrophy, contradicting the TrainingGoal enum
# docstring ("HYPERTROPHY: 6-12 reps"). The fix introduces goal-aware
# multipliers so heavy/moderate/light days for HYPERTROPHY stay within (or
# very close to) the 6-12 hypertrophy band, while STRENGTH heavy days still
# drop to true strength reps (3-6 / 1-3).
#
# Reference: Schoenfeld et al. 2017 — hypertrophy can occur across a wide
# rep range (6-15+) but the per-set intensity must remain in the hypertrophy
# zone (RIR 1-3). DUP for hypertrophy should rotate load within the
# hypertrophy band, NOT cross into strength territory.

_DUP_DAY_MODIFIERS_HYPERTROPHY: dict[str, dict[str, float]] = {
    # Stay within 6-12 rep band. Heavy = lower end (6-8), Moderate = mid (8-10),
    # Light = upper end (10-15). Rest still scales as classic DUP.
    "heavy":    {"reps_lo_mult": 1.0, "reps_hi_mult": 1.0, "rpe_delta": +0.5, "rest_mult": 1.5},
    "moderate": {"reps_lo_mult": 1.2, "reps_hi_mult": 1.25, "rpe_delta": 0.0, "rest_mult": 1.0},
    "light":    {"reps_lo_mult": 1.5, "reps_hi_mult": 1.6, "rpe_delta": -1.0, "rest_mult": 0.6},
}

_DUP_DAY_MODIFIERS_STRENGTH: dict[str, dict[str, float]] = {
    # Strength DUP: heavy day drops to 2-4 reps (true peaking),
    # moderate 3-6, light 5-10. (v3.1.4: docstring corrected from
    # "1-3 / 4-6 / 8-10" to match actual rounded output.)
    "heavy":    {"reps_lo_mult": 0.5, "reps_hi_mult": 0.7, "rpe_delta": +0.5, "rest_mult": 1.5},
    "moderate": {"reps_lo_mult": 1.0, "reps_hi_mult": 1.0, "rpe_delta": 0.0, "rest_mult": 1.0},
    "light":    {"reps_lo_mult": 1.5, "reps_hi_mult": 1.8, "rpe_delta": -1.0, "rest_mult": 0.6},
}

# Default (used for GENERAL_FITNESS / FAT_LOSS / RECOMP / MAINTENANCE):
# moderate rotation within the goal's preset band.
_DUP_DAY_MODIFIERS_DEFAULT: dict[str, dict[str, float]] = {
    "heavy":    {"reps_lo_mult": 0.8, "reps_hi_mult": 0.85, "rpe_delta": +0.5, "rest_mult": 1.25},
    "moderate": {"reps_lo_mult": 1.0, "reps_hi_mult": 1.0, "rpe_delta": 0.0, "rest_mult": 1.0},
    "light":    {"reps_lo_mult": 1.25, "reps_hi_mult": 1.4, "rpe_delta": -1.0, "rest_mult": 0.7},
}


def _dup_modifiers_for_goal(goal: TrainingGoal) -> dict[str, dict[str, float]]:
    """Pick the right DUP modifier table for the goal."""
    hypertrophy_goals = {
        TrainingGoal.HYPERTROPHY,
        TrainingGoal.MUSCLE_GAIN,
        TrainingGoal.RECOMP,
    }
    if goal in hypertrophy_goals:
        return _DUP_DAY_MODIFIERS_HYPERTROPHY
    if goal == TrainingGoal.STRENGTH:
        return _DUP_DAY_MODIFIERS_STRENGTH
    return _DUP_DAY_MODIFIERS_DEFAULT


def _round_half_up(x: float) -> int:
    """Round half-up (away from zero on tie), avoiding banker's rounding.

    Python's built-in ``round`` uses banker's rounding (round half to even),
    so ``round(4.5) == 4`` and ``round(5.5) == 6``. For rep-range math this
    produces surprising results: STRENGTH light day with multiplier 1.5 on
    base 3 gives ``round(4.5) == 4`` → "4-11" instead of the documented
    "5-10". This helper rounds 4.5 → 5 (away from zero on tie), matching
    what users expect from "round up at the half".

    v3.1.4 H3 fix.
    """
    import math
    return math.floor(x + 0.5) if x >= 0 else math.ceil(x - 0.5)


def _modify_reps_for_dup(base_reps: str, day_type: str, goal: TrainingGoal) -> str:
    """Apply DUP day-type modifier to a rep range like '5-8'."""
    modifiers = _dup_modifiers_for_goal(goal)
    if day_type not in modifiers or "-" not in base_reps:
        return base_reps
    try:
        lo, hi = (int(x) for x in base_reps.split("-"))
    except ValueError:
        return base_reps
    mod = modifiers[day_type]
    # v3.1.4 H3: use half-up rounding (not banker's) so e.g. 3×1.5 → 5
    # (not 4) for STRENGTH light day. Previously Python's round(4.5) returned
    # 4, producing "4-11" instead of the documented "5-10".
    new_lo = max(1, _round_half_up(lo * mod["reps_lo_mult"]))
    new_hi = max(new_lo + 1, _round_half_up(hi * mod["reps_hi_mult"]))
    return f"{new_lo}-{new_hi}"


def _modify_rpe_for_dup(base_rpe: float, day_type: str, goal: TrainingGoal) -> float:
    modifiers = _dup_modifiers_for_goal(goal)
    if day_type not in modifiers:
        return base_rpe
    delta = modifiers[day_type]["rpe_delta"]
    return max(4.0, min(10.0, base_rpe + delta))


def _modify_rest_for_dup(base_rest: int, day_type: str, goal: TrainingGoal) -> int:
    modifiers = _dup_modifiers_for_goal(goal)
    if day_type not in modifiers:
        return base_rest
    mult = modifiers[day_type]["rest_mult"]
    return max(30, round(base_rest * mult))


# === Block periodization phase modifiers ===
# Block periodization has 3 phases: accumulation → intensification → peak
# (deload is a per-microcycle flag, not a mesocycle phase — applied via `is_deload`).
# The architect decides which mesocycle is in which phase, then applies these.
# previously the third key was `"deload"` (dead — `get_block_phases_for_program`
# emits `"peak"`), so the peak mesocycle of an advanced strength program silently
# received NO modifier. Now the key matches the emitted phase name and contains
# a real peak recipe (lower reps, fewer sets, higher RPE — classic peaking).

_BLOCK_PHASE_MODIFIERS: dict[str, dict] = {
    "accumulation":  {"reps_mult": 1.2, "sets_delta": +1, "rpe_delta": -0.5},  # more volume, lower intensity
    "intensification": {"reps_mult": 0.6, "sets_delta": -1, "rpe_delta": +1.0},  # less volume, higher intensity
    "peak":          {"reps_mult": 0.5, "sets_delta": -2, "rpe_delta": +1.5},  # peaking: low reps, low volume, high intensity
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

        # Layer 2: DUP day-type modifier (now goal-aware)
        if progression == ProgressionScheme.DUP and day_type:
            reps = _modify_reps_for_dup(reps, day_type, goal)
            rpe = _modify_rpe_for_dup(rpe, day_type, goal)
            rest = _modify_rest_for_dup(rest, day_type, goal)

        # Layer 3: Block phase modifier
        if progression == ProgressionScheme.BLOCK and block_phase:
            # v3.1.2: for STRENGTH goal, consult STRENGTH_PHASE_SPECS for the
            # RPE/RIR targets per phase (per RippedBody Tables 7.11-7.13).
            # Previously these specs were dead code — _BLOCK_PHASE_MODIFIERS
            # used arbitrary multipliers not derived from the source. Now
            # STRENGTH uses the spec's RPE range midpoint for compound_primary
            # exercises (the main lifts), while other categories still use
            # the generic _BLOCK_PHASE_MODIFIERS.
            spec_applied = False
            if goal == TrainingGoal.STRENGTH and category == ExerciseCategory.COMPOUND_PRIMARY:
                try:
                    from .intensity_model import STRENGTH_PHASE_SPECS, StrengthPhase
                    # Map block_phase string → StrengthPhase enum.
                    phase_map = {
                        "accumulation": StrengthPhase.VOLUME,
                        "intensification": StrengthPhase.LOAD,
                        "peak": StrengthPhase.PEAK,
                    }
                    sp = phase_map.get(block_phase)
                    if sp is not None:
                        spec = STRENGTH_PHASE_SPECS[sp]
                        # Use the midpoint of the spec's RPE range.
                        rpe_lo, rpe_hi = spec.main_lift_rpe_range
                        rpe = (rpe_lo + rpe_hi) / 2.0
                        # Use the spec's reps range — backoff_reps for LOAD/PEAK,
                        # secondary_reps for VOLUME (which has no backoff).
                        if sp == StrengthPhase.VOLUME:
                            rep_lo, rep_hi = spec.secondary_reps
                        else:
                            rep_lo, rep_hi = spec.backoff_reps
                        # Strength-rep ranges are typically 3-6; clamp to ≥1.
                        rep_lo = max(1, rep_lo)
                        rep_hi = max(rep_lo + 1, rep_hi)
                        reps = f"{rep_lo}-{rep_hi}"
                        # Adjust sets: spec's main_lift_singles_per_week range midpoint.
                        singles_lo, singles_hi = spec.main_lift_singles_per_week
                        sets = max(1, (singles_lo + singles_hi) // 2)
                        spec_applied = True
                except (ImportError, KeyError, AttributeError):
                    pass  # Fall through to generic _BLOCK_PHASE_MODIFIERS.

            if not spec_applied:
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

        # Layer 4: Deload week — reduce VOLUME AND INTENSITY.
        # CRITICAL FIX: previously only volume was reduced (-40% sets) with
        # RPE unchanged, citing "RippedBody deload protocol". The actual
        # RippedBody Rule 8.3 spec reduces BOTH volume (-30 to -50% sets) AND
        # intensity (RIR +1 to +2, equivalent to RPE -1 to -2). Keeping RPE
        # at 8.5 during a deload leaves the user still fatigued — defeating
        # the purpose of the deload. Now: -50% sets (mid-range of source)
        # AND RPE -1.5 (midpoint of -1..-2). The `max(1, ...)` floor on sets
        # (was `max(2, ...)`) ensures 2-set accessories actually deload to 1
        # set instead of staying at 2 (the previous floor defeated the deload
        # for low-set accessories).
        if is_deload:
            sets = max(1, round(sets * 0.5))
            rpe = max(4.0, rpe - 1.5)

        # Layer 5: RIR clamp — applied AFTER DUP/block/deload modifications
        # so it operates on the FINAL rep range. (Clamping before DUP would
        # use the preset reps and then DUP would transform them, leaving RPE
        # clamped against the wrong range — e.g. RPE 6-8 instead of RPE 7-9
        # for 3-6 reps on a heavy compound.)
        try:
            # Parse the FINAL rep range (post-DUP, post-block) for the clamp.
            if "-" in reps and not reps.endswith("min") and not reps.endswith("sec"):
                parts = reps.split("-")
                reps_lo = int(parts[0])
                reps_hi = int(parts[-1])
                rir_lo, rir_hi = get_rir_range(we.exercise, reps_lo, reps_hi)
                # Convert RIR range to RPE range (RPE = 10 - RIR)
                rir_based_rpe_hi = rir_to_rpe(rir_lo)
                rir_based_rpe_lo = rir_to_rpe(rir_hi)
                # Clamp the (possibly DUP-/block-modified) RPE to the RIR-based
                # range so heavy compounds aren't prescribed above RPE 9.
                if rpe > rir_based_rpe_hi:
                    rpe = rir_based_rpe_hi
                elif rpe < rir_based_rpe_lo:
                    rpe = rir_based_rpe_lo
        except (ValueError, TypeError, AttributeError):
            # If RIR lookup fails (e.g. cardio/mobility reps, or we.exercise is
            # None and category access raises AttributeError), keep preset RPE.
            # Narrowed exception to avoid masking real bugs; includes
            # AttributeError for the defensive case where we.exercise is None.
            pass

        we.reps = reps
        we.rest_sec = rest
        we.rpe_target = round(rpe, 1)
        we.sets = sets

    return workout


# === Mesocycle / program duration rules ===

def get_mesocycle_length(experience) -> int:
    """Return the recommended mesocycle length (in weeks, including deload)."""
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

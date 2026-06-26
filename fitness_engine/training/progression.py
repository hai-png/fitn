"""
Progressive overload schemes.

Phase-1 implements basic linear and DUP schemes. Future versions will add
block periodization and advanced progression algorithms.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProgressionState(str, Enum):
    INCREASING = "increasing"      # adding load
    STALLED = "stalled"            # failed to add load for 2+ sessions
    DELOAD_NEEDED = "deload_needed"


@dataclass
class ProgressionEntry:
    """One session's progression data."""
    session_number: int
    exercise_name: str
    weight_kg: float
    sets_completed: int
    reps_per_set: list[int]
    rpe: float
    state: ProgressionState = ProgressionState.INCREASING


def linear_progression_next(
    current_weight_kg: float,
    last_reps_achieved: list[int],
    target_reps: tuple[int, int],   # (low, high), e.g. (5, 8)
    increment_kg: float = 2.5,
) -> tuple[float, str]:
    """
    Linear progression: add weight when target reps are achieved in all sets.

    Returns (next_weight, explanation).

    Phase-6 fix: explicitly handle the empty-list case. Previously
    `all([]) == True` meant an empty `last_reps_achieved` returned "Reps in
    target range but not all ≥ {high}" — a lie that suggested the user had
    performed reps. Now returns "no data yet" so the message is honest.
    """
    if not last_reps_achieved:
        return current_weight_kg, "no data yet — repeat current weight"
    low, high = target_reps
    all_at_target = all(reps >= high for reps in last_reps_achieved)

    if all_at_target and len(last_reps_achieved) >= 1:
        # `>= 1` (not `>= 3`) so 2-set exercises (accessories, deloads,
        # isolation) can also trigger progression when all sets hit the top
        # of the rep target.
        next_weight = current_weight_kg + increment_kg
        return next_weight, (
            f"All sets achieved {high}+ reps → +{increment_kg}kg "
            f"({current_weight_kg} → {next_weight}kg)"
        )
    elif all(reps >= low for reps in last_reps_achieved):
        # Stay at current weight, aim for more reps
        return current_weight_kg, (
            f"Reps in target range but not all ≥ {high} → repeat {current_weight_kg}kg"
        )
    else:
        # Failed to hit minimum reps — deload 10%
        deload_weight = current_weight_kg * 0.90
        return deload_weight, (
            f"Failed to hit {low} reps in all sets → deload 10% "
            f"({current_weight_kg} → {deload_weight:.1f}kg)"
        )


def dup_next(
    current_weights: dict[str, float],   # day_type → weight, e.g. {"heavy": 100, "moderate": 90, "light": 80}
    last_reps: dict[str, list[int]],     # day_type → reps achieved
    goal: "TrainingGoal | None" = None,  # v3.1.4: optional, for goal-aware targets
) -> dict[str, tuple[float, str]]:
    """
    Daily Undulating Periodization: rotate heavy/moderate/light days.

    Each day type progresses independently with linear progression rules.

    v3.1.4 fixes:
      - **H1**: targets now match ``apply_periodization``'s actual output
        (was hardcoded ``{"heavy": (3,6), "moderate": (5,8), "light": (8,14)}``
        which only matched the old pre-v3.1.0 fixed hypertrophy multipliers).
        When ``goal`` is provided, targets are derived from the goal's base
        preset (COMPOUND_PRIMARY) using the same ``_dup_modifiers_for_goal``
        table that ``apply_periodization`` uses, so progression triggers at
        the same rep count the periodization layer targets.
      - **H4**: unknown ``day_type`` keys no longer raise ``KeyError`` —
        they're skipped with a "no target for day_type" note. Previously a
        custom split with a non-standard day_type (e.g. ``"peak"``) crashed.

    Args:
      current_weights: ``{day_type: weight_kg}``
      last_reps: ``{day_type: [reps_per_set]}``
      goal: optional ``TrainingGoal`` for goal-aware targets. If ``None``,
        falls back to the legacy fixed targets (HYPERTROPHY-equivalent).
    """
    # v3.1.4 H1: derive targets from the same modifier table that
    # apply_periodization uses, so progression triggers match the actual
    # rep ranges produced for the user's goal.
    if goal is not None:
        from ..models.training import ExerciseCategory, TrainingGoal
        from .periodization import _dup_modifiers_for_goal, _GOAL_PRESETS
        presets = _GOAL_PRESETS.get(goal, _GOAL_PRESETS[TrainingGoal.HYPERTROPHY])
        preset = presets[ExerciseCategory.COMPOUND_PRIMARY]
        try:
            base_lo, base_hi = (int(x) for x in preset.reps.split("-"))
        except (ValueError, AttributeError):
            base_lo, base_hi = 5, 8  # defensive fallback
        modifiers = _dup_modifiers_for_goal(goal)
        from .periodization import _round_half_up
        targets: dict[str, tuple[int, int]] = {}
        for day_type, mod in modifiers.items():
            new_lo = max(1, _round_half_up(base_lo * mod["reps_lo_mult"]))
            new_hi = max(new_lo + 1, _round_half_up(base_hi * mod["reps_hi_mult"]))
            targets[day_type] = (new_lo, new_hi)
    else:
        # Legacy default — matches the old hardcoded HYPERTROPHY targets.
        targets = {"heavy": (3, 6), "moderate": (5, 8), "light": (8, 14)}

    next_state = {}
    for day_type, weight in current_weights.items():
        # v3.1.4 H4: skip unknown day_types with a clear note instead of
        # raising KeyError. Callers with custom day_types (e.g. "peak") get
        # a graceful degradation rather than a crash.
        if day_type not in targets:
            next_state[day_type] = (weight, f"no target for day_type {day_type!r} — repeat weight")
            continue
        reps = last_reps.get(day_type, [])
        if reps:
            next_w, expl = linear_progression_next(
                weight, reps, targets[day_type], increment_kg=2.5
            )
            next_state[day_type] = (next_w, expl)
        else:
            next_state[day_type] = (weight, "no data yet")
    return next_state


__all__ = [
    "ProgressionState", "ProgressionEntry",
    "linear_progression_next", "dup_next",
]


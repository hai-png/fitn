"""
Exercise selector — fills MovementPatternSlots with concrete Exercise
objects from the loaded library.

The selector is the bridge between declarative split templates (which say
"give me a horizontal-push compound-primary exercise for chest") and the
1,217-exercise JSON database. It applies four filters:

  1. Equipment filter  — only exercises the user can actually perform
  2. Experience filter — beginners don't get advanced exercises
  3. Muscle + pattern match — exercise's primary muscle matches the slot
  4. Variety           — don't reuse the same exercise within a workout

Selection priority (when multiple matches):
  - Environment-preferred equipment first (Phase-4 enhancement)
  - Experience closest to user's level (NOT a hardcoded beginner bias —
    an INTERMEDIATE user should get Intermediate exercises, not Beginner
    ones). Distance from user's max rank, ascending.
  - Then by popularity (views count, descending)
  - Then alphabetically for stable ordering

If no exact match is found, the selector falls back to broader queries:
  - Same muscle, any category
  - Same pattern, any muscle
  - Any exercise in the allowed equipment set (last resort)
"""
from __future__ import annotations

import logging

from ..models.profile import EquipmentAccess, TrainingStatus
from ..models.training import (
    Exercise,
    ExerciseCategory,
    ExperienceLevel,
)
from .exercise_categorization import (
    _infer_environment,
    get_environment_preferred_equipment,
    get_movement_pattern,
)
from .exercise_library import EXERCISES

_log = logging.getLogger(__name__)


# === Pattern → muscle + category + force hints ===
# This table maps the slot's `pattern` field to which muscle groups and
# force types are acceptable. The pattern is the primary key; the slot's
# `primary_muscle` field narrows it further.
_PATTERN_TO_FORCE_TYPE = {
    "squat": "Push",
    "front_squat": "Push",
    "hinge": "Hinge",
    "romanian_deadlift": "Hinge",
    "horizontal_push": "Push",
    "horizontal_push_dumbbell": "Push",
    "incline_push": "Push",
    "decline_push": "Push",
    "vertical_push": "Push",
    "vertical_push_dumbbell": "Push",
    "horizontal_pull": "Pull",
    "pendlay_row": "Pull",
    "chest_supported_row": "Pull",
    "seated_row": "Pull",
    "inverted_row": "Pull",
    "vertical_pull": "Pull",
    "lunge": "Push",
    "single_leg": "Push",
    "leg_press": "Push",
    "hip_thrust": "Push",
    "knee_flexion": None,         # isolation, no force_type
    "knee_extension": None,
    "ankle_plantarflexion": None,
    "elbow_flexion": None,
    "elbow_extension": None,
    "lateral_raise": None,
    "rear_delt": None,
    "front_raise": None,
    "chest_fly": None,
    "chest_dip": None,
    "push_up": None,
    "hammer_curl": None,
    "preacher_curl": None,
    "overhead_tricep": None,
    "tricep_dip": None,
    "core_anti_extension": None,
    "core_anti_rotation": None,
    "core_flexion": None,
    "hip_flexion": None,
    "mobility": None,
}


# === Equipment vocabularies (mirrors splits.py Phase-2 logic) ===

# HIGH-severity fix: previously 9 equipment types present in the DB
# (tiger_tail, bench, rings, valslide, hip_thruster, fat_bar, safety_bar,
# tire, plate) were not in any allowed set, so the 34 exercises using them
# could NEVER be selected. Added to _FULL_GYM_EQUIPMENT so they're at least
# eligible (the equipment_preference_rank will still deprioritize them when
# a better option exists).
_FULL_GYM_EQUIPMENT = {
    "barbell", "dumbbell", "bodyweight", "cable", "machine",
    "kettlebell", "bands", "exercise_ball", "other",
    "medicine_ball", "rope", "sled", "foam_roll", "ez_bar",
    "landmine", "box", "lacrosse_ball", "trap_bar", "jump_rope",
    "chains",
    # equipment types present in DB but previously missing from any set:
    "tiger_tail",       # 8 exercises (foam-roller alternative)
    "bench",            # 7 exercises (e.g. bench-jack-knife, swiss-ball work)
    "rings",            # 7 exercises (ring push-up, ring dip, ring fly)
    "valslide",         # 6 exercises (valslide push-up, leg curl)
    "hip_thruster",     # 3 exercises
    "fat_bar",          # 1 exercise
    "safety_bar",       # 1 exercise
    "tire",             # 1 exercise
    "weight_plate",     # many plate-loaded exercises use this string
    "plate",            # variant form
    "bar",              # bare bar reference
}

_HOME_GYM_EQUIPMENT = {
    "barbell", "dumbbell", "kettlebell", "bodyweight",
    "bands", "ez_bar", "landmine", "trap_bar", "exercise_ball",
}

_BODYWEIGHT_EQUIPMENT = {
    "bodyweight", "bands",
}


def get_equipment_allowed_set(equipment_access) -> set[str]:
    """Return the set of allowed equipment strings for a given access level."""
    if equipment_access == EquipmentAccess.FULL_GYM:
        return set(_FULL_GYM_EQUIPMENT)
    elif equipment_access == EquipmentAccess.HOME_GYM:
        return set(_HOME_GYM_EQUIPMENT)
    else:  # BODYWEIGHT_ONLY
        return set(_BODYWEIGHT_EQUIPMENT)


# === Experience mapping ===

def _experience_rank(ex: Exercise) -> int:
    """Beginner=0, Intermediate=1, Advanced=2, unknown=1.

    An exercise with no experience_level metadata is treated as Intermediate
    (rank 1) — safer than assuming Advanced (would be too hard for beginners)
    and more useful than assuming Beginner (would bias selection away from
    legitimate intermediate exercises that just lack the metadata).
    """
    if ex.experience_level is None:
        return 1
    return {
        ExperienceLevel.BEGINNER: 0,
        ExperienceLevel.INTERMEDIATE: 1,
        ExperienceLevel.ADVANCED: 2,
    }.get(ex.experience_level, 1)


def _user_max_experience_rank(status: TrainingStatus) -> int:
    """Beginner users get Beginner exercises only; novices get B+I; etc."""
    return {
        TrainingStatus.BEGINNER: 0,           # Beginner only
        TrainingStatus.NOVICE: 1,             # Beginner + Intermediate
        TrainingStatus.INTERMEDIATE: 2,       # all
        TrainingStatus.ADVANCED: 2,           # all
    }.get(status, 1)


# === View-count parsing for popularity sort ===
# _view_count now imports from the shared _utils module
# (was duplicated in exercise_categorization.py).
from ._utils import parse_view_count as _view_count

# === Pattern matching ===

def _matches_pattern(ex: Exercise, pattern: str) -> bool:
    """
    Check if an exercise matches a movement pattern.

    Phase-4 enhancement: uses the exercise_categorization system to
    detect the exercise's canonical pattern, then compares to the slot's
    pattern. Falls back to force_type matching if categorization fails.
    """
    # use canonical pattern detection
    ex_pattern = get_movement_pattern(ex)
    if ex_pattern == pattern:
        return True

    # Fallback: force_type matching (Phase-3 logic)
    expected_force = _PATTERN_TO_FORCE_TYPE.get(pattern)
    if expected_force:
        if not ex.force_type:
            return False
        ex_force_root = ex.force_type.split("(")[0].strip().lower()
        return ex_force_root == expected_force.lower()
    return False


def _matches_muscle(
    ex: Exercise,
    primary_muscle: str,
    *,
    match_secondary: bool = True,
) -> bool:
    """Check if exercise targets the slot's primary muscle.

    HIGH-severity fix: previously this function unconditionally matched on
    `ex.secondary_muscles` too, which caused Tier-4/5 fallbacks to pick
    wrong-muscle exercises — e.g. "Close Grip Bench Press" (primary=triceps,
    secondary=chest) was returned for a CHEST slot, and "Tricep Dip" was
    returned for a CHEST slot. Both inflated triceps volume and
    under-trained chest.

    Now ``match_secondary`` defaults to True (preserving Tier-1..3 behavior
    where broader matching is desirable), but Tier-4/5 fallbacks pass
    ``match_secondary=False`` so only exercises where the muscle is PRIMARY
    are accepted. This prevents the wrong-muscle selection cascade.
    """
    muscle = primary_muscle.lower()
    primary_muscles_lower = [m.lower() for m in ex.muscle_groups]
    if muscle in primary_muscles_lower:
        return True
    if match_secondary and muscle in [m.lower() for m in ex.secondary_muscles]:
        return True
    # Special case: "back" matches upper_back, lats, lower_back, traps
    if muscle == "back":
        back_targets = {"upper_back", "lats", "lower_back", "traps", "middle_back"}
        if any(m in back_targets for m in primary_muscles_lower):
            return True
        if match_secondary and any(
            m in back_targets for m in [x.lower() for x in ex.secondary_muscles]
        ):
            return True
    return False


# === Category matching ===

def _matches_category(ex: Exercise, slot_category: ExerciseCategory) -> bool:
    """Check if exercise's category matches the slot's required category."""
    return ex.category == slot_category


# === Equipment preference ranking (Phase-4) ===

def _equipment_preference_rank(
    ex: Exercise,
    pattern: str,
    equipment_allowed: set[str],
) -> int:
    """
    Rank an exercise's equipment for the given pattern + environment.

    Lower = better. Uses the environment-aware preference list from
    exercise_categorization.MOVEMENT_PATTERNS.

    Returns:
      - 0..N-1: rank in the preferred list (0 = best)
      - 99: equipment not in preferred list (still allowed, but last priority)
    """
    env = _infer_environment(equipment_allowed)
    preferred = get_environment_preferred_equipment(pattern, env)
    try:
        return preferred.index(ex.equipment)
    except ValueError:
        return 99


# === Main selector ===

def select_exercise_for_slot(
    slot,
    equipment_allowed: set[str],
    user_experience: TrainingStatus,
    exclude_slugs: set[str],
) -> Exercise | None:
    """
    Pick the best exercise for a given MovementPatternSlot.

    Selection priority:
      1. Exact: pattern + muscle + category + equipment + experience
      2. Pattern + muscle + category + equipment (skip experience cap)
      3. Pattern + muscle + equipment (any category)
      4. Muscle + category + equipment (any pattern)
      5. Muscle + equipment (any category, any pattern)
      6. Any exercise in allowed equipment (last resort — keeps workout non-empty)

    Within each tier, sort by:
      a. Environment-preferred equipment (Phase-4)
      b. Beginner-friendliness (Beginner > Intermediate > Advanced)
      c. Popularity (views, desc)
      d. Alphabetical name (stable tiebreaker)
    """
    max_rank = _user_max_experience_rank(user_experience)
    # CRITICAL FIX: removed dead `expected_force` variable (was computed but
    # never used — pattern matching is delegated to _matches_pattern which
    # has its own force_type fallback).

    def _filter_pool(
        require_pattern: bool = True,
        require_muscle: bool = True,
        require_category: bool = True,
        match_muscle_secondary: bool = True,
    ) -> list[Exercise]:
        pool = []
        for ex in EXERCISES:
            if ex.equipment not in equipment_allowed:
                continue
            if ex.slug and ex.slug in exclude_slugs:
                continue
            # Filter out cardio/mobility exercises from strength slots
            # (they should never be selected for hypertrophy/strength work).
            if ex.category in (ExerciseCategory.CARDIO, ExerciseCategory.MOBILITY):
                continue
            # HIGH-severity fix: plyometric exercises are contraindicated for
            # beginners (high-impact, requires movement competency). Filter
            # them out so e.g. "Bodyweight Squat Jump" is never prescribed
            # to a BEGINNER for their first squat exercise.
            if (
                user_experience == TrainingStatus.BEGINNER
                and ex.exercise_type
                and "plyometric" in ex.exercise_type.lower()
            ):
                continue
            if require_pattern and not _matches_pattern(ex, slot.pattern):
                continue
            if require_muscle and not _matches_muscle(
                ex, slot.primary_muscle, match_secondary=match_muscle_secondary,
            ):
                continue
            if require_category and not _matches_category(ex, slot.category):
                continue
            pool.append(ex)
        return pool

    def _sort_and_pick(pool: list[Exercise], enforce_experience: bool) -> Exercise | None:
        if enforce_experience:
            pool = [ex for ex in pool if _experience_rank(ex) <= max_rank]
        if not pool:
            return None
        # CRITICAL FIX: previously the sort key was `_experience_rank(ex)`
        # ascending, which ALWAYS preferred Beginner exercises (rank 0) over
        # Intermediate/Advanced — regardless of the user's level. So an
        # INTERMEDIATE user got "Decline Bench Press" (Beginner) instead of
        # "Barbell Bench Press" (Intermediate). Now we sort by ABSOLUTE
        # DISTANCE from the user's max rank, so an INTERMEDIATE user gets
        # Intermediate-ranked exercises first, a BEGINNER gets Beginner
        # first, an ADVANCED gets Advanced first.
        pool.sort(key=lambda ex: (
            _equipment_preference_rank(ex, slot.pattern, equipment_allowed),
            abs(_experience_rank(ex) - max_rank),
            -_view_count(ex),
            ex.name.lower(),
        ))
        return pool[0]

    # Tier 1: pattern + muscle + category + experience
    pool = _filter_pool(require_pattern=True, require_muscle=True, require_category=True)
    pick = _sort_and_pick(pool, enforce_experience=True)
    if pick:
        return pick

    # Tier 2: pattern + muscle + category (skip experience cap)
    pick = _sort_and_pick(pool, enforce_experience=False)
    if pick:
        # HIGH-severity fix: upgrade from debug to warning — Tier-2 fallback
        # means the user may get an exercise beyond their experience level,
        # which is a real concern (not just a debug detail).
        _log.warning(
            "Tier-2 fallback for slot %s: %s (experience cap relaxed)",
            slot.name, pick.name,
        )
        return pick

    # Tier 3: pattern + muscle (any category)
    pool = _filter_pool(require_pattern=True, require_muscle=True, require_category=False)
    pick = _sort_and_pick(pool, enforce_experience=True)
    if pick:
        _log.debug("Tier-3 fallback for slot %s: %s", slot.name, pick.name)
        return pick

    # Tier 4: muscle + category (any pattern) — match muscle as PRIMARY only
    # so e.g. close-grip-bench-press (primary=triceps, secondary=chest)
    # is NOT selected for a chest slot.
    pool = _filter_pool(
        require_pattern=False, require_muscle=True, require_category=True,
        match_muscle_secondary=False,
    )
    pick = _sort_and_pick(pool, enforce_experience=True)
    if pick:
        _log.debug("Tier-4 fallback for slot %s: %s", slot.name, pick.name)
        return pick

    # Tier 5: muscle only (any category, any pattern) — match muscle as
    # PRIMARY only (same reason as Tier 4).
    pool = _filter_pool(
        require_pattern=False, require_muscle=True, require_category=False,
        match_muscle_secondary=False,
    )
    pick = _sort_and_pick(pool, enforce_experience=True)
    if pick:
        _log.debug("Tier-5 fallback for slot %s: %s", slot.name, pick.name)
        return pick

    # Tier 6: any exercise in allowed equipment (last resort)
    pool = _filter_pool(require_pattern=False, require_muscle=False, require_category=False)
    pick = _sort_and_pick(pool, enforce_experience=True)
    if pick:
        _log.warning("Tier-6 last-resort fallback for slot %s: %s", slot.name, pick.name)
        return pick

    _log.warning("No exercise found for slot %s (pattern=%s, muscle=%s)",
                 slot.name, slot.pattern, slot.primary_muscle)
    return None


__all__ = [
    "select_exercise_for_slot",
    "get_equipment_allowed_set",
]

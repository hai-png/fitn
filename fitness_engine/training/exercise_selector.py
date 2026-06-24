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
  - Beginner-friendly first (Beginner > Intermediate > Advanced)
  - Then by popularity (views count, descending)
  - Then alphabetically for stable ordering

If no exact match is found, the selector falls back to broader queries:
  - Same muscle, any category
  - Same pattern, any muscle
  - Any exercise in the allowed equipment set (last resort)
"""
from __future__ import annotations

import logging
from typing import Optional

from ..models.profile import TrainingStatus, EquipmentAccess
from ..models.training import (
    Exercise,
    ExerciseCategory,
    ExperienceLevel,
)
from .exercise_library import EXERCISES
from .exercise_categorization import (
    get_movement_pattern,
    get_environment_preferred_equipment,
    _infer_environment,
)


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

_FULL_GYM_EQUIPMENT = {
    "barbell", "dumbbell", "bodyweight", "cable", "machine",
    "kettlebell", "bands", "exercise_ball", "other",
    "medicine_ball", "rope", "sled", "foam_roll", "ez_bar",
    "landmine", "box", "lacrosse_ball", "trap_bar", "jump_rope",
    "chains",
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
    """Beginner=0, Intermediate=1, Advanced=2, unknown=1."""
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

def _view_count(ex: Exercise) -> int:
    if not ex.views:
        return 0
    v = ex.views.upper().replace(" ", "")
    try:
        if "K" in v:
            return int(float(v.replace("K", "")) * 1_000)
        if "M" in v:
            return int(float(v.replace("M", "")) * 1_000_000)
        return int(v)
    except (ValueError, TypeError):
        return 0


# === Pattern matching ===

def _matches_pattern(ex: Exercise, pattern: str) -> bool:
    """
    Check if an exercise matches a movement pattern.

    Phase-4 enhancement: uses the exercise_categorization system to
    detect the exercise's canonical pattern, then compares to the slot's
    pattern. Falls back to force_type matching if categorization fails.
    """
    # Phase-4: use canonical pattern detection
    ex_pattern = get_movement_pattern(ex)
    if ex_pattern == pattern:
        return True

    # Fallback: force_type matching (Phase-3 logic)
    expected_force = _PATTERN_TO_FORCE_TYPE.get(pattern)
    if expected_force:
        if not ex.force_type:
            return False
        ex_force_root = ex.force_type.split("(")[0].strip().lower()
        if ex_force_root != expected_force.lower():
            return False
        return True
    return False


def _matches_muscle(ex: Exercise, primary_muscle: str) -> bool:
    """Check if exercise targets the slot's primary muscle."""
    muscle = primary_muscle.lower()
    if muscle in [m.lower() for m in ex.muscle_groups]:
        return True
    if muscle in [m.lower() for m in ex.secondary_muscles]:
        return True
    # Special case: "back" matches upper_back, lats, lower_back, traps
    if muscle == "back":
        return any(m in ["upper_back", "lats", "lower_back", "traps", "middle_back"]
                   for m in [x.lower() for x in ex.muscle_groups + ex.secondary_muscles])
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
) -> Optional[Exercise]:
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
    expected_force = _PATTERN_TO_FORCE_TYPE.get(slot.pattern)

    def _filter_pool(
        require_pattern: bool = True,
        require_muscle: bool = True,
        require_category: bool = True,
    ) -> list[Exercise]:
        pool = []
        for ex in EXERCISES:
            if ex.equipment not in equipment_allowed:
                continue
            if ex.slug and ex.slug in exclude_slugs:
                continue
            if require_pattern and not _matches_pattern(ex, slot.pattern):
                continue
            if require_muscle and not _matches_muscle(ex, slot.primary_muscle):
                continue
            if require_category and not _matches_category(ex, slot.category):
                continue
            pool.append(ex)
        return pool

    def _sort_and_pick(pool: list[Exercise], enforce_experience: bool) -> Optional[Exercise]:
        if enforce_experience:
            pool = [ex for ex in pool if _experience_rank(ex) <= max_rank]
        if not pool:
            return None
        pool.sort(key=lambda ex: (
            _equipment_preference_rank(ex, slot.pattern, equipment_allowed),
            _experience_rank(ex),
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
        _log.debug("Tier-2 fallback for slot %s: %s", slot.name, pick.name)
        return pick

    # Tier 3: pattern + muscle (any category)
    pool = _filter_pool(require_pattern=True, require_muscle=True, require_category=False)
    pick = _sort_and_pick(pool, enforce_experience=True)
    if pick:
        _log.debug("Tier-3 fallback for slot %s: %s", slot.name, pick.name)
        return pick

    # Tier 4: muscle + category (any pattern)
    pool = _filter_pool(require_pattern=False, require_muscle=True, require_category=True)
    pick = _sort_and_pick(pool, enforce_experience=True)
    if pick:
        _log.debug("Tier-4 fallback for slot %s: %s", slot.name, pick.name)
        return pick

    # Tier 5: muscle only (any category, any pattern)
    pool = _filter_pool(require_pattern=False, require_muscle=True, require_category=False)
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

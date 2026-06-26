"""
Exercise library — Phase-2 loads from content_files/all_exercises.json.

This module replaces the Phase-1 hardcoded list of 41 exercises with
the full 1,217-exercise database. The public API (EXERCISES,
EXERCISE_INDEX, get_exercise, exercises_by_muscle,
exercises_by_category, exercises_by_equipment) is preserved so the
existing training planner keeps working unchanged.

The actual loading + normalization logic lives in exercise_loader.py.

Tier 3.34 fix: EXERCISES / EXERCISE_INDEX / EXERCISE_SLUG_INDEX are now
lazy — they are populated on first access via get_exercises() /
get_exercise_index() / get_exercise_slug_index(). This avoids parsing
the 3 MB JSON at import time, which was slowing tests and preventing
monkey-patching. The module-level names are kept as backward-compat
properties that delegate to the lazy accessors.
"""
from __future__ import annotations

import dataclasses
from functools import lru_cache

from ..models.training import Exercise, ExerciseCategory
from .exercise_loader import (
    get_exercise_by_name,  # noqa: F401 — re-exported for test_modules.py
    get_exercise_by_slug,
    load_exercises,
    normalize_equipment,
)

# === Lazy accessors ===
# The JSON is ~3 MB and parsing takes ~50 ms. The first call to
# get_exercises() pays the cost; subsequent calls hit the lru_cache.

@lru_cache(maxsize=1)
def get_exercises() -> tuple[Exercise, ...]:
    """Lazy-loaded exercise database (cached). Returns a tuple for hashability."""
    return tuple(load_exercises())


@lru_cache(maxsize=1)
def get_exercise_index() -> dict[str, Exercise]:
    """Lazy index by exercise display name."""
    return {ex.name: ex for ex in get_exercises()}


@lru_cache(maxsize=1)
def get_exercise_slug_index() -> dict[str, Exercise]:
    """Lazy index by exercise slug (canonical ID)."""
    return {ex.slug: ex for ex in get_exercises() if ex.slug}


def _clear_exercise_cache() -> None:
    """Clear all exercise caches (for tests).

    Phase-6 fix: previously this only cleared the three caches in this
    module (get_exercises, get_exercise_index, get_exercise_slug_index)
    but NOT the `_load_raw_db` and `_build_indexes` caches in
    `exercise_loader`. Tests that monkey-patched the JSON path saw
    stale data from those caches. Now also clears them.

    Phase-6 consolidation: also clears the movement-pattern cache in
    `exercise_categorization` so tests that swap the exercise JSON also
    invalidate pattern detection.
    """
    get_exercises.cache_clear()
    get_exercise_index.cache_clear()
    get_exercise_slug_index.cache_clear()
    # clear the loader-level caches too — they hold the raw
    # parsed JSON and the by-id/by-slug indexes. Without this, a test that
    # points to a different JSON file still sees the previous data.
    from . import exercise_loader
    exercise_loader._load_raw_db.cache_clear()
    exercise_loader._build_indexes.cache_clear()
    # clear the categorization pattern cache too.
    from .exercise_categorization import _clear_pattern_cache
    _clear_pattern_cache()


# === Backward-compat module-level accessors ===
# These were previously eager-loaded module-level lists/dicts. Now they're
# properties that delegate to the lazy accessors. This preserves the
# `from exercise_library import EXERCISES` import pattern while making
# the loading lazy.

class _LazyExercises:
    """List-like proxy that lazily loads on first access."""
    def __iter__(self):
        return iter(get_exercises())
    def __len__(self):
        return len(get_exercises())
    def __getitem__(self, idx):
        return get_exercises()[idx]
    def __contains__(self, item):
        return item in get_exercises()
    def __repr__(self):
        return f"<LazyExercises: {len(get_exercises())} exercises>"


class _LazyExerciseIndex:
    """Dict-like proxy that lazily loads on first access."""
    def __getitem__(self, key):
        return get_exercise_index()[key]
    def __contains__(self, key):
        return key in get_exercise_index()
    def get(self, key, default=None):
        return get_exercise_index().get(key, default)
    def keys(self):
        return get_exercise_index().keys()
    def values(self):
        return get_exercise_index().values()
    def items(self):
        return get_exercise_index().items()
    def __iter__(self):
        return iter(get_exercise_index())
    def __len__(self):
        return len(get_exercise_index())


class _LazyExerciseSlugIndex:
    """Dict-like proxy that lazily loads on first access."""
    def __getitem__(self, key):
        return get_exercise_slug_index()[key]
    def __contains__(self, key):
        return key in get_exercise_slug_index()
    def get(self, key, default=None):
        return get_exercise_slug_index().get(key, default)
    def keys(self):
        return get_exercise_slug_index().keys()
    def values(self):
        return get_exercise_slug_index().values()
    def items(self):
        return get_exercise_slug_index().items()
    def __iter__(self):
        return iter(get_exercise_slug_index())
    def __len__(self):
        return len(get_exercise_slug_index())


EXERCISES = _LazyExercises()
EXERCISE_INDEX = _LazyExerciseIndex()
EXERCISE_SLUG_INDEX = _LazyExerciseSlugIndex()


def get_exercise(name: str) -> Exercise | None:
    """
    Look up an exercise by name.

    Tries (in order):
      1. Exact name match (e.g. "Barbell Back Squat")
      2. Slug match (e.g. "barbell-back-squat")
      3. Case-insensitive name match
      4. Substring match (e.g. "squat" → first exercise with 'squat' in name)

    Returns None if no match.
    """
    # 1. Exact
    if name in EXERCISE_INDEX:
        return EXERCISE_INDEX[name]
    # 2. Slug
    if name in EXERCISE_SLUG_INDEX:
        return EXERCISE_SLUG_INDEX[name]
    # 3. Case-insensitive
    lower = name.lower()
    for n, ex in EXERCISE_INDEX.items():
        if n.lower() == lower:
            return ex
    # 4. Substring
    for n, ex in EXERCISE_INDEX.items():
        if lower in n.lower():
            return ex
    return None


def exercises_by_muscle(muscle: str) -> list[Exercise]:
    """
    Return all exercises that target a given muscle group (primary or secondary).

    Muscle argument should be normalized lowercase, e.g. "quads", "chest",
    "upper_back", "lats". Matching is exact on the normalized tag.
    """
    muscle_norm = muscle.lower().replace(" ", "_").replace("-", "_")
    return [
        ex for ex in EXERCISES
        if muscle_norm in ex.muscle_groups or muscle_norm in ex.secondary_muscles
    ]


def exercises_by_category(category: ExerciseCategory) -> list[Exercise]:
    """Return all exercises in a given category."""
    return [ex for ex in EXERCISES if ex.category == category]


def exercises_by_equipment(equipment: str) -> list[Exercise]:
    """Return all exercises that use a given equipment type (normalized)."""
    equip_norm = normalize_equipment(equipment)
    return [ex for ex in EXERCISES if ex.equipment == equip_norm]


def exercises_by_experience(level: str) -> list[Exercise]:
    """
    Return all exercises matching an experience level.

    level should be "Beginner", "Intermediate", or "Advanced"
    (case-insensitive).
    """
    target = level.lower()
    return [
        ex for ex in EXERCISES
        if ex.experience_level and ex.experience_level.value.lower() == target
    ]


def exercises_by_force_type(force_type: str) -> list[Exercise]:
    """Return all exercises matching a force type (e.g. 'Push', 'Pull')."""
    if not force_type:
        return []
    target = force_type.lower()
    return [
        ex for ex in EXERCISES
        if ex.force_type and ex.force_type.lower().startswith(target)
    ]


# === Convenience aliases for backward compatibility ===
# Legacy exercise names (used by older planner templates) mapped to the
# closest matching slug in the current DB so those templates keep working.

PHASE1_TO_PHASE2_SLUG_MAP = {
    # Squat pattern
    "Barbell Back Squat": "high-bar-back-squat",
    "Front Squat": "front-squat",
    "Goblet Squat": "dumbbell-goblet-squat",
    "Bodyweight Squat": "bodyweight-wall-squat",
    # Hinge pattern
    "Conventional Deadlift": "deadlifts",  # the new DB calls it "Deadlift"
    "Romanian Deadlift (RDL)": "romanian-deadlift",
    "Single-Leg RDL": "1-kettlebell-single-leg-deadlift",
    "Hip Thrust": "barbell-hip-thrust",
    "Kettlebell Swing": "kettlebell-swing",
    # Horizontal push
    "Barbell Bench Press": "barbell-bench-press",
    "Dumbbell Bench Press": "dumbbell-bench-press",
    "Incline Dumbbell Press": "incline-dumbbell-bench-press",
    "Push-Up": "push-up",
    # Vertical push
    "Overhead Press (OHP)": "military-press",
    "Dumbbell Shoulder Press": "seated-dumbbell-press",
    "Pike Push-Up": "incline-push-ups",  # closest match (no pike push-up in DB)
    # Horizontal pull
    "Barbell Bent-Over Row": "bent-over-barbell-row",
    "Pendlay Row": "pendlay-row",
    "Chest-Supported Row": "chest-supported-dumbbell-row",
    "Seated Cable Row": "seated-row",  # new DB slug is "seated-row"
    "Inverted Row": "high-inverted-row",
    # Vertical pull
    "Pull-Up": "pull-up",
    "Chin-Up": "chin-up",
    "Lat Pulldown": "lat-pull-down",
    # Lunge / single-leg
    "Walking Lunge": "barbell-lunge",
    "Bulgarian Split Squat": "one-leg-dumbbell-squat-aka-bulgarian-squat",
    "Step-Up": "dumbbell-step-up",
    # Accessories
    "Bicep Curl": "standing-dumbbell-curl",
    "Tricep Pushdown": "cable-tricep-extension-with-v-bar",
    "Lateral Raise": "dumbbell-lateral-raise",
    "Face Pull": "cable-face-pull",
    "Leg Curl": "leg-curl",
    "Leg Extension": "leg-extension",
    "Calf Raise": "seated-calf-raise",
    "Hanging Leg Raise": "hanging-leg-raise",
    "Plank": "hover",
    "Russian Twist": "russian-twist",
    # Cardio (new DB has limited cardio; map to closest equivalents).
    # Three Phase-1 cardio names ("Incline Walk", "Cycling (moderate)",
    # "Swimming") have NO Phase-2 equivalent — callers get None from
    # ``get_exercise_by_phase1_name`` (correct: no equivalent available).
    # "Rowing Machine" stays mapped — the concept-2-rower slug IS the
    # rowing machine (correct mapping).
    "Rowing Machine": "concept-2-rowing-machine",
    "Leg Press": "45-degree-leg-press",
}


def get_exercise_by_phase1_name(name: str) -> Exercise | None:
    """
    Look up an exercise using the Phase-1 hardcoded name.

    Used by the training planner templates so we can keep referencing
    familiar names like "Barbell Back Squat" while the underlying
    database has changed.
    """
    slug = PHASE1_TO_PHASE2_SLUG_MAP.get(name)
    if slug:
        ex = get_exercise_by_slug(slug)
        if ex:
            # Override the display name to match the Phase-1 name (so the
            # planner output stays readable for users familiar with Phase-1).
            # ``dataclasses.replace`` does this in one line and stays in sync
            # if fields are added to Exercise in the future.
            return dataclasses.replace(ex, name=name)
    # Fall back to general lookup
    return get_exercise(name)


__all__ = [
    "EXERCISES", "EXERCISE_INDEX", "EXERCISE_SLUG_INDEX",
    "PHASE1_TO_PHASE2_SLUG_MAP",
    "get_exercise", "get_exercise_by_phase1_name",
    "exercises_by_muscle", "exercises_by_category",
    "exercises_by_equipment", "exercises_by_experience",
    "exercises_by_force_type",
]

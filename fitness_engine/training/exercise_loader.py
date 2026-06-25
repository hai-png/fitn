"""
Exercise loader — loads the rich exercise database from
content_files/all_exercises.json (1,217 exercises) and normalizes it
into the engine's Exercise dataclass.

Normalization rules:
  - Equipment: "Dumbbell" → "dumbbell", "Kettle Bells" → "kettlebell",
    "Exercise Ball" → "exercise_ball", "EZ Bar" → "ez_bar", etc.
  - Muscle groups: "Quads" → "quads", "Upper Back" → "upper_back",
    "Lower Back" → "lower_back", "Hip Flexors" → "hip_flexors", etc.
  - Category: derived from mechanics + force_type + exercise_type
    (COMPOUND_PRIMARY / COMPOUND_SECONDARY / ACCESSORY / CARDIO / MOBILITY)
  - Experience level: kept as-is (Beginner / Intermediate / Advanced)

The loader is loaded lazily on first access to avoid slowing tests.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from ..models.training import (
    Exercise,
    ExerciseCategory,
    ExperienceLevel,
)


# === Path resolution ===
# content_files/ lives at the repo root, two levels up from this file:
#   fitness_engine/training/exercise_loader.py  →  ../../content_files/
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_EXERCISES_JSON = _REPO_ROOT / "content_files" / "all_exercises.json"


# === Equipment normalization ===
_EQUIPMENT_MAP = {
    # Capitalized → lowercase snake
    "Barbell": "barbell",
    "Dumbbell": "dumbbell",
    "Bodyweight": "bodyweight",
    "Cable": "cable",
    "Machine": "machine",
    "Kettle Bells": "kettlebell",
    "Bands": "bands",
    "Exercise Ball": "exercise_ball",
    "Other": "other",
    "Medicine Ball": "medicine_ball",
    "Rope": "rope",
    "Sled": "sled",
    "Foam Roll": "foam_roll",
    "EZ Bar": "ez_bar",
    "Landmine": "landmine",
    "Box": "box",
    "Lacrosse Ball": "lacrosse_ball",
    "Trap Bar": "trap_bar",
    "Jump Rope": "jump_rope",
    "Chains": "chains",
}


def normalize_equipment(raw: Optional[str]) -> str:
    """Normalize equipment string to lowercase snake_case."""
    if not raw:
        return "other"
    if raw in _EQUIPMENT_MAP:
        return _EQUIPMENT_MAP[raw]
    # Fallback: lowercase + snake
    return raw.lower().replace(" ", "_").replace("-", "_")


# === Muscle group normalization ===
_MUSCLE_MAP = {
    # Title Case from new DB → lowercase snake
    "Quads": "quads",
    "Shoulders": "shoulders",
    "Chest": "chest",
    "Abs": "abs",
    "Triceps": "triceps",
    "Biceps": "biceps",
    "Hamstrings": "hamstrings",
    "Calves": "calves",
    "Upper Back": "upper_back",
    "Middle Back": "middle_back",
    "Lats": "lats",
    "Forearms": "forearms",
    "Glutes": "glutes",
    "Traps": "traps",
    "Obliques": "obliques",
    "Hip Flexors": "hip_flexors",
    "Adductors": "adductors",
    "Lower Back": "lower_back",
    "Abductors": "abductors",
    "IT Band": "it_band",
    "Neck": "neck",
    "Palmar Fascia": "palmar_fascia",
    "Plantar Fascia": "plantar_fascia",
}


def normalize_muscle(raw: Optional[str]) -> list[str]:
    """
    Normalize a muscle string into one or more lowercase engine tags.

    The new DB often lists multiple muscles comma-separated, e.g.
    "Calves, Forearms, Glutes, Hamstrings, Middle Back, Quads, Traps".
    """
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",")]
    out = []
    seen = set()
    for p in parts:
        norm = _MUSCLE_MAP.get(p, p.lower().replace(" ", "_").replace("-", "_"))
        if norm and norm not in seen:
            seen.add(norm)
            out.append(norm)
    return out


# === Category derivation ===

# Movement patterns that qualify an exercise as a "compound primary".
# These are the canonical barbell / heavy dumbbell lifts.
_COMPOUND_PRIMARY_SLUGS = {
    # Squat pattern
    "barbell-back-squat", "front-squat", "hack-squat",
    "sumo-squat", "narrow-squat", "deep-squat", "deep-front-squat",
    "wide-stance-front-squat", "wide-smith-machine-squat",
    # Hinge pattern
    "conventional-deadlift", "sumo-deadlift", "trap-bar-deadlift",
    "snatch-grip-deadlift", "deficit-deadlift", "rack-pull",
    "romanian-deadlift", "stiff-leg-deadlift", "single-leg-romanian-deadlift",
    # Horizontal push
    "barbell-bench-press", "dumbbell-bench-press",
    "incline-dumbbell-bench-press", "decline-bench-press",
    # Vertical push
    "military-press", "seated-dumbbell-press", "standing-dumbbell-press",
    "arnold-press", "smith-machine-shoulder-press",
    # Horizontal pull
    "bent-over-barbell-row", "pendlay-row", "t-bar-row",
    "chest-supported-dumbbell-row",
    # Vertical pull
    "pull-up", "chin-up", "lat-pull-down", "wide-grip-pull-down",
    "v-bar-pull-down",
    # weighted variants of pull-up / chin-up were missing —
    # they would be demoted to COMPOUND_SECONDARY despite being mechanically
    # identical to the bodyweight versions (just loaded). Add them so the
    # slug-based promotion is consistent.
    "weighted-pull-up", "weighted-chin-up",
}


def derive_category(
    slug: str,
    mechanics: Optional[str],
    force_type: Optional[str],
    exercise_type: Optional[str],
    equipment: str,
) -> ExerciseCategory:
    """
    Derive an ExerciseCategory from the new DB's free-form fields.

    Rules (in priority order):
      1. exercise_type == "Cardio" → CARDIO
      2. exercise_type contains "Mobility" / "Stretching" / "Foam Roll" → MOBILITY
      3. slug in _COMPOUND_PRIMARY_SLUGS → COMPOUND_PRIMARY
      4. mechanics == "Compound" → COMPOUND_SECONDARY
      5. mechanics == "Isolation" → ACCESSORY
      6. Default → ACCESSORY
    """
    if exercise_type:
        et = exercise_type.lower()
        if "cardio" in et:
            return ExerciseCategory.CARDIO
        if any(k in et for k in ("mobility", "stretch", "foam roll", "warm")):
            return ExerciseCategory.MOBILITY

    if slug in _COMPOUND_PRIMARY_SLUGS:
        return ExerciseCategory.COMPOUND_PRIMARY

    if mechanics == "Compound":
        return ExerciseCategory.COMPOUND_SECONDARY
    if mechanics == "Isolation":
        return ExerciseCategory.ACCESSORY

    return ExerciseCategory.ACCESSORY


# === Default sets / reps / rest by category ===
# These are sensible defaults the planner can override.
_DEFAULTS_BY_CATEGORY = {
    ExerciseCategory.COMPOUND_PRIMARY:    (4, "5-8",   180),
    ExerciseCategory.COMPOUND_SECONDARY:  (3, "8-12",  120),
    ExerciseCategory.ACCESSORY:           (3, "10-15",  60),
    ExerciseCategory.CARDIO:              (1, "20-45 min", 0),
    ExerciseCategory.MOBILITY:            (2, "30-60 sec", 30),
}


def _parse_views(raw: Optional[str]) -> Optional[str]:
    """Pass through views string ('6.6M', '2M', etc.) — kept as string for fidelity."""
    return raw


# === Loader ===

@lru_cache(maxsize=1)
def _load_raw_db(json_path: Optional[str] = None) -> dict:
    """Load and cache the raw JSON database."""
    path = Path(json_path) if json_path else _DEFAULT_EXERCISES_JSON
    if not path.exists():
        raise FileNotFoundError(
            f"Exercise database not found at {path}. "
            "Expected content_files/all_exercises.json in the repo root."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_exercises(json_path: Optional[str] = None) -> list[Exercise]:
    """
    Load all exercises from the JSON database and normalize them.

    Returns a list of Exercise dataclasses. Slugs are preserved as the
    canonical identifier (use get_exercise_by_slug for lookups).
    """
    raw = _load_raw_db(json_path)
    exercises_dict = raw.get("exercises", {})
    out: list[Exercise] = []

    for slug, ex_data in exercises_dict.items():
        # === Required fields ===
        name = ex_data.get("name") or slug.replace("-", " ").title()
        equipment = normalize_equipment(ex_data.get("equipment"))

        # Muscle groups: prefer `target_muscle_group` + `secondary_muscles`
        primary = normalize_muscle(ex_data.get("target_muscle_group"))
        secondary = normalize_muscle(ex_data.get("secondary_muscles"))
        # Also pull in the `categories` list (lower-case slug versions)
        categories_raw = ex_data.get("categories", []) or []
        categories_norm = []
        for c in categories_raw:
            key = c.lower().replace(" ", "_").replace("-", "_")
            if key not in categories_norm:
                categories_norm.append(key)
        # Use target_muscle_group as the authoritative primary;
        # fall back to categories if target is missing
        muscle_groups = primary if primary else categories_norm

        mechanics = ex_data.get("mechanics")
        force_type = ex_data.get("force_type")
        exercise_type = ex_data.get("exercise_type")
        category = derive_category(slug, mechanics, force_type, exercise_type, equipment)

        default_sets, default_reps, default_rest = _DEFAULTS_BY_CATEGORY[category]

        # === Experience level ===
        exp_raw = ex_data.get("experience_level")
        try:
            experience_level = ExperienceLevel(exp_raw) if exp_raw else None
        except ValueError:
            experience_level = None

        out.append(Exercise(
            name=name,
            category=category,
            muscle_groups=muscle_groups,
            equipment=equipment,
            default_sets=default_sets,
            default_reps=default_reps,
            default_rest_sec=default_rest,
            notes=ex_data.get("overview") or "",
            slug=slug,
            source_url=ex_data.get("url"),
            video_url=ex_data.get("video_url"),
            video_id=ex_data.get("video_id"),
            video_thumbnail=ex_data.get("video_thumbnail"),
            views=_parse_views(ex_data.get("views")),
            instructions=ex_data.get("instructions") or [],
            tips=ex_data.get("tips") or [],
            overview=ex_data.get("overview"),
            secondary_muscles=secondary,
            experience_level=experience_level,
            force_type=force_type,
            mechanics=mechanics,
            exercise_type=exercise_type,
        ))

    return out


# === Convenience indexes (built lazily) ===

@lru_cache(maxsize=1)
def _build_indexes(json_path: Optional[str] = None) -> tuple[dict, dict]:
    """Build name→Exercise and slug→Exercise indexes."""
    exercises = load_exercises(json_path)
    by_name = {}
    by_slug = {}
    for ex in exercises:
        # by_name: last-write-wins on name collisions (rare)
        by_name[ex.name] = ex
        if ex.slug:
            by_slug[ex.slug] = ex
    return by_name, by_slug


def get_exercise_by_slug(slug: str) -> Optional[Exercise]:
    """Look up an exercise by its canonical slug (e.g. 'military-press')."""
    by_name, by_slug = _build_indexes()
    return by_slug.get(slug)


def get_exercise_by_name(name: str) -> Optional[Exercise]:
    """Look up an exercise by its display name (case-sensitive)."""
    by_name, by_slug = _build_indexes()
    return by_name.get(name)


__all__ = [
    "normalize_equipment",
    "normalize_muscle",
    "derive_category",
    "load_exercises",
    "get_exercise_by_slug",
    "get_exercise_by_name",
]

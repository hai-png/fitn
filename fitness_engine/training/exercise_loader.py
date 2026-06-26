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

Path resolution (v3.1.1 fix):
  1. Try `importlib.resources` first (works when installed as a wheel —
     the JSON is packaged at `fitness_engine/data/all_exercises.json`).
  2. Fall back to the source-tree path `_REPO_ROOT/content_files/...`
     (works when running from a git checkout).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ..models.training import (
    Exercise,
    ExerciseCategory,
    ExperienceLevel,
)

# === Path resolution ===
# Source-tree path: content_files/ lives at the repo root, two levels up
# from this file:  fitness_engine/training/exercise_loader.py  →  ../../content_files/
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_EXERCISES_JSON = _REPO_ROOT / "content_files" / "all_exercises.json"


def _resolve_exercises_json_path() -> Path:
    """Locate all_exercises.json — installed wheel first, source tree fallback.

    v3.1.1 fix: when fitn is `pip install`ed from PyPI, the JSON is packaged
    at `fitness_engine/data/all_exercises.json` (per pyproject.toml's
    [tool.hatch.build.targets.wheel.shared-data]). When running from a git
    checkout, it lives at `<repo>/content_files/all_exercises.json`. This
    helper tries the installed location first (via importlib.resources) and
    falls back to the source-tree path.
    """
    # Try installed-wheel location via importlib.resources.
    try:
        from importlib.resources import files  # py3.9+
        candidate = files("fitness_engine") / "data" / "all_exercises.json"
        # `files()` returns a Traversable; convert to a real filesystem path
        # if possible. Use str() — for uninstalled packages this raises.
        path_str = str(candidate)
        if Path(path_str).is_file():
            return Path(path_str)
    except (ImportError, ModuleNotFoundError, FileNotFoundError, OSError):
        pass

    # Fall back to source-tree path (git checkout / `pip install -e .`).
    if _DEFAULT_EXERCISES_JSON.is_file():
        return _DEFAULT_EXERCISES_JSON

    raise FileNotFoundError(
        f"Could not locate all_exercises.json. Tried:\n"
        f"  1. importlib.resources: fitness_engine/data/all_exercises.json\n"
        f"  2. source tree: {_DEFAULT_EXERCISES_JSON}\n"
        f"If you installed from PyPI, the wheel may be missing the data file — "
        f"report this issue. If running from source, ensure content_files/ "
        f"is present at the repo root."
    )


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


def normalize_equipment(raw: str | None) -> str:
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


def normalize_muscle(raw: str | None) -> list[str]:
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
#
# CRITICAL FIX (was: 9 ghost slugs pointing at non-existent entries):
# The previous list contained slugs like "barbell-back-squat" and
# "conventional-deadlift" that DO NOT EXIST in all_exercises.json — the actual
# DB uses "squat" (name "Barbell Back Squat") and "deadlifts" (plural, name
# "Deadlift"). Because of the mismatch, both lifts were silently demoted to
# COMPOUND_SECONDARY, which (a) gave them the wrong periodization presets for
# STRENGTH-goal users and (b) prevented them from being selected for
# COMPOUND_PRIMARY slots in split_designs.py (the selector fell through to
# Tier 2-6 fallbacks, sometimes picking the wrong exercise entirely).
# Verified against the actual DB slug set on 2026-06.
_COMPOUND_PRIMARY_SLUGS = {
    # Squat pattern
    "squat",                              # was "barbell-back-squat" — DB name is "Barbell Back Squat"
    "high-bar-back-squat", "low-bar-back-squat",
    "front-squat", "hack-squat",
    "sumo-squat", "narrow-squat", "deep-squat",
    "deep-front-squats",                  # was "deep-front-squat" (singular)
    "wide-stance-front-squat", "wide-smith-machine-squat",
    # Hinge pattern
    "deadlifts",                          # was "conventional-deadlift" — DB slug is plural
    "sumo-deadlift", "trap-bar-deadlift",
    "snatch-grip-deadlift",
    "snatch-grip-deficit-deadlift", "trap-bar-deficit-deadlifts", "sumo-deficit-deadlift",
    "trap-bar-rack-pull",                 # was "rack-pull" (only variant in DB)
    "romanian-deadlift",
    "stiff-leg-deadlift-aka-romanian-deadlift",  # was "stiff-leg-deadlift"
    "straight-leg-deadlift",
    "single-leg-barbell-romanian-deadlift",      # was "single-leg-romanian-deadlift"
    # Horizontal push
    "barbell-bench-press", "dumbbell-bench-press",
    "incline-dumbbell-bench-press", "decline-bench-press",
    # Vertical push
    "military-press", "seated-dumbbell-press", "standing-dumbbell-press",
    "seated-arnold-press", "standing-arnold-press",   # was "arnold-press" (no bare slug in DB)
    "smith-machine-shoulder-press",
    # Horizontal pull
    "bent-over-barbell-row",              # verified DB slug for "Bent Over Row" (barbell)
    "pendlay-row",
    "machine-t-bar-row", "banded-machine-t-bar-row",  # was "t-bar-row" (only machine variants in DB)
    "chest-supported-dumbbell-row-with-isohold",
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
    mechanics: str | None,
    force_type: str | None,
    exercise_type: str | None,
    equipment: str,
) -> ExerciseCategory:
    """
    Derive an ExerciseCategory from the new DB's free-form fields.

    Rules (in priority order):
      1. exercise_type contains "Cardio" / "Conditioning" → CARDIO
         (Conditioning-type exercises like rowing-machine, assault bike, sled
         pushes are cardiometabolic — not strength work.)
      2. exercise_type contains "Mobility" / "Stretching" / "Foam Roll" /
         "SMR" / "Activation" → MOBILITY
         (SMR = self-myofascial release e.g. lacrosse ball, foam roller.
         Activation = warmup-style dynamic mobility work.)
      3. slug in _COMPOUND_PRIMARY_SLUGS → COMPOUND_PRIMARY
      4. mechanics == "Compound" (case-insensitive) → COMPOUND_SECONDARY
      5. mechanics == "Isolation" (case-insensitive) → ACCESSORY
      6. Default → ACCESSORY

    HIGH-severity fix: previously SMR (32 exercises), Conditioning (39),
    Activation (7), and Plyometrics (33) were not handled — they fell through
    to mechanics-based classification and ended up as COMPOUND_SECONDARY or
    ACCESSORY, leading to nonsensical prescriptions (foam rolling at RPE 6
    for 10-15 reps, plyometric squat jumps prescribed to beginners).
    """
    if exercise_type:
        et = exercise_type.lower()
        # v3.1.4: added "plyometric" — previously Plyometrics exercises (33
        # in the DB) fell through to mechanics-based classification and
        # ended up as COMPOUND_SECONDARY, getting prescribed as strength work
        # (e.g. Bodyweight Squat Jump at RPE 6 for 8-12 reps) when they're
        # actually high-velocity metabolic work that doesn't belong in a
        # hypertrophy slot.
        if "cardio" in et or "conditioning" in et or "plyometric" in et:
            return ExerciseCategory.CARDIO
        if any(k in et for k in (
            "mobility", "stretch", "foam roll", "warm",
            "smr", "activation", "self-massage",
        )):
            return ExerciseCategory.MOBILITY

    if slug in _COMPOUND_PRIMARY_SLUGS:
        return ExerciseCategory.COMPOUND_PRIMARY

    # Case-insensitive mechanics check (was: exact-match only — would silently
    # misclassify exercises if the DB ever contained "compound" lowercase).
    if mechanics:
        m = mechanics.lower()
        if m == "compound":
            return ExerciseCategory.COMPOUND_SECONDARY
        if m == "isolation":
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


def _parse_views(raw: str | None) -> str | None:
    """Pass through views string ('6.6M', '2M', etc.) — kept as string for fidelity."""
    return raw


# === Loader ===

@lru_cache(maxsize=1)
def _load_raw_db(json_path: str | None = None) -> dict:
    """Load and cache the raw JSON database.

    v3.1.1 fix: when ``json_path`` is None (the default), use the new
    ``_resolve_exercises_json_path`` helper which tries the installed-wheel
    location first and falls back to the source-tree path. This makes
    `pip install fitn` actually work (previously the loader hard-coded the
    source-tree path, which doesn't exist in an installed wheel).
    """
    if json_path is not None:
        path = Path(json_path)
    else:
        path = _resolve_exercises_json_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Exercise database not found at {path}. "
            "Expected content_files/all_exercises.json in the repo root "
            "(source tree) or fitness_engine/data/all_exercises.json (wheel)."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_exercises(json_path: str | None = None) -> list[Exercise]:
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
def _build_indexes(json_path: str | None = None) -> tuple[dict, dict]:
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


def get_exercise_by_slug(slug: str) -> Exercise | None:
    """Look up an exercise by its canonical slug (e.g. 'military-press')."""
    by_name, by_slug = _build_indexes()
    return by_slug.get(slug)


def get_exercise_by_name(name: str) -> Exercise | None:
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

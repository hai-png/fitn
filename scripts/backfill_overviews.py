"""
Backfill missing `overview` field for exercises in all_exercises.json.

v3.1.2: 353 of 1,217 exercises had `overview: null` or empty. This script
generates a metadata-derived placeholder overview from the exercise's existing
fields (name, muscle_groups, secondary_muscles, equipment, force_type,
mechanics, category, instructions) so the engine's `Exercise.overview` field
is always populated.

The placeholder is clearly marked with a `[curation-note]` prefix so it's
distinguishable from author-written overviews. Future curation can replace
these with real summaries scraped from the source website.

Run:  python scripts/backfill_overviews.py
Reads:  content_files/all_exercises.json
Writes: same file in-place (after backing up to .bak).
Idempotent: re-running on already-backfilled files is a no-op.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "content_files" / "all_exercises.json"

# Category derivation (mirrors exercise_loader.derive_category).
COMPOUND_PRIMARY_SLUGS = {
    "squat", "high-bar-back-squat", "low-bar-back-squat",
    "front-squat", "hack-squat", "sumo-squat", "narrow-squat", "deep-squat",
    "deep-front-squats", "wide-stance-front-squat", "wide-smith-machine-squat",
    "deadlifts", "sumo-deadlift", "trap-bar-deadlift", "snatch-grip-deadlift",
    "snatch-grip-deficit-deadlift", "trap-bar-deficit-deadlifts",
    "sumo-deficit-deadlift", "trap-bar-rack-pull", "romanian-deadlift",
    "stiff-leg-deadlift-aka-romanian-deadlift", "straight-leg-deadlift",
    "single-leg-barbell-romanian-deadlift", "barbell-bench-press",
    "dumbbell-bench-press", "incline-dumbbell-bench-press", "decline-bench-press",
    "military-press", "seated-dumbbell-press", "standing-dumbbell-press",
    "seated-arnold-press", "standing-arnold-press", "smith-machine-shoulder-press",
    "bent-over-row", "pendlay-row", "machine-t-bar-row",
    "banded-machine-t-bar-row", "chest-supported-dumbbell-row-with-isohold",
    "pull-up", "chin-up", "lat-pull-down", "wide-grip-pull-down",
    "v-bar-pull-down", "weighted-pull-up", "weighted-chin-up",
}


def _derive_category(slug: str, mechanics: str | None, exercise_type: str | None) -> str:
    """Simplified mirror of exercise_loader.derive_category."""
    if exercise_type:
        et = exercise_type.lower()
        if "cardio" in et or "conditioning" in et:
            return "cardio"
        if any(k in et for k in ("mobility", "stretch", "foam roll", "warm", "smr", "activation")):
            return "mobility"
    if slug in COMPOUND_PRIMARY_SLUGS:
        return "compound_primary"
    if mechanics:
        m = mechanics.lower()
        if m == "compound":
            return "compound_secondary"
        if m == "isolation":
            return "accessory"
    return "accessory"


def _build_overview(ex: dict) -> str:
    """Build a metadata-derived overview for an exercise.

    Format:
      [curation-note: auto-generated from metadata]
      <Name> is a <category> exercise targeting <primary_muscles>[, with
      secondary emphasis on <secondary_muscles>]. It uses <equipment>[ and
      is classified as <force_type> / <mechanics>]. <first_instruction
      sentence>.
    """
    name = ex.get("name", "This exercise")
    slug = ex.get("slug", "")
    mechanics = ex.get("mechanics")
    force_type = ex.get("force_type")
    exercise_type = ex.get("exercise_type")
    equipment = ex.get("equipment", "bodyweight")
    muscle_groups = ex.get("muscle_groups", []) or []
    secondary_muscles = ex.get("secondary_muscles", []) or []
    instructions = ex.get("instructions", []) or []

    category = _derive_category(slug, mechanics, exercise_type)

    parts = ["[curation-note: auto-generated from metadata]"]

    # Sentence 1: identity + category + primary target.
    muscle_str = ", ".join(muscle_groups[:3]) if muscle_groups else "multiple muscle groups"
    parts.append(
        f"{name} is a {category.replace('_', ' ')} exercise primarily targeting {muscle_str}."
    )

    # Sentence 2: secondary muscles.
    if secondary_muscles:
        sec_str = ", ".join(secondary_muscles[:3])
        parts.append(f"It also engages {sec_str} as secondary movers.")

    # Sentence 3: equipment + force + mechanics.
    equip_phrase = f"It is performed using {equipment.lower()}"
    classifiers = []
    if force_type:
        classifiers.append(f"force type: {force_type}")
    if mechanics:
        classifiers.append(f"mechanics: {mechanics.lower()}")
    if classifiers:
        equip_phrase += f" ({'; '.join(classifiers)})"
    equip_phrase += "."
    parts.append(equip_phrase)

    # Sentence 4: first instruction (truncated).
    if instructions:
        first_instr = instructions[0]
        if len(first_instr) > 200:
            first_instr = first_instr[:197] + "..."
        parts.append(first_instr)

    return " ".join(parts)


def main() -> None:
    print("=== Exercise overview backfill (v3.1.2) ===\n")
    if not DB_PATH.is_file():
        print(f"  ERROR: {DB_PATH} does not exist")
        return

    # Back up (only first time).
    backup = DB_PATH.with_suffix(DB_PATH.suffix + ".bak")
    if not backup.exists():
        shutil.copy2(DB_PATH, backup)
        print(f"  Backed up to {backup.name}")

    with open(DB_PATH, encoding="utf-8") as f:
        db = json.load(f)
    exercises = db.get("exercises", {})
    print(f"  Loaded {len(exercises)} exercises")

    backfilled = 0
    for slug, ex in exercises.items():
        overview = ex.get("overview")
        if not overview or (isinstance(overview, str) and not overview.strip()):
            ex["overview"] = _build_overview(ex)
            backfilled += 1

    if backfilled > 0:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Backfilled {backfilled}/{len(exercises)} exercises with generated overviews")
    else:
        print(f"  ✓ No backfill needed (all exercises have overview)")

    print(f"\n=== Done. ===")


if __name__ == "__main__":
    main()

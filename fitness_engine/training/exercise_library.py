"""
Minimal exercise library — Phase-1 starter set.

This is a FRAMEWORK-READY scaffold: the user will provide detailed exercise
resources later. The Phase-1 library covers the foundational compounds and
key accessories sufficient to generate functional training plans.

Future extension: load a richer library from JSON / external resource file.
"""
from __future__ import annotations

from ..models.training import Exercise, ExerciseCategory


# === Compound primary (foundational) ===
EXERCISES = [
    # === Squat pattern ===
    Exercise("Barbell Back Squat", ExerciseCategory.COMPOUND_PRIMARY,
             ["quads", "glutes", "hamstrings", "core"], "barbell",
             4, "5-8", 180),
    Exercise("Front Squat", ExerciseCategory.COMPOUND_PRIMARY,
             ["quads", "glutes", "core"], "barbell",
             4, "5-8", 180),
    Exercise("Goblet Squat", ExerciseCategory.COMPOUND_PRIMARY,
             ["quads", "glutes", "core"], "dumbbell",
             3, "8-12", 120),
    Exercise("Bodyweight Squat", ExerciseCategory.COMPOUND_PRIMARY,
             ["quads", "glutes"], "bodyweight",
             3, "12-20", 60),

    # === Hinge pattern ===
    Exercise("Conventional Deadlift", ExerciseCategory.COMPOUND_PRIMARY,
             ["hamstrings", "glutes", "back", "traps", "core"], "barbell",
             3, "3-5", 240),
    Exercise("Romanian Deadlift (RDL)", ExerciseCategory.COMPOUND_PRIMARY,
             ["hamstrings", "glutes", "back"], "barbell",
             3, "6-10", 150),
    Exercise("Single-Leg RDL", ExerciseCategory.COMPOUND_SECONDARY,
             ["hamstrings", "glutes", "core"], "dumbbell",
             3, "8-12", 90),
    Exercise("Hip Thrust", ExerciseCategory.COMPOUND_SECONDARY,
             ["glutes", "hamstrings"], "barbell",
             3, "8-12", 120),
    Exercise("Kettlebell Swing", ExerciseCategory.COMPOUND_SECONDARY,
             ["glutes", "hamstrings", "back", "shoulders"], "kettlebell",
             3, "12-20", 60),

    # === Horizontal push ===
    Exercise("Barbell Bench Press", ExerciseCategory.COMPOUND_PRIMARY,
             ["chest", "triceps", "shoulders"], "barbell",
             4, "5-8", 180),
    Exercise("Dumbbell Bench Press", ExerciseCategory.COMPOUND_PRIMARY,
             ["chest", "triceps", "shoulders"], "dumbbell",
             4, "6-10", 150),
    Exercise("Incline Dumbbell Press", ExerciseCategory.COMPOUND_PRIMARY,
             ["chest_upper", "triceps", "shoulders"], "dumbbell",
             3, "8-12", 120),
    Exercise("Push-Up", ExerciseCategory.COMPOUND_PRIMARY,
             ["chest", "triceps", "shoulders", "core"], "bodyweight",
             3, "10-20", 60),

    # === Vertical push ===
    Exercise("Overhead Press (OHP)", ExerciseCategory.COMPOUND_PRIMARY,
             ["shoulders", "triceps", "core"], "barbell",
             4, "5-8", 180),
    Exercise("Dumbbell Shoulder Press", ExerciseCategory.COMPOUND_PRIMARY,
             ["shoulders", "triceps"], "dumbbell",
             3, "8-12", 120),
    Exercise("Pike Push-Up", ExerciseCategory.COMPOUND_PRIMARY,
             ["shoulders", "triceps", "core"], "bodyweight",
             3, "8-15", 90),

    # === Horizontal pull ===
    Exercise("Barbell Bent-Over Row", ExerciseCategory.COMPOUND_PRIMARY,
             ["back", "biceps", "rear_delts"], "barbell",
             4, "6-10", 150),
    Exercise("Pendlay Row", ExerciseCategory.COMPOUND_PRIMARY,
             ["back", "biceps", "rear_delts"], "barbell",
             4, "5-8", 180),
    Exercise("Chest-Supported Row", ExerciseCategory.COMPOUND_PRIMARY,
             ["back", "biceps", "rear_delts"], "dumbbell",
             3, "8-12", 120),
    Exercise("Seated Cable Row", ExerciseCategory.COMPOUND_PRIMARY,
             ["back", "biceps", "rear_delts"], "cable",
             3, "8-12", 120),
    Exercise("Inverted Row", ExerciseCategory.COMPOUND_PRIMARY,
             ["back", "biceps", "rear_delts"], "bodyweight",
             3, "8-15", 90),

    # === Vertical pull ===
    Exercise("Pull-Up", ExerciseCategory.COMPOUND_PRIMARY,
             ["back", "biceps", "rear_delts"], "bodyweight",
             4, "5-10", 150),
    Exercise("Chin-Up", ExerciseCategory.COMPOUND_PRIMARY,
             ["back", "biceps"], "bodyweight",
             4, "5-10", 150),
    Exercise("Lat Pulldown", ExerciseCategory.COMPOUND_PRIMARY,
             ["back", "biceps"], "cable",
             3, "8-12", 120),

    # === Lunge / single-leg ===
    Exercise("Walking Lunge", ExerciseCategory.COMPOUND_SECONDARY,
             ["quads", "glutes", "hamstrings"], "dumbbell",
             3, "10-16", 90),
    Exercise("Bulgarian Split Squat", ExerciseCategory.COMPOUND_SECONDARY,
             ["quads", "glutes", "core"], "dumbbell",
             3, "8-12", 90),
    Exercise("Step-Up", ExerciseCategory.COMPOUND_SECONDARY,
             ["quads", "glutes"], "dumbbell",
             3, "10-15", 90),

    # === Accessories ===
    Exercise("Bicep Curl", ExerciseCategory.ACCESSORY,
             ["biceps"], "dumbbell", 3, "10-15", 60),
    Exercise("Tricep Pushdown", ExerciseCategory.ACCESSORY,
             ["triceps"], "cable", 3, "10-15", 60),
    Exercise("Lateral Raise", ExerciseCategory.ACCESSORY,
             ["shoulders_lateral"], "dumbbell", 3, "12-15", 60),
    Exercise("Face Pull", ExerciseCategory.ACCESSORY,
             ["rear_delts", "rotator_cuff"], "cable", 3, "12-20", 60),
    Exercise("Leg Curl", ExerciseCategory.ACCESSORY,
             ["hamstrings"], "machine", 3, "10-15", 60),
    Exercise("Leg Extension", ExerciseCategory.ACCESSORY,
             ["quads"], "machine", 3, "12-15", 60),
    Exercise("Calf Raise", ExerciseCategory.ACCESSORY,
             ["calves"], "machine", 3, "12-20", 60),
    Exercise("Hanging Leg Raise", ExerciseCategory.ACCESSORY,
             ["core", "hip_flexors"], "bodyweight", 3, "10-15", 60),
    Exercise("Plank", ExerciseCategory.ACCESSORY,
             ["core"], "bodyweight", 3, "30-60 sec", 45),
    Exercise("Russian Twist", ExerciseCategory.ACCESSORY,
             ["core", "obliques"], "dumbbell", 3, "15-25", 60),

    # === Cardio options ===
    Exercise("Incline Walk", ExerciseCategory.CARDIO,
             ["full_body"], "treadmill", 1, "20-45 min", 0),
    Exercise("Cycling (moderate)", ExerciseCategory.CARDIO,
             ["legs", "cardio"], "bike", 1, "20-45 min", 0),
    Exercise("Rowing Machine", ExerciseCategory.CARDIO,
             ["back", "legs", "cardio"], "rower", 1, "15-30 min", 0),
    Exercise("Swimming", ExerciseCategory.CARDIO,
             ["full_body", "cardio"], "pool", 1, "20-40 min", 0),
]

# Index by name for fast lookup
EXERCISE_INDEX = {ex.name: ex for ex in EXERCISES}


def get_exercise(name: str) -> Exercise | None:
    """Look up an exercise by name."""
    return EXERCISE_INDEX.get(name)


def exercises_by_muscle(muscle: str) -> list[Exercise]:
    """Return all exercises that target a given muscle group."""
    return [ex for ex in EXERCISES if muscle in ex.muscle_groups]


def exercises_by_category(category: ExerciseCategory) -> list[Exercise]:
    """Return all exercises in a given category."""
    return [ex for ex in EXERCISES if ex.category == category]


def exercises_by_equipment(equipment: str) -> list[Exercise]:
    """Return all exercises that use a given equipment type."""
    return [ex for ex in EXERCISES if ex.equipment == equipment]


__all__ = [
    "EXERCISES", "EXERCISE_INDEX",
    "get_exercise", "exercises_by_muscle",
    "exercises_by_category", "exercises_by_equipment",
]

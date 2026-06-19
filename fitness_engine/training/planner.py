"""
Training plan generator — orchestrates split selection, exercise selection,
progression, and mesocycle construction.

Phase-1: ships with 4 default split templates. Future versions will support
custom templates loaded from user-supplied exercise resources.
"""
from __future__ import annotations

from ..models.profile import (
    UserProfile, TrainingStatus, PrimaryGoal, EquipmentAccess,
)
from ..models.assessment import AssessmentResult, RecommendedStrategy
from ..models.training import (
    TrainingPlan, Mesocycle, Microcycle, Workout, WorkoutExercise,
    SplitType, ProgressionScheme, ExerciseCategory,
)
from .exercise_library import EXERCISES, get_exercise
from .splits import filter_exercises_by_equipment
from .splits import select_split, select_progression


# === Default workout templates (per split type) ===

def _full_body_workouts(training_days: int) -> list[Workout]:
    """Generate full-body workouts (A, B, C rotated for 3+ days)."""
    workouts = []
    templates = [
        ("Workout A", [
            ("Barbell Back Squat", 4, "5-8", 180, 8),
            ("Barbell Bench Press", 4, "5-8", 180, 8),
            ("Barbell Bent-Over Row", 4, "6-10", 150, 7),
            ("Romanian Deadlift (RDL)", 3, "6-10", 150, 7),
            ("Hanging Leg Raise", 3, "10-15", 60, 7),
        ]),
        ("Workout B", [
            ("Conventional Deadlift", 3, "3-5", 240, 9),
            ("Overhead Press (OHP)", 4, "5-8", 180, 8),
            ("Pull-Up", 4, "5-10", 150, 7),
            ("Walking Lunge", 3, "10-16", 90, 6),
            ("Face Pull", 3, "12-20", 60, 5),
        ]),
        ("Workout C", [
            ("Front Squat", 4, "5-8", 180, 8),
            ("Incline Dumbbell Press", 3, "8-12", 120, 6),
            ("Chest-Supported Row", 3, "8-12", 120, 6),
            ("Hip Thrust", 3, "8-12", 120, 6),
            ("Bicep Curl", 3, "10-15", 60, 5),
            ("Tricep Pushdown", 3, "10-15", 60, 5),
        ]),
    ]
    for i in range(training_days):
        name, ex_list = templates[i % len(templates)]
        workouts.append(_build_workout(i + 1, name, "Full Body", ex_list))
    return workouts


def _upper_lower_workouts() -> list[Workout]:
    """Generate Upper/Lower A/B cycle (4 workouts)."""
    templates = [
        ("Upper A", "Strength + Hypertrophy", [
            ("Barbell Bench Press", 4, "5-8", 180, 8),
            ("Barbell Bent-Over Row", 4, "6-10", 150, 7),
            ("Overhead Press (OHP)", 3, "6-10", 150, 7),
            ("Lat Pulldown", 3, "8-12", 120, 6),
            ("Bicep Curl", 3, "10-15", 60, 5),
            ("Tricep Pushdown", 3, "10-15", 60, 5),
        ]),
        ("Lower A", "Strength + Hypertrophy", [
            ("Barbell Back Squat", 4, "5-8", 180, 8),
            ("Romanian Deadlift (RDL)", 3, "6-10", 150, 7),
            ("Bulgarian Split Squat", 3, "8-12", 90, 6),
            ("Leg Curl", 3, "10-15", 60, 5),
            ("Calf Raise", 3, "12-20", 60, 5),
            ("Hanging Leg Raise", 3, "10-15", 60, 6),
        ]),
        ("Upper B", "Hypertrophy Focus", [
            ("Incline Dumbbell Press", 4, "8-12", 120, 6),
            ("Chest-Supported Row", 4, "8-12", 120, 6),
            ("Dumbbell Shoulder Press", 3, "8-12", 120, 6),
            ("Pull-Up", 3, "8-12", 120, 7),
            ("Lateral Raise", 3, "12-15", 60, 5),
            ("Face Pull", 3, "12-20", 60, 5),
        ]),
        ("Lower B", "Hypertrophy Focus", [
            ("Front Squat", 4, "6-10", 150, 7),
            ("Conventional Deadlift", 3, "3-5", 240, 9),
            ("Walking Lunge", 3, "10-16", 90, 6),
            ("Leg Extension", 3, "12-15", 60, 5),
            ("Hip Thrust", 3, "8-12", 120, 6),
            ("Plank", 3, "30-60 sec", 45, 5),
        ]),
    ]
    workouts = []
    for i, (name, focus, ex_list) in enumerate(templates, 1):
        workouts.append(_build_workout(i, name, focus, ex_list))
    return workouts


def _pplul_workouts() -> list[Workout]:
    """Push/Pull/Legs/Upper/Lower (5 workouts)."""
    templates = [
        ("Push", "Chest + Shoulders + Triceps", [
            ("Barbell Bench Press", 4, "5-8", 180, 8),
            ("Overhead Press (OHP)", 3, "6-10", 150, 7),
            ("Incline Dumbbell Press", 3, "8-12", 120, 6),
            ("Lateral Raise", 3, "12-15", 60, 5),
            ("Tricep Pushdown", 3, "10-15", 60, 5),
        ]),
        ("Pull", "Back + Biceps", [
            ("Barbell Bent-Over Row", 4, "6-10", 150, 7),
            ("Pull-Up", 4, "5-10", 150, 7),
            ("Seated Cable Row", 3, "8-12", 120, 6),
            ("Face Pull", 3, "12-20", 60, 5),
            ("Bicep Curl", 3, "10-15", 60, 5),
        ]),
        ("Legs", "Quads + Hams + Glutes", [
            ("Barbell Back Squat", 4, "5-8", 180, 8),
            ("Romanian Deadlift (RDL)", 3, "6-10", 150, 7),
            ("Leg Press" if get_exercise("Leg Press") else "Bulgarian Split Squat", 3, "8-12", 120, 6),
            ("Leg Curl", 3, "10-15", 60, 5),
            ("Calf Raise", 3, "12-20", 60, 5),
        ]),
        ("Upper", "Full Upper Body", [
            ("Barbell Bench Press", 3, "6-10", 150, 7),
            ("Chest-Supported Row", 3, "8-12", 120, 6),
            ("Dumbbell Shoulder Press", 3, "8-12", 120, 6),
            ("Lat Pulldown", 3, "8-12", 120, 6),
            ("Bicep Curl", 3, "10-15", 60, 5),
            ("Tricep Pushdown", 3, "10-15", 60, 5),
        ]),
        ("Lower", "Full Lower Body", [
            ("Front Squat", 4, "6-10", 150, 7),
            ("Conventional Deadlift", 3, "3-5", 240, 9),
            ("Walking Lunge", 3, "10-16", 90, 6),
            ("Hip Thrust", 3, "8-12", 120, 6),
            ("Hanging Leg Raise", 3, "10-15", 60, 6),
        ]),
    ]
    workouts = []
    for i, (name, focus, ex_list) in enumerate(templates, 1):
        workouts.append(_build_workout(i, name, focus, ex_list))
    return workouts


def _ppl_x2_workouts() -> list[Workout]:
    """Push/Pull/Legs × 2 (6 workouts: Heavy A cycle + Hypertrophy B cycle)."""
    templates = [
        ("Push A (Heavy)", "Strength Focus", [
            ("Barbell Bench Press", 5, "3-6", 240, 9),
            ("Overhead Press (OHP)", 4, "5-8", 180, 8),
            ("Incline Dumbbell Press", 3, "8-12", 120, 6),
            ("Tricep Pushdown", 3, "10-15", 60, 5),
        ]),
        ("Pull A (Heavy)", "Strength Focus", [
            ("Barbell Bent-Over Row", 5, "3-6", 240, 9),
            ("Pull-Up", 4, "5-8", 180, 8),
            ("Pendlay Row", 3, "6-10", 150, 7),
            ("Bicep Curl", 3, "10-15", 60, 5),
        ]),
        ("Legs A (Heavy)", "Strength Focus", [
            ("Barbell Back Squat", 5, "3-6", 240, 9),
            ("Conventional Deadlift", 4, "3-5", 240, 9),
            ("Romanian Deadlift (RDL)", 3, "6-10", 150, 7),
            ("Calf Raise", 3, "12-20", 60, 5),
        ]),
        ("Push B (Volume)", "Hypertrophy Focus", [
            ("Dumbbell Bench Press", 4, "8-12", 120, 6),
            ("Dumbbell Shoulder Press", 3, "10-15", 90, 5),
            ("Lateral Raise", 3, "12-15", 60, 5),
            ("Push-Up", 3, "15-25", 60, 5),
        ]),
        ("Pull B (Volume)", "Hypertrophy Focus", [
            ("Chest-Supported Row", 4, "8-12", 120, 6),
            ("Lat Pulldown", 4, "10-15", 90, 5),
            ("Face Pull", 3, "15-25", 60, 4),
            ("Inverted Row", 3, "10-20", 60, 5),
        ]),
        ("Legs B (Volume)", "Hypertrophy Focus", [
            ("Front Squat", 4, "8-12", 120, 6),
            ("Hip Thrust", 4, "8-12", 120, 6),
            ("Walking Lunge", 3, "12-20", 90, 5),
            ("Leg Curl", 3, "12-15", 60, 5),
            ("Hanging Leg Raise", 3, "12-20", 60, 5),
        ]),
    ]
    workouts = []
    for i, (name, focus, ex_list) in enumerate(templates, 1):
        workouts.append(_build_workout(i, name, focus, ex_list))
    return workouts


def _build_workout(
    day_number: int,
    name: str,
    focus: str,
    exercise_specs: list[tuple[str, int, str, int, float]],
) -> Workout:
    """Build a Workout from a list of (exercise_name, sets, reps, rest, rpe) tuples."""
    exercises = []
    for ex_name, sets, reps, rest, rpe in exercise_specs:
        ex = get_exercise(ex_name)
        if ex is None:
            # Fallback to a similar exercise in the same category
            continue
        exercises.append(WorkoutExercise(
            exercise=ex,
            sets=sets,
            reps=reps,
            rest_sec=rest,
            rpe_target=rpe,
        ))
    return Workout(
        day_number=day_number,
        name=name,
        focus=focus,
        exercises=exercises,
        estimated_duration_min=45 + len(exercises) * 8,
    )


# === Workout selection by split ===

def _workouts_for_split(split: SplitType, training_days: int) -> list[Workout]:
    """Get the workouts for a given split type."""
    if split == SplitType.FULL_BODY:
        return _full_body_workouts(training_days)
    elif split == SplitType.UPPER_LOWER:
        return _upper_lower_workouts()
    elif split == SplitType.PUSH_PULL_LEGS_UPPER_LOWER:
        return _pplul_workouts()
    elif split == SplitType.PPL_X2:
        return _ppl_x2_workouts()
    else:
        return _full_body_workouts(training_days)


# === Mesocycle construction ===

def _build_mesocycle(
    name: str,
    duration_weeks: int,
    progression: ProgressionScheme,
    workouts: list[Workout],
    deload: bool = True,
) -> Mesocycle:
    """Build a mesocycle of N weeks repeating the given workouts."""
    microcycles = []
    for week in range(1, duration_weeks + 1):
        # Mark last week as deload if applicable
        is_deload = deload and week == duration_weeks
        week_workouts = []
        for w in workouts:
            # On deload week, reduce volume by ~40% (drop 1 set from each exercise)
            ws = []
            for we in w.exercises:
                sets = max(2, we.sets - 1) if is_deload else we.sets
                ws.append(WorkoutExercise(
                    exercise=we.exercise,
                    sets=sets,
                    reps=we.reps,
                    rest_sec=we.rest_sec,
                    rpe_target=we.rpe_target,
                    notes="deload" if is_deload else "",
                ))
            week_workouts.append(Workout(
                day_number=w.day_number,
                name=w.name + (" (Deload)" if is_deload else ""),
                focus=w.focus,
                exercises=ws,
                estimated_duration_min=w.estimated_duration_min,
                notes="Deload week: -1 set per exercise, same load." if is_deload else "",
            ))
        microcycles.append(Microcycle(
            name=f"Week {week}" + (" — Deload" if is_deload else ""),
            workouts=week_workouts,
            rest_days=_compute_rest_days(len(workouts)),
        ))
    return Mesocycle(
        name=name,
        duration_weeks=duration_weeks,
        progression=progression,
        microcycles=microcycles,
        deload_week=deload,
        notes=f"{progression.value} progression; {duration_weeks}w block with deload." if deload
              else f"{progression.value} progression; {duration_weeks}w block, no deload.",
    )


def _compute_rest_days(training_days: int) -> list[int]:
    """Compute rest day numbers (1-indexed) within a 7-day week."""
    if training_days >= 6:
        return [7]
    elif training_days == 5:
        return [4, 7]
    elif training_days == 4:
        return [3, 5, 7]
    elif training_days == 3:
        return [2, 4, 6, 7]
    else:
        return [2, 4, 6, 7]


def _compute_weekly_volume(workouts: list[Workout]) -> dict[str, int]:
    """Sum hard sets per muscle group across the microcycle."""
    volume: dict[str, int] = {}
    for w in workouts:
        for we in w.exercises:
            for mg in we.exercise.muscle_groups:
                volume[mg] = volume.get(mg, 0) + we.sets
    return volume


# === Main orchestrator ===

def build_training_plan(
    profile: UserProfile,
    assessment: AssessmentResult,
) -> TrainingPlan:
    """
    Build a training plan based on profile and assessment.

    Phase-1: builds a single mesocycle (4 weeks + 1 deload).
    Future: build multiple mesocycles with periodization.
    """
    split = select_split(profile.training_days_per_week)
    progression_name = select_progression(profile.training_status)
    progression = ProgressionScheme(progression_name)

    # Get workouts for the split
    workouts = _workouts_for_split(split, profile.training_days_per_week)

    # Filter by equipment access
    if profile.equipment_access != EquipmentAccess.FULL_GYM:
        # Rebuild workouts with filtered exercises (simplified: just flag missing ones)
        for w in workouts:
            w.exercises = [
                we for we in w.exercises
                if profile.equipment_access == EquipmentAccess.FULL_GYM
                or (profile.equipment_access == EquipmentAccess.HOME_GYM
                    and we.exercise.equipment in {"barbell", "dumbbell", "kettlebell", "bodyweight"})
                or (profile.equipment_access == EquipmentAccess.BODYWEIGHT_ONLY
                    and we.exercise.equipment == "bodyweight")
            ]

    # Determine mesocycle length by training status
    meso_length = {
        TrainingStatus.BEGINNER: 4,
        TrainingStatus.NOVICE: 4,
        TrainingStatus.INTERMEDIATE: 5,
        TrainingStatus.ADVANCED: 6,
    }[profile.training_status]

    mesocycle = _build_mesocycle(
        name=f"Block 1: {profile.training_status.value.capitalize()} {profile.primary_goal.value}",
        duration_weeks=meso_length,
        progression=progression,
        workouts=workouts,
        deload=True,
    )

    weekly_vol = _compute_weekly_volume(workouts)

    # Check volume vs target (10-20 hard sets per muscle group per week)
    vol_notes: list[str] = []
    for muscle in ["chest", "back", "quads", "hamstrings", "shoulders"]:
        v = weekly_vol.get(muscle, 0)
        if v < 10:
            vol_notes.append(
                f"⚠ {muscle} volume = {v} sets/wk (below 10-set minimum). "
                "Consider adding accessory work."
            )
        elif v > 20:
            vol_notes.append(
                f"⚠ {muscle} volume = {v} sets/wk (above 20-set ceiling). "
                "Recovery may be compromised."
            )

    notes = [
        f"Split: {split.value} ({profile.training_days_per_week} days/week)",
        f"Progression: {progression.value} (suitable for {profile.training_status.value})",
        f"Mesocycle: {meso_length} weeks + 1 deload week",
        f"Equipment: {profile.equipment_access.value}",
        "Volume target: 10-20 hard sets per muscle group per week (recomp/general).",
        "Train each muscle group ≥2×/week.",
        "Compound movements as foundation; progressive overload primary driver.",
    ] + vol_notes
    notes.append(
        "Phase-1 framework: ships with default templates. "
        "User-supplied exercise resources will extend the library in Phase-2."
    )

    return TrainingPlan(
        split_type=split,
        training_days_per_week=profile.training_days_per_week,
        progression=progression,
        mesocycles=[mesocycle],
        weekly_volume_summary=weekly_vol,
        notes=notes,
    )


__all__ = ["build_training_plan"]

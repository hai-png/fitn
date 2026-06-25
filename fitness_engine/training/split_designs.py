"""
Split designs — declarative definitions of every split pattern the
training system supports.

Each split is defined as a SplitDesign containing a list of WorkoutTemplate
objects. Each WorkoutTemplate has a list of MovementPatternSlot objects
describing what kind of exercise should fill that slot (e.g., "horizontal
push primary, chest-focused"). The exercise_selector.py module fills
these slots with actual exercises from the loaded library, filtered by
the user's equipment + experience + muscle_focus.

This separation (data vs. selection logic) makes it easy to:
  - Add new splits without touching the architect
  - Test split definitions in isolation
  - Customize splits for muscle_focus without mutating base definitions
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..models.profile import TrainingStatus
from ..models.training import (
    ExerciseCategory,
    SplitType,
    TrainingGoal,
)


# === Slot template ===

@dataclass
class MovementPatternSlot:
    """
    A single exercise slot in a workout template.

    The slot describes WHAT kind of exercise should fill it (muscle + pattern
    + category). The exercise_selector fills it with an actual Exercise
    object based on equipment + experience + variety.

    Reps/rest/RPE are NOT set here — they're applied by periodization.py
    based on the user's TrainingGoal + ProgressionScheme.
    """
    name: str                              # "Horizontal Push Primary"
    primary_muscle: str                    # "chest" (normalized lowercase)
    pattern: str                           # "horizontal_push" / "vertical_pull" / "squat" / "hinge" / etc.
    category: ExerciseCategory             # COMPOUND_PRIMARY, ACCESSORY, etc.
    sets: int                              # # of work sets
    secondary_muscles: list[str] = field(default_factory=list)
    # Optional: force_type hint for better exercise matching
    force_type_hint: Optional[str] = None  # "Push" / "Pull" / "Hinge" / etc.
    # Optional: tag this slot as added by muscle_focus (for transparency)
    is_focus_emphasis: bool = False


@dataclass
class WorkoutTemplate:
    """A single workout session template — list of slots to fill."""
    name: str                              # "Upper A"
    focus: str                             # "Strength + Hypertrophy"
    slots: list[MovementPatternSlot] = field(default_factory=list)
    # Optional day-type tag for periodization (e.g., "heavy" / "moderate" / "light")
    day_type: Optional[str] = None


@dataclass
class SplitDesign:
    """
    A complete split pattern definition.

    A SplitDesign is the *blueprint*. The architect picks one based on
    (days_per_week, experience, goal), then the exercise_selector fills
    each slot with a concrete exercise to produce a list of Workout objects.
    """
    name: str                              # "upper_lower"
    split_type: SplitType
    days_per_week: int
    description: str
    templates: list[WorkoutTemplate]
    rest_days: list[int]                   # 1-indexed day-of-week (1=Mon, 7=Sun)
    suitable_for_experience: list[TrainingStatus] = field(default_factory=list)
    suitable_for_goals: list[TrainingGoal] = field(default_factory=list)


# === Helper builders for common slot patterns ===

def _compound_primary(primary: str, pattern: str, sets: int = 4,
                      secondary: list[str] = None, force: str = None,
                      is_focus: bool = False) -> MovementPatternSlot:
    return MovementPatternSlot(
        name=f"{pattern.replace('_', ' ').title()} Primary",
        primary_muscle=primary,
        pattern=pattern,
        category=ExerciseCategory.COMPOUND_PRIMARY,
        sets=sets,
        secondary_muscles=secondary or [],
        force_type_hint=force,
        is_focus_emphasis=is_focus,
    )


def _compound_secondary(primary: str, pattern: str, sets: int = 3,
                        secondary: list[str] = None, force: str = None,
                        is_focus: bool = False) -> MovementPatternSlot:
    return MovementPatternSlot(
        name=f"{pattern.replace('_', ' ').title()} Secondary",
        primary_muscle=primary,
        pattern=pattern,
        category=ExerciseCategory.COMPOUND_SECONDARY,
        sets=sets,
        secondary_muscles=secondary or [],
        force_type_hint=force,
        is_focus_emphasis=is_focus,
    )


def _accessory(primary: str, pattern: str, sets: int = 3,
                secondary: list[str] = None, is_focus: bool = False) -> MovementPatternSlot:
    return MovementPatternSlot(
        name=f"{pattern.replace('_', ' ').title()} Accessory",
        primary_muscle=primary,
        pattern=pattern,
        category=ExerciseCategory.ACCESSORY,
        sets=sets,
        secondary_muscles=secondary or [],
        is_focus_emphasis=is_focus,
    )


# === Full Body (2-3 days) ===

FULL_BODY_2DAY = SplitDesign(
    name="full_body_2day",
    split_type=SplitType.FULL_BODY,
    days_per_week=2,
    description="Full Body A/B alternation. Each session hits every major muscle group. "
                "Best for beginners with limited time, or maintenance training.",
    templates=[
        WorkoutTemplate(
            name="Full Body A",
            focus="Strength + Hypertrophy",
            slots=[
                _compound_primary("quads", "squat", sets=4, secondary=["glutes", "hamstrings"], force="Push"),
                _compound_primary("chest", "horizontal_push", sets=4, secondary=["triceps", "shoulders"], force="Push"),
                _compound_primary("upper_back", "horizontal_pull", sets=4, secondary=["biceps", "lats"], force="Pull"),
                _compound_secondary("hamstrings", "hinge", sets=3, secondary=["glutes", "lower_back"], force="Hinge"),
                _accessory("abs", "core_anti_extension", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Full Body B",
            focus="Strength + Hypertrophy",
            slots=[
                _compound_primary("hamstrings", "hinge", sets=3, secondary=["glutes", "lower_back", "traps"], force="Hinge"),
                _compound_primary("shoulders", "vertical_push", sets=4, secondary=["triceps", "abs"], force="Push"),
                _compound_primary("lats", "vertical_pull", sets=4, secondary=["biceps", "upper_back"], force="Pull"),
                _compound_secondary("quads", "lunge", sets=3, secondary=["glutes", "hamstrings"], force="Push"),
                _accessory("shoulders", "rear_delt", sets=3),
            ],
        ),
    ],
    rest_days=[2, 3, 5, 6, 7],   # Tier 2.21 fix: 5 rest days for 2-day/week (was [1,4,7] = 3 rest → implied 4 training)
    suitable_for_experience=[TrainingStatus.BEGINNER, TrainingStatus.NOVICE, TrainingStatus.INTERMEDIATE],
    suitable_for_goals=[
        TrainingGoal.STRENGTH, TrainingGoal.HYPERTROPHY, TrainingGoal.MUSCLE_GAIN, TrainingGoal.RECOMP, TrainingGoal.GENERAL_FITNESS,
        TrainingGoal.FAT_LOSS, TrainingGoal.RECOMP, TrainingGoal.MAINTENANCE,
    ],
)

FULL_BODY_3DAY = SplitDesign(
    name="full_body_3day",
    split_type=SplitType.FULL_BODY,
    days_per_week=3,
    description="Full Body A/B/C rotation. Each session emphasizes a different movement pattern. "
                "Best for beginners and early novices.",
    templates=[
        WorkoutTemplate(
            name="Full Body A",
            focus="Squat + Horizontal Push/Pull",
            slots=[
                _compound_primary("quads", "squat", sets=4, secondary=["glutes", "hamstrings"], force="Push"),
                _compound_primary("chest", "horizontal_push", sets=4, secondary=["triceps", "shoulders"], force="Push"),
                _compound_primary("upper_back", "horizontal_pull", sets=4, secondary=["biceps", "lats"], force="Pull"),
                _compound_secondary("hamstrings", "hinge", sets=3, secondary=["glutes", "lower_back"], force="Hinge"),
                _accessory("abs", "core_anti_extension", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Full Body B",
            focus="Hinge + Vertical Push/Pull",
            slots=[
                _compound_primary("hamstrings", "hinge", sets=3, secondary=["glutes", "lower_back", "traps"], force="Hinge"),
                _compound_primary("shoulders", "vertical_push", sets=4, secondary=["triceps", "abs"], force="Push"),
                _compound_primary("lats", "vertical_pull", sets=4, secondary=["biceps", "upper_back"], force="Pull"),
                _compound_secondary("quads", "lunge", sets=3, secondary=["glutes", "hamstrings"], force="Push"),
                _accessory("shoulders", "rear_delt", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Full Body C",
            focus="Front Squat + Upper Hypertrophy",
            slots=[
                _compound_primary("quads", "front_squat", sets=4, secondary=["glutes", "abs"], force="Push"),
                _compound_secondary("chest", "incline_push", sets=3, secondary=["shoulders", "triceps"], force="Push"),
                _compound_secondary("upper_back", "chest_supported_row", sets=3, secondary=["biceps", "lats"], force="Pull"),
                _compound_secondary("glutes", "hip_thrust", sets=3, secondary=["hamstrings"], force="Push"),
                _accessory("biceps", "elbow_flexion", sets=3),
                _accessory("triceps", "elbow_extension", sets=3),
            ],
        ),
    ],
    rest_days=[2, 4, 6, 7],   # Tier 2.21 fix: 4 rest days for 3-day/week (was [1,4,7] = 3 rest)
    suitable_for_experience=[TrainingStatus.BEGINNER, TrainingStatus.NOVICE, TrainingStatus.INTERMEDIATE],
    suitable_for_goals=[
        TrainingGoal.STRENGTH, TrainingGoal.HYPERTROPHY, TrainingGoal.MUSCLE_GAIN, TrainingGoal.RECOMP, TrainingGoal.GENERAL_FITNESS,
        TrainingGoal.FAT_LOSS, TrainingGoal.RECOMP, TrainingGoal.MAINTENANCE,
    ],
)


# === Upper/Lower (4 days) ===

UPPER_LOWER_4DAY = SplitDesign(
    name="upper_lower_4day",
    split_type=SplitType.UPPER_LOWER,
    days_per_week=4,
    description="Upper/Lower A/B cycle. Hits each muscle group 2x/week with one strength-focused "
                "and one hypertrophy-focused session per region. Best all-around split for novices+.",
    templates=[
        WorkoutTemplate(
            name="Upper A",
            focus="Strength Focus",
            day_type="heavy",
            slots=[
                _compound_primary("chest", "horizontal_push", sets=4, secondary=["triceps", "shoulders"], force="Push"),
                _compound_primary("upper_back", "horizontal_pull", sets=4, secondary=["biceps", "lats"], force="Pull"),
                _compound_secondary("shoulders", "vertical_push", sets=3, secondary=["triceps", "abs"], force="Push"),
                _compound_secondary("lats", "vertical_pull", sets=3, secondary=["biceps", "upper_back"], force="Pull"),
                _accessory("biceps", "elbow_flexion", sets=3),
                _accessory("triceps", "elbow_extension", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Lower A",
            focus="Strength Focus",
            day_type="heavy",
            slots=[
                _compound_primary("quads", "squat", sets=4, secondary=["glutes", "hamstrings"], force="Push"),
                _compound_secondary("hamstrings", "hinge", sets=3, secondary=["glutes", "lower_back"], force="Hinge"),
                _compound_secondary("quads", "single_leg", sets=3, secondary=["glutes"], force="Push"),
                _accessory("hamstrings", "knee_flexion", sets=3),
                _accessory("calves", "ankle_plantarflexion", sets=3),
                _accessory("abs", "core_anti_extension", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Upper B",
            focus="Hypertrophy Focus",
            day_type="moderate",
            slots=[
                _compound_secondary("chest", "incline_push", sets=4, secondary=["shoulders", "triceps"], force="Push"),
                _compound_secondary("upper_back", "chest_supported_row", sets=4, secondary=["biceps", "lats"], force="Pull"),
                _compound_secondary("shoulders", "vertical_push", sets=3, secondary=["triceps"], force="Push"),
                _compound_secondary("lats", "vertical_pull", sets=3, secondary=["biceps"], force="Pull"),
                _accessory("shoulders", "lateral_raise", sets=3),
                _accessory("shoulders", "rear_delt", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Lower B",
            focus="Hypertrophy Focus",
            day_type="moderate",
            slots=[
                _compound_secondary("quads", "front_squat", sets=4, secondary=["glutes", "abs"], force="Push"),
                _compound_primary("hamstrings", "hinge", sets=3, secondary=["glutes", "lower_back", "traps"], force="Hinge"),
                _compound_secondary("quads", "lunge", sets=3, secondary=["glutes", "hamstrings"], force="Push"),
                _accessory("quads", "knee_extension", sets=3),
                _compound_secondary("glutes", "hip_thrust", sets=3, secondary=["hamstrings"], force="Push"),
                _accessory("abs", "core_anti_rotation", sets=3),
            ],
        ),
    ],
    rest_days=[3, 5, 7],   # Wed, Fri, Sun
    suitable_for_experience=[TrainingStatus.NOVICE, TrainingStatus.INTERMEDIATE, TrainingStatus.ADVANCED],
    suitable_for_goals=[
        TrainingGoal.STRENGTH, TrainingGoal.HYPERTROPHY, TrainingGoal.MUSCLE_GAIN, TrainingGoal.RECOMP,
        TrainingGoal.FAT_LOSS, TrainingGoal.RECOMP, TrainingGoal.MAINTENANCE,
    ],
)


# === Push/Pull/Legs (3 days) ===

PPL_3DAY = SplitDesign(
    name="ppl_3day",
    split_type=SplitType.PPL,
    days_per_week=3,
    description="Push / Pull / Legs. Each workout specializes in one movement pattern. "
                "Best for novices who want focused sessions; hits each muscle 1x/week "
                "(use PPL_X2 for 2x/week frequency).",
    templates=[
        WorkoutTemplate(
            name="Push",
            focus="Chest + Shoulders + Triceps",
            slots=[
                _compound_primary("chest", "horizontal_push", sets=4, secondary=["triceps", "shoulders"], force="Push"),
                _compound_secondary("shoulders", "vertical_push", sets=3, secondary=["triceps", "abs"], force="Push"),
                _compound_secondary("chest", "incline_push", sets=3, secondary=["shoulders", "triceps"], force="Push"),
                _accessory("shoulders", "lateral_raise", sets=3),
                _accessory("triceps", "elbow_extension", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Pull",
            focus="Back + Biceps",
            slots=[
                _compound_primary("upper_back", "horizontal_pull", sets=4, secondary=["biceps", "lats"], force="Pull"),
                _compound_primary("lats", "vertical_pull", sets=4, secondary=["biceps", "upper_back"], force="Pull"),
                _compound_secondary("upper_back", "seated_row", sets=3, secondary=["biceps", "lats"], force="Pull"),
                _accessory("shoulders", "rear_delt", sets=3),
                _accessory("biceps", "elbow_flexion", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Legs",
            focus="Quads + Hams + Glutes",
            slots=[
                _compound_primary("quads", "squat", sets=4, secondary=["glutes", "hamstrings"], force="Push"),
                _compound_secondary("hamstrings", "hinge", sets=3, secondary=["glutes", "lower_back"], force="Hinge"),
                _compound_secondary("quads", "leg_press", sets=3, secondary=["glutes"], force="Push"),
                _accessory("hamstrings", "knee_flexion", sets=3),
                _accessory("calves", "ankle_plantarflexion", sets=3),
                _accessory("abs", "core_anti_extension", sets=3),
            ],
        ),
    ],
    rest_days=[2, 4, 5, 7],   # Tier 2.21 fix: 4 rest days for 3-day/week (was [4,5,7] = 3 rest → implied 4 training)
    suitable_for_experience=[TrainingStatus.NOVICE, TrainingStatus.INTERMEDIATE, TrainingStatus.ADVANCED],
    suitable_for_goals=[
        TrainingGoal.HYPERTROPHY, TrainingGoal.MUSCLE_GAIN, TrainingGoal.GENERAL_FITNESS,
        TrainingGoal.MAINTENANCE,
    ],
)


# === Push/Pull/Legs × 2 (6 days) ===

PPL_X2_6DAY = SplitDesign(
    name="ppl_x2_6day",
    split_type=SplitType.PPL_X2,
    days_per_week=6,
    description="Push/Pull/Legs × 2. Heavy A cycle + Volume B cycle. Hits each muscle 2x/week "
                "with strength and hypertrophy days. Best for intermediate/advanced trainees "
                "who can recover from 6 sessions/week.",
    templates=[
        WorkoutTemplate(
            name="Push A (Heavy)",
            focus="Strength Focus",
            day_type="heavy",
            slots=[
                _compound_primary("chest", "horizontal_push", sets=5, secondary=["triceps", "shoulders"], force="Push"),
                _compound_secondary("shoulders", "vertical_push", sets=4, secondary=["triceps", "abs"], force="Push"),
                _compound_secondary("chest", "incline_push", sets=3, secondary=["shoulders", "triceps"], force="Push"),
                _accessory("triceps", "elbow_extension", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Pull A (Heavy)",
            focus="Strength Focus",
            day_type="heavy",
            slots=[
                _compound_primary("upper_back", "horizontal_pull", sets=5, secondary=["biceps", "lats"], force="Pull"),
                _compound_primary("lats", "vertical_pull", sets=4, secondary=["biceps", "upper_back"], force="Pull"),
                _compound_secondary("upper_back", "pendlay_row", sets=3, secondary=["biceps", "lats"], force="Pull"),
                _accessory("biceps", "elbow_flexion", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Legs A (Heavy)",
            focus="Strength Focus",
            day_type="heavy",
            slots=[
                _compound_primary("quads", "squat", sets=5, secondary=["glutes", "hamstrings"], force="Push"),
                _compound_primary("hamstrings", "hinge", sets=4, secondary=["glutes", "lower_back", "traps"], force="Hinge"),
                _compound_secondary("hamstrings", "romanian_deadlift", sets=3, secondary=["glutes"], force="Hinge"),
                _accessory("calves", "ankle_plantarflexion", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Push B (Volume)",
            focus="Hypertrophy Focus",
            day_type="moderate",
            slots=[
                _compound_secondary("chest", "horizontal_push_dumbbell", sets=4, secondary=["triceps", "shoulders"], force="Push"),
                _compound_secondary("shoulders", "vertical_push", sets=3, secondary=["triceps"], force="Push"),
                _accessory("shoulders", "lateral_raise", sets=3),
                _accessory("chest", "push_up", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Pull B (Volume)",
            focus="Hypertrophy Focus",
            day_type="moderate",
            slots=[
                _compound_secondary("upper_back", "chest_supported_row", sets=4, secondary=["biceps", "lats"], force="Pull"),
                _compound_secondary("lats", "vertical_pull", sets=4, secondary=["biceps"], force="Pull"),
                _accessory("shoulders", "rear_delt", sets=3),
                _compound_secondary("upper_back", "inverted_row", sets=3, secondary=["biceps", "lats"], force="Pull"),
            ],
        ),
        WorkoutTemplate(
            name="Legs B (Volume)",
            focus="Hypertrophy Focus",
            day_type="moderate",
            slots=[
                _compound_secondary("quads", "front_squat", sets=4, secondary=["glutes", "abs"], force="Push"),
                _compound_secondary("glutes", "hip_thrust", sets=4, secondary=["hamstrings"], force="Push"),
                _compound_secondary("quads", "lunge", sets=3, secondary=["glutes", "hamstrings"], force="Push"),
                _accessory("hamstrings", "knee_flexion", sets=3),
                _accessory("abs", "core_anti_extension", sets=3),
            ],
        ),
    ],
    rest_days=[7],
    suitable_for_experience=[TrainingStatus.INTERMEDIATE, TrainingStatus.ADVANCED],
    suitable_for_goals=[
        TrainingGoal.HYPERTROPHY, TrainingGoal.MUSCLE_GAIN, TrainingGoal.RECOMP, TrainingGoal.STRENGTH,
    ],
)


# === PPL + Upper/Lower (5 days) ===

PPL_UL_5DAY = SplitDesign(
    name="ppl_ul_5day",
    split_type=SplitType.PUSH_PULL_LEGS_UPPER_LOWER,
    days_per_week=5,
    description="Push / Pull / Legs / Upper / Lower. Combines PPL specialization with Upper/Lower "
                "frequency. Best for intermediate trainees who want 5 days/week.",
    templates=[
        WorkoutTemplate(
            name="Push",
            focus="Chest + Shoulders + Triceps",
            slots=[
                _compound_primary("chest", "horizontal_push", sets=4, secondary=["triceps", "shoulders"], force="Push"),
                _compound_secondary("shoulders", "vertical_push", sets=3, secondary=["triceps", "abs"], force="Push"),
                _compound_secondary("chest", "incline_push", sets=3, secondary=["shoulders", "triceps"], force="Push"),
                _accessory("shoulders", "lateral_raise", sets=3),
                _accessory("triceps", "elbow_extension", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Pull",
            focus="Back + Biceps",
            slots=[
                _compound_primary("upper_back", "horizontal_pull", sets=4, secondary=["biceps", "lats"], force="Pull"),
                _compound_primary("lats", "vertical_pull", sets=4, secondary=["biceps", "upper_back"], force="Pull"),
                _compound_secondary("upper_back", "seated_row", sets=3, secondary=["biceps", "lats"], force="Pull"),
                _accessory("shoulders", "rear_delt", sets=3),
                _accessory("biceps", "elbow_flexion", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Legs",
            focus="Quads + Hams + Glutes",
            slots=[
                _compound_primary("quads", "squat", sets=4, secondary=["glutes", "hamstrings"], force="Push"),
                _compound_secondary("hamstrings", "hinge", sets=3, secondary=["glutes", "lower_back"], force="Hinge"),
                _compound_secondary("quads", "leg_press", sets=3, secondary=["glutes"], force="Push"),
                _accessory("hamstrings", "knee_flexion", sets=3),
                _accessory("calves", "ankle_plantarflexion", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Upper",
            focus="Full Upper Body",
            slots=[
                _compound_secondary("chest", "horizontal_push", sets=3, secondary=["triceps", "shoulders"], force="Push"),
                _compound_secondary("upper_back", "chest_supported_row", sets=3, secondary=["biceps", "lats"], force="Pull"),
                _compound_secondary("shoulders", "vertical_push", sets=3, secondary=["triceps"], force="Push"),
                _compound_secondary("lats", "vertical_pull", sets=3, secondary=["biceps"], force="Pull"),
                _accessory("biceps", "elbow_flexion", sets=3),
                _accessory("triceps", "elbow_extension", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Lower",
            focus="Full Lower Body",
            slots=[
                _compound_secondary("quads", "front_squat", sets=4, secondary=["glutes", "abs"], force="Push"),
                _compound_primary("hamstrings", "hinge", sets=3, secondary=["glutes", "lower_back", "traps"], force="Hinge"),
                _compound_secondary("quads", "lunge", sets=3, secondary=["glutes", "hamstrings"], force="Push"),
                _compound_secondary("glutes", "hip_thrust", sets=3, secondary=["hamstrings"], force="Push"),
                _accessory("abs", "core_anti_extension", sets=3),
            ],
        ),
    ],
    rest_days=[4, 7],
    suitable_for_experience=[TrainingStatus.INTERMEDIATE, TrainingStatus.ADVANCED],
    suitable_for_goals=[
        TrainingGoal.HYPERTROPHY, TrainingGoal.MUSCLE_GAIN, TrainingGoal.RECOMP, TrainingGoal.MAINTENANCE,
    ],
)


# === Body Part Split (5 days) ===

BODY_PART_5DAY = SplitDesign(
    name="body_part_5day",
    split_type=SplitType.BODY_PART,
    days_per_week=5,
    description="Body part split: Chest / Back / Legs / Shoulders / Arms. One muscle group per day "
                "with high volume. Best for advanced bodybuilders; lower frequency (1x/week) "
                "may be suboptimal for strength gains.",
    templates=[
        WorkoutTemplate(
            name="Chest Day",
            focus="Chest Hypertrophy",
            slots=[
                _compound_primary("chest", "horizontal_push", sets=4, secondary=["triceps", "shoulders"], force="Push"),
                _compound_secondary("chest", "incline_push", sets=4, secondary=["shoulders", "triceps"], force="Push"),
                _compound_secondary("chest", "decline_push", sets=3, secondary=["triceps"], force="Push"),
                _accessory("chest", "chest_fly", sets=3),
                _accessory("chest", "chest_dip", sets=3, secondary=["triceps"]),
            ],
        ),
        WorkoutTemplate(
            name="Back Day",
            focus="Back Hypertrophy",
            slots=[
                _compound_primary("hamstrings", "hinge", sets=3, secondary=["glutes", "lower_back", "traps"], force="Hinge"),
                _compound_primary("upper_back", "horizontal_pull", sets=4, secondary=["biceps", "lats"], force="Pull"),
                _compound_primary("lats", "vertical_pull", sets=4, secondary=["biceps", "upper_back"], force="Pull"),
                _compound_secondary("upper_back", "seated_row", sets=3, secondary=["biceps", "lats"], force="Pull"),
                _accessory("shoulders", "rear_delt", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Legs Day",
            focus="Legs Hypertrophy",
            slots=[
                _compound_primary("quads", "squat", sets=4, secondary=["glutes", "hamstrings"], force="Push"),
                _compound_secondary("hamstrings", "hinge", sets=3, secondary=["glutes", "lower_back"], force="Hinge"),
                _compound_secondary("quads", "leg_press", sets=3, secondary=["glutes"], force="Push"),
                _accessory("hamstrings", "knee_flexion", sets=3),
                _accessory("quads", "knee_extension", sets=3),
                _accessory("calves", "ankle_plantarflexion", sets=4),
            ],
        ),
        WorkoutTemplate(
            name="Shoulders Day",
            focus="Shoulders Hypertrophy",
            slots=[
                _compound_primary("shoulders", "vertical_push", sets=4, secondary=["triceps", "abs"], force="Push"),
                _compound_secondary("shoulders", "vertical_push_dumbbell", sets=3, secondary=["triceps"], force="Push"),
                _accessory("shoulders", "lateral_raise", sets=4),
                _accessory("shoulders", "rear_delt", sets=4),
                _accessory("shoulders", "front_raise", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Arms Day",
            focus="Biceps + Triceps Hypertrophy",
            slots=[
                _accessory("biceps", "elbow_flexion", sets=4),
                _accessory("triceps", "elbow_extension", sets=4),
                _accessory("biceps", "hammer_curl", sets=3),
                _accessory("triceps", "overhead_tricep", sets=3),
                _accessory("biceps", "preacher_curl", sets=3),
                _accessory("triceps", "tricep_dip", sets=3, secondary=["chest"]),
            ],
        ),
    ],
    rest_days=[6, 7],
    suitable_for_experience=[TrainingStatus.ADVANCED],
    suitable_for_goals=[
        TrainingGoal.HYPERTROPHY, TrainingGoal.MUSCLE_GAIN,
    ],
)


# === Push/Pull (4 days) — alternative for 4-day splits ===

PUSH_PULL_4DAY = SplitDesign(
    name="push_pull_4day",
    split_type=SplitType.PUSH_PULL,
    days_per_week=4,
    description="Push/Pull × 2. Alternates push (chest/shoulders/triceps) and pull (back/biceps/legs posterior) days. "
                "Useful when the user wants upper/lower alternative with more arm focus.",
    templates=[
        WorkoutTemplate(
            name="Push A (Heavy)",
            focus="Strength Focus",
            day_type="heavy",
            slots=[
                _compound_primary("chest", "horizontal_push", sets=4, secondary=["triceps", "shoulders"], force="Push"),
                _compound_secondary("shoulders", "vertical_push", sets=3, secondary=["triceps", "abs"], force="Push"),
                _compound_secondary("quads", "squat", sets=4, secondary=["glutes", "hamstrings"], force="Push"),
                _accessory("triceps", "elbow_extension", sets=3),
                _accessory("calves", "ankle_plantarflexion", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Pull A (Heavy)",
            focus="Strength Focus",
            day_type="heavy",
            slots=[
                _compound_primary("hamstrings", "hinge", sets=3, secondary=["glutes", "lower_back", "traps"], force="Hinge"),
                _compound_primary("upper_back", "horizontal_pull", sets=4, secondary=["biceps", "lats"], force="Pull"),
                _compound_secondary("lats", "vertical_pull", sets=3, secondary=["biceps", "upper_back"], force="Pull"),
                _accessory("biceps", "elbow_flexion", sets=3),
                _accessory("abs", "core_anti_extension", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Push B (Volume)",
            focus="Hypertrophy Focus",
            day_type="moderate",
            slots=[
                _compound_secondary("chest", "incline_push", sets=4, secondary=["shoulders", "triceps"], force="Push"),
                _compound_secondary("shoulders", "vertical_push_dumbbell", sets=3, secondary=["triceps"], force="Push"),
                _compound_secondary("quads", "leg_press", sets=3, secondary=["glutes"], force="Push"),
                _accessory("shoulders", "lateral_raise", sets=3),
                _accessory("triceps", "elbow_extension", sets=3),
            ],
        ),
        WorkoutTemplate(
            name="Pull B (Volume)",
            focus="Hypertrophy Focus",
            day_type="moderate",
            slots=[
                _compound_secondary("upper_back", "chest_supported_row", sets=4, secondary=["biceps", "lats"], force="Pull"),
                _compound_secondary("lats", "vertical_pull", sets=4, secondary=["biceps"], force="Pull"),
                _compound_secondary("glutes", "hip_thrust", sets=3, secondary=["hamstrings"], force="Push"),
                _accessory("shoulders", "rear_delt", sets=3),
                _accessory("biceps", "elbow_flexion", sets=3),
            ],
        ),
    ],
    rest_days=[3, 5, 7],
    suitable_for_experience=[TrainingStatus.NOVICE, TrainingStatus.INTERMEDIATE],
    suitable_for_goals=[
        TrainingGoal.HYPERTROPHY, TrainingGoal.MUSCLE_GAIN, TrainingGoal.GENERAL_FITNESS,
    ],
)


# === Registry of all splits ===

ALL_SPLITS: list[SplitDesign] = [
    FULL_BODY_2DAY,
    FULL_BODY_3DAY,
    UPPER_LOWER_4DAY,
    PPL_3DAY,
    PPL_X2_6DAY,
    PPL_UL_5DAY,
    BODY_PART_5DAY,
    PUSH_PULL_4DAY,
]


def get_splits_for_days(days_per_week: int) -> list[SplitDesign]:
    """Return all splits matching the requested days-per-week."""
    return [s for s in ALL_SPLITS if s.days_per_week == days_per_week]


def get_split(name: str) -> Optional[SplitDesign]:
    """Look up a split by name."""
    for s in ALL_SPLITS:
        if s.name == name:
            return s
    return None


__all__ = [
    "MovementPatternSlot",
    "WorkoutTemplate",
    "SplitDesign",
    "ALL_SPLITS",
    "get_splits_for_days",
    "get_split",
    # Split constants
    "FULL_BODY_2DAY", "FULL_BODY_3DAY",
    "UPPER_LOWER_4DAY",
    "PPL_3DAY", "PPL_X2_6DAY", "PPL_UL_5DAY",
    "BODY_PART_5DAY", "PUSH_PULL_4DAY",
    # Helpers
    "_compound_primary", "_compound_secondary", "_accessory",
]

"""
Exercise categorization system — Phase-4 (RippedBody-informed).

This module systematically categorizes every exercise in the 1,217-exercise
JSON database by:

  1. **Movement pattern** (canonical taxonomy of 40 movement patterns)
     - squat, hinge, horizontal_push, vertical_push, horizontal_pull,
       vertical_pull, lunge, hip_thrust, knee_flexion, knee_extension,
       ankle_plantarflexion, elbow_flexion, elbow_extension, lateral_raise,
       rear_delt, front_raise, chest_fly, chest_dip, push_up, hip_flexion,
       core_anti_extension, core_anti_rotation, core_flexion, mobility

  2. **Pattern family** (broader grouping for volume tallying)
     - PUSH (horizontal_push + vertical_push + push_up + chest_dip + chest_fly)
     - PULL (horizontal_pull + vertical_pull + rear_delt)
     - LOWER (squat + hinge + lunge + hip_thrust + knee_flexion + knee_extension + ankle_plantarflexion)
     - ARMS (elbow_flexion + elbow_extension)
     - SHOULDERS (lateral_raise + front_raise + vertical_push)
     - CORE (core_anti_extension + core_anti_rotation + core_flexion + hip_flexion)
     - MOBILITY

  3. **Equipment environment preference** (per pattern)
     - For each movement pattern, defines which equipment is preferred
       in each of the 3 environments (FULL_GYM, HOME_GYM, BODYWEIGHT_ONLY)

  4. **Swap groups** (exercises that target the same pattern + primary muscle)
     - Two exercises are swappable if they share the same pattern + primary_muscle
     - Equipment filter applied at swap time so user only sees variations
       they can actually perform

Public API:
  - categorize_exercise(exercise) → ExerciseCategoryInfo
  - get_movement_pattern(exercise) → str
  - get_pattern_family(pattern) → PatternFamily
  - get_swappable_exercises(exercise, equipment_allowed, exclude_slugs=set()) → list[Exercise]
  - get_environment_preferred_equipment(pattern, environment) → list[str]
  - MOVEMENT_PATTERNS: dict[str, MovementPatternSpec]
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ..models.training import Exercise, ExerciseCategory

# === Pattern families ===

class PatternFamily(str, Enum):
    """Broader grouping for volume tallying (RippedBody Rule 10.3)."""
    PUSH = "push"
    PULL = "pull"
    LOWER = "lower"
    ARMS = "arms"
    SHOULDERS = "shoulders"
    CORE = "core"
    MOBILITY = "mobility"
    CARDIO = "cardio"


# === Movement pattern taxonomy (40 canonical patterns) ===

@dataclass
class MovementPatternSpec:
    """Specification for a single movement pattern."""
    name: str
    family: PatternFamily
    primary_muscles: list[str]          # normalized lowercase
    description: str
    # Environment preference: ordered list of preferred equipment per environment
    # First match wins; the selector tries each in order.
    env_preference: dict[str, list[str]] = field(default_factory=dict)
    # Keywords used to detect this pattern from an exercise's name/slug/force_type
    detection_keywords: list[str] = field(default_factory=list)


# === The 40-pattern taxonomy ===

MOVEMENT_PATTERNS: dict[str, MovementPatternSpec] = {
    # === Lower body compound ===
    "squat": MovementPatternSpec(
        name="squat",
        family=PatternFamily.LOWER,
        primary_muscles=["quads", "glutes", "hamstrings"],
        description="Bilateral knee-dominant compound (back squat, front squat, goblet)",
        env_preference={
            "full_gym": ["barbell", "machine", "dumbbell", "kettlebell", "bodyweight"],
            "home_gym": ["barbell", "dumbbell", "kettlebell", "bodyweight"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["squat", "hack-squat", "goblet-squat"],  # removed "leg-press" (separate pattern, was tie-breaking to squat)
    ),
    "front_squat": MovementPatternSpec(
        name="front_squat",
        family=PatternFamily.LOWER,
        primary_muscles=["quads", "glutes", "abs"],
        description="Front-loaded squat variant (emphasizes quads + core)",
        env_preference={
            "full_gym": ["barbell", "dumbbell", "kettlebell"],
            "home_gym": ["barbell", "dumbbell", "kettlebell"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["front-squat"],
    ),
    "hinge": MovementPatternSpec(
        name="hinge",
        family=PatternFamily.LOWER,
        primary_muscles=["hamstrings", "glutes", "lower_back", "traps"],
        description="Hip-hinge compound (deadlift, RDL, stiff-leg deadlift)",
        env_preference={
            "full_gym": ["barbell", "trap_bar", "dumbbell", "kettlebell", "bodyweight"],
            "home_gym": ["barbell", "trap_bar", "dumbbell", "kettlebell", "bodyweight"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["deadlift", "rdl", "romanian", "stiff-leg", "good-morning", "hip-hinge",
                            # v3.1.4 H5 fix: add single-leg deadlift / RDL
                            # keywords so they score 119 / 113 respectively,
                            # beating the generic "single-leg" keyword (110)
                            # in the single_leg pattern. Without this,
                            # "Single Leg Deadlift" was mis-bucketed as
                            # single_leg instead of hinge.
                            "single-leg-deadlift", "single-leg-rdl",
                            "single-leg-romanian"],
    ),
    "romanian_deadlift": MovementPatternSpec(
        name="romanian_deadlift",
        family=PatternFamily.LOWER,
        primary_muscles=["hamstrings", "glutes"],
        description="RDL — submaximal hinge for hypertrophy",
        env_preference={
            "full_gym": ["barbell", "dumbbell", "kettlebell"],
            "home_gym": ["barbell", "dumbbell", "kettlebell"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["romanian", "rdl", "stiff-leg-deadlift"],
    ),
    "lunge": MovementPatternSpec(
        name="lunge",
        family=PatternFamily.LOWER,
        primary_muscles=["quads", "glutes", "hamstrings"],
        description="Single-leg lunge / split squat pattern",
        env_preference={
            "full_gym": ["dumbbell", "barbell", "kettlebell", "bodyweight"],
            "home_gym": ["dumbbell", "barbell", "kettlebell", "bodyweight"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["lunge", "split-squat", "step-up", "bulgarian"],
    ),
    "single_leg": MovementPatternSpec(
        name="single_leg",
        family=PatternFamily.LOWER,
        primary_muscles=["quads", "glutes"],
        description="Single-leg squat / step-up pattern",
        env_preference={
            "full_gym": ["dumbbell", "barbell", "kettlebell", "bodyweight"],
            "home_gym": ["dumbbell", "barbell", "kettlebell", "bodyweight"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["single-leg", "pistol", "step-up", "one-leg"],
    ),
    "leg_press": MovementPatternSpec(
        name="leg_press",
        family=PatternFamily.LOWER,
        primary_muscles=["quads", "glutes"],
        description="Machine leg press (45° or horizontal)",
        env_preference={
            "full_gym": ["machine"],
            "home_gym": ["dumbbell"],  # substitute: goblet squat
            "bodyweight_only": ["bodyweight"],  # substitute: wall sit
        },
        detection_keywords=["leg-press", "45-degree-leg-press"],
    ),
    "hip_thrust": MovementPatternSpec(
        name="hip_thrust",
        family=PatternFamily.LOWER,
        primary_muscles=["glutes", "hamstrings"],
        description="Hip thrust / glute bridge pattern",
        env_preference={
            "full_gym": ["barbell", "dumbbell", "kettlebell", "bodyweight"],
            "home_gym": ["barbell", "dumbbell", "kettlebell", "bodyweight"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["hip-thrust", "glute-bridge"],
    ),
    # === Lower body isolation ===
    "knee_flexion": MovementPatternSpec(
        name="knee_flexion",
        family=PatternFamily.LOWER,
        primary_muscles=["hamstrings"],
        description="Leg curl (seated, lying, single-leg)",
        env_preference={
            "full_gym": ["machine", "cable", "dumbbell", "bodyweight"],
            "home_gym": ["dumbbell", "bodyweight", "bands"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["leg-curl", "hamstring-curl", "nordic",
                            # v3.1.4 H5 fix: add "single-leg-curl" so
                            # single-leg hamstring curls score 115 (100+15)
                            # beating the generic "single-leg" keyword (110)
                            # in the single_leg pattern. Without this,
                            # "Single Leg Curl" was mis-bucketed as
                            # single_leg instead of knee_flexion.
                            "single-leg-curl"],
    ),
    "knee_extension": MovementPatternSpec(
        name="knee_extension",
        family=PatternFamily.LOWER,
        primary_muscles=["quads"],
        description="Leg extension (machine isolation)",
        env_preference={
            "full_gym": ["machine", "cable"],
            "home_gym": ["dumbbell", "bodyweight"],  # substitute: split squat
            "bodyweight_only": ["bodyweight"],  # substitute: sissy squat
        },
        detection_keywords=["leg-extension"],
    ),
    "ankle_plantarflexion": MovementPatternSpec(
        name="ankle_plantarflexion",
        family=PatternFamily.LOWER,
        primary_muscles=["calves"],
        description="Calf raise (standing, seated, single-leg)",
        env_preference={
            "full_gym": ["machine", "barbell", "dumbbell", "bodyweight"],
            "home_gym": ["dumbbell", "barbell", "bodyweight"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["calf-raise", "toe-raise"],
    ),
    # === Upper body push ===
    "horizontal_push": MovementPatternSpec(
        name="horizontal_push",
        family=PatternFamily.PUSH,
        primary_muscles=["chest", "triceps", "shoulders"],
        description="Bench press / flat press pattern",
        env_preference={
            "full_gym": ["barbell", "dumbbell", "machine", "cable", "bodyweight"],
            "home_gym": ["barbell", "dumbbell", "bodyweight"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["bench-press", "chest-press", "push-up", "pushup"],  # removed "dumbbell-press" (caused seated-dumbbell-press/shoulder press to miscategorize as horizontal_push)
    ),
    "horizontal_push_dumbbell": MovementPatternSpec(
        name="horizontal_push_dumbbell",
        family=PatternFamily.PUSH,
        primary_muscles=["chest", "triceps", "shoulders"],
        description="Dumbbell bench press variant",
        env_preference={
            "full_gym": ["dumbbell", "barbell", "machine", "bodyweight"],
            "home_gym": ["dumbbell", "barbell", "bodyweight"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["dumbbell-bench-press", "dumbbell-chest-press"],
    ),
    "incline_push": MovementPatternSpec(
        name="incline_push",
        family=PatternFamily.PUSH,
        primary_muscles=["chest", "shoulders", "triceps"],
        description="Incline press (upper chest emphasis)",
        env_preference={
            "full_gym": ["barbell", "dumbbell", "machine", "cable", "bodyweight"],
            "home_gym": ["dumbbell", "barbell", "bodyweight"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["incline", "incline-press", "incline-push"],
    ),
    "decline_push": MovementPatternSpec(
        name="decline_push",
        family=PatternFamily.PUSH,
        primary_muscles=["chest", "triceps"],
        description="Decline press (lower chest emphasis)",
        env_preference={
            "full_gym": ["barbell", "dumbbell", "machine", "bodyweight"],
            "home_gym": ["dumbbell", "barbell", "bodyweight"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["decline"],
    ),
    "vertical_push": MovementPatternSpec(
        name="vertical_push",
        family=PatternFamily.SHOULDERS,
        primary_muscles=["shoulders", "triceps", "abs"],
        description="Overhead press (military, dumbbell, push press)",
        env_preference={
            "full_gym": ["barbell", "dumbbell", "machine", "kettlebell", "bodyweight"],
            "home_gym": ["barbell", "dumbbell", "kettlebell", "bodyweight"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["overhead-press", "shoulder-press", "military-press", "arnold-press", "pike-push"],
    ),
    "vertical_push_dumbbell": MovementPatternSpec(
        name="vertical_push_dumbbell",
        family=PatternFamily.SHOULDERS,
        primary_muscles=["shoulders", "triceps"],
        description="Dumbbell overhead press variant",
        env_preference={
            "full_gym": ["dumbbell", "barbell", "machine", "kettlebell"],
            "home_gym": ["dumbbell", "barbell", "kettlebell"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["dumbbell-press", "seated-dumbbell-press", "standing-dumbbell-press"],
    ),
    # === Upper body pull ===
    "horizontal_pull": MovementPatternSpec(
        name="horizontal_pull",
        family=PatternFamily.PULL,
        primary_muscles=["upper_back", "lats", "biceps"],
        description="Bent-over row / T-bar row pattern",
        env_preference={
            "full_gym": ["barbell", "dumbbell", "cable", "machine", "bodyweight"],
            "home_gym": ["barbell", "dumbbell", "bodyweight"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["bent-over", "row", "pendlay", "t-bar"],
    ),
    "pendlay_row": MovementPatternSpec(
        name="pendlay_row",
        family=PatternFamily.PULL,
        primary_muscles=["upper_back", "lats", "biceps"],
        description="Pendlay row (dead-stop barbell row)",
        env_preference={
            "full_gym": ["barbell"],
            "home_gym": ["barbell"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["pendlay"],
    ),
    "chest_supported_row": MovementPatternSpec(
        name="chest_supported_row",
        family=PatternFamily.PULL,
        primary_muscles=["upper_back", "lats", "biceps"],
        description="Chest-supported row (less lower-back stress)",
        env_preference={
            "full_gym": ["dumbbell", "machine", "cable", "barbell"],
            "home_gym": ["dumbbell", "barbell"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["chest-supported", "incline-row"],
    ),
    "seated_row": MovementPatternSpec(
        name="seated_row",
        family=PatternFamily.PULL,
        primary_muscles=["upper_back", "lats", "biceps"],
        description="Seated cable row",
        env_preference={
            "full_gym": ["cable", "machine"],
            "home_gym": ["dumbbell", "bands"],  # substitute: DB row
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["seated-row", "cable-row"],
    ),
    "inverted_row": MovementPatternSpec(
        name="inverted_row",
        family=PatternFamily.PULL,
        primary_muscles=["upper_back", "lats", "biceps"],
        description="Inverted row (bodyweight horizontal pull)",
        env_preference={
            "full_gym": ["bodyweight"],
            "home_gym": ["bodyweight"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["inverted-row", "bodyweight-row"],
    ),
    "vertical_pull": MovementPatternSpec(
        name="vertical_pull",
        family=PatternFamily.PULL,
        primary_muscles=["lats", "biceps", "upper_back"],
        description="Pull-up / chin-up / lat pulldown pattern",
        env_preference={
            "full_gym": ["bodyweight", "cable", "machine"],
            "home_gym": ["bodyweight", "bands"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["pull-up", "pulldown", "pull-down", "chin-up"],
    ),
    # === Shoulders / arms isolation ===
    "lateral_raise": MovementPatternSpec(
        name="lateral_raise",
        family=PatternFamily.SHOULDERS,
        primary_muscles=["shoulders"],
        description="Lateral raise (side deltoid isolation)",
        env_preference={
            "full_gym": ["dumbbell", "cable", "machine"],
            "home_gym": ["dumbbell", "bands"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["lateral-raise", "side-raise"],
    ),
    "rear_delt": MovementPatternSpec(
        name="rear_delt",
        family=PatternFamily.PULL,
        primary_muscles=["shoulders"],
        description="Rear delt fly / face pull",
        env_preference={
            "full_gym": ["cable", "dumbbell", "machine", "bands"],
            "home_gym": ["dumbbell", "bands"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["face-pull", "rear-delt", "reverse-fly", "rear-fly"],
    ),
    "front_raise": MovementPatternSpec(
        name="front_raise",
        family=PatternFamily.SHOULDERS,
        primary_muscles=["shoulders"],
        description="Front raise (anterior deltoid isolation)",
        env_preference={
            "full_gym": ["dumbbell", "barbell", "cable"],
            "home_gym": ["dumbbell", "barbell", "bands"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["front-raise"],
    ),
    "chest_fly": MovementPatternSpec(
        name="chest_fly",
        family=PatternFamily.PUSH,
        primary_muscles=["chest"],
        description="Chest fly (dumbbell, cable, pec deck)",
        env_preference={
            "full_gym": ["dumbbell", "cable", "machine"],
            "home_gym": ["dumbbell", "bands"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["fly", "pec-dec", "crossover"],
    ),
    "chest_dip": MovementPatternSpec(
        name="chest_dip",
        family=PatternFamily.PUSH,
        primary_muscles=["chest", "triceps"],
        description="Chest dip (bodyweight pushing)",
        env_preference={
            "full_gym": ["bodyweight"],
            "home_gym": ["bodyweight"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["chest-dip", "weighted-chest-dip"],
    ),
    "push_up": MovementPatternSpec(
        name="push_up",
        family=PatternFamily.PUSH,
        primary_muscles=["chest", "triceps", "shoulders", "abs"],
        description="Push-up (bodyweight horizontal push)",
        env_preference={
            "full_gym": ["bodyweight"],
            "home_gym": ["bodyweight"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["push-up", "pushup"],
    ),
    "elbow_flexion": MovementPatternSpec(
        name="elbow_flexion",
        family=PatternFamily.ARMS,
        primary_muscles=["biceps"],
        description="Bicep curl (barbell, dumbbell, cable, EZ bar)",
        env_preference={
            "full_gym": ["dumbbell", "barbell", "cable", "ez_bar"],
            "home_gym": ["dumbbell", "barbell", "ez_bar", "bands"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["curl", "bicep-curl", "preacher-curl", "hammer-curl"],
    ),
    "hammer_curl": MovementPatternSpec(
        name="hammer_curl",
        family=PatternFamily.ARMS,
        primary_muscles=["biceps", "forearms"],
        description="Hammer curl (neutral grip)",
        env_preference={
            "full_gym": ["dumbbell", "cable", "rope"],
            "home_gym": ["dumbbell", "bands"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["hammer-curl"],
    ),
    "preacher_curl": MovementPatternSpec(
        name="preacher_curl",
        family=PatternFamily.ARMS,
        primary_muscles=["biceps"],
        description="Preacher curl (preacher bench isolation)",
        env_preference={
            "full_gym": ["ez_bar", "barbell", "dumbbell", "machine"],
            "home_gym": ["ez_bar", "dumbbell"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["preacher-curl"],
    ),
    "elbow_extension": MovementPatternSpec(
        name="elbow_extension",
        family=PatternFamily.ARMS,
        primary_muscles=["triceps"],
        description="Tricep extension / pushdown",
        env_preference={
            "full_gym": ["cable", "dumbbell", "barbell", "ez_bar"],
            "home_gym": ["dumbbell", "ez_bar", "barbell", "bands"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["tricep", "pushdown", "extension", "skullcrusher", "kickback"],
    ),
    "overhead_tricep": MovementPatternSpec(
        name="overhead_tricep",
        family=PatternFamily.ARMS,
        primary_muscles=["triceps"],
        description="Overhead tricep extension (long head emphasis)",
        env_preference={
            "full_gym": ["dumbbell", "cable", "ez_bar", "rope"],
            "home_gym": ["dumbbell", "ez_bar", "bands"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["overhead-tricep", "overhead-extension"],
    ),
    "tricep_dip": MovementPatternSpec(
        name="tricep_dip",
        family=PatternFamily.ARMS,
        primary_muscles=["triceps"],
        description="Tricep dip (bench dip or parallel bar dip)",
        env_preference={
            "full_gym": ["bodyweight"],
            "home_gym": ["bodyweight"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["tricep-dip", "bench-dip"],
    ),
    # === Core ===
    "core_anti_extension": MovementPatternSpec(
        name="core_anti_extension",
        family=PatternFamily.CORE,
        primary_muscles=["abs"],
        description="Plank / ab wheel rollout (anti-extension)",
        env_preference={
            "full_gym": ["bodyweight", "cable", "machine"],
            "home_gym": ["bodyweight", "bands"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["plank", "hover", "ab-wheel", "rollout", "stir"],
    ),
    "core_anti_rotation": MovementPatternSpec(
        name="core_anti_rotation",
        family=PatternFamily.CORE,
        primary_muscles=["abs", "obliques"],
        description="Pallof press / anti-rotation cable",
        env_preference={
            "full_gym": ["cable", "bands"],
            "home_gym": ["bands"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["pallof", "anti-rotation", "chop", "lift"],
    ),
    "core_flexion": MovementPatternSpec(
        name="core_flexion",
        family=PatternFamily.CORE,
        primary_muscles=["abs"],
        description="Crunch / sit-up / leg raise (spinal flexion)",
        env_preference={
            "full_gym": ["bodyweight", "cable", "machine"],
            "home_gym": ["bodyweight", "bands"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["crunch", "sit-up", "leg-raise", "russian-twist", "knee-raise"],
    ),
    "hip_flexion": MovementPatternSpec(
        name="hip_flexion",
        family=PatternFamily.CORE,
        primary_muscles=["abs", "hip_flexors"],
        description="Hanging leg raise / hip flexion",
        env_preference={
            "full_gym": ["bodyweight", "cable"],
            "home_gym": ["bodyweight", "bands"],
            "bodyweight_only": ["bodyweight", "bands"],
        },
        detection_keywords=["hanging-leg", "hip-raise", "knee-tuck"],
    ),
    # === Mobility ===
    "mobility": MovementPatternSpec(
        name="mobility",
        family=PatternFamily.MOBILITY,
        primary_muscles=[],
        description="Mobility / stretching / foam rolling",
        env_preference={
            "full_gym": ["foam_roll", "bodyweight", "bands"],
            "home_gym": ["foam_roll", "bodyweight", "bands"],
            "bodyweight_only": ["bodyweight", "bands", "foam_roll"],
        },
        detection_keywords=["stretch", "mobil", "foam-roll", "tiger-tail", "lacrosse"],
    ),
}


# === Pattern detection ===

def _detect_pattern(exercise: Exercise) -> str:
    """
    Detect the canonical movement pattern for an exercise.

    Strategy (v3.1.4 — exercise_type FIRST):
      0. Match by ``exercise_type`` for non-strength categories
         (cardio / conditioning / plyometrics / warmup / activation / SMR /
         stretching). These must be checked BEFORE keyword matching so a
         "Concept 2 Rowing Machine" (Conditioning) doesn't get mis-bucketed
         as ``horizontal_pull`` just because the slug contains "row".
      1. Match by slug against detection_keywords (most reliable)
      2. Match by name against detection_keywords (fallback)
      3. Match by force_type + primary_muscle (last resort)
      4. Default: "mobility" if exercise_type is mobility/stretching
      5. Default: "core_flexion" for abs-targeted bodyweight
      6. Default: "horizontal_push" / "horizontal_pull" based on force
    """
    # 0. Non-strength exercise_type → short-circuit before keyword matching.
    # v3.1.4 CRITICAL FIX: previously this check ran AFTER keyword matching
    # (step 4-5 below), so 31/39 Conditioning, 33/33 Plyometrics, 18/50
    # Warmup, and 3/7 Activation exercises whose slugs contained strength
    # keywords (e.g. "row", "press", "squat") were mis-bucketed as strength
    # patterns. Moving the check to the top ensures every exercise with a
    # non-strength exercise_type gets the right pattern regardless of slug.
    if exercise.exercise_type:
        et = exercise.exercise_type.lower()
        # Cardio / conditioning / plyometrics → "cardio" pattern (the
        # selector already filters CARDIO-category exercises out of strength
        # slots, so the pattern is used only for volume tracking + reporting).
        if "cardio" in et or "conditioning" in et or "plyometric" in et:
            return "cardio"
        # Mobility / warmup / activation / SMR / stretching → "mobility".
        if any(k in et for k in (
            "mobility", "stretch", "warm", "smr", "activation", "self-massage",
            "foam roll",
        )):
            return "mobility"

    slug = (exercise.slug or "").lower()
    name = exercise.name.lower()
    combined = f"{slug} {name}"

    # 1+2. Keyword match
    best_match = None
    best_score = 0
    for pattern_name, spec in MOVEMENT_PATTERNS.items():
        for kw in spec.detection_keywords:
            kw_lower = kw.lower()
            if kw_lower in slug:
                score = 100 + len(kw_lower)  # slug match scores highest
            elif kw_lower in combined:
                score = len(kw_lower)  # name match scores by keyword length
            else:
                continue
            if score > best_score:
                best_score = score
                best_match = pattern_name

    if best_match:
        return best_match

    # 3. Force type + primary muscle
    if exercise.force_type:
        ft = exercise.force_type.lower().split("(")[0].strip()
        primary = (exercise.muscle_groups[0] if exercise.muscle_groups else "").lower()
        if ft == "push":
            if primary in ("chest",):
                return "horizontal_push"
            if primary in ("shoulders",):
                return "vertical_push"
            if primary in ("triceps",):
                return "elbow_extension"
            if primary in ("quads",):
                return "squat"
        elif ft == "pull":
            if primary in ("upper_back", "lats", "middle_back"):
                return "horizontal_pull"
            if primary in ("biceps",):
                return "elbow_flexion"
            if primary in ("hamstrings",):
                return "hinge"
        elif ft == "hinge":
            return "hinge"

    # 4. Mobility (defensive — already handled in step 0 for typed exercises,
    # but kept for exercises whose exercise_type is None yet category is set).
    if exercise.exercise_type and "mobility" in exercise.exercise_type.lower():
        return "mobility"
    if exercise.exercise_type and "stretch" in exercise.exercise_type.lower():
        return "mobility"

    # 5. Cardio (defensive — already handled in step 0).
    if exercise.exercise_type and "cardio" in exercise.exercise_type.lower():
        return "cardio"

    # 6. Default by category
    if exercise.category == ExerciseCategory.CARDIO:
        return "cardio"  # was "mobility"
    if exercise.category == ExerciseCategory.MOBILITY:
        return "mobility"

    # Default: pick by primary muscle
    if exercise.muscle_groups:
        primary = exercise.muscle_groups[0].lower()
        muscle_to_pattern = {
            "chest": "horizontal_push",
            "shoulders": "vertical_push",
            "triceps": "elbow_extension",
            "biceps": "elbow_flexion",
            "upper_back": "horizontal_pull",
            "lats": "vertical_pull",
            "middle_back": "horizontal_pull",
            "quads": "squat",
            "hamstrings": "hinge",
            "glutes": "hip_thrust",
            "calves": "ankle_plantarflexion",
            "abs": "core_flexion",
            "obliques": "core_anti_rotation",
            "forearms": "elbow_flexion",
        }
        return muscle_to_pattern.get(primary, "mobility")

    return "mobility"


# === Category info dataclass ===

@dataclass
class ExerciseCategoryInfo:
    """Full categorization of an exercise."""
    exercise: Exercise
    movement_pattern: str
    pattern_family: PatternFamily
    primary_muscles: list[str]
    environment_preferences: dict[str, list[str]]


# === Cache ===
# Pattern detection is deterministic per exercise; cache by slug (or name as
# fallback). Kept as a module-level dict because `Exercise` is a regular
# @dataclass (not frozen), so @lru_cache can't be applied directly to a
# function that takes an Exercise. The dict is clearable via
# `_clear_pattern_cache()`, which is registered with
# `exercise_library._clear_exercise_cache` so tests that monkey-patch the
# exercise JSON path also invalidate pattern detection.
_pattern_cache: dict[str, str] = {}


def _clear_pattern_cache() -> None:
    """Clear the movement-pattern cache (for tests)."""
    _pattern_cache.clear()


def get_movement_pattern(exercise: Exercise) -> str:
    """Get the canonical movement pattern for an exercise (cached)."""
    key = exercise.slug or exercise.name
    if key in _pattern_cache:
        return _pattern_cache[key]
    pattern = _detect_pattern(exercise)
    _pattern_cache[key] = pattern
    return pattern


def get_pattern_family(pattern: str) -> PatternFamily:
    """Get the broader family for a movement pattern."""
    spec = MOVEMENT_PATTERNS.get(pattern)
    return spec.family if spec else PatternFamily.MOBILITY


def categorize_exercise(exercise: Exercise) -> ExerciseCategoryInfo:
    """Get full categorization info for an exercise."""
    pattern = get_movement_pattern(exercise)
    spec = MOVEMENT_PATTERNS.get(pattern, MOVEMENT_PATTERNS["mobility"])
    return ExerciseCategoryInfo(
        exercise=exercise,
        movement_pattern=pattern,
        pattern_family=spec.family,
        primary_muscles=spec.primary_muscles,
        environment_preferences=spec.env_preference,
    )


# === Environment-aware preferred equipment ===

def get_environment_preferred_equipment(
    pattern: str,
    environment: str,
) -> list[str]:
    """
    Get the ordered list of preferred equipment for a pattern in an environment.

    Args:
      pattern: movement pattern name (e.g. "squat", "horizontal_push")
      environment: "full_gym" / "home_gym" / "bodyweight_only"

    Returns ordered list of equipment strings (best first).
    """
    spec = MOVEMENT_PATTERNS.get(pattern)
    if not spec:
        return ["bodyweight", "dumbbell", "barbell"]
    return spec.env_preference.get(environment, ["bodyweight"])


# === Swap system ===

def get_swappable_exercises(
    exercise: Exercise,
    equipment_allowed: set[str] | None = None,
    exclude_slugs: set[str] | None = None,
    limit: int = 10,
    experience_cap: str | None = None,
) -> list[Exercise]:
    """
    Get exercises that are swappable with the given exercise.

    Two exercises are swappable if they:
      1. Share the same movement pattern
      2. Share at least one primary muscle
      3. Use equipment in `equipment_allowed` (if specified)
      4. Are not in `exclude_slugs` (if specified)
      5. Are at or below `experience_cap` (if specified)

    Args:
      exercise: the reference exercise to find swaps for
      equipment_allowed: set of allowed equipment strings (None = no filter)
      exclude_slugs: set of slugs to exclude (e.g. the exercise itself + already-used)
      limit: max number of swaps to return (default 10)
      experience_cap: max experience level ("Beginner", "Intermediate", "Advanced")

    Returns list of Exercises, sorted by:
      1. Equipment preference for the pattern (best first)
      2. Beginner-friendliness
      3. Popularity (views, desc)
      4. Alphabetical name
    """
    from ..models.training import ExperienceLevel
    from .exercise_library import EXERCISES

    pattern = get_movement_pattern(exercise)
    spec = MOVEMENT_PATTERNS.get(pattern)
    if not spec:
        return []

    # Determine target primary muscles (intersection of slot + spec)
    target_muscles = set(exercise.muscle_groups) & set(spec.primary_muscles)
    if not target_muscles:
        # If the exercise's muscle_groups don't overlap with spec's,
        # use the exercise's own muscle_groups (rare edge case)
        target_muscles = set(exercise.muscle_groups)

    exclude_slugs = exclude_slugs or set()
    if exercise.slug:
        exclude_slugs.add(exercise.slug)

    # Experience rank helper
    exp_rank = {
        ExperienceLevel.BEGINNER: 0,
        ExperienceLevel.INTERMEDIATE: 1,
        ExperienceLevel.ADVANCED: 2,
    }
    max_rank = 2
    if experience_cap == "Beginner":
        max_rank = 0
    elif experience_cap == "Intermediate":
        max_rank = 1

    # Find candidates
    candidates: list[Exercise] = []
    for ex in EXERCISES:
        if ex.slug and ex.slug in exclude_slugs:
            continue
        if equipment_allowed is not None and ex.equipment not in equipment_allowed:
            continue
        # Must share the same movement pattern
        ex_pattern = get_movement_pattern(ex)
        if ex_pattern != pattern:
            continue
        # Must share at least one target muscle
        ex_muscles = set(ex.muscle_groups) | set(ex.secondary_muscles)
        if not (ex_muscles & target_muscles):
            continue
        # Experience filter
        if ex.experience_level and exp_rank.get(ex.experience_level, 1) > max_rank:
            continue
        candidates.append(ex)

    # Sort by equipment preference + beginner-friendliness + popularity
    # Determine the environment from equipment_allowed
    env = _infer_environment(equipment_allowed)
    preferred_order = get_environment_preferred_equipment(pattern, env)

    # use shared _view_count from _utils (was a local duplicate).
    from ._utils import parse_view_count as _view_count

    def _sort_key(ex: Exercise) -> tuple:
        # Equipment preference rank (lower = better)
        try:
            equip_rank = preferred_order.index(ex.equipment)
        except ValueError:
            equip_rank = 99
        # Beginner-friendliness (Beginner=0 first)
        exp_rank_val = exp_rank.get(ex.experience_level, 1) if ex.experience_level else 1
        return (equip_rank, exp_rank_val, -_view_count(ex), ex.name.lower())

    candidates.sort(key=_sort_key)
    return candidates[:limit]


def _infer_environment(equipment_allowed: set[str] | None) -> str:
    """Infer the environment name from the equipment_allowed set."""
    if equipment_allowed is None:
        return "full_gym"
    if equipment_allowed <= {"bodyweight", "bands"}:
        return "bodyweight_only"
    # Full gym has machines + cables
    if "machine" in equipment_allowed and "cable" in equipment_allowed:
        return "full_gym"
    return "home_gym"


__all__ = [
    "PatternFamily",
    "MovementPatternSpec",
    "ExerciseCategoryInfo",
    "MOVEMENT_PATTERNS",
    "categorize_exercise",
    "get_movement_pattern",
    "get_pattern_family",
    "get_environment_preferred_equipment",
    "get_swappable_exercises",
]

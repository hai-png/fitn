"""
Training architect — Phase-3 clean top-level orchestrator.

This module replaces the legacy planner.py with a systematic, declarative
approach:

    profile + assessment
        ↓
    1. Derive TrainingGoal from assessment.recommended_strategy + profile.primary_goal
    2. Pick SplitDesign based on (training_days_per_week, experience, goal)
    3. Pick ProgressionScheme based on experience
    4. Decide PlanType (STANDARD vs PROGRAM) — auto or user-specified
    5. Apply muscle_focus adjustments to split templates (add extra slots)
    6. For each WorkoutTemplate:
         a. Fill each MovementPatternSlot via exercise_selector
         b. Apply periodization (reps/rest/RPE) based on goal + progression
    7. Assemble into Mesocycle(s) + Microcycle(s) + Workout(s)
    8. Compute weekly volume summary
    9. Return TrainingPlan

Inputs (all from profile + assessment):
  - assessment output (BF%, FFMI, strategy)
  - goal (from profile.primary_goal)
  - experience level (from profile.training_status)
  - number of workout days (from profile.training_days_per_week)
  - equipment access (from profile.equipment_access)
  - optional muscle group focus (new parameter, default None)

Outputs:
  - STANDARD plan: ongoing rotation (1 mesocycle, 1 microcycle, 0 duration)
  - PROGRAM plan: time-bound (1+ mesocycles, defined duration_weeks)
"""
from __future__ import annotations

import logging
from typing import Optional

from ..models.profile import (
    UserProfile, TrainingStatus, PrimaryGoal, EquipmentAccess,
)
from ..models.assessment import AssessmentResult, RecommendedStrategy
from ..models.training import (
    TrainingPlan, Mesocycle, Microcycle, Workout, WorkoutExercise,
    Exercise, ExerciseCategory,
    SplitType, PlanType, TrainingGoal, ProgressionScheme,
)
from .exercise_selector import (
    select_exercise_for_slot,
    get_equipment_allowed_set,
)
from .split_designs import (
    SplitDesign, WorkoutTemplate, MovementPatternSlot,
    ALL_SPLITS, get_splits_for_days,
    _compound_primary, _compound_secondary, _accessory,
)
from .periodization import (
    apply_periodization,
    get_mesocycle_length,
    get_program_duration_weeks,
    get_block_phases_for_program,
)
from .exercise_library import EXERCISES


_log = logging.getLogger(__name__)


# === Step 1: derive training goal ===

def _derive_training_goal(profile: UserProfile, assessment: AssessmentResult) -> TrainingGoal:
    """
    Map (profile.primary_goal, assessment.recommended_strategy) → TrainingGoal.

    The recommended_strategy is the assessment's expert opinion (e.g. "you
    should cut even though you said maintenance"). The profile's primary_goal
    is the user's stated intent. We trust the assessment's strategy when
    they conflict, since the assessment has safety overrides.

    Tier 2.18 fix: now honors profile.primary_goal=STRENGTH. Previously the
    function only read assessment.recommended_strategy (which has no STRENGTH
    value), so strength-focused users were silently remapped to HYPERTROPHY.
    Now: if the user explicitly set primary_goal=STRENGTH AND the assessment
    strategy is MAINTENANCE/BULK/RECOMP (not a safety-override CUT), we
    honor the strength request.
    """
    strategy = assessment.recommended_strategy

    # Tier 2.18: honor explicit STRENGTH goal when it's safe to do so.
    # The assessment's safety overrides (CUT for obese users, HABIT_CHANGE_FIRST
    # for obese beginners) always take precedence. But for maintenance/bulk/
    # recomp strategies, a user who explicitly wants strength gets it.
    if profile.primary_goal == PrimaryGoal.STRENGTH:
        if strategy in (RecommendedStrategy.MAINTENANCE, RecommendedStrategy.BULK,
                        RecommendedStrategy.RECOMP):
            _log.info(
                "User explicitly requested STRENGTH goal; assessment strategy=%s "
                "is compatible — honoring STRENGTH.", strategy.value
            )
            return TrainingGoal.STRENGTH
        else:
            _log.info(
                "User requested STRENGTH but assessment strategy=%s takes "
                "precedence (safety override). Using assessment strategy.",
                strategy.value
            )

    mapping = {
        RecommendedStrategy.CUT:               TrainingGoal.FAT_LOSS,
        RecommendedStrategy.BULK:              TrainingGoal.MUSCLE_GAIN,
        RecommendedStrategy.RECOMP:            TrainingGoal.RECOMP,
        RecommendedStrategy.MAINTENANCE:       TrainingGoal.MAINTENANCE,
        RecommendedStrategy.HABIT_CHANGE_FIRST: TrainingGoal.GENERAL_FITNESS,
    }
    return mapping.get(strategy, TrainingGoal.HYPERTROPHY)


# === Step 2: pick split ===

def _pick_split(
    days_per_week: int,
    experience: TrainingStatus,
    goal: TrainingGoal,
) -> SplitDesign:
    """
    Pick the best SplitDesign for the given inputs.

    Selection logic:
      1. Get all splits matching days_per_week
      2. Filter by suitable_for_experience (must include the user's level)
      3. Filter by suitable_for_goals (must include the user's goal)
      4. If multiple match, prefer in this order:
         - FULL_BODY for beginners
         - UPPER_LOWER for novices/intermediate
         - PPL_X2 for advanced
         - BODY_PART only for advanced hypertrophy
      5. If no exact match, fall back to the first available
    """
    candidates = get_splits_for_days(days_per_week)

    if not candidates:
        # Phase-6 fix: raise ValueError for unsupported frequencies (1, 7 days).
        # Previously silently fell back to a different day-count split, which
        # meant `TrainingPlan.training_days_per_week` lied and `rest_days`
        # were misaligned. Supported: 2, 3, 4, 5, 6 days/week.
        if days_per_week < 2 or days_per_week > 6:
            raise ValueError(
                f"Unsupported training_days_per_week={days_per_week}. "
                f"Supported values: 2, 3, 4, 5, 6. "
                f"1-day and 7-day splits are not yet implemented."
            )
        # For 2-6 days with no exact match (shouldn't happen, but defensive):
        closest = min(ALL_SPLITS, key=lambda s: abs(s.days_per_week - days_per_week))
        _log.warning(
            "No split for %d days/week; falling back to %s (%d days)",
            days_per_week, closest.name, closest.days_per_week,
        )
        return closest

    # Filter by experience + goal
    filtered = [
        s for s in candidates
        if experience in s.suitable_for_experience
        and goal in s.suitable_for_goals
    ]
    if not filtered:
        # Try just experience
        filtered = [s for s in candidates if experience in s.suitable_for_experience]
    if not filtered:
        # Try just goal
        filtered = [s for s in candidates if goal in s.suitable_for_goals]
    if not filtered:
        filtered = candidates

    # Prefer specific splits by experience
    # Note: days_per_week filter already happened, so preference only matters
    # when multiple split types match the same day count.
    preference_order = {
        TrainingStatus.BEGINNER: [SplitType.FULL_BODY, SplitType.UPPER_LOWER, SplitType.PPL],
        TrainingStatus.NOVICE: [SplitType.FULL_BODY, SplitType.UPPER_LOWER, SplitType.PPL,
                                 SplitType.PUSH_PULL],
        TrainingStatus.INTERMEDIATE: [SplitType.UPPER_LOWER, SplitType.FULL_BODY,
                                       SplitType.PPL, SplitType.PUSH_PULL_LEGS_UPPER_LOWER,
                                       SplitType.PPL_X2],
        TrainingStatus.ADVANCED: [SplitType.PPL_X2, SplitType.PUSH_PULL_LEGS_UPPER_LOWER,
                                   SplitType.BODY_PART, SplitType.UPPER_LOWER,
                                   SplitType.FULL_BODY],
    }
    preferred = preference_order.get(experience, [SplitType.UPPER_LOWER])
    for split_type in preferred:
        for s in filtered:
            if s.split_type == split_type:
                return s

    return filtered[0]


# === Step 3: pick progression scheme ===

def _pick_progression(
    experience: TrainingStatus,
    goal: Optional[TrainingGoal] = None,
) -> ProgressionScheme:
    """Map experience (and optionally goal) to progression scheme.

    Phase-6 fix: STRENGTH goal now uses BLOCK periodization for INTERMEDIATE
    and ADVANCED (per RippedBody Tables 7.11-7.13, strength blocks are
    inherently block-periodized: volume → load → peak). Previously
    intermediate strength athletes got DUP, which is suboptimal for peaking
    strength.
    """
    # Phase-6: strength goal → block periodization for non-beginners
    if goal == TrainingGoal.STRENGTH and experience in (
        TrainingStatus.INTERMEDIATE, TrainingStatus.ADVANCED,
    ):
        return ProgressionScheme.BLOCK
    return {
        TrainingStatus.BEGINNER:     ProgressionScheme.LINEAR,
        TrainingStatus.NOVICE:       ProgressionScheme.LINEAR,
        TrainingStatus.INTERMEDIATE: ProgressionScheme.DUP,
        TrainingStatus.ADVANCED:     ProgressionScheme.BLOCK,
    }.get(experience, ProgressionScheme.LINEAR)


# === Step 4: decide plan type ===

def _decide_plan_type(
    profile: UserProfile,
    goal: TrainingGoal,
    user_choice: Optional[PlanType] = None,
) -> PlanType:
    """
    Decide whether to produce a STANDARD rotation or a PROGRAM.

    Auto-rule:
      - HABIT_CHANGE_FIRST / GENERAL_FITNESS / MAINTENANCE → STANDARD
      - CUT / BULK / RECOMP / MUSCLE_GAIN / STRENGTH → PROGRAM

    User can override with the `plan_type` parameter.
    """
    if user_choice is not None:
        return user_choice

    if goal in (TrainingGoal.GENERAL_FITNESS, TrainingGoal.MAINTENANCE):
        return PlanType.STANDARD
    return PlanType.PROGRAM


# === Step 5: apply muscle_focus adjustments ===

# Maps muscle group → pattern + accessory slot to add
_FOCUS_ACCESSORIES: dict[str, list[MovementPatternSlot]] = {
    "chest": [
        _accessory("chest", "chest_fly", sets=3, is_focus=True),
        _accessory("chest", "incline_push", sets=3, is_focus=True),
    ],
    "back": [
        _accessory("upper_back", "seated_row", sets=3, is_focus=True),
        _accessory("lats", "vertical_pull", sets=3, is_focus=True),
    ],
    "quads": [
        _accessory("quads", "knee_extension", sets=3, is_focus=True),
        _compound_secondary("quads", "front_squat", sets=3, is_focus=True),
    ],
    "hamstrings": [
        _accessory("hamstrings", "knee_flexion", sets=3, is_focus=True),
        _accessory("hamstrings", "romanian_deadlift", sets=3, is_focus=True),
    ],
    "glutes": [
        _compound_secondary("glutes", "hip_thrust", sets=3, is_focus=True),
        _accessory("glutes", "glute_isolation", sets=3, is_focus=True),
    ],
    "shoulders": [
        _accessory("shoulders", "lateral_raise", sets=4, is_focus=True),
        _accessory("shoulders", "rear_delt", sets=3, is_focus=True),
    ],
    "arms": [
        _accessory("biceps", "elbow_flexion", sets=4, is_focus=True),
        _accessory("triceps", "elbow_extension", sets=4, is_focus=True),
    ],
    "biceps": [_accessory("biceps", "elbow_flexion", sets=4, is_focus=True)],
    "triceps": [_accessory("triceps", "elbow_extension", sets=4, is_focus=True)],
    "calves": [_accessory("calves", "ankle_plantarflexion", sets=5, is_focus=True)],
    "abs": [
        _accessory("abs", "core_anti_extension", sets=3, is_focus=True),
        _accessory("abs", "core_anti_rotation", sets=3, is_focus=True),
    ],
}


def _apply_muscle_focus(
    split: SplitDesign,
    muscle_focus: list[str],
) -> SplitDesign:
    """
    Return a new SplitDesign with extra accessory slots for the focus muscles.

    Strategy: for each focus muscle, add the corresponding accessory slots to
    the workout(s) that already train that muscle. Distribute evenly so we
    don't overload one workout.
    """
    if not muscle_focus:
        return split

    # Make a shallow copy of the split with deep-copied templates
    new_templates = []
    for tmpl in split.templates:
        new_slots = list(tmpl.slots)  # shallow copy of slots list
        new_templates.append(WorkoutTemplate(
            name=tmpl.name,
            focus=tmpl.focus,
            slots=new_slots,
            day_type=tmpl.day_type,
        ))

    new_split = SplitDesign(
        name=split.name + "_focused",
        split_type=split.split_type,
        days_per_week=split.days_per_week,
        description=split.description + f" (focus: {', '.join(muscle_focus)})",
        templates=new_templates,
        rest_days=list(split.rest_days),
        suitable_for_experience=list(split.suitable_for_experience),
        suitable_for_goals=list(split.suitable_for_goals),
    )

    # For each focus muscle, distribute the accessory slots across the workouts
    # that already train it
    # Tier 2.19 fix: muscle group alias map. 'back' expands to ['upper_back',
    # 'lats', 'lower_back', 'middle_back', 'traps'] so that slot matching works.
    _MUSCLE_ALIASES = {
        "back": ["upper_back", "lats", "lower_back", "middle_back", "traps"],
        "chest": ["chest"],
        "shoulders": ["shoulders", "side_delts", "rear_delts"],
        "arms": ["biceps", "triceps", "forearms"],
        "legs": ["quads", "hamstrings", "glutes", "calves"],
    }
    for muscle in muscle_focus:
        muscle_lower = muscle.lower()
        accessories = _FOCUS_ACCESSORIES.get(muscle_lower)
        if not accessories:
            _log.warning("Unknown muscle_focus '%s' — skipping", muscle)
            continue

        # Tier 2.19 fix: expand aliases so 'back' matches 'upper_back'/'lats' slots
        muscle_variants = _MUSCLE_ALIASES.get(muscle_lower, [muscle_lower])

        # Find which templates already train this muscle (or any alias)
        matching_templates = []
        for tmpl in new_split.templates:
            for slot in tmpl.slots:
                if (slot.primary_muscle in muscle_variants
                        or any(v in slot.secondary_muscles for v in muscle_variants)):
                    matching_templates.append(tmpl)
                    break

        if not matching_templates:
            # Add to all templates that target upper/lower body accordingly
            # Tier 2.19 fix: include the actual muscle tag names used in slots
            upper_muscles = {
                "chest", "back", "shoulders", "biceps", "triceps", "arms",
                "upper_back", "lats", "lower_back", "middle_back", "traps",
                "rear_delts", "side_delts",
            }
            lower_muscles = {"quads", "hamstrings", "glutes", "calves", "abs"}
            if muscle_lower in upper_muscles or any(v in upper_muscles for v in muscle_variants):
                matching_templates = [
                    t for t in new_split.templates
                    if any(s.primary_muscle in upper_muscles for s in t.slots)
                ]
            elif muscle_lower in lower_muscles or any(v in lower_muscles for v in muscle_variants):
                matching_templates = [
                    t for t in new_split.templates
                    if any(s.primary_muscle in lower_muscles for s in t.slots)
                ]
            else:
                matching_templates = new_split.templates[:1]

        # Distribute accessories round-robin across matching templates
        for i, acc in enumerate(accessories):
            target_tmpl = matching_templates[i % len(matching_templates)]
            target_tmpl.slots.append(acc)

    return new_split


# === Step 6: build workouts from templates ===

def _build_workout_from_template(
    template: WorkoutTemplate,
    day_number: int,
    equipment_allowed: set[str],
    user_experience: TrainingStatus,
) -> Workout:
    """
    Fill each slot in a WorkoutTemplate with a concrete Exercise.

    The exercise_selector picks the best match per slot; we exclude already-used
    slugs within the same workout for variety.
    """
    exercises: list[WorkoutExercise] = []
    used_slugs: set[str] = set()
    skipped: list[str] = []

    for slot in template.slots:
        ex = select_exercise_for_slot(
            slot=slot,
            equipment_allowed=equipment_allowed,
            user_experience=user_experience,
            exclude_slugs=used_slugs,
        )
        if ex is None:
            skipped.append(f"{slot.name} (no match)")
            continue

        if ex.slug:
            used_slugs.add(ex.slug)

        exercises.append(WorkoutExercise(
            exercise=ex,
            sets=slot.sets,
            reps="",          # filled by periodization
            rest_sec=0,       # filled by periodization
            rpe_target=None,  # filled by periodization
            notes="focus emphasis" if slot.is_focus_emphasis else "",
        ))

    # Tier 4.53 fix: extracted magic numbers to named constants.
    # 45 min base = warmup + transitions; 8 min per exercise = ~3 sets × 2.5 min.
    WORKOUT_BASE_DURATION_MIN = 45
    WORKOUT_MIN_PER_EXERCISE = 8
    est_duration = WORKOUT_BASE_DURATION_MIN + len(exercises) * WORKOUT_MIN_PER_EXERCISE

    return Workout(
        day_number=day_number,
        name=template.name,
        focus=template.focus,
        exercises=exercises,
        estimated_duration_min=est_duration,
        notes=(f"Skipped {len(skipped)} slot(s): {', '.join(skipped)}"
               if skipped else ""),
    )


def _build_workouts_for_split(
    split: SplitDesign,
    equipment_allowed: set[str],
    user_experience: TrainingStatus,
) -> list[Workout]:
    """Build all workouts for a split (one per template)."""
    workouts = []
    for i, tmpl in enumerate(split.templates, 1):
        w = _build_workout_from_template(
            template=tmpl,
            day_number=i,
            equipment_allowed=equipment_allowed,
            user_experience=user_experience,
        )
        workouts.append(w)
    return workouts


# === Step 7: build mesocycles ===

def _build_mesocycle(
    name: str,
    duration_weeks: int,
    progression: ProgressionScheme,
    base_workouts: list[Workout],
    goal: TrainingGoal,
    deload: bool = True,
    block_phase: str | None = None,
) -> Mesocycle:
    """
    Build a mesocycle of N weeks repeating the base workouts.

    The last week is a deload (volume reduced, RPE lowered) if deload=True.
    Periodization is applied per-workout based on goal + progression + day_type.
    """
    microcycles: list[Microcycle] = []

    for week in range(1, duration_weeks + 1):
        is_deload = deload and week == duration_weeks
        week_workouts: list[Workout] = []

        for base_w in base_workouts:
            # Find the matching template's day_type for DUP.
            # Tier 2.20 fix: the inner `break` only exits the inner loop; the
            # outer loop continues and overwrites `template_day_type` for every
            # split containing a template with the same name. Now we break the
            # outer loop too once a match is found. Better long-term: pre-index
            # all templates by name into a single dict at module load.
            template_day_type = None
            for tmpl in ALL_SPLITS:
                found = False
                for t in tmpl.templates:
                    if t.name == base_w.name:
                        template_day_type = t.day_type
                        found = True
                        break
                if found:
                    break  # Tier 2.20 fix: exit outer loop on first match
            # Build a copy with periodization applied
            new_exercises = []
            for we in base_w.exercises:
                new_exercises.append(WorkoutExercise(
                    exercise=we.exercise,
                    sets=we.sets,
                    reps=we.reps,
                    rest_sec=we.rest_sec,
                    rpe_target=we.rpe_target,
                    notes=we.notes,
                ))
            new_w = Workout(
                day_number=base_w.day_number,
                name=base_w.name + (" (Deload)" if is_deload else ""),
                focus=base_w.focus,
                exercises=new_exercises,
                estimated_duration_min=base_w.estimated_duration_min,
                notes="Deload: -1 set, -2 RPE" if is_deload else "",
            )
            apply_periodization(
                workout=new_w,
                goal=goal,
                progression=progression,
                day_type=template_day_type,
                block_phase=block_phase,
                is_deload=is_deload,
            )
            week_workouts.append(new_w)

        # Compute rest days from the split design (passed via base_workouts
        # metadata — we need to look it up). For now, use the split's rest_days
        # from the first matching SplitDesign.
        rest_days = _find_rest_days_for_workouts(base_workouts)

        microcycles.append(Microcycle(
            name=f"Week {week}" + (" — Deload" if is_deload else ""),
            workouts=week_workouts,
            rest_days=rest_days,
            is_deload=is_deload,
        ))

    return Mesocycle(
        name=name,
        duration_weeks=duration_weeks,
        progression=progression,
        microcycles=microcycles,
        deload_week=deload,
        notes=f"{progression.value} progression; {duration_weeks}w block"
              + (" with deload" if deload else ""),
    )


def _find_rest_days_for_workouts(workouts: list[Workout]) -> list[int]:
    """Look up the rest days from whichever split these workouts came from."""
    # Match by workout name pattern
    workout_names = {w.name for w in workouts}
    for split in ALL_SPLITS:
        split_names = {t.name for t in split.templates}
        if split_names & workout_names:
            return list(split.rest_days)
    return [7]  # default: rest on Sunday


# === Step 8: compute weekly volume ===

def _compute_weekly_volume(workouts: list[Workout]) -> dict[str, int]:
    """
    Sum hard sets per muscle group across the microcycle.

    Primary muscles get full credit; secondary muscles get 0.5x credit
    (so a bench press doesn't credit full sets to triceps).
    """
    volume: dict[str, float] = {}
    for w in workouts:
        for we in w.exercises:
            for mg in we.exercise.muscle_groups:
                volume[mg] = volume.get(mg, 0) + we.sets
            for mg in we.exercise.secondary_muscles:
                if mg not in we.exercise.muscle_groups:
                    volume[mg] = volume.get(mg, 0) + we.sets * 0.5
    return {k: round(v) for k, v in volume.items()}


# === Step 9: top-level orchestrator ===

def build_training_plan(
    profile: UserProfile,
    assessment: AssessmentResult,
    plan_type: Optional[PlanType] = None,
    muscle_focus: Optional[list[str]] = None,
    program_duration_weeks: Optional[int] = None,
) -> TrainingPlan:
    """
    Build a complete training plan based on profile + assessment.

    Args:
      profile:           user profile (carries goal, experience, days, equipment)
      assessment:        assessment result (carries recommended strategy)
      plan_type:         STANDARD (ongoing rotation) or PROGRAM (time-bound).
                         If None, auto-decided based on goal.
      muscle_focus:      optional list of muscle groups to emphasize
                         (e.g. ["chest", "arms"]). Adds extra accessory volume.
      program_duration_weeks: override the auto-computed program duration.

    Returns a TrainingPlan with mesocycles + microcycles + workouts.
    """
    # Step 1: derive training goal
    goal = _derive_training_goal(profile, assessment)

    # Step 2: pick split
    split = _pick_split(
        days_per_week=profile.training_days_per_week,
        experience=profile.training_status,
        goal=goal,
    )

    # Step 3: pick progression (Phase-6: now passes goal so STRENGTH+INTERMEDIATE → BLOCK)
    progression = _pick_progression(profile.training_status, goal)

    # Step 4: decide plan type
    actual_plan_type = _decide_plan_type(profile, goal, plan_type)

    # Step 5: apply muscle_focus adjustments
    raw_focus = [m.lower() for m in (muscle_focus or [])]
    # Filter out unknown muscles (warned but not crashed)
    focus_muscles = [m for m in raw_focus if m in _FOCUS_ACCESSORIES]
    unknown_focus = [m for m in raw_focus if m not in _FOCUS_ACCESSORIES]
    for unknown in unknown_focus:
        _log.warning("Unknown muscle_focus '%s' — skipping", unknown)
    if focus_muscles:
        split = _apply_muscle_focus(split, focus_muscles)

    # Step 6: build base workouts (slot filling + equipment filter)
    equipment_allowed = get_equipment_allowed_set(profile.equipment_access)
    base_workouts = _build_workouts_for_split(
        split=split,
        equipment_allowed=equipment_allowed,
        user_experience=profile.training_status,
    )

    # Step 7: build mesocycles based on plan type
    if actual_plan_type == PlanType.STANDARD:
        # Single microcycle — user repeats this indefinitely
        # Apply periodization to the base workouts (no deload)
        for w in base_workouts:
            template_day_type = _find_day_type_for_workout(w)
            apply_periodization(
                workout=w,
                goal=goal,
                progression=progression,
                day_type=template_day_type,
                is_deload=False,
            )
        rest_days = _find_rest_days_for_workouts(base_workouts)
        meso = Mesocycle(
            name=f"{split.split_type.value} rotation",
            duration_weeks=1,  # repeatable
            progression=progression,
            microcycles=[Microcycle(
                name="Weekly Rotation",
                workouts=base_workouts,
                rest_days=rest_days,
                is_deload=False,
            )],
            deload_week=False,
            notes="Standard rotation — repeat weekly. Add deload week every 4-6 weeks.",
        )
        mesocycles = [meso]
        total_duration = 0
    else:
        # PROGRAM: 1+ mesocycles with deload
        meso_length = get_mesocycle_length(profile.training_status)
        total_duration = program_duration_weeks or get_program_duration_weeks(
            profile.training_status, goal,
        )
        num_mesocycles = max(1, total_duration // meso_length)

        # For BLOCK periodization, assign each mesocycle a phase
        if progression == ProgressionScheme.BLOCK:
            phases = get_block_phases_for_program(num_mesocycles)
        else:
            phases = [None] * num_mesocycles

        mesocycles = []
        for i in range(num_mesocycles):
            phase = phases[i] if i < len(phases) else None
            phase_label = f" — {phase.capitalize()}" if phase else ""
            meso = _build_mesocycle(
                name=f"Block {i+1}{phase_label}",
                duration_weeks=meso_length,
                progression=progression,
                base_workouts=base_workouts,
                goal=goal,
                deload=True,
                block_phase=phase,
            )
            mesocycles.append(meso)

        # Adjust total_duration to actual sum
        total_duration = sum(m.duration_weeks for m in mesocycles)

    # Step 8: compute weekly volume
    weekly_vol = _compute_weekly_volume(base_workouts)

    # Step 9: volume notes
    vol_notes: list[str] = []
    target_muscles = ["chest", "upper_back", "quads", "hamstrings", "shoulders", "lats"]
    # Include focus muscles in the check
    for fm in focus_muscles:
        if fm not in target_muscles:
            target_muscles.append(fm)

    # Phase-6 fix: replaced muscle-agnostic 10/20-set cutoffs with muscle-
    # specific validate_weekly_volume() (uses MEV/MRV from DEFAULT_MUSCLE_LANDMARKS).
    # Also replaced substring matching ("abs" matching "abductors") with the
    # explicit _MUSCLE_ALIASES map already defined above.
    _ALIASES_FOR_VOLUME = {
        "back": ["upper_back", "lats", "lower_back", "middle_back", "traps"],
        "chest": ["chest"],
        "shoulders": ["shoulders", "side_delts", "rear_delts"],
        "arms": ["biceps", "triceps", "forearms"],
        "legs": ["quads", "hamstrings", "glutes", "calves"],
        "abs": ["abs", "obliques"],
    }
    from .volume_landmarks import validate_weekly_volume, VolumeTier
    # Build a per-muscle weekly volume dict using alias expansion
    expanded_vol: dict[str, float] = {}
    for muscle, sets in weekly_vol.items():
        expanded_vol[muscle] = expanded_vol.get(muscle, 0.0) + sets
    # For each target muscle, sum volume across its aliases
    target_vol: dict[str, float] = {}
    for muscle in target_muscles:
        aliases = _ALIASES_FOR_VOLUME.get(muscle, [muscle])
        total = sum(expanded_vol.get(a, 0.0) for a in aliases)
        if total > 0:
            target_vol[muscle] = total
    # Also include any muscles in weekly_vol not covered by target_muscles
    for muscle, sets in expanded_vol.items():
        if muscle not in target_vol:
            target_vol[muscle] = sets

    # Use the muscle-specific validator (Phase-6 fix)
    vol_notes.extend(validate_weekly_volume(
        target_vol,
        goal=goal,
        experience=profile.training_status,
        tier=VolumeTier.MEDIUM,
    ))

    # Step 10: assemble final plan
    notes = [
        f"Plan type: {actual_plan_type.value.upper()}"
        + (f" ({total_duration} weeks)" if total_duration > 0 else " (ongoing rotation)"),
        f"Goal: {goal.value}",
        f"Split: {split.split_type.value} ({split.days_per_week} days/week) — {split.description[:80]}",
        f"Progression: {progression.value} (suitable for {profile.training_status.value})",
        f"Equipment: {profile.equipment_access.value} "
        f"({len(equipment_allowed)} equipment types allowed)",
        f"Exercise library: {len(EXERCISES)} exercises loaded",
    ]
    if focus_muscles:
        notes.append(f"Muscle focus: {', '.join(focus_muscles)} "
                     "(extra accessory volume added)")
    if actual_plan_type == PlanType.PROGRAM:
        notes.append(f"Mesocycles: {len(mesocycles)} × "
                     f"{mesocycles[0].duration_weeks} weeks "
                     f"(each ends with deload week)")
        if progression == ProgressionScheme.BLOCK:
            phases = get_block_phases_for_program(len(mesocycles))
            notes.append(f"Block phases: {' → '.join(phases)}")
    notes.append("Volume target: 10-20 hard sets per muscle group per week.")
    notes.append("Compound movements as foundation; progressive overload primary driver.")
    notes.append("Each exercise includes instructions, tips, and video URL.")

    # Tier 2.27 fix: enforce 11-set per-session cap (RippedBody Rule 2.6).
    # check_session_volume_cap exists in volume_landmarks but was never called.
    # Now we scan the first microcycle's workouts and surface warnings.
    from .volume_landmarks import check_session_volume_cap, PER_SESSION_SET_CAP
    cap_warnings: list[str] = []
    if mesocycles and mesocycles[0].microcycles:
        for workout in mesocycles[0].microcycles[0].workouts:
            session_sets: dict[str, float] = {}
            for we in workout.exercises:
                if not we.exercise:
                    continue
                # Exercise.muscle_groups is a list; first entry is primary.
                all_muscles = we.exercise.muscle_groups or []
                if all_muscles:
                    primary = all_muscles[0]
                    session_sets[primary] = session_sets.get(primary, 0) + we.sets
                    # Count secondary muscles at 0.5 (fractional set counting)
                    for sec in all_muscles[1:]:
                        session_sets[sec] = session_sets.get(sec, 0) + we.sets * 0.5
            warnings = check_session_volume_cap(session_sets)
            for w in warnings:
                cap_warnings.append(f"{workout.name}: {w}")
    if cap_warnings:
        notes.append(
            f"⚠ Per-session volume cap ({PER_SESSION_SET_CAP} sets/muscle) exceeded in "
            f"{len(cap_warnings)} workout(s). Increase weekly frequency to distribute volume."
        )
        for cw in cap_warnings[:3]:  # limit to first 3 to avoid note bloat
            notes.append(f"  - {cw}")
    notes.extend(vol_notes)

    return TrainingPlan(
        plan_type=actual_plan_type,
        goal=goal,
        split_type=split.split_type,
        training_days_per_week=split.days_per_week,
        progression=progression,
        mesocycles=mesocycles,
        total_duration_weeks=total_duration,
        muscle_focus=focus_muscles,
        weekly_volume_summary=weekly_vol,
        notes=notes,
    )


# === Helper: find day_type for a workout ===

def _find_day_type_for_workout(workout: Workout) -> Optional[str]:
    """Look up the day_type tag from the original template."""
    for split in ALL_SPLITS:
        for tmpl in split.templates:
            if tmpl.name == workout.name:
                return tmpl.day_type
    return None


__all__ = ["build_training_plan"]

"""
Regression tests for Tier 2 training subsystem fixes.

Covers:
  - Tier 2.19: muscle_focus=['back'] now matches upper_back/lats slots
  - Tier 2.21: rest_days count == 7 - days_per_week for all 8 splits
  - Tier 2.22: 'leg-press' slug categorized as 'leg_press' not 'squat'
  - Tier 2.23: 'seated-dumbbell-press' NOT categorized as 'horizontal_push'
  - Tier 2.24: all STRENGTH_LIFT_LANDMARKS entries have MRV >= MAV_hi
  - Tier 2.28: linear_progression_next works with 1-2 sets
  - Tier 2.29: double_progression_next adds weight when all sets hit hi
"""
import pytest

from fitness_engine.training.split_designs import ALL_SPLITS
from fitness_engine.training.exercise_categorization import get_movement_pattern
from fitness_engine.training.volume_landmarks import STRENGTH_LIFT_LANDMARKS
from fitness_engine.training.progression import (
    linear_progression_next, double_progression_next,
)


class TestRestDaysConsistency:
    """Tier 2.21 — len(rest_days) must equal 7 - days_per_week for every split."""

    @pytest.mark.parametrize("split", ALL_SPLITS, ids=lambda s: s.name)
    def test_rest_days_count_matches_days_per_week(self, split):
        expected_rest = 7 - split.days_per_week
        actual_rest = len(split.rest_days)
        assert actual_rest == expected_rest, (
            f"{split.name}: days_per_week={split.days_per_week} implies {expected_rest} "
            f"rest days, but rest_days={split.rest_days} has {actual_rest}. "
            f"This was the Tier 2.21 bug — microcycle implied wrong training-day count."
        )

    def test_full_body_2day_has_5_rest_days(self):
        fb2 = next(s for s in ALL_SPLITS if s.name == "full_body_2day")
        assert len(fb2.rest_days) == 5

    def test_full_body_3day_has_4_rest_days(self):
        fb3 = next(s for s in ALL_SPLITS if s.name == "full_body_3day")
        assert len(fb3.rest_days) == 4

    def test_ppl_3day_has_4_rest_days(self):
        ppl3 = next(s for s in ALL_SPLITS if s.name == "ppl_3day")
        assert len(ppl3.rest_days) == 4


class TestExerciseCategorizationFixes:
    """Tier 2.22 & 2.23 — pattern keyword collisions fixed."""

    def test_leg_press_categorized_as_leg_press_not_squat(self):
        """Tier 2.22: 'leg-press' must categorize as 'leg_press', not 'squat'."""
        # Build a minimal exercise-like object with the slug
        class FakeExercise:
            def __init__(self, slug, name=""):
                self.slug = slug
                self.name = name or slug.replace("-", " ").title()
                self.exercise_type = "Strength"
                self.force_type = "Push"
                self.category = None
                self.muscle_groups = ["quads"]
                self.secondary_muscles = []

        ex = FakeExercise(slug="leg-press", name="Leg Press")
        pattern = get_movement_pattern(ex)
        assert pattern == "leg_press", (
            f"'leg-press' should categorize as 'leg_press', not '{pattern}'. "
            f"This was the Tier 2.22 bug — 'leg-press' was in squat keywords."
        )

    def test_seated_dumbbell_press_not_horizontal_push(self):
        """Tier 2.23: 'seated-dumbbell-press' (shoulder press) must NOT
        categorize as 'horizontal_push' (chest press). It should be a
        vertical_push variant."""
        class FakeExercise:
            def __init__(self, slug, name=""):
                self.slug = slug
                self.name = name or slug.replace("-", " ").title()
                self.exercise_type = "Strength"
                self.force_type = "Push"
                self.category = None
                self.muscle_groups = ["shoulders"]
                self.secondary_muscles = ["triceps"]

        ex = FakeExercise(slug="seated-dumbbell-press", name="Seated Dumbbell Press")
        pattern = get_movement_pattern(ex)
        assert pattern != "horizontal_push", (
            f"'seated-dumbbell-press' must NOT be 'horizontal_push' (it's a shoulder press). "
            f"Got '{pattern}'. This was the Tier 2.23 bug."
        )
        # It should be some kind of vertical push
        assert "push" in pattern or "press" in pattern, (
            f"Expected a push/press pattern; got '{pattern}'"
        )


class TestStrengthLiftLandmarksCoherence:
    """Tier 2.24 — MRV must be >= MAV_hi for all strength lifts."""

    @pytest.mark.parametrize("lift_name,landmarks", STRENGTH_LIFT_LANDMARKS.items())
    def test_mrv_gte_mav_hi(self, lift_name, landmarks):
        assert landmarks.mrv >= landmarks.mav_hi, (
            f"{lift_name}: MRV ({landmarks.mrv}) must be >= MAV_hi ({landmarks.mav_hi}). "
            f"This was the Tier 2.24 bug — MRV < MAV_hi is mathematically incoherent."
        )


class TestLinearProgressionFix:
    """Tier 2.28 — linear_progression_next works with 1-2 sets (was >= 3)."""

    def test_progresses_with_single_set(self):
        """A 1-set exercise that hits target reps should progress."""
        next_w, expl = linear_progression_next(
            current_weight_kg=80,
            last_reps_achieved=[12],  # 1 set, hit 12 reps
            target_reps=(8, 12),
            increment_kg=2.5,
        )
        assert next_w == 82.5, f"Should progress 80→82.5; got {next_w}"

    def test_progresses_with_two_sets(self):
        """A 2-set exercise that hits target reps in both should progress."""
        next_w, expl = linear_progression_next(
            current_weight_kg=50,
            last_reps_achieved=[12, 12],  # 2 sets, both hit 12
            target_reps=(8, 12),
            increment_kg=2.5,
        )
        assert next_w == 52.5

    def test_does_not_progress_when_not_all_hit_hi(self):
        next_w, expl = linear_progression_next(
            current_weight_kg=50,
            last_reps_achieved=[12, 8],  # one set at hi, one at lo
            target_reps=(8, 12),
        )
        assert next_w == 50  # repeat weight


class TestDoubleProgression:
    """Tier 2.29 — double_progression_next implemented."""

    def test_all_sets_hit_hi_adds_weight_and_resets_to_lo(self):
        next_w, next_target, expl = double_progression_next(
            current_weight_kg=60,
            reps_achieved=[12, 12, 12],  # all hit hi
            reps_target_lo=8,
            reps_target_hi=12,
            increment_kg=2.5,
        )
        assert next_w == 62.5
        assert next_target == 8  # reset to lo

    def test_all_sets_hit_lo_but_not_hi_keeps_weight_targets_hi(self):
        next_w, next_target, expl = double_progression_next(
            current_weight_kg=60,
            reps_achieved=[10, 8, 9],  # all >= lo, not all >= hi
            reps_target_lo=8,
            reps_target_hi=12,
        )
        assert next_w == 60  # keep weight
        assert next_target == 12  # push for hi

    def test_failed_to_hit_lo_keeps_weight_targets_lo(self):
        next_w, next_target, expl = double_progression_next(
            current_weight_kg=60,
            reps_achieved=[6, 7],  # missed lo
            reps_target_lo=8,
            reps_target_hi=12,
        )
        assert next_w == 60
        assert next_target == 8

    def test_empty_reps_keeps_weight(self):
        next_w, next_target, expl = double_progression_next(
            current_weight_kg=60,
            reps_achieved=[],
            reps_target_lo=8,
            reps_target_hi=12,
        )
        assert next_w == 60
        assert next_target == 8


class TestMuscleFocusBack:
    """Tier 2.19 — muscle_focus=['back'] now matches upper_back/lats slots."""

    def test_back_focus_adds_accessories_to_upper_workouts(self):
        """Previously 'back' didn't match 'upper_back'/'lats' in slots, so
        no accessories were added. Now with the alias map, back-focused
        accessories are distributed across the matching workouts."""
        from fitness_engine.training.architect import _apply_muscle_focus
        from fitness_engine.training.split_designs import ALL_SPLITS

        # Use UPPER_LOWER_4DAY which has Upper A and Upper B
        ul = next(s for s in ALL_SPLITS if s.name == "upper_lower_4day")
        focused = _apply_muscle_focus(ul, ["back"])

        # Count total slots across all templates — should be more than the
        # original split's slots (because we added back accessories)
        original_slot_count = sum(len(t.slots) for t in ul.templates)
        focused_slot_count = sum(len(t.slots) for t in focused.templates)
        assert focused_slot_count > original_slot_count, (
            f"muscle_focus=['back'] should add accessory slots. "
            f"Original: {original_slot_count}, focused: {focused_slot_count}"
        )

        # The added slots should target upper_back or lats (back muscles)
        added_slots = []
        for orig_t, foc_t in zip(ul.templates, focused.templates):
            if len(foc_t.slots) > len(orig_t.slots):
                added_slots.extend(foc_t.slots[len(orig_t.slots):])
        back_muscles = {"upper_back", "lats", "lower_back", "middle_back", "traps"}
        back_slot_muscles = [s.primary_muscle for s in added_slots if s.primary_muscle in back_muscles]
        assert len(back_slot_muscles) > 0, (
            f"Added slots should target back muscles (upper_back/lats); "
            f"got primary_muscles: {[s.primary_muscle for s in added_slots]}"
        )

"""
End-to-end pipeline tests for the fitness engine.

These tests exercise the full pipeline:
    UserProfile → assess_profile → propose_plan → to_dict → JSON

They are designed to find bugs by asserting high-level invariants that should
hold for ANY valid input, rather than testing specific implementation details.
"""
from __future__ import annotations

import json

import pytest

from fitness_engine import (
    FitnessPlan,
    UserProfile,
    assess_profile,
    propose_plan,
)
from fitness_engine.models.profile import (
    ActivityLevel,
    DietType,
    EquipmentAccess,
    PrimaryGoal,
    Sex,
    TrainingStatus,
)

# ============================================================
# Helpers — generate diverse profiles for parameterized tests
# ============================================================

def _profile(
    *,
    age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
    activity=ActivityLevel.LIGHTLY_ACTIVE,
    status=TrainingStatus.INTERMEDIATE,
    goal=PrimaryGoal.MAINTENANCE,
    days=4, equipment=EquipmentAccess.FULL_GYM,
    diet=DietType.OMNIVORE, body_fat_pct=18.0,
    neck_cm=38.0, waist_cm=85.0, hip_cm=None,
    **kwargs,
) -> UserProfile:
    """Build a UserProfile with sensible defaults; override anything."""
    return UserProfile(
        age=age, sex=sex, height_cm=height_cm, weight_kg=weight_kg,
        body_fat_pct=body_fat_pct,
        neck_cm=neck_cm, waist_cm=waist_cm, hip_cm=hip_cm,
        activity_level=activity,
        training_status=status,
        primary_goal=goal,
        training_days_per_week=days,
        equipment_access=equipment,
        diet_type=diet,
        **kwargs,
    )


def _female_profile(**kwargs) -> UserProfile:
    """Female profile with hip_cm (required for Navy BF% for women)."""
    kwargs.setdefault("sex", Sex.FEMALE)
    kwargs.setdefault("height_cm", 165)
    kwargs.setdefault("weight_kg", 65)
    kwargs.setdefault("body_fat_pct", 28.0)
    kwargs.setdefault("neck_cm", 33.0)
    kwargs.setdefault("waist_cm", 72.0)
    kwargs.setdefault("hip_cm", 96.0)
    return _profile(**kwargs)


# Diverse profile matrix for parameterized tests
PROFILE_MATRIX = [
    # (label, profile-factory)
    ("male-30-cut", lambda: _profile(
        age=30, sex=Sex.MALE, height_cm=178, weight_kg=82, body_fat_pct=18,
        goal=PrimaryGoal.FAT_LOSS, status=TrainingStatus.INTERMEDIATE, days=4,
    )),
    ("male-25-bulk", lambda: _profile(
        age=25, sex=Sex.MALE, height_cm=175, weight_kg=70, body_fat_pct=12,
        goal=PrimaryGoal.MUSCLE_GAIN, status=TrainingStatus.NOVICE, days=4,
    )),
    ("male-40-recomp", lambda: _profile(
        age=40, sex=Sex.MALE, height_cm=180, weight_kg=85, body_fat_pct=22,
        goal=PrimaryGoal.RECOMP, status=TrainingStatus.INTERMEDIATE, days=3,
    )),
    ("male-50-maintenance", lambda: _profile(
        age=50, sex=Sex.MALE, height_cm=172, weight_kg=78, body_fat_pct=20,
        goal=PrimaryGoal.MAINTENANCE, status=TrainingStatus.ADVANCED, days=5,
    )),
    ("female-30-cut", lambda: _female_profile(
        age=30, weight_kg=68, body_fat_pct=28,
        goal=PrimaryGoal.FAT_LOSS, status=TrainingStatus.INTERMEDIATE, days=4,
    )),
    ("female-25-bulk", lambda: _female_profile(
        age=25, weight_kg=58, body_fat_pct=20,
        goal=PrimaryGoal.MUSCLE_GAIN, status=TrainingStatus.NOVICE, days=3,
    )),
    ("female-35-recomp", lambda: _female_profile(
        age=35, weight_kg=70, body_fat_pct=32,
        goal=PrimaryGoal.RECOMP, status=TrainingStatus.INTERMEDIATE, days=4,
    )),
    ("female-45-maintenance", lambda: _female_profile(
        age=45, weight_kg=62, body_fat_pct=25,
        goal=PrimaryGoal.MAINTENANCE, status=TrainingStatus.ADVANCED, days=5,
    )),
    ("male-beginner", lambda: _profile(
        age=22, sex=Sex.MALE, height_cm=180, weight_kg=65, body_fat_pct=14,
        goal=PrimaryGoal.MUSCLE_GAIN, status=TrainingStatus.BEGINNER, days=3,
    )),
    ("male-advanced", lambda: _profile(
        age=35, sex=Sex.MALE, height_cm=178, weight_kg=88, body_fat_pct=14,
        goal=PrimaryGoal.STRENGTH, status=TrainingStatus.ADVANCED, days=5,
    )),
    ("vegan-male-cut", lambda: _profile(
        age=30, sex=Sex.MALE, height_cm=178, weight_kg=82, body_fat_pct=18,
        goal=PrimaryGoal.FAT_LOSS, diet=DietType.VEGAN, days=4,
    )),
    ("vegetarian-female-bulk", lambda: _female_profile(
        age=28, weight_kg=58, body_fat_pct=22,
        goal=PrimaryGoal.MUSCLE_GAIN, diet=DietType.VEGETARIAN, days=4,
    )),
    ("obese-male-cut", lambda: _profile(
        age=42, sex=Sex.MALE, height_cm=175, weight_kg=110, body_fat_pct=30,
        goal=PrimaryGoal.FAT_LOSS, status=TrainingStatus.BEGINNER, days=3,
        waist_cm=110,
    )),
    ("very-active-male", lambda: _profile(
        age=28, sex=Sex.MALE, height_cm=180, weight_kg=75, body_fat_pct=12,
        goal=PrimaryGoal.MUSCLE_GAIN, activity=ActivityLevel.HIGHLY_ACTIVE, days=6,
    )),
    ("sedentary-female", lambda: _female_profile(
        age=38, weight_kg=72, body_fat_pct=32,
        goal=PrimaryGoal.FAT_LOSS, activity=ActivityLevel.SEDENTARY, days=2,
    )),
    ("home-gym-male", lambda: _profile(
        age=30, sex=Sex.MALE, height_cm=178, weight_kg=82, body_fat_pct=18,
        goal=PrimaryGoal.MUSCLE_GAIN, equipment=EquipmentAccess.HOME_GYM, days=3,
    )),
    ("bodyweight-female", lambda: _female_profile(
        age=30, weight_kg=62, body_fat_pct=22,
        goal=PrimaryGoal.MAINTENANCE, equipment=EquipmentAccess.BODYWEIGHT_ONLY, days=3,
    )),
]


def _matrix_ids():
    return [label for label, _ in PROFILE_MATRIX]


def _matrix_profiles():
    return [factory() for _, factory in PROFILE_MATRIX]


# ============================================================
# Test 1: Full pipeline smoke test — every profile in the matrix
# ============================================================

class TestPipelineSmoke:
    """Every profile in the matrix should produce a valid FitnessPlan."""

    @pytest.mark.parametrize("label,profile_factory", PROFILE_MATRIX, ids=_matrix_ids())
    def test_full_pipeline_produces_plan(self, label, profile_factory):
        profile = profile_factory()
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        assert isinstance(plan, FitnessPlan)
        assert plan.nutrition is not None
        assert plan.training is not None
        assert plan.meal is not None
        assert isinstance(plan.summary, str) and len(plan.summary) > 0

    @pytest.mark.parametrize("label,profile_factory", PROFILE_MATRIX, ids=_matrix_ids())
    def test_plan_serializes_to_json(self, label, profile_factory):
        """Plan.to_dict() must produce JSON-serializable output."""
        profile = profile_factory()
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        d = plan.to_dict()
        # Must not raise
        json_str = json.dumps(d, default=str)
        assert len(json_str) > 100  # non-trivial output

    @pytest.mark.parametrize("label,profile_factory", PROFILE_MATRIX, ids=_matrix_ids())
    def test_assessment_serializes_to_json(self, label, profile_factory):
        profile = profile_factory()
        assessment = assess_profile(profile)
        d = assessment.to_dict()
        json_str = json.dumps(d, default=str)
        assert len(json_str) > 50


# ============================================================
# Test 2: Determinism — same input always produces same output
# ============================================================

class TestDeterminism:
    """The engine is documented as fully deterministic. Verify."""

    @pytest.mark.parametrize("label,profile_factory", PROFILE_MATRIX, ids=_matrix_ids())
    def test_same_input_same_output(self, label, profile_factory):
        profile = profile_factory()
        a1 = assess_profile(profile)
        a2 = assess_profile(profile)
        assert a1.to_dict() == a2.to_dict()

        p1 = propose_plan(profile, a1)
        p2 = propose_plan(profile, a2)
        assert p1.to_dict() == p2.to_dict()

    def test_determinism_across_many_runs(self):
        """Run the same profile 5 times; all outputs must be byte-identical."""
        profile = _profile()
        baseline = None
        for _ in range(5):
            assessment = assess_profile(profile)
            plan = propose_plan(profile, assessment)
            d = plan.to_dict()
            if baseline is None:
                baseline = d
            else:
                assert d == baseline, "Engine is not deterministic!"

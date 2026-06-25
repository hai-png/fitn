"""
Top-level pytest configuration and shared fixtures.

Phase-6: consolidates the duplicated `cut_profile` / `bulk_profile` / etc.
fixtures that were previously defined inline in 18+ test files.
"""
import pytest

from fitness_engine import UserProfile
from fitness_engine.models.profile import (
    Sex, ActivityLevel, TrainingStatus, PrimaryGoal, EquipmentAccess,
    DietType,
)


# === Shared user profiles ===

@pytest.fixture
def cut_profile() -> UserProfile:
    """Standard male cut profile: 30y, 178cm, 82kg, 18% BF, moderate activity."""
    return UserProfile(
        age=30,
        sex=Sex.MALE,
        height_cm=178,
        weight_kg=82,
        body_fat_pct=18.0,
        neck_cm=38.0,
        waist_cm=85.0,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        training_status=TrainingStatus.INTERMEDIATE,
        primary_goal=PrimaryGoal.FAT_LOSS,
        training_days_per_week=4,
        equipment_access=EquipmentAccess.FULL_GYM,
        diet_type=DietType.OMNIVORE,
    )


@pytest.fixture
def bulk_profile() -> UserProfile:
    """Standard male bulk profile: 25y, 175cm, 70kg, 12% BF, moderate activity."""
    return UserProfile(
        age=25,
        sex=Sex.MALE,
        height_cm=175,
        weight_kg=70,
        body_fat_pct=12.0,
        neck_cm=37.0,
        waist_cm=78.0,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        training_status=TrainingStatus.NOVICE,
        primary_goal=PrimaryGoal.MUSCLE_GAIN,
        training_days_per_week=4,
        equipment_access=EquipmentAccess.FULL_GYM,
        diet_type=DietType.OMNIVORE,
    )


@pytest.fixture
def recomp_profile() -> UserProfile:
    """Standard recomp profile: 28y, 180cm, 80kg, 22% BF."""
    return UserProfile(
        age=28,
        sex=Sex.MALE,
        height_cm=180,
        weight_kg=80,
        body_fat_pct=22.0,
        neck_cm=39.0,
        waist_cm=90.0,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        training_status=TrainingStatus.INTERMEDIATE,
        primary_goal=PrimaryGoal.RECOMP,
        training_days_per_week=4,
        equipment_access=EquipmentAccess.FULL_GYM,
        diet_type=DietType.OMNIVORE,
    )


@pytest.fixture
def maintenance_profile() -> UserProfile:
    """Standard maintenance profile: 35y, 170cm, 65kg, 18% BF."""
    return UserProfile(
        age=35,
        sex=Sex.FEMALE,
        height_cm=170,
        weight_kg=65,
        body_fat_pct=24.0,
        neck_cm=33.0,
        waist_cm=72.0,
        hip_cm=96.0,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        training_status=TrainingStatus.INTERMEDIATE,
        primary_goal=PrimaryGoal.MAINTENANCE,
        training_days_per_week=3,
        equipment_access=EquipmentAccess.FULL_GYM,
        diet_type=DietType.OMNIVORE,
    )


@pytest.fixture
def female_cut_profile() -> UserProfile:
    """Standard female cut profile: 32y, 165cm, 68kg, 30% BF."""
    return UserProfile(
        age=32,
        sex=Sex.FEMALE,
        height_cm=165,
        weight_kg=68,
        body_fat_pct=30.0,
        neck_cm=32.0,
        waist_cm=78.0,
        hip_cm=104.0,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        training_status=TrainingStatus.NOVICE,
        primary_goal=PrimaryGoal.FAT_LOSS,
        training_days_per_week=3,
        equipment_access=EquipmentAccess.HOME_GYM,
        diet_type=DietType.OMNIVORE,
    )


@pytest.fixture
def vegan_profile() -> UserProfile:
    """Vegan profile: 28y, 175cm, 72kg, 16% BF."""
    return UserProfile(
        age=28,
        sex=Sex.MALE,
        height_cm=175,
        weight_kg=72,
        body_fat_pct=16.0,
        neck_cm=37.0,
        waist_cm=78.0,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        training_status=TrainingStatus.INTERMEDIATE,
        primary_goal=PrimaryGoal.MAINTENANCE,
        training_days_per_week=4,
        equipment_access=EquipmentAccess.FULL_GYM,
        diet_type=DietType.VEGAN,
    )


# === Pytest configuration ===

# Markers are registered in pyproject.toml [tool.pytest.ini_options].

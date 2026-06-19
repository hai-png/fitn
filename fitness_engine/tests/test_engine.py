"""Integration tests for the top-level engine API."""
import json
import pytest

from fitness_engine import (
    UserProfile, assess_profile, propose_plan, FitnessPlan,
)
from fitness_engine.models.profile import (
    Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType,
)


# === Test fixtures ===

@pytest.fixture
def cut_profile():
    """30yo male novice, 18% BF, fat loss goal."""
    return UserProfile(
        age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
        body_fat_pct=18, neck_cm=38, waist_cm=86, hip_cm=98,
        activity_level=ActivityLevel.MOSTLY_SEDENTARY,
        training_status=TrainingStatus.NOVICE,
        primary_goal=PrimaryGoal.FAT_LOSS,
        training_days_per_week=4,
        equipment_access=EquipmentAccess.FULL_GYM,
        diet_type=DietType.OMNIVORE,
    )


@pytest.fixture
def bulk_profile():
    """25yo male beginner, 12% BF, muscle gain goal."""
    return UserProfile(
        age=25, sex=Sex.MALE, height_cm=183, weight_kg=75,
        body_fat_pct=12, neck_cm=36, waist_cm=78, hip_cm=95,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        training_status=TrainingStatus.BEGINNER,
        primary_goal=PrimaryGoal.MUSCLE_GAIN,
        training_days_per_week=4,
        equipment_access=EquipmentAccess.FULL_GYM,
        diet_type=DietType.OMNIVORE,
    )


@pytest.fixture
def recomp_profile():
    """28yo female beginner, 28% BF, recomp goal."""
    return UserProfile(
        age=28, sex=Sex.FEMALE, height_cm=165, weight_kg=68,
        body_fat_pct=28, neck_cm=33, waist_cm=75, hip_cm=100,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        training_status=TrainingStatus.BEGINNER,
        primary_goal=PrimaryGoal.RECOMP,
        training_days_per_week=3,
        equipment_access=EquipmentAccess.HOME_GYM,
        diet_type=DietType.OMNIVORE,
    )


# === Engine API tests ===

class TestEngineAPI:
    def test_assess_returns_assessment_result(self, cut_profile):
        result = assess_profile(cut_profile)
        assert result.body_composition is not None
        assert result.health_risk is not None
        assert result.muscular_potential is not None
        assert result.recommended_strategy is not None

    def test_assessment_summary_is_human_readable(self, cut_profile):
        result = assess_profile(cut_profile)
        assert "BF%" in result.summary
        assert "FFMI" in result.summary
        assert "CUT" in result.summary.upper() or "BULK" in result.summary.upper()

    def test_propose_plan_returns_fitness_plan(self, cut_profile):
        assessment = assess_profile(cut_profile)
        plan = propose_plan(cut_profile, assessment)
        assert isinstance(plan, FitnessPlan)
        assert plan.nutrition is not None
        assert plan.training is not None
        assert plan.meal is not None
        assert len(plan.summary) > 100

    def test_plan_to_dict_json_serializable(self, cut_profile):
        assessment = assess_profile(cut_profile)
        plan = propose_plan(cut_profile, assessment)
        d = plan.to_dict()
        json_str = json.dumps(d, default=str)
        assert len(json_str) > 1000   # should be substantial

    def test_assessment_to_dict_json_serializable(self, cut_profile):
        assessment = assess_profile(cut_profile)
        d = assessment.to_dict()
        json_str = json.dumps(d, default=str)
        assert len(json_str) > 500


# === End-to-end scenario tests ===

class TestScenarios:
    def test_cut_scenario(self, cut_profile):
        """30yo male novice, 18% BF, fat loss goal."""
        assessment = assess_profile(cut_profile)
        assert assessment.recommended_strategy.value == "cut"

        plan = propose_plan(cut_profile, assessment)
        # TDEE should be reasonable (~2500-2700)
        assert 2400 < plan.nutrition.tdee.final_tdee_kcal < 2800
        # Cut target should be below TDEE
        assert plan.nutrition.calories.target_calories_kcal < plan.nutrition.tdee.final_tdee_kcal
        # Protein should be ~1.14 g/lb LBM
        assert plan.nutrition.macros.protein_g > 150
        # Training plan should have 4 workouts (upper/lower)
        assert plan.training.split_type.value == "upper_lower"
        assert len(plan.training.mesocycles[0].microcycles[0].workouts) == 4
        # Meal plan should have 7 days
        assert len(plan.meal.days) == 7
        # Each day should have 3 meals (default)
        assert len(plan.meal.days[0].meals) == 3

    def test_bulk_scenario(self, bulk_profile):
        """25yo male beginner, 12% BF, muscle gain goal."""
        assessment = assess_profile(bulk_profile)
        assert assessment.recommended_strategy.value == "bulk"

        plan = propose_plan(bulk_profile, assessment)
        # Bulk target should be above TDEE
        assert plan.nutrition.calories.target_calories_kcal > plan.nutrition.tdee.final_tdee_kcal
        # Beginner bulk rate = 2% BW/month
        assert "2.00%" in plan.nutrition.calories.rate_label

    def test_recomp_scenario(self, recomp_profile):
        """28yo female beginner, 28% BF, recomp goal."""
        assessment = assess_profile(recomp_profile)
        # 28% BF for female → good recomp potential (25-35% range)
        assert assessment.recommended_strategy.value == "recomp"

        plan = propose_plan(recomp_profile, assessment)
        # Recomp target should be slightly below TDEE
        assert plan.nutrition.calories.target_calories_kcal <= plan.nutrition.tdee.final_tdee_kcal
        # Home gym equipment → check exercises filtered
        for w in plan.training.mesocycles[0].microcycles[0].workouts:
            for we in w.exercises:
                # No machine-only exercises when home_gym
                assert we.exercise.equipment in {"barbell", "dumbbell", "kettlebell", "bodyweight"}

    def test_obese_beginner_habit_change_first(self):
        """35yo male beginner, 32% BF, maintenance goal → habit_change_first."""
        profile = UserProfile(
            age=35, sex=Sex.MALE, height_cm=178, weight_kg=110,
            body_fat_pct=32, neck_cm=42, waist_cm=110, hip_cm=110,
            activity_level=ActivityLevel.SEDENTARY,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        )
        assessment = assess_profile(profile)
        assert assessment.recommended_strategy.value == "habit_change_first"

        plan = propose_plan(profile, assessment)
        # For habit_change_first: calories = maintenance
        # (no aggressive deficit; let habit changes + training drive recomp)
        assert plan.nutrition.calories.strategy.value == "maintenance"


# === Test all split types ===

class TestSplits:
    @pytest.mark.parametrize("days,expected_split", [
        (2, "full_body"),
        (3, "full_body"),
        (4, "upper_lower"),
        (5, "pplul"),
        (6, "ppl_x2"),
    ])
    def test_split_selection(self, days, expected_split):
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=80,
            body_fat_pct=15,
            activity_level=ActivityLevel.MOSTLY_SEDENTARY,
            training_status=TrainingStatus.INTERMEDIATE,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            training_days_per_week=days,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        )
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        assert plan.training.split_type.value == expected_split


# === Test meal frequency options ===

class TestMealFrequency:
    @pytest.mark.parametrize("freq", [2, 3, 4, 5])
    def test_meal_frequency_generates_correct_meal_count(self, freq, cut_profile):
        assessment = assess_profile(cut_profile)
        plan = propose_plan(cut_profile, assessment, meal_frequency=freq)
        # 2-meal = LUNCH + DINNER
        # 3-meal = BREAKFAST + LUNCH + DINNER
        # 4-meal = + SNACK
        # 5-meal = BREAKFAST + SNACK + LUNCH + SNACK + DINNER
        assert len(plan.meal.days[0].meals) == freq

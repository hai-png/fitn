"""
Tests for the unified information flow + PlanPreferences.

Verifies:
  - PlanPreferences dataclass works with defaults
  - PlanPreferences.from_kwargs builds from flat kwargs
  - propose_plan accepts PlanPreferences
  - propose_plan still works with flat kwargs (backward compat)
  - Flat kwargs override PlanPreferences when both passed
  - PlanPreferences is JSON-serializable via to_dict()
  - End-to-end flow: profile → assessment → plan
"""
import json
import pytest

from fitness_engine import (
    UserProfile, assess_profile, propose_plan, PlanPreferences,
    PlanType, TrainingGoal,
)
from fitness_engine.models.profile import (
    Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType,
)
from fitness_engine.models.preferences import PlanPreferences


# === Fixtures ===

@pytest.fixture
def cut_profile():
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


# === PlanPreferences tests ===

class TestPlanPreferences:
    def test_default_preferences(self):
        """PlanPreferences should have sensible defaults."""
        prefs = PlanPreferences()
        assert prefs.meal_frequency == 3
        assert prefs.exercise_hours_per_day == 1.0
        assert prefs.exercise_intensity == "moderate"
        assert prefs.climate == "temperate"
        assert prefs.in_active_deficit is False
        assert prefs.weight_reduced_pct == 0.0
        assert prefs.plan_type is None
        assert prefs.muscle_focus is None
        assert prefs.program_duration_weeks is None
        assert prefs.cuisine_preference is None
        assert prefs.allergens_to_avoid is None
        assert prefs.excluded_ingredients is None
        assert prefs.include_pre_post_workout is False

    def test_custom_preferences(self):
        """PlanPreferences should accept custom values."""
        prefs = PlanPreferences(
            meal_frequency=5,
            include_pre_post_workout=True,
            muscle_focus=["chest", "arms"],
            cuisine_preference="ethiopian",
            allergens_to_avoid=["dairy", "gluten"],
        )
        assert prefs.meal_frequency == 5
        assert prefs.include_pre_post_workout is True
        assert prefs.muscle_focus == ["chest", "arms"]
        assert prefs.cuisine_preference == "ethiopian"
        assert prefs.allergens_to_avoid == ["dairy", "gluten"]

    def test_from_kwargs_filters_unknown(self):
        """from_kwargs should silently ignore unknown keys."""
        prefs = PlanPreferences.from_kwargs(
            meal_frequency=4,
            unknown_param="ignored",
            include_pre_post_workout=True,
        )
        assert prefs.meal_frequency == 4
        assert prefs.include_pre_post_workout is True

    def test_to_dict_serializable(self):
        """to_dict should produce JSON-serializable output."""
        prefs = PlanPreferences(
            meal_frequency=4,
            muscle_focus=["chest"],
            plan_type=PlanType.PROGRAM,
        )
        d = prefs.to_dict()
        assert d["meal_frequency"] == 4
        assert d["muscle_focus"] == ["chest"]
        assert d["plan_type"] == "program"   # enum → string value
        # Should be JSON-serializable
        json_str = json.dumps(d)
        assert len(json_str) > 0


# === Engine flow tests ===

class TestEngineFlow:
    def test_propose_plan_with_default_preferences(self, cut_profile):
        """propose_plan should work with no preferences (defaults)."""
        assessment = assess_profile(cut_profile)
        plan = propose_plan(cut_profile, assessment)
        assert plan.nutrition is not None
        assert plan.training is not None
        assert plan.meal is not None

    def test_propose_plan_with_preferences(self, cut_profile):
        """propose_plan should accept a PlanPreferences object."""
        assessment = assess_profile(cut_profile)
        preferences = PlanPreferences(
            meal_frequency=4,
            include_pre_post_workout=True,
            muscle_focus=["chest"],
        )
        plan = propose_plan(cut_profile, assessment, preferences)
        assert plan.meal.meal_frequency == 4
        assert plan.training.muscle_focus == ["chest"]

    def test_propose_plan_flat_kwargs_backward_compat(self, cut_profile):
        """propose_plan should still work with flat kwargs (backward compat)."""
        assessment = assess_profile(cut_profile)
        plan = propose_plan(
            cut_profile, assessment,
            meal_frequency=4,
            include_pre_post_workout=True,
            muscle_focus=["chest", "arms"],
        )
        assert plan.meal.meal_frequency == 4
        assert plan.training.muscle_focus == ["chest", "arms"]

    def test_flat_kwargs_override_preferences(self, cut_profile):
        """Explicit flat kwargs should override PlanPreferences values."""
        assessment = assess_profile(cut_profile)
        preferences = PlanPreferences(meal_frequency=3)
        # Override with flat kwarg
        plan = propose_plan(
            cut_profile, assessment, preferences,
            meal_frequency=5,
        )
        assert plan.meal.meal_frequency == 5

    def test_preferences_pass_through_to_meal_plan(self, cut_profile):
        """cuisine_preference + allergens should reach the meal plan."""
        assessment = assess_profile(cut_profile)
        preferences = PlanPreferences(
            cuisine_preference="ethiopian",
            allergens_to_avoid=["dairy"],
        )
        plan = propose_plan(cut_profile, assessment, preferences)
        # Verify no dairy in any meal
        from fitness_engine.meal_plan import check_allergens
        for day in plan.meal.days:
            for meal in day.meals:
                if meal.recipe:
                    violations = check_allergens(meal.recipe, ["dairy"])
                    assert violations == [], (
                        f"Meal {meal.name} contains dairy"
                    )

    def test_preferences_pass_through_to_training(self, cut_profile):
        """plan_type + muscle_focus should reach the training plan."""
        assessment = assess_profile(cut_profile)
        preferences = PlanPreferences(
            plan_type=PlanType.STANDARD,
            muscle_focus=["chest", "back"],
        )
        plan = propose_plan(cut_profile, assessment, preferences)
        assert plan.training.plan_type == PlanType.STANDARD
        assert "chest" in plan.training.muscle_focus
        assert "back" in plan.training.muscle_focus

    def test_preferences_pass_through_to_nutrition(self, cut_profile):
        """climate + exercise_intensity should reach the nutrition plan."""
        assessment = assess_profile(cut_profile)
        preferences = PlanPreferences(
            climate="hot",
            exercise_intensity="intense",
            exercise_hours_per_day=2.0,
        )
        plan = propose_plan(cut_profile, assessment, preferences)
        # Hot climate + intense exercise → higher hydration
        assert plan.nutrition.hydration.water_liters_per_day > 2.5

    def test_full_plan_serializes(self, cut_profile):
        """Full plan should serialize to valid JSON."""
        assessment = assess_profile(cut_profile)
        preferences = PlanPreferences(include_pre_post_workout=True)
        plan = propose_plan(cut_profile, assessment, preferences)
        d = plan.to_dict()
        json_str = json.dumps(d, default=str)
        assert len(json_str) > 10_000


# === File cleanup verification ===

class TestFileCleanup:
    def test_no_v2_files_exist(self):
        """No file should have _v2 suffix."""
        from pathlib import Path
        engine_path = Path(__file__).resolve().parents[1]
        v2_files = list(engine_path.rglob("*_v2.py"))
        assert len(v2_files) == 0, f"Found v2 files: {v2_files}"

    def test_no_shim_files_exist(self):
        """No shim files (planner.py that just re-exports) should exist in training/."""
        from pathlib import Path
        engine_path = Path(__file__).resolve().parents[1]
        # training/planner.py and training/splits.py should not exist
        assert not (engine_path / "training" / "planner.py").exists()
        assert not (engine_path / "training" / "splits.py").exists()

    def test_no_legacy_allocator_in_meal_plan(self):
        """meal_plan/allocator.py should be the clean implementation (not legacy)."""
        from pathlib import Path
        engine_path = Path(__file__).resolve().parents[1]
        allocator_path = engine_path / "meal_plan" / "allocator.py"
        assert allocator_path.exists()
        # Should contain the new SelectedMeal class
        content = allocator_path.read_text()
        assert "class SelectedMeal" in content
        assert "def allocate_meal" in content

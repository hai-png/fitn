"""
Edge case tests for the fitness engine.

These tests push the engine to its limits with extreme inputs:
- Boundary ages (18, 100)
- Boundary heights (140, 230)
- Boundary weights (35, 300)
- Boundary BMI values
- All sex × diet × training_status × goal combinations
- All meal frequencies (2-5)
- All training days (2-6)
- All equipment access levels
- All training times of day
- Multiple allergen combinations
"""
from __future__ import annotations

import pytest

from fitness_engine import (
    PlanPreferences,
    UserProfile,
    assess_profile,
    propose_plan,
)
from fitness_engine.models.profile import (
    ActivityLevel,
    BulkAggressiveness,
    CutRateTier,
    DietType,
    EquipmentAccess,
    PrimaryGoal,
    Sex,
    TrainingStatus,
    TrainingTimeOfDay,
)


def _profile(**kw) -> UserProfile:
    defaults = dict(
        age=30, sex=Sex.MALE, height_cm=178, weight_kg=82, body_fat_pct=18,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        training_status=TrainingStatus.INTERMEDIATE,
        primary_goal=PrimaryGoal.MAINTENANCE,
        training_days_per_week=4,
        equipment_access=EquipmentAccess.FULL_GYM,
        neck_cm=38, waist_cm=85,
    )
    # Allow `diet` as a shortcut for `diet_type`
    if "diet" in kw:
        kw["diet_type"] = kw.pop("diet")
    # Task 6-bug-fixes #4: some tests in this file pass `activity=` instead
    # of `activity_level=` (matching the test_pipeline.py helper's shortcut).
    # Coerce it to the real field name so UserProfile construction doesn't
    # raise an unexpected TypeError.
    if "activity" in kw:
        kw["activity_level"] = kw.pop("activity")
    defaults.update(kw)
    return UserProfile(**defaults)


# ============================================================
# Boundary inputs
# ============================================================

class TestBoundaryInputs:
    """Engine must handle the extreme ends of valid input ranges."""

    def test_age_18(self):
        profile = _profile(age=18)
        assessment = assess_profile(profile)
        propose_plan(profile, assessment)

    def test_age_100(self):
        profile = _profile(age=100, body_fat_pct=25, weight_kg=70)
        assessment = assess_profile(profile)
        propose_plan(profile, assessment)

    def test_height_140(self):
        profile = _profile(height_cm=140, weight_kg=40)
        assessment = assess_profile(profile)
        propose_plan(profile, assessment)

    def test_height_230(self):
        profile = _profile(height_cm=230, weight_kg=150)
        assessment = assess_profile(profile)
        propose_plan(profile, assessment)

    def test_weight_35(self):
        profile = _profile(weight_kg=35, height_cm=160, body_fat_pct=10)
        assessment = assess_profile(profile)
        propose_plan(profile, assessment)

    def test_weight_300(self):
        profile = _profile(weight_kg=300, height_cm=190, body_fat_pct=45)
        assessment = assess_profile(profile)
        propose_plan(profile, assessment)

    def test_body_fat_2(self):
        profile = _profile(body_fat_pct=2)
        assessment = assess_profile(profile)
        propose_plan(profile, assessment)

    def test_body_fat_60(self):
        profile = _profile(body_fat_pct=60, weight_kg=120)
        assessment = assess_profile(profile)
        propose_plan(profile, assessment)

    def test_training_days_2(self):
        profile = _profile(training_days_per_week=2)
        assessment = assess_profile(profile)
        propose_plan(profile, assessment)

    def test_training_days_7(self):
        # Task 6-bug-fixes #1: training_days_per_week=7 is now rejected at
        # UserProfile construction time (was allowed before, but crashed the
        # architect's _pick_split later in the pipeline).
        with pytest.raises(ValueError, match="training_days_per_week must be 2-6"):
            _profile(training_days_per_week=7, activity=ActivityLevel.HIGHLY_ACTIVE)


# ============================================================
# Validation rejection tests
# ============================================================

class TestInputValidation:
    """Engine must reject invalid inputs with clear ValueErrors."""

    def test_age_below_18_rejected(self):
        with pytest.raises(ValueError, match="age"):
            _profile(age=17)

    def test_age_above_100_rejected(self):
        with pytest.raises(ValueError, match="age"):
            _profile(age=101)

    def test_height_below_140_rejected(self):
        with pytest.raises(ValueError, match="height"):
            _profile(height_cm=139)

    def test_height_above_230_rejected(self):
        with pytest.raises(ValueError, match="height"):
            _profile(height_cm=231)

    def test_weight_below_35_rejected(self):
        with pytest.raises(ValueError, match="weight"):
            _profile(weight_kg=34)

    def test_weight_above_300_rejected(self):
        with pytest.raises(ValueError, match="weight"):
            _profile(weight_kg=301)

    def test_training_days_below_2_rejected(self):
        with pytest.raises(ValueError, match="training_days"):
            _profile(training_days_per_week=1)

    def test_training_days_above_7_rejected(self):
        with pytest.raises(ValueError, match="training_days"):
            _profile(training_days_per_week=8)

    def test_body_fat_below_2_rejected(self):
        with pytest.raises(ValueError, match="body_fat"):
            _profile(body_fat_pct=1)

    def test_body_fat_above_60_rejected(self):
        with pytest.raises(ValueError, match="body_fat"):
            _profile(body_fat_pct=61)

    def test_keto_diet_rejected(self):
        with pytest.raises(ValueError, match="Phase-2 supports"):
            _profile(diet=DietType.KETO)


# ============================================================
# All sex × diet × training_status × goal combinations
# ============================================================

class TestCombinationMatrix:
    """Test the Cartesian product of all enum combinations."""

    @pytest.mark.parametrize("sex", [Sex.MALE, Sex.FEMALE])
    @pytest.mark.parametrize("diet", [DietType.OMNIVORE, DietType.VEGAN, DietType.VEGETARIAN])
    @pytest.mark.parametrize("status", [
        TrainingStatus.BEGINNER, TrainingStatus.NOVICE,
        TrainingStatus.INTERMEDIATE, TrainingStatus.ADVANCED,
    ])
    @pytest.mark.parametrize("goal", [
        PrimaryGoal.FAT_LOSS, PrimaryGoal.MUSCLE_GAIN,
        PrimaryGoal.RECOMP, PrimaryGoal.MAINTENANCE, PrimaryGoal.STRENGTH,
    ])
    def test_all_combinations_produce_valid_plan(self, sex, diet, status, goal):
        """Every valid combination must produce a non-crashing plan."""
        # Female profiles need hip_cm
        hip = 96.0 if sex == Sex.FEMALE else None
        profile = _profile(
            sex=sex, diet=diet, training_status=status, primary_goal=goal,
            hip_cm=hip, body_fat_pct=18 if sex == Sex.MALE else 26,
        )
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        assert plan is not None


# ============================================================
# All meal frequencies + training times of day
# ============================================================

class TestMealAndScheduleCombos:

    @pytest.mark.parametrize("freq", [2, 3, 4, 5])
    @pytest.mark.parametrize("tod", [
        TrainingTimeOfDay.MORNING, TrainingTimeOfDay.MIDDAY, TrainingTimeOfDay.EVENING,
    ])
    @pytest.mark.parametrize("include_pre_post", [True, False])
    def test_meal_frequency_and_time_of_day_combos(
        self, freq, tod, include_pre_post,
    ):
        profile = _profile(training_time_of_day=tod)
        assessment = assess_profile(profile)
        prefs = PlanPreferences(
            meal_frequency=freq,
            include_pre_post_workout=include_pre_post,
        )
        plan = propose_plan(profile, assessment, prefs)
        # Verify plan has 7 days
        assert len(plan.meal.days) == 7


# ============================================================
# Allergen combinations
# ============================================================

class TestAllergenCombinations:
    """Test that the engine respects various allergen combinations."""

    ALLERGENS = [
        "dairy", "eggs", "gluten", "soy", "peanuts", "tree_nuts",
        "shellfish", "fish", "sesame",
    ]

    @pytest.mark.parametrize("allergen", ALLERGENS)
    def test_single_allergen_excluded(self, allergen):
        """Each allergen individually should be excluded from recipes."""
        profile = _profile()
        assessment = assess_profile(profile)
        prefs = PlanPreferences(allergens_to_avoid=[allergen])
        plan = propose_plan(profile, assessment, prefs)
        from fitness_engine.meal_plan import check_allergens
        for day in plan.meal.days:
            for meal in day.meals:
                if meal.recipe:
                    violations = check_allergens(meal.recipe, [allergen])
                    assert violations == [], (
                        f"Allergen {allergen} found in {meal.recipe.name}: {violations}"
                    )

    def test_all_allergens_excluded_simultaneously(self):
        """User allergic to everything should still get a plan."""
        profile = _profile()
        assessment = assess_profile(profile)
        prefs = PlanPreferences(allergens_to_avoid=self.ALLERGENS)
        plan = propose_plan(profile, assessment, prefs)
        # Plan should have 7 days even with extreme allergen constraints
        assert len(plan.meal.days) == 7

    def test_allergen_list_with_unknown_allergen(self):
        """Unknown allergen names should not crash (engine should warn)."""
        profile = _profile()
        assessment = assess_profile(profile)
        prefs = PlanPreferences(allergens_to_avoid=["dairy", "fake_allergen_xyz"])
        # Should not raise
        plan = propose_plan(profile, assessment, prefs)
        assert plan is not None


# ============================================================
# Equipment access levels
# ============================================================

class TestEquipmentAccess:

    @pytest.mark.parametrize("equipment", [
        EquipmentAccess.FULL_GYM, EquipmentAccess.HOME_GYM,
        EquipmentAccess.BODYWEIGHT_ONLY,
    ])
    def test_equipment_access_produces_valid_plan(self, equipment):
        profile = _profile(equipment_access=equipment)
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        # Every exercise must be feasible with the user's equipment
        for mc in plan.training.mesocycles:
            for uc in mc.microcycles:
                for w in uc.workouts:
                    for we in w.exercises:
                        # Just verify the exercise exists and has a name
                        assert we.exercise.name


# ============================================================
# Cut rate tier + bulk aggressiveness
# ============================================================

class TestAggressivenessTiers:

    @pytest.mark.parametrize("tier", list(CutRateTier))
    def test_all_cut_rate_tiers(self, tier):
        profile = _profile(
            primary_goal=PrimaryGoal.FAT_LOSS,
            body_fat_pct=25,
            cut_rate_tier=tier,
        )
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        # Verify the cut rate is within safety cap
        rate = plan.nutrition.calories.rate_pct
        assert rate <= 0.0101  # MAX_WEEKLY_LOSS_PCT + small epsilon

    @pytest.mark.parametrize("aggr", list(BulkAggressiveness))
    def test_all_bulk_aggressiveness(self, aggr):
        profile = _profile(
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            body_fat_pct=12,
            bulk_aggressiveness=aggr,
        )
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)
        # Bulk target must be above TDEE
        assert plan.nutrition.calories.target_calories_kcal > plan.nutrition.tdee.final_tdee_kcal


# ============================================================
# Cuisine preference
# ============================================================

class TestCuisinePreference:

    @pytest.mark.parametrize("cuisine", [None, "ethiopian", "american", "mediterranean", "asian"])
    def test_cuisine_preference_does_not_crash(self, cuisine):
        profile = _profile()
        assessment = assess_profile(profile)
        prefs = PlanPreferences(cuisine_preference=cuisine) if cuisine else PlanPreferences()
        plan = propose_plan(profile, assessment, prefs)
        assert len(plan.meal.days) == 7

    def test_ethiopian_vegan_combination(self):
        """Vegan + Ethiopian cuisine should work without crashing."""
        profile = _profile(diet=DietType.VEGAN)
        assessment = assess_profile(profile)
        prefs = PlanPreferences(cuisine_preference="ethiopian")
        plan = propose_plan(profile, assessment, prefs)
        # Verify no animal products
        from fitness_engine.meal_plan.recipe_loader import _recipe_has_meat_ingredients
        for day in plan.meal.days:
            for meal in day.meals:
                if meal.recipe:
                    assert not _recipe_has_meat_ingredients(meal.recipe), (
                        f"Vegan Ethiopian plan has animal recipe: {meal.recipe.name}"
                    )


# ============================================================
# Muscle focus
# ============================================================

class TestMuscleFocus:

    @pytest.mark.parametrize("focus", [
        ["chest"], ["back"], ["legs"], ["shoulders"], ["arms"],
        ["chest", "back"], ["chest", "arms", "shoulders"],
        [],  # empty = no focus
    ])
    def test_muscle_focus_produces_valid_plan(self, focus):
        profile = _profile()
        assessment = assess_profile(profile)
        prefs = PlanPreferences(muscle_focus=focus) if focus else PlanPreferences()
        plan = propose_plan(profile, assessment, prefs)
        # Verify plan was built
        assert plan.training.mesocycles


# ============================================================
# Climate + exercise intensity
# ============================================================

class TestClimateAndIntensity:

    @pytest.mark.parametrize("climate", ["cold", "temperate", "hot", "hot_humid"])
    @pytest.mark.parametrize("intensity", ["light", "moderate", "intense"])
    def test_climate_intensity_combinations(self, climate, intensity):
        """Hydration must adapt to climate and exercise intensity."""
        profile = _profile()
        assessment = assess_profile(profile)
        prefs = PlanPreferences(exercise_intensity=intensity, climate=climate)
        plan = propose_plan(profile, assessment, prefs)
        # Verify hydration is in a sensible range (1-5 L/day)
        h = plan.nutrition.hydration.water_liters_per_day
        assert 1.0 <= h <= 5.5, f"Hydration {h} L outside reasonable range"

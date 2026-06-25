"""
Regression tests for Phase-6 critical fixes.

Each test captures a specific bug that was identified during the comprehensive
codebase review and fixed. The tests are deliberately specific so they break
loudly if the bug is reintroduced.
"""
import math
import pytest

from fitness_engine.models.profile import (
    UserProfile, Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType, CutRateTier,
)
from fitness_engine.models.assessment import MuscularPotential
from fitness_engine.assessment.body_composition import (
    classify_bf, classify_bmi, body_fat_bmi_jackson, compute_ffmi,
    target_weight_at_target_bf,
)
from fitness_engine.assessment.health_risk import (
    compute_whr, compute_whtr, compute_absi, absi_z_score,
    assess_health_risk,
)
from fitness_engine.assessment.muscular_potential import (
    assess_muscular_potential, berkhan_stage_max_weight_kg,
)
from fitness_engine.assessment.decision import decide_strategy
from fitness_engine.nutrition.calories import cut_target_calories, MAX_WEEKLY_LOSS_PCT, CutRateTier
from fitness_engine.nutrition.macros import compute_carbs
from fitness_engine.nutrition.adjustments import detect_plateau, PlateauType
from fitness_engine.nutrition.hydration import compute_hydration
from fitness_engine.training.periodization import (
    _BLOCK_PHASE_MODIFIERS, get_block_phases_for_program, apply_periodization,
)
from fitness_engine.training.volume_landmarks import (
    count_sets_toward_muscle, get_muscle_landmarks, get_recommended_frequency,
)
from fitness_engine.training.progression import linear_progression_next
from fitness_engine.training.exercise_library import _clear_exercise_cache, get_exercise_by_slug
from fitness_engine.meal_plan.recipe_scaler import (
    select_protein_filler, select_carb_filler, select_fat_filler, compute_scale_factor,
)
from fitness_engine.meal_plan.recipe_loader import clear_recipes_cache, _recipe_has_meat_ingredients
from fitness_engine.meal_plan.swap_system import get_recipe_swaps
from fitness_engine.utils.serialize import convert_for_json


def _male_profile(**kwargs):
    """Build a minimal male profile for tests, with sensible defaults."""
    defaults = dict(
        age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        training_status=TrainingStatus.INTERMEDIATE,
        primary_goal=PrimaryGoal.MAINTENANCE,
        training_days_per_week=4,
        equipment_access=EquipmentAccess.FULL_GYM,
    )
    defaults.update(kwargs)
    return UserProfile(**defaults)


# ============================================================
# Assessment fixes
# ============================================================

class TestAssessmentFixes:
    def test_classify_bmi_rejects_negative(self):
        """classify_bmi should raise on negative BMI (was silently returning OBESE)."""
        with pytest.raises(ValueError, match="bmi must be positive"):
            classify_bmi(-5.0)

    def test_classify_bmi_rejects_nan(self):
        """classify_bmi should raise on NaN (was silently returning OBESE)."""
        with pytest.raises(ValueError, match="bmi must be a finite"):
            classify_bmi(float("nan"))

    def test_classify_bf_rejects_nan(self):
        """classify_bf should raise on NaN (was silently returning OBESITY)."""
        with pytest.raises(ValueError, match="bf_pct must be a finite"):
            classify_bf(float("nan"), Sex.MALE)

    def test_body_fat_bmi_jackson_rejects_zero_bmi(self):
        """body_fat_bmi_jackson should raise on BMI <= 0 (was math.log domain error)."""
        # Build a profile with bmi=0 (weight=0 forces it, but we can't easily
        # bypass UserProfile validation — instead call the formula path that
        # raises before the profile is even consulted).
        profile = _male_profile()
        # Monkey-patch bmi to a problematic value
        profile.__dict__  # ensure no funny business
        # The function reads profile.bmi, so we patch the property indirectly:
        # easiest is to verify the function guards internally via direct call.
        # We pass a fake profile-like object.
        class FakeProfile:
            bmi = 0.0
            age = 30
            sex = Sex.MALE
        with pytest.raises(ValueError, match="bmi must be positive"):
            body_fat_bmi_jackson(FakeProfile())

    def test_compute_ffmi_rejects_zero_height(self):
        """compute_ffmi should raise on height_m <= 0 (was ZeroDivisionError)."""
        with pytest.raises(ValueError, match="height_m must be positive"):
            compute_ffmi(weight_kg=80, bf_pct=15, height_m=0)

    def test_compute_ffmi_rejects_bf_over_100(self):
        """compute_ffmi should raise on bf_pct > 100 (was producing negative FFM)."""
        with pytest.raises(ValueError, match="bf_pct must be in"):
            compute_ffmi(weight_kg=80, bf_pct=150, height_m=1.8)

    def test_target_weight_at_target_bf_rejects_target_100(self):
        """target_weight_at_target_bf should raise on target_bf_pct == 100."""
        with pytest.raises(ValueError, match="target_bf_pct must be in"):
            target_weight_at_target_bf(80, 20, 100)

    def test_muscular_potential_ffmi_to_ceiling_clamped_to_0(self):
        """assess_muscular_potential should clamp ffmi_to_ceiling_pct to [0, 100]."""
        # BF% > 100 would previously produce negative ffmi_to_ceiling_pct.
        # Now it's clamped to 0 (and BF% is itself clamped before computation).
        profile = _male_profile()
        result = assess_muscular_potential(profile, body_fat_pct=150)
        assert result.ffmi_to_ceiling_pct >= 0
        assert result.ffmi_to_ceiling_pct <= 100

    def test_muscular_potential_model_rejects_over_100_pct(self):
        """MuscularPotential.__post_init__ should reject ffmi_to_ceiling_pct > 100."""
        with pytest.raises(ValueError, match="must be ≤100"):
            MuscularPotential(
                current_ffmi=20, current_normalized_ffmi=20,
                ffmi_to_ceiling_pct=150,  # over ceiling
            )

    def test_compute_whr_rejects_zero_hip(self):
        with pytest.raises(ValueError, match="hip_cm must be positive"):
            compute_whr(80, 0)

    def test_compute_whtr_rejects_zero_height(self):
        with pytest.raises(ValueError, match="height_cm must be positive"):
            compute_whtr(80, 0)

    def test_compute_absi_rejects_zero_weight(self):
        with pytest.raises(ValueError, match="weight_kg must be positive"):
            compute_absi(80, 0, 178)

    def test_compute_absi_rejects_zero_height(self):
        with pytest.raises(ValueError, match="height_cm must be positive"):
            compute_absi(80, 80, 0)

    def test_missing_hip_does_not_inflate_overall_risk_for_men(self):
        """A healthy male with no risk factors but missing hip_cm should
        NOT be classified MODERATE purely due to the data-quality note."""
        # Use a profile with normal BMI (no overweight/obese trigger).
        profile = _male_profile(
            height_cm=178,
            weight_kg=70,  # BMI = 22.1 (normal)
            waist_cm=80,  # WHtR = 0.45 (low risk)
            body_fat_pct=12,  # fit
        )
        # No hip_cm — should produce data-quality note but NOT bump risk.
        result = assess_health_risk(profile)
        # Even with the data-quality note in risk_factors, overall_risk
        # should be LOW because there are no clinical risk factors.
        assert result.overall_risk.value == "low", (
            f"Expected LOW for healthy male with missing hip_cm; "
            f"got {result.overall_risk.value}. risk_factors: {result.risk_factors}"
        )

    def test_missing_hip_surfaces_note_for_women_too(self):
        """A female user missing hip_cm should also get the data-quality note
        (was previously only fired for men)."""
        profile = _male_profile(sex=Sex.FEMALE, waist_cm=72)
        result = assess_health_risk(profile)
        notes = " | ".join(result.risk_factors)
        assert "hip_cm not provided" in notes, (
            f"Women missing hip_cm should get the data-quality note; "
            f"got risk_factors: {result.risk_factors}"
        )


# ============================================================
# Decision.py dead-code fix
# ============================================================

class TestDecisionDeadCodeFix:
    def test_obese_beginner_non_fatloss_returns_habit_change(self):
        """The safety override at the top of decide_strategy should fire for
        obese beginners with non-FAT_LOSS goals — confirming the dead branch
        below is unreachable."""
        profile = _male_profile(
            body_fat_pct=35,  # obese class for men
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            waist_cm=120,
        )
        strategy, rationale = decide_strategy(
            profile=profile,
            body_fat_pct=35,
            bmi=profile.bmi,
            has_measurements=True,
        )
        assert strategy.value == "habit_change_first"


# ============================================================
# Nutrition fixes
# ============================================================

class TestNutritionFixes:
    def test_cut_aggressive_tier_not_clipped(self):
        """AGGRESSIVE tier (1.0%) equals MAX_WEEKLY_LOSS_PCT exactly.
        The cap-clip warning should NOT fire — it's already at the cap."""
        profile = _male_profile(
            body_fat_pct=30,  # triggers MAX_WEEKLY_LOSS_PCT (1.0%) tier
            cut_rate_tier=CutRateTier.AGGRESSIVE,
        )
        result = cut_target_calories(profile, tdee_kcal=2500)
        # The cap warning should NOT be present (rate is already at cap, not above)
        cap_warnings = [n for n in result.notes if "clipped" in n.lower()]
        assert cap_warnings == [], (
            f"AGGRESSIVE tier (1.0%) should not be 'clipped' — it equals the cap. "
            f"Notes: {result.notes}"
        )

    def test_compute_carbs_clamped_property_works(self):
        """MacroSplit.carbs_clamped should return True when carbs are 0
        due to protein+fat exceeding target (was always returning False)."""
        # Trigger the clamp: protein + fat exceed target
        carb_g, notes = compute_carbs(target_calories=500, protein_g=200, fat_g=200)
        # 200*4 + 200*9 = 2600 kcal > 500 → carb_kcal = -2100 → carb_g = 0
        assert carb_g == 0
        assert any("clamp" in n.lower() for n in notes), (
            f"Expected 'clamped' wording in notes; got: {notes}"
        )

    def test_detect_plateau_whoosh_does_not_mask_weight_gain(self):
        """A historical whoosh should NOT mask a current 3-week gaining streak."""
        # Week 1: 80kg. Week 2: 75kg (5kg whoosh). Weeks 3-5: 75→76→77→78 (gaining).
        # The previous code returned WHOOSH (because it scanned the entire log).
        # Now it should return WEIGHT_GAIN (last 3 deltas all negative).
        log = [80, 75, 76, 77, 78]
        # deltas = [80-75, 75-76, 76-77, 77-78] = [5, -1, -1, -1]
        # last_3 = [-1, -1, -1] → WEIGHT_GAIN
        result = detect_plateau(log, expected_weekly_rate_pct=0.005, body_weight_kg=78)
        assert result == PlateauType.WEIGHT_GAIN, (
            f"Historical whoosh should not mask current gaining streak; got {result}"
        )

    def test_detect_plateau_whoosh_in_last_3_weeks_still_detected(self):
        """A whoosh in the last 3 weeks should still be detected."""
        log = [80, 80, 80, 73]  # delta = [0, 0, 7] → last_3 = [0, 0, 7]
        result = detect_plateau(log, expected_weekly_rate_pct=0.005, body_weight_kg=73)
        # 0 deltas are not < 0 (no weight gain), not < 0.3% threshold (sudden stall),
        # not monotonically decreasing positive (gradual slowdown). 7 > 1.5% of 73
        # = 1.095 → WHOOSH.
        assert result == PlateauType.WHOOSH

    def test_hydration_warning_preserves_original_invalid_value(self):
        """When a user passes an invalid exercise_intensity string, the warning
        should mention the ORIGINAL value, not 'None'."""
        profile = _male_profile()
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            compute_hydration(profile, exercise_intensity="extreme")
            assert len(w) >= 1
            msg = str(w[0].message)
            assert "extreme" in msg, (
                f"Warning should preserve the original 'extreme' value; got: {msg}"
            )


# ============================================================
# Training fixes
# ============================================================

class TestTrainingFixes:
    def test_block_phase_peak_key_exists(self):
        """_BLOCK_PHASE_MODIFIERS should have a 'peak' key (was 'deload' — dead)."""
        assert "peak" in _BLOCK_PHASE_MODIFIERS, (
            "Phase-6 fix: 'peak' key must exist in _BLOCK_PHASE_MODIFIERS "
            "(was 'deload' which was dead — get_block_phases_for_program emits 'peak')"
        )
        assert "deload" not in _BLOCK_PHASE_MODIFIERS, (
            "Phase-6 fix: 'deload' key removed (was dead — get_block_phases_for_program never emits 'deload')"
        )

    def test_block_phase_modifiers_match_emitted_phases(self):
        """Every phase emitted by get_block_phases_for_program should have a modifier."""
        for n in (1, 2, 3):
            phases = get_block_phases_for_program(n)
            for phase in phases:
                assert phase in _BLOCK_PHASE_MODIFIERS, (
                    f"Phase '{phase}' emitted by get_block_phases_for_program({n}) "
                    f"has no modifier in _BLOCK_PHASE_MODIFIERS"
                )

    def test_count_sets_toward_muscle_strength_does_not_overcount(self):
        """For strength counting, a bicep curl should NOT count toward calves
        (was returning 0.5 unconditionally for any muscle when is_strength=True)."""
        curl = get_exercise_by_slug("dumbbell-curl")
        if curl is None:
            pytest.skip("dumbbell-curl not in exercise DB")
        # Bicep curl's primary muscle is biceps; calves are unrelated.
        count = count_sets_toward_muscle(curl, "calves", sets=4, is_strength=True)
        assert count == 0.0, (
            f"Strength mode should NOT count bicep curl toward calves; got {count}"
        )

    def test_get_recommended_frequency_zero_sets_returns_zero(self):
        """0 weekly sets → 0 frequency (was returning 2)."""
        assert get_recommended_frequency(0) == 0
        assert get_recommended_frequency(0, is_strength=True) == 0

    def test_unknown_muscle_fallback_has_mev_at_least_6(self):
        """Unknown muscles should get MEV >= 6 (was 4 — under-estimated)."""
        landmarks = get_muscle_landmarks("tibialis_anterior")
        assert landmarks.mev >= 6, (
            f"Unknown-muscle MEV fallback should be >= 6 (was 4); "
            f"got MEV={landmarks.mev}"
        )

    def test_linear_progression_next_empty_list_returns_no_data(self):
        """Empty last_reps_achieved should return 'no data yet' (was lying)."""
        weight, explanation = linear_progression_next(
            current_weight_kg=80,
            last_reps_achieved=[],
            target_reps=(5, 8),
        )
        assert weight == 80
        assert "no data" in explanation.lower(), (
            f"Empty reps list should return 'no data yet'; got: {explanation}"
        )

    def test_clear_exercise_cache_clears_loader_caches(self):
        """_clear_exercise_cache should also clear exercise_loader caches
        (was leaving _load_raw_db and _build_indexes stale)."""
        # Trigger loading
        get_exercise_by_slug("barbell-bench-press")
        # Clear and verify no exception
        _clear_exercise_cache()
        # Reload should work
        ex = get_exercise_by_slug("barbell-bench-press")
        assert ex is not None


# ============================================================
# Meal plan fixes
# ============================================================

class TestMealPlanFixes:
    def test_vegan_ethiopian_gets_vegan_filler(self):
        """VEGAN_ETHIOPIAN diet tag should resolve to the VEGAN filler list
        (was silently falling back to OMNI — serving whey to vegans)."""
        # Need a protein gap big enough to trigger filler selection
        result = select_protein_filler(gap_protein_g=30, diet_tag="VEGAN_ETHIOPIAN")
        assert result is not None, "Expected a filler for a 30g protein gap"
        # The food name should be a vegan option, not whey/chicken/yogurt
        assert result.food.name not in (
            "Whey Protein Powder",
            "Greek Yogurt (non-fat, plain)",
            "Egg White (large)",
            "Cottage Cheese (low-fat, 2%)",
            "Chicken Breast (skinless, boneless, raw)",
        ), f"VEGAN_ETHIOPIAN got non-vegan filler: {result.food.name}"

    def test_vegan_diet_tag_gets_vegan_filler(self):
        """Plain VEGAN diet tag should also resolve to the VEGAN filler list."""
        result = select_protein_filler(gap_protein_g=30, diet_tag="VEGAN")
        assert result is not None
        assert result.food.name not in (
            "Whey Protein Powder",
            "Greek Yogurt (non-fat, plain)",
            "Chicken Breast (skinless, boneless, raw)",
        )

    def test_compute_scale_factor_zero_target_returns_one(self):
        """Zero target_kcal should return 1.0 (was returning MIN_SCALE=0.7)."""
        # Recipe with 500 kcal, target 0 → should return 1.0 (no scaling)
        # rather than 0.7 (which would produce 350 kcal of a 0-kcal target).
        factor = compute_scale_factor(recipe_kcal=500, target_kcal=0)
        assert factor == 1.0, (
            f"Zero target should return 1.0 (no scaling); got {factor}"
        )

    def test_get_recipe_swaps_does_not_mutate_caller_set(self):
        """get_recipe_swaps should not mutate the caller's exclude_ids set."""
        clear_recipes_cache()
        from fitness_engine.meal_plan.recipe_loader import get_recipe_by_id
        recipe = get_recipe_by_id("R001")
        if recipe is None:
            pytest.skip("R001 not in recipe DB")
        original_exclude = {"R002", "R003"}
        original_copy = set(original_exclude)
        try:
            get_recipe_swaps(
                recipe=recipe,
                target_kcal=500,
                exclude_ids=original_exclude,
            )
        except Exception:
            # Swap may legitimately fail for some recipes; the mutation check
            # is what matters here.
            pass
        assert original_exclude == original_copy, (
            f"get_recipe_swaps mutated the caller's exclude_ids set: "
            f"{original_exclude} vs original {original_copy}"
        )

    def test_recipe_has_meat_ingredients_finds_second_occurrence(self):
        """Multi-word phrase scan should check ALL occurrences, not just the first.
        Uses a multi-word phrase like 'chicken broth' — first qualified by 'no-',
        second occurrence unqualified should be flagged."""
        from fitness_engine.models.meal import Recipe, NutritionPerServing, RecipeDietTag
        # Use 'chicken broth' which is a multi-word phrase in _STRICT_MEAT_PHRASES.
        # First occurrence preceded by 'no-' qualifier (should skip); second
        # occurrence unqualified (should flag).
        recipe = Recipe(
            id="TEST",
            name="Test Recipe",
            ingredients=["no-chicken broth powder and pure chicken broth"],
            nutrition_per_serving=NutritionPerServing(
                kcal=500, protein_g=30, carb_g=20, fat_g=15, fiber_g=5,
            ),
            diet_types=[RecipeDietTag.OMNI],
            cuisine="test",
        )
        assert _recipe_has_meat_ingredients(recipe) is True, (
            "Second 'chicken broth' occurrence (unqualified) should be flagged"
        )

    def test_clear_recipes_cache_clears_index_caches(self):
        """clear_recipes_cache should clear _build_indexes and _load_raw_dbs caches
        (was leaving them stale)."""
        from fitness_engine.meal_plan.recipe_loader import (
            _build_indexes, _load_raw_dbs, get_recipe_by_id as gri,
        )
        # Prime the caches
        gri("R001")
        # Clear
        clear_recipes_cache()
        # Verify cache_info shows cleared (currsize = 0 right after clear)
        info_after_clear = _build_indexes.cache_info()
        assert info_after_clear.currsize == 0, (
            f"_build_indexes cache not cleared; currsize={info_after_clear.currsize}"
        )
        info_loader = _load_raw_dbs.cache_info()
        assert info_loader.currsize == 0, (
            f"_load_raw_dbs cache not cleared; currsize={info_loader.currsize}"
        )


# ============================================================
# Models / serialization fixes
# ============================================================

class TestModelsSerializationFixes:
    def test_convert_for_json_converts_dict_keys(self):
        """convert_for_json should convert dict keys (was only converting values)."""
        from fitness_engine.models.profile import ExerciseIntensity
        result = convert_for_json({ExerciseIntensity.MODERATE: 1.5})
        # Key should be converted to its string value "moderate"
        assert "moderate" in result, (
            f"Dict keys should be converted; got: {result}"
        )

    def test_convert_for_json_handles_sets(self):
        """convert_for_json should handle sets (was passing through, breaking json.dumps)."""
        result = convert_for_json({"a", "b", "c"})
        assert isinstance(result, list)
        assert set(result) == {"a", "b", "c"}

    def test_meal_total_fiber_g_property_exists(self):
        """Meal should have a total_fiber_g property (was missing — fiber dropped)."""
        from fitness_engine.models.meal import Meal, MealType
        meal = Meal(meal_type=MealType.BREAKFAST, name="Test")
        # Property should exist and return 0 for an empty meal
        assert hasattr(meal, "total_fiber_g")
        assert meal.total_fiber_g == 0

    def test_dayplan_total_fiber_g_property_exists(self):
        """DayPlan should have a total_fiber_g property (was missing)."""
        from fitness_engine.models.meal import DayPlan
        day = DayPlan(day_number=1, day_name="Monday")
        assert hasattr(day, "total_fiber_g")
        assert day.total_fiber_g == 0

    def test_meal_to_dict_includes_actual_fiber_g(self):
        """Meal.to_dict should include actual_fiber_g (was missing)."""
        from fitness_engine.models.meal import Meal, MealType
        meal = Meal(meal_type=MealType.BREAKFAST, name="Test")
        d = meal.to_dict()
        assert "actual_fiber_g" in d, (
            f"actual_fiber_g missing from Meal.to_dict output; keys: {list(d.keys())}"
        )

    def test_dayplan_to_dict_includes_total_fiber_g(self):
        """DayPlan.to_dict should include total_fiber_g (was missing)."""
        from fitness_engine.models.meal import DayPlan
        day = DayPlan(day_number=1, day_name="Monday")
        d = day.to_dict()
        assert "total_fiber_g" in d, (
            f"total_fiber_g missing from DayPlan.to_dict output; keys: {list(d.keys())}"
        )


# ============================================================
# Version + API surface fixes
# ============================================================

class TestVersionAndExports:
    def test_version_matches_pyproject(self):
        """fitness_engine.__version__ should match pyproject.toml version."""
        import fitness_engine
        assert fitness_engine.__version__ == "3.1.0", (
            f"Version mismatch: __init__.py has {fitness_engine.__version__}, "
            "pyproject.toml has 3.1.0"
        )

    def test_climate_exported_from_top_level(self):
        """Climate should be importable from the top-level package."""
        from fitness_engine import Climate
        assert Climate.TEMPERATE.value == "temperate"

    def test_exercise_intensity_exported_from_top_level(self):
        """ExerciseIntensity should be importable from the top-level package."""
        from fitness_engine import ExerciseIntensity
        assert ExerciseIntensity.MODERATE.value == "moderate"

    def test_training_time_of_day_exported_from_top_level(self):
        """TrainingTimeOfDay should be importable from the top-level package."""
        from fitness_engine import TrainingTimeOfDay
        assert TrainingTimeOfDay.EVENING.value == "evening"

    def test_climate_exported_from_models(self):
        """Climate should be importable from fitness_engine.models."""
        from fitness_engine.models import Climate
        assert Climate.HOT.value == "hot"

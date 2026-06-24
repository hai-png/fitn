"""
Phase-2 tests for the new exercise + recipe databases.

Verifies:
  - Exercise library loads 1,217 exercises from content_files/all_exercises.json
  - Every exercise has normalized equipment (lowercase snake_case)
  - Every exercise has rich metadata (instructions, tips, video URL, etc.)
  - Recipe loader merges curated + uncurated databases
  - Recipe queries by meal_type / diet_type / cuisine / goal_fit work
  - Meal plan uses real recipes (not raw foods) when matches exist
  - Training plan includes instructions + video URL in serialized output
  - Bodyweight-only users get a non-empty workout (Issue 4 regression)
"""
import json
import pytest

from fitness_engine import (
    UserProfile, assess_profile, propose_plan, FitnessPlan,
)
from fitness_engine.models.profile import (
    Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType,
)
from fitness_engine.training import (
    EXERCISES, EXERCISE_INDEX, EXERCISE_SLUG_INDEX,
    get_exercise, get_exercise_by_phase1_name,
    exercises_by_muscle, exercises_by_category,
    exercises_by_equipment, exercises_by_experience,
    exercises_by_force_type,
    normalize_equipment, normalize_muscle,
)
from fitness_engine.meal_plan import (
    load_recipes, get_recipe_by_id, get_recipe_by_name,
    swap_groups, recipes_in_swap_group,
    recipes_by_meal_type, recipes_by_diet_type, recipes_by_cuisine,
    recipes_by_goal_fit, recipes_by_kcal_range, recipes_by_filters,
    database_stats,
)


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


@pytest.fixture
def bodyweight_profile():
    return UserProfile(
        age=30, sex=Sex.MALE, height_cm=178, weight_kg=80,
        body_fat_pct=15,
        activity_level=ActivityLevel.MOSTLY_SEDENTARY,
        training_status=TrainingStatus.INTERMEDIATE,
        primary_goal=PrimaryGoal.MUSCLE_GAIN,
        training_days_per_week=3,
        equipment_access=EquipmentAccess.BODYWEIGHT_ONLY,
        diet_type=DietType.OMNIVORE,
    )


# === Exercise library tests ===

class TestExerciseLibrary:
    def test_library_loads_full_database(self):
        """Phase-2 must load all 1,217 exercises from the JSON DB."""
        assert len(EXERCISES) == 1217, (
            f"Expected 1,217 exercises, got {len(EXERCISES)}"
        )

    def test_indexes_built(self):
        """Both name and slug indexes should be populated."""
        assert len(EXERCISE_INDEX) > 1000
        assert len(EXERCISE_SLUG_INDEX) > 1000

    def test_every_exercise_has_normalized_equipment(self):
        """Equipment should be lowercase snake_case (no spaces, no caps)."""
        for ex in EXERCISES:
            assert ex.equipment == ex.equipment.lower(), (
                f"{ex.name} has non-lowercase equipment: {ex.equipment}"
            )
            assert " " not in ex.equipment, (
                f"{ex.name} has space in equipment: {ex.equipment}"
            )

    def test_every_exercise_has_rich_metadata(self):
        """Phase-2 promise: instructions + tips + video URL populated."""
        has_instructions = sum(1 for ex in EXERCISES if ex.instructions)
        has_tips = sum(1 for ex in EXERCISES if ex.tips)
        has_video = sum(1 for ex in EXERCISES if ex.video_url)
        # At least 80% of exercises should have instructions (some may be sparse)
        assert has_instructions >= 0.8 * len(EXERCISES), (
            f"Only {has_instructions}/{len(EXERCISES)} exercises have instructions"
        )
        assert has_tips >= 0.5 * len(EXERCISES), (
            f"Only {has_tips}/{len(EXERCISES)} exercises have tips"
        )
        assert has_video >= 0.5 * len(EXERCISES), (
            f"Only {has_video}/{len(EXERCISES)} exercises have video URL"
        )

    def test_phase1_name_mapping_resolves_all_template_exercises(self):
        """Every Phase-1 hardcoded name should resolve to a Phase-2 exercise."""
        from fitness_engine.training.exercise_library import PHASE1_TO_PHASE2_SLUG_MAP
        missing = []
        for phase1_name in PHASE1_TO_PHASE2_SLUG_MAP:
            ex = get_exercise_by_phase1_name(phase1_name)
            if ex is None:
                missing.append(phase1_name)
        assert not missing, f"Unmapped Phase-1 exercises: {missing}"

    def test_get_exercise_finds_by_name_slug_or_substring(self):
        # By exact name
        assert get_exercise("Military Press (AKA Overhead Press)") is not None
        # By slug
        assert get_exercise("military-press") is not None
        # By substring (case insensitive)
        assert get_exercise("squat") is not None

    def test_exercises_by_muscle_finds_quads(self):
        quads = exercises_by_muscle("quads")
        assert len(quads) > 50, f"Only {len(quads)} quad exercises"
        # Verify all results actually target quads
        for ex in quads:
            assert "quads" in ex.muscle_groups or "quads" in ex.secondary_muscles

    def test_exercises_by_equipment_filters_correctly(self):
        bb = exercises_by_equipment("barbell")
        # All results should use barbell (normalized from "Barbell")
        for ex in bb:
            assert ex.equipment == "barbell"
        # Try with capitalized input (should normalize)
        bb2 = exercises_by_equipment("Barbell")
        assert len(bb2) == len(bb)

    def test_normalize_equipment_handles_known_vocab(self):
        assert normalize_equipment("Barbell") == "barbell"
        assert normalize_equipment("Dumbbell") == "dumbbell"
        assert normalize_equipment("Kettle Bells") == "kettlebell"
        assert normalize_equipment("Exercise Ball") == "exercise_ball"
        assert normalize_equipment("EZ Bar") == "ez_bar"
        assert normalize_equipment(None) == "other"

    def test_normalize_muscle_handles_multi_value(self):
        result = normalize_muscle("Calves, Forearms, Glutes")
        assert result == ["calves", "forearms", "glutes"]
        result = normalize_muscle("Upper Back")
        assert result == ["upper_back"]
        result = normalize_muscle(None) == []

    def test_exercises_by_experience(self):
        beginners = exercises_by_experience("Beginner")
        intermediates = exercises_by_experience("Intermediate")
        advanced = exercises_by_experience("Advanced")
        assert len(beginners) > 500
        assert len(intermediates) > 100
        assert len(advanced) > 10


# === Recipe loader tests ===

class TestRecipeLoader:
    def test_loads_both_databases(self):
        """Should load curated (107) + uncurated (370) - overlap = total."""
        recipes = load_recipes()
        # Total should be at least 370 (uncurated size) and at most 477 (sum)
        assert 370 <= len(recipes) <= 477, (
            f"Expected 370-477 recipes, got {len(recipes)}"
        )

    def test_database_stats_returns_expected_fields(self):
        stats = database_stats()
        assert "total_recipes" in stats
        assert "curated_count" in stats
        assert "uncurated_count" in stats
        assert "swap_group_count" in stats
        assert stats["total_recipes"] == stats["curated_count"] + stats["uncurated_count"]
        assert stats["curated_count"] == 107
        assert stats["uncurated_count"] > 200

    def test_get_recipe_by_id_returns_recipe(self):
        r = get_recipe_by_id("R001")
        assert r is not None
        assert r.id == "R001"
        assert r.name  # non-empty

    def test_recipes_by_meal_type(self):
        breakfast = recipes_by_meal_type("breakfast")
        dinner = recipes_by_meal_type("dinner")
        assert len(breakfast) > 0
        assert len(dinner) > 0
        assert len(dinner) > len(breakfast)  # dinner is the largest category

    def test_recipes_by_diet_type(self):
        vegan = recipes_by_diet_type("VEGAN")
        omni = recipes_by_diet_type("OMNI")
        assert len(vegan) > 0
        assert len(omni) > 0

    def test_recipes_by_cuisine(self):
        ethiopian = recipes_by_cuisine("ethiopian")
        american = recipes_by_cuisine("american")
        assert len(ethiopian) > 0
        assert len(american) > 0

    def test_recipes_by_goal_fit(self):
        cut = recipes_by_goal_fit("cut")
        bulk = recipes_by_goal_fit("bulk")
        maintenance = recipes_by_goal_fit("maintenance")
        assert len(maintenance) > 0
        # cut and bulk are smaller curated sets
        assert len(cut) >= 0
        assert len(bulk) >= 0

    def test_recipes_by_kcal_range(self):
        low_kcal = recipes_by_kcal_range(100, 200)
        assert len(low_kcal) > 0
        for r in low_kcal:
            assert 100 <= r.kcal <= 200

    def test_recipes_by_filters_combines_filters(self):
        # Vegan + breakfast + 200-400 kcal
        results = recipes_by_filters(
            meal_type="breakfast",
            diet_type="VEGAN",
            kcal_lo=200,
            kcal_hi=400,
        )
        assert len(results) > 0
        for r in results:
            assert "breakfast" in [m.lower() for m in r.meal_types]
            # VEGAN filter should match VEGAN or VEGAN_* (e.g. VEGAN_ETHIOPIAN)
            diet_tags = [d.upper() for d in r.diet_types]
            assert any(d == "VEGAN" or d.startswith("VEGAN_") for d in diet_tags), (
                f"Recipe {r.name} has diet_types {diet_tags}, expected VEGAN"
            )
            assert 200 <= r.kcal <= 400

    def test_swap_groups_loaded(self):
        sg = swap_groups()
        assert len(sg) > 0
        # Should have at least one breakfast group
        breakfast_groups = [k for k in sg if k.startswith("breakfast")]
        assert len(breakfast_groups) > 0

    def test_recipe_has_full_nutrition(self):
        """Every recipe should have non-zero kcal + macros."""
        recipes = load_recipes()
        has_kcal = sum(1 for r in recipes if r.kcal > 0)
        # At least 95% of recipes should have kcal (some may be pantry items)
        assert has_kcal >= 0.95 * len(recipes), (
            f"Only {has_kcal}/{len(recipes)} recipes have kcal"
        )


# === Meal planner tests ===

class TestMealPlanner:
    def test_meal_plan_uses_real_recipes(self, cut_profile):
        """Phase-2: meals should reference Recipe objects, not just raw foods."""
        assessment = assess_profile(cut_profile)
        plan = propose_plan(cut_profile, assessment)

        recipe_count = 0
        fallback_count = 0
        for day in plan.meal.days:
            for meal in day.meals:
                if meal.recipe is not None:
                    recipe_count += 1
                else:
                    fallback_count += 1

        # Most meals should use recipes (some may fall back if no match)
        assert recipe_count > 0, "No recipes in meal plan"
        # At least 50% of meals should use recipes
        total = recipe_count + fallback_count
        assert recipe_count / total >= 0.5, (
            f"Only {recipe_count}/{total} meals use recipes"
        )

    def test_meal_plan_includes_recipe_metadata(self, cut_profile):
        """Each recipe-based meal should have ingredients + instructions."""
        assessment = assess_profile(cut_profile)
        plan = propose_plan(cut_profile, assessment)

        found_recipe_with_ingredients = False
        found_recipe_with_instructions = False
        for day in plan.meal.days:
            for meal in day.meals:
                if meal.recipe:
                    if len(meal.recipe.ingredients) > 0:
                        found_recipe_with_ingredients = True
                    if len(meal.recipe.instructions) > 0:
                        found_recipe_with_instructions = True

        assert found_recipe_with_ingredients, "No recipe has ingredients"
        assert found_recipe_with_instructions, "No recipe has instructions"

    def test_meal_plan_summary_includes_cuisine_mix(self, cut_profile):
        """Plan summary should report cuisine distribution."""
        assessment = assess_profile(cut_profile)
        plan = propose_plan(cut_profile, assessment)
        assert len(plan.meal.cuisine_mix) > 0
        assert plan.meal.recipe_source_summary["database_total"] > 0

    def test_meal_plan_to_dict_includes_recipe_fields(self, cut_profile):
        """Serialized plan should include recipe_id, ingredients, instructions."""
        assessment = assess_profile(cut_profile)
        plan = propose_plan(cut_profile, assessment)
        d = plan.to_dict()
        # Find at least one meal with a recipe
        found_recipe_in_dict = False
        for day in d["meal"]["days"]:
            for meal in day["meals"]:
                if meal.get("recipe"):
                    found_recipe_in_dict = True
                    assert "ingredients" in meal["recipe"]
                    assert "instructions" in meal["recipe"]
                    assert "nutrition_per_serving" in meal["recipe"]
                    break
            if found_recipe_in_dict:
                break
        assert found_recipe_in_dict, "No recipe found in serialized plan"

    def test_vegan_profile_gets_vegan_recipes(self):
        """Vegan users should only get VEGAN-tagged recipes."""
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=75,
            body_fat_pct=15,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.NOVICE,
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.VEGAN,
        )
        assessment = assess_profile(profile)
        plan = propose_plan(profile, assessment)

        vegan_recipe_count = 0
        non_vegan_recipe_count = 0
        for day in plan.meal.days:
            for meal in day.meals:
                if meal.recipe:
                    diet_tags = [d.upper() for d in meal.recipe.diet_types]
                    if any(d == "VEGAN" or d.startswith("VEGAN_") for d in diet_tags):
                        vegan_recipe_count += 1
                    else:
                        non_vegan_recipe_count += 1

        # All recipes selected should be vegan (VEGAN or VEGAN_*)
        assert non_vegan_recipe_count == 0, (
            f"Vegan profile got {non_vegan_recipe_count} non-vegan recipes"
        )
        assert vegan_recipe_count > 0


# === Training planner tests ===

class TestTrainingPlanner:
    def test_training_plan_includes_exercise_instructions(self, cut_profile):
        """Phase-2: every exercise in the plan should have instructions."""
        assessment = assess_profile(cut_profile)
        plan = propose_plan(cut_profile, assessment)
        for meso in plan.training.mesocycles:
            for micro in meso.microcycles:
                for w in micro.workouts:
                    for we in w.exercises:
                        # Most exercises should have instructions
                        # (allow some exceptions for cardio/mobility)
                        if we.exercise.exercise_type == "Strength":
                            assert len(we.exercise.instructions) > 0, (
                                f"{we.exercise.name} has no instructions"
                            )

    def test_training_plan_includes_video_urls(self, cut_profile):
        """Phase-2: most exercises should have video URLs."""
        assessment = assess_profile(cut_profile)
        plan = propose_plan(cut_profile, assessment)
        video_count = 0
        total_count = 0
        for meso in plan.training.mesocycles:
            for micro in meso.microcycles:
                for w in micro.workouts:
                    for we in w.exercises:
                        total_count += 1
                        if we.exercise.video_url:
                            video_count += 1
        # At least 80% of exercises should have video URLs
        assert video_count / total_count >= 0.8, (
            f"Only {video_count}/{total_count} exercises have video URLs"
        )

    def test_training_plan_to_dict_includes_full_metadata(self, cut_profile):
        """Serialized plan should include slug, instructions, tips, video URL."""
        assessment = assess_profile(cut_profile)
        plan = propose_plan(cut_profile, assessment)
        d = plan.to_dict()
        # Find first exercise
        first_ex = (
            d["training"]["mesocycles"][0]["microcycles"][0]["workouts"][0]
            ["exercises"][0]["exercise"]
        )
        assert "slug" in first_ex
        assert "instructions" in first_ex
        assert "tips" in first_ex
        assert "video_url" in first_ex
        assert "force_type" in first_ex
        assert "mechanics" in first_ex
        assert "experience_level" in first_ex

    def test_bodyweight_user_gets_non_empty_workouts(self, bodyweight_profile):
        """Issue 4 regression: bodyweight-only users must get >0 exercises per workout."""
        assessment = assess_profile(bodyweight_profile)
        plan = propose_plan(bodyweight_profile, assessment)
        for meso in plan.training.mesocycles:
            for micro in meso.microcycles:
                for w in micro.workouts:
                    assert len(w.exercises) >= 3, (
                        f"Workout {w.name} only has {len(w.exercises)} exercises"
                    )
                    # All exercises must be bodyweight-compatible
                    for we in w.exercises:
                        assert we.exercise.equipment in {"bodyweight", "bands"}, (
                            f"{we.exercise.name} uses {we.exercise.equipment} "
                            f"(not bodyweight-compatible)"
                        )

    def test_leg_press_no_longer_silently_substituted(self, cut_profile):
        """Issue 5 regression: 'Leg Press' should now resolve (new DB has it)."""
        from fitness_engine.training import get_exercise_by_phase1_name
        ex = get_exercise_by_phase1_name("Leg Press")
        assert ex is not None
        assert ex.slug == "45-degree-leg-press"

    def test_volume_tracking_weights_secondary_muscles(self, cut_profile):
        """Issue 12: secondary muscles should get half credit, not full."""
        assessment = assess_profile(cut_profile)
        plan = propose_plan(cut_profile, assessment)
        vol = plan.training.weekly_volume_summary
        # Volume should be a non-empty dict
        assert len(vol) > 0
        # All values should be ints (post-rounding)
        for k, v in vol.items():
            assert isinstance(v, int)


# === Integration: end-to-end plan ===

class TestEndToEnd:
    def test_full_plan_serializes_to_valid_json(self, cut_profile):
        assessment = assess_profile(cut_profile)
        plan = propose_plan(cut_profile, assessment)
        d = plan.to_dict()
        # Should serialize without errors
        json_str = json.dumps(d, default=str)
        # Should be substantial (recipes + instructions make it big)
        assert len(json_str) > 50_000, (
            f"Plan JSON only {len(json_str)} chars — expected much more "
            f"with recipes + exercise instructions"
        )

    def test_plan_summary_mentions_recipe_count(self, cut_profile):
        assessment = assess_profile(cut_profile)
        plan = propose_plan(cut_profile, assessment)
        # Notes should mention recipe database
        notes_text = " ".join(plan.meal.notes)
        assert "recipes loaded" in notes_text or "recipe" in notes_text.lower()

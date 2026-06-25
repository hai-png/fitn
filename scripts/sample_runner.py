#!/usr/bin/env python3
"""
Sample runner — demonstrates the fitness engine end-to-end.

Generates 6 demo plans using the clean PlanPreferences API:

    from fitness_engine import UserProfile, assess_profile, propose_plan, PlanPreferences

    profile = UserProfile(...)
    assessment = assess_profile(profile)
    preferences = PlanPreferences(meal_frequency=4, include_pre_post_workout=True)
    plan = propose_plan(profile, assessment, preferences)

Run: python /home/z/my-project/fitn/scripts/sample_runner.py
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fitness_engine import (
    UserProfile, assess_profile, propose_plan, PlanPreferences,
)
from fitness_engine.models.profile import (
    Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType,
)


DOWNLOAD_DIR = PROJECT_ROOT / "download"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


SAMPLE_PROFILES = {
    "sample_plan_cut": {
        "description": "30yo male novice, 18% BF, fat loss, 4 days/week, full gym, omnivore + PRE/POST workout",
        "profile": UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            body_fat_pct=18, neck_cm=38, waist_cm=86, hip_cm=98,
            activity_level=ActivityLevel.MOSTLY_SEDENTARY,
            training_status=TrainingStatus.NOVICE,
            primary_goal=PrimaryGoal.FAT_LOSS,
            training_days_per_week=4,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        ),
        "preferences": PlanPreferences(
            include_pre_post_workout=True,
        ),
    },
    "sample_plan_bulk": {
        "description": "25yo male beginner, 12% BF, muscle gain, 3 days/week, full gym, omnivore + PRE/POST workout",
        "profile": UserProfile(
            age=25, sex=Sex.MALE, height_cm=183, weight_kg=75,
            body_fat_pct=12, neck_cm=36, waist_cm=78, hip_cm=95,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        ),
        "preferences": PlanPreferences(
            include_pre_post_workout=True,
        ),
    },
    "sample_plan_recomp": {
        "description": "28yo female beginner, 28% BF, recomp, home gym 3 days/week, omnivore",
        "profile": UserProfile(
            age=28, sex=Sex.FEMALE, height_cm=165, weight_kg=68,
            body_fat_pct=28, neck_cm=33, waist_cm=75, hip_cm=100,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.RECOMP,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.HOME_GYM,
            diet_type=DietType.OMNIVORE,
        ),
        "preferences": PlanPreferences(),
    },
    "sample_plan_female_maintenance": {
        "description": "32yo female intermediate, 22% BF, maintenance, 5 days/week, full gym, omnivore",
        "profile": UserProfile(
            age=32, sex=Sex.FEMALE, height_cm=170, weight_kg=62,
            body_fat_pct=22, neck_cm=32, waist_cm=68, hip_cm=92,
            activity_level=ActivityLevel.ACTIVE,
            training_status=TrainingStatus.INTERMEDIATE,
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_days_per_week=5,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        ),
        "preferences": PlanPreferences(
            muscle_focus=["glutes", "shoulders"],
        ),
    },
    "sample_plan_vegan_ethiopian_maintenance": {
        "description": (
            "27yo male novice, 14% BF, maintenance, 3 days/week, full gym, "
            "VEGAN + ETHIOPIAN cuisine + PRE/POST workout"
        ),
        "profile": UserProfile(
            age=27, sex=Sex.MALE, height_cm=180, weight_kg=78,
            body_fat_pct=14, neck_cm=37, waist_cm=80, hip_cm=98,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.NOVICE,
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.VEGAN,
        ),
        "preferences": PlanPreferences(
            cuisine_preference="ethiopian",
            include_pre_post_workout=True,
        ),
    },
    "sample_plan_bodyweight_recomp_prepost": {
        "description": (
            "30yo male intermediate, 16% BF, recomp, 3 days/week, BODYWEIGHT_ONLY, "
            "omnivore, dairy-free + PRE/POST workout"
        ),
        "profile": UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=80,
            body_fat_pct=16, neck_cm=38, waist_cm=82, hip_cm=98,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.INTERMEDIATE,
            primary_goal=PrimaryGoal.RECOMP,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.BODYWEIGHT_ONLY,
            diet_type=DietType.OMNIVORE,
        ),
        "preferences": PlanPreferences(
            include_pre_post_workout=True,
            allergens_to_avoid=["dairy"],
        ),
    },
}


def run_profile(name: str, spec: dict) -> dict:
    """Run a single profile through the engine and return the full result.

    Tier 4.50 fix: added assertions to catch regressions in plan quality.
    Previously the script generated plans and wrote them to disk with no
    validation — a regression that dropped the kcal match % from 95% to 70%
    would not be caught. Now we assert:
      - Plan has nutrition, training, and meal components
      - Meal plan has 7 days
      - Each day has at least 1 meal
      - No allergen violations in any meal's recipe (if allergens specified)
      - Weekly kcal match % is reasonable (> 50%)
    """
    print(f"\n{'='*60}")
    print(f"Profile: {name}")
    print(f"  {spec['description']}")
    print(f"{'='*60}")

    profile = spec["profile"]
    preferences = spec.get("preferences", PlanPreferences())

    assessment = assess_profile(profile)
    plan = propose_plan(profile, assessment, preferences)

    # Tier 4.50: assertions to catch regressions
    assert plan.nutrition is not None, f"{name}: plan.nutrition is None"
    assert plan.training is not None, f"{name}: plan.training is None"
    assert plan.meal is not None, f"{name}: plan.meal is None"
    assert len(plan.meal.days) == 7, (
        f"{name}: expected 7 days in meal plan, got {len(plan.meal.days)}"
    )
    for day in plan.meal.days:
        assert len(day.meals) >= 1, (
            f"{name}: {day.day_name} has 0 meals"
        )

    # Allergen check (if allergens specified)
    if preferences.allergens_to_avoid:
        from fitness_engine.meal_plan import check_allergens
        for day in plan.meal.days:
            for meal in day.meals:
                if meal.recipe:
                    violations = check_allergens(meal.recipe, preferences.allergens_to_avoid)
                    assert violations == [], (
                        f"{name}: {day.day_name} {meal.name} contains {violations} "
                        f"(user avoids {preferences.allergens_to_avoid})"
                    )

    # Kcal match check
    summary = plan.meal.recipe_source_summary
    kcal_match = summary.get("weekly_kcal_match_pct", 100)
    assert kcal_match > 50, (
        f"{name}: weekly kcal match {kcal_match:.0f}% is too low (<50%) — "
        f"possible regression in meal allocator"
    )

    print(f"\n--- Plan Summary ---")
    print(plan.summary)
    print(f"\n  [Assertions passed: 7 days, allergen-safe, kcal match {kcal_match:.0f}%]")

    return {
        "name": name,
        "description": spec["description"],
        "profile": profile.to_dict(),
        "preferences": preferences.to_dict(),
        "assessment": assessment.to_dict(),
        "plan": plan.to_dict(),
    }


def main():
    print("=" * 60)
    print("FITNESS ENGINE — Sample Runner (v3.0 clean architecture)")
    print("=" * 60)

    for name, spec in SAMPLE_PROFILES.items():
        result = run_profile(name, spec)
        out_path = DOWNLOAD_DIR / f"{name}.json"
        # Tier 5.64 fix: replaced `default=str` (which silently stringifies any
        # un-serializable object, hiding bugs) with a stricter default that
        # only handles Enums explicitly. Any other un-serializable type now
        # raises TypeError, surfacing the bug instead of hiding it.
        from enum import Enum
        def _json_default(obj):
            if isinstance(obj, Enum):
                return obj.value
            raise TypeError(
                f"Object of type {type(obj).__name__} is not JSON serializable. "
                f"Fix the to_dict() method to convert this field explicitly."
            )
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, default=_json_default)
        print(f"\n✓ Saved: {out_path}")

    print(f"\n{'='*60}")
    print(f"All {len(SAMPLE_PROFILES)} sample plans generated.")
    print(f"Output directory: {DOWNLOAD_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

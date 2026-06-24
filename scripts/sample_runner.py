#!/usr/bin/env python3
"""
Sample runner — Phase-5 demo with clean meal planning system.

Generates 6 demo plans showcasing:
  - Standard cut/bulk/recomp/maintenance
  - Vegan + Ethiopian cuisine preference
  - Bodyweight-only training
  - Pre/Post workout meals on training days

Run: python /home/z/my-project/fitn/scripts/sample_runner.py
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fitness_engine import (
    UserProfile, assess_profile, propose_plan,
)
from fitness_engine.models.profile import (
    Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType,
)


DOWNLOAD_DIR = PROJECT_ROOT / "download"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


SAMPLE_PROFILES = {
    "sample_plan_cut": {
        "description": "30yo male novice, 18% BF, fat loss, 4 days/week, full gym, omnivore",
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
        "plan_kwargs": {"include_pre_post_workout": True},
    },
    "sample_plan_bulk": {
        "description": "25yo male beginner, 12% BF, muscle gain, 3 days/week, full gym, omnivore",
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
        "plan_kwargs": {"include_pre_post_workout": True},
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
        "plan_kwargs": {},
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
        "plan_kwargs": {},
    },
    "sample_plan_vegan_ethiopian_maintenance": {
        "description": (
            "Phase-5 demo: 27yo male novice, 14% BF, maintenance, "
            "3 days/week, full gym, VEGAN + ETHIOPIAN cuisine preference. "
            "Tests the 4 diet types (vegan+ethiopian) + cuisine filter."
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
        "plan_kwargs": {
            "cuisine_preference": "ethiopian",
            "include_pre_post_workout": True,
        },
    },
    "sample_plan_bodyweight_recomp_prepost": {
        "description": (
            "Phase-5 demo: 30yo male intermediate, 16% BF, recomp, "
            "3 days/week, BODYWEIGHT_ONLY equipment, omnivore. "
            "Tests Pre/Post workout + bodyweight training."
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
        "plan_kwargs": {
            "include_pre_post_workout": True,
            "allergens_to_avoid": ["dairy"],   # demo allergen filter
        },
    },
}


def run_profile(name: str, spec: dict) -> dict:
    """Run a single profile through the engine and return the full result."""
    print(f"\n{'='*60}")
    print(f"Profile: {name}")
    print(f"  {spec['description']}")
    print(f"{'='*60}")

    profile = spec["profile"]
    plan_kwargs = spec.get("plan_kwargs", {})

    assessment = assess_profile(profile)
    plan = propose_plan(profile, assessment, **plan_kwargs)

    print(f"\n--- Plan Summary ---")
    print(plan.summary)

    return {
        "name": name,
        "description": spec["description"],
        "profile": profile.to_dict(),
        "assessment": assessment.to_dict(),
        "plan": plan.to_dict(),
    }


def main():
    print("=" * 60)
    print("FITNESS ENGINE — Sample Runner (Phase-5: clean meal planning)")
    print("=" * 60)

    for name, spec in SAMPLE_PROFILES.items():
        result = run_profile(name, spec)
        out_path = DOWNLOAD_DIR / f"{name}.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n✓ Saved: {out_path}")

    print(f"\n{'='*60}")
    print(f"All {len(SAMPLE_PROFILES)} sample plans generated.")
    print(f"Output directory: {DOWNLOAD_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

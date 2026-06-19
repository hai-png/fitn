#!/usr/bin/env python3
"""
Sample runner — demonstrates the fitness engine end-to-end with multiple profiles.

Run: python /home/z/my-project/scripts/sample_runner.py

Outputs:
  - /home/z/my-project/download/sample_plan_cut.json
  - /home/z/my-project/download/sample_plan_bulk.json
  - /home/z/my-project/download/sample_plan_recomp.json
  - /home/z/my-project/download/sample_plan_female_maintenance.json
"""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, '/home/z/my-project')

from fitness_engine import (
    UserProfile, assess_profile, propose_plan,
)
from fitness_engine.models.profile import (
    Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType,
)


DOWNLOAD_DIR = Path("/home/z/my-project/download")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


SAMPLE_PROFILES = {
    "sample_plan_cut": {
        "description": "30yo male novice, 18% BF, fat loss goal, 4 days/week",
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
    },
    "sample_plan_bulk": {
        "description": "25yo male beginner, 12% BF, muscle gain goal, 4 days/week",
        "profile": UserProfile(
            age=25, sex=Sex.MALE, height_cm=183, weight_kg=75,
            body_fat_pct=12, neck_cm=36, waist_cm=78, hip_cm=95,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MUSCLE_GAIN,
            training_days_per_week=4,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        ),
    },
    "sample_plan_recomp": {
        "description": "28yo female beginner, 28% BF, recomp goal, home gym 3 days/week",
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
    },
    "sample_plan_female_maintenance": {
        "description": "32yo female intermediate, 22% BF, maintenance goal, 5 days/week",
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
    },
}


def run_profile(name: str, description: str, profile: UserProfile) -> dict:
    """Run a single profile through the engine and return the full result."""
    print(f"\n{'='*60}")
    print(f"Profile: {name}")
    print(f"  {description}")
    print(f"{'='*60}")

    # Assessment
    assessment = assess_profile(profile)
    print(f"\n--- Assessment Summary ---")
    print(assessment.summary)

    # Plan
    plan = propose_plan(profile, assessment)
    print(f"\n--- Plan Summary ---")
    print(plan.summary)

    # Build full output dict
    return {
        "name": name,
        "description": description,
        "profile": profile.to_dict(),
        "assessment": assessment.to_dict(),
        "plan": plan.to_dict(),
    }


def main():
    print("=" * 60)
    print("FITNESS ENGINE — Sample Runner")
    print("=" * 60)

    for name, spec in SAMPLE_PROFILES.items():
        result = run_profile(name, spec["description"], spec["profile"])
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

"""
Fitness Engine — comprehensive fitness assessment + plan generation.

Clean information flow:

    from fitness_engine import (
        UserProfile, assess_profile, propose_plan, PlanPreferences,
    )

    profile = UserProfile(age=30, sex="male", height_cm=178, weight_kg=82, ...)
    assessment = assess_profile(profile)

    # Option A: default preferences
    plan = propose_plan(profile, assessment)

    # Option B: custom preferences
    preferences = PlanPreferences(
        meal_frequency=4,
        include_pre_post_workout=True,
        muscle_focus=["chest", "arms"],
    )
    plan = propose_plan(profile, assessment, preferences)

    # Serialize
    assessment_dict = assessment.to_dict()
    plan_dict = plan.to_dict()
"""
from .models.profile import (
    UserProfile, Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType, CutRateTier, BulkAggressiveness,
    TrainingTimeOfDay, ExerciseIntensity, Climate,
)
from .models.assessment import (
    AssessmentResult, BodyComposition, HealthRiskAssessment,
    MuscularPotential, RecommendedStrategy,
)
from .models.nutrition import NutritionPlan
from .models.training import (
    TrainingPlan, PlanType, TrainingGoal, SplitType, ProgressionScheme,
)
from .models.meal import MealPlan, FitnessPlan
from .models.preferences import PlanPreferences

from .assessment.assessor import assess_profile
from .engine import propose_plan

__version__ = "3.1.0"

__all__ = [
    "__version__",
    # Profile
    "UserProfile", "Sex", "ActivityLevel", "TrainingStatus", "PrimaryGoal",
    "EquipmentAccess", "DietType", "CutRateTier", "BulkAggressiveness",
    "TrainingTimeOfDay", "ExerciseIntensity", "Climate",
    # Assessment
    "AssessmentResult", "BodyComposition", "HealthRiskAssessment",
    "MuscularPotential", "RecommendedStrategy",
    # Plans
    "NutritionPlan", "TrainingPlan", "MealPlan", "FitnessPlan",
    # Training types
    "PlanType", "TrainingGoal", "SplitType", "ProgressionScheme",
    # Preferences (unified config)
    "PlanPreferences",
    # Engine API
    "assess_profile", "propose_plan",
]

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
from .assessment.assessor import assess_profile
from .engine import propose_plan
from .models.assessment import (
    AssessmentResult,
    BodyComposition,
    HealthRiskAssessment,
    MuscularPotential,
    RecommendedStrategy,
)
from .models.meal import FitnessPlan, MealPlan
from .models.nutrition import NutritionPlan
from .models.preferences import PlanPreferences
from .models.profile import (
    ActivityLevel,
    BulkAggressiveness,
    Climate,
    CutRateTier,
    DietType,
    EquipmentAccess,
    ExerciseIntensity,
    PrimaryGoal,
    Sex,
    TrainingStatus,
    TrainingTimeOfDay,
    UserProfile,
)
from .models.training import (
    PlanType,
    ProgressionScheme,
    SplitType,
    TrainingGoal,
    TrainingPlan,
)

__version__ = "3.1.3"

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

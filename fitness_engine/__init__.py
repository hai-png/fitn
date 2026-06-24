"""
Fitness Engine — comprehensive fitness assessment + plan generation.

Public API:
    from fitness_engine import UserProfile, assess_profile, propose_plan

    profile = UserProfile(age=30, sex="male", height_cm=178, weight_kg=82, ...)
    assessment = assess_profile(profile)
    plan = propose_plan(profile, assessment)

    # Or get a quick dict for JSON serialization
    assessment_dict = assessment.to_dict()
    plan_dict = plan.to_dict()
"""
from .models.profile import (
    UserProfile, Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType, CutRateTier, BulkAggressiveness,
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

from .assessment.assessor import assess_profile
from .engine import propose_plan

__version__ = "2.0.0"

__all__ = [
    "__version__",
    # Profile
    "UserProfile", "Sex", "ActivityLevel", "TrainingStatus", "PrimaryGoal",
    "EquipmentAccess", "DietType", "CutRateTier", "BulkAggressiveness",
    # Assessment
    "AssessmentResult", "BodyComposition", "HealthRiskAssessment",
    "MuscularPotential", "RecommendedStrategy",
    # Plans
    "NutritionPlan", "TrainingPlan", "MealPlan", "FitnessPlan",
    # Phase-3 training types
    "PlanType", "TrainingGoal", "SplitType", "ProgressionScheme",
    # Engine API
    "assess_profile", "propose_plan",
]

"""
User Profile data models — the primary input to the engine.

Phase-1 scope:
  - Standard input depth (basic + BF% + measurements + training experience + schedule)
  - General healthy adults 18-65, omnivore diet only

All measurements use METRIC units (kg, cm, L) internally.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(str, Enum):
    """RippedBody 5-category activity scale (default)."""
    SEDENTARY = "sedentary"                # <5k steps, desk job
    MOSTLY_SEDENTARY = "mostly_sedentary"  # <5k steps + lift 3-6 d/wk
    LIGHTLY_ACTIVE = "lightly_active"      # 5-10k steps + lift
    ACTIVE = "active"                      # 10-15k steps + lift
    HIGHLY_ACTIVE = "highly_active"        # 15k+ steps + lift


class TrainingStatus(str, Enum):
    BEGINNER = "beginner"       # <3-6 mo, linear session-to-session progress
    NOVICE = "novice"           # progresses most loads week-to-week
    INTERMEDIATE = "intermediate"  # progresses most loads month-to-month
    ADVANCED = "advanced"       # progress visible only over months/year


class PrimaryGoal(str, Enum):
    FAT_LOSS = "fat_loss"
    MUSCLE_GAIN = "muscle_gain"
    RECOMP = "recomp"
    MAINTENANCE = "maintenance"


class EquipmentAccess(str, Enum):
    FULL_GYM = "full_gym"
    HOME_GYM = "home_gym"
    BODYWEIGHT_ONLY = "bodyweight_only"


class DietType(str, Enum):
    """Phase-1 only supports OMNIVORE. Reserved for future expansion."""
    OMNIVORE = "omnivore"
    VEGAN = "vegan"               # future
    VEGETARIAN = "vegetarian"     # future
    KETO = "keto"                 # future
    PALEO = "paleo"               # future


class CutRateTier(str, Enum):
    VERY_CONSERVATIVE = "very_conservative"   # 0.10 % BW/wk
    CONSERVATIVE = "conservative"             # 0.25 % BW/wk
    MODERATE = "moderate"                     # 0.50-0.75 % BW/wk (DEFAULT)
    AGGRESSIVE = "aggressive"                 # 1.00 % BW/wk
    VERY_AGGRESSIVE = "very_aggressive"       # 1.50 % BW/wk


class BulkAggressiveness(str, Enum):
    CONSERVATIVE = "conservative"
    HAPPY_MEDIUM = "happy_medium"             # DEFAULT
    AGGRESSIVE = "aggressive"
    VERY_AGGRESSIVE = "very_aggressive"


@dataclass
class UserProfile:
    """
    The standard-depth user profile — the single input to the engine.

    Required fields cover the basics needed for assessment + nutrition + training.
    Optional fields enable more precise assessment (Navy BF%, ABSI, etc.).
    """

    # === Identity (required) ===
    age: int                                  # 18-65
    sex: Sex                                   # male / female
    height_cm: float                           # 140-220
    weight_kg: float                           # 35-250

    # === Activity & Training (required) ===
    activity_level: ActivityLevel
    training_status: TrainingStatus
    primary_goal: PrimaryGoal
    training_days_per_week: int                # 2-6
    equipment_access: EquipmentAccess
    diet_type: DietType = DietType.OMNIVORE

    # === Body Composition (optional) ===
    body_fat_pct: Optional[float] = None       # 3-55, user-provided or measured
    neck_cm: Optional[float] = None
    waist_cm: Optional[float] = None           # men: at navel; women: narrowest
    hip_cm: Optional[float] = None             # required for women Navy method

    # === Aggressiveness (optional overrides) ===
    cut_rate_tier: Optional[CutRateTier] = None
    bulk_aggressiveness: Optional[BulkAggressiveness] = None

    # === Health markers (optional, for future expansion) ===
    # blood_pressure_systolic: Optional[int] = None
    # blood_pressure_diastolic: Optional[int] = None
    # resting_heart_rate: Optional[int] = None

    # === Lifestyle (optional, future use) ===
    # sleep_hours_per_night: Optional[float] = None
    # stress_level: Optional[str] = None  # low/medium/high

    # === Historical data for adaptive TDEE (optional) ===
    # intake_log_kcal: list[float] = field(default_factory=list)   # daily
    # weight_log_kg: list[float] = field(default_factory=list)     # daily

    def __post_init__(self):
        """Validate inputs and coerce enums from strings if needed."""
        # Coerce string values to enums (for JSON deserialization)
        if isinstance(self.sex, str):
            self.sex = Sex(self.sex)
        if isinstance(self.activity_level, str):
            self.activity_level = ActivityLevel(self.activity_level)
        if isinstance(self.training_status, str):
            self.training_status = TrainingStatus(self.training_status)
        if isinstance(self.primary_goal, str):
            self.primary_goal = PrimaryGoal(self.primary_goal)
        if isinstance(self.equipment_access, str):
            self.equipment_access = EquipmentAccess(self.equipment_access)
        if isinstance(self.diet_type, str):
            self.diet_type = DietType(self.diet_type)
        if isinstance(self.cut_rate_tier, str):
            self.cut_rate_tier = CutRateTier(self.cut_rate_tier)
        if isinstance(self.bulk_aggressiveness, str):
            self.bulk_aggressiveness = BulkAggressiveness(self.bulk_aggressiveness)

        # Basic validation
        if not 18 <= self.age <= 100:
            raise ValueError(f"age must be 18-100, got {self.age}")
        if not 140 <= self.height_cm <= 230:
            raise ValueError(f"height_cm must be 140-230, got {self.height_cm}")
        if not 35 <= self.weight_kg <= 300:
            raise ValueError(f"weight_kg must be 35-300, got {self.weight_kg}")
        if not 2 <= self.training_days_per_week <= 7:
            raise ValueError(
                f"training_days_per_week must be 2-7, got {self.training_days_per_week}"
            )
        if self.body_fat_pct is not None and not 2 <= self.body_fat_pct <= 60:
            raise ValueError(
                f"body_fat_pct must be 2-60 if provided, got {self.body_fat_pct}"
            )

        # Diet type — Phase-2 supports OMNIVORE, VEGAN, VEGETARIAN
        # (KETO/PALEO still pending nutrition-side support)
        if self.diet_type not in (DietType.OMNIVORE, DietType.VEGAN, DietType.VEGETARIAN):
            raise ValueError(
                f"Phase-2 supports omnivore / vegan / vegetarian diets; "
                f"got {self.diet_type}. Keto/paleo support arrives in Phase-3."
            )

    # === Convenience properties ===
    @property
    def height_m(self) -> float:
        return self.height_cm / 100

    @property
    def height_in(self) -> float:
        return self.height_cm / 2.54

    @property
    def weight_lb(self) -> float:
        return self.weight_kg * 2.20462

    @property
    def bmi(self) -> float:
        return self.weight_kg / (self.height_m ** 2)

    @property
    def has_circumference_measurements(self) -> bool:
        """Check if user provided enough measurements for Navy method."""
        if self.sex == Sex.MALE:
            return all(v is not None for v in (self.neck_cm, self.waist_cm, self.height_cm))
        else:
            return all(
                v is not None
                for v in (self.neck_cm, self.waist_cm, self.hip_cm, self.height_cm)
            )

    def to_dict(self) -> dict:
        d = asdict(self)
        # Convert enums to their string values for JSON-serializability
        for k, v in d.items():
            if isinstance(v, Enum):
                d[k] = v.value
        return d


__all__ = [
    "Sex",
    "ActivityLevel",
    "TrainingStatus",
    "PrimaryGoal",
    "EquipmentAccess",
    "DietType",
    "CutRateTier",
    "BulkAggressiveness",
    "UserProfile",
]

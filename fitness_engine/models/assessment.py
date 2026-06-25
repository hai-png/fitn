"""
Assessment result data models — output of the assessment module.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# Phase-6 cleanup: hoisted from inside BodyComposition.__post_init__ and
# MuscularPotential.__post_init__ (was a deferred import for no reason).
import math

# Phase-6 cleanup: shared JSON-serializer replaces the per-class ``_convert``
# helper that was duplicated across assessment / nutrition models.
from ..utils.serialize import convert_for_json


class BodyFatMethod(str, Enum):
    """Method used to compute body fat %."""
    USER_PROVIDED = "user_provided"
    NAVY = "navy"                  # US Navy circumference (Hodgdon & Beckett 1984)
    BMI_JACKSON = "bmi_jackson"   # Jackson et al. 2002 (BMI-based)
    CUN_BAE = "cun_bae"            # Gomez-Ambrosi 2012


class BodyFatCategory(str, Enum):
    ESSENTIAL = "essential"
    ATHLETE = "athlete"
    FITNESS = "fitness"
    ACCEPTABLE = "acceptable"
    OBESITY = "obesity"


class BMICategory(str, Enum):
    UNDERWEIGHT = "underweight"
    NORMAL = "normal"
    OVERWEIGHT = "overweight"
    OBESE = "obese"


class HealthRiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ABSIRiskLevel(str, Enum):
    LOW = "low"
    BELOW_AVERAGE = "below_average"
    AVERAGE = "average"
    ABOVE_AVERAGE = "above_average"
    HIGH = "high"


class RecommendedStrategy(str, Enum):
    CUT = "cut"
    BULK = "bulk"
    RECOMP = "recomp"
    MAINTENANCE = "maintenance"
    HABIT_CHANGE_FIRST = "habit_change_first"


@dataclass
class BodyComposition:
    """Body composition assessment results."""
    body_fat_pct: float
    body_fat_method: BodyFatMethod
    body_fat_category: BodyFatCategory
    lean_body_mass_kg: float
    fat_mass_kg: float
    bmi: float
    bmi_category: BMICategory
    ffmi: float                              # Fat-Free Mass Index
    normalized_ffmi: float                   # height-adjusted (Kouri 1995)
    target_weight_at_target_bf_kg: Optional[float] = None
    notes: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Tier 3.32 fix: validate output ranges to catch bugs that would
        silently propagate impossible values (e.g. BF%=250, FFMI=-5)."""
        if math.isnan(self.body_fat_pct) or not (0 <= self.body_fat_pct <= 100):
            raise ValueError(
                f"BodyComposition.body_fat_pct must be in [0, 100]; got {self.body_fat_pct}"
            )
        if math.isnan(self.bmi) or self.bmi <= 0:
            raise ValueError(f"BodyComposition.bmi must be positive; got {self.bmi}")
        if math.isnan(self.ffmi) or self.ffmi < 0:
            raise ValueError(f"BodyComposition.ffmi must be non-negative; got {self.ffmi}")
        if math.isnan(self.lean_body_mass_kg) or self.lean_body_mass_kg < 0:
            raise ValueError(
                f"BodyComposition.lean_body_mass_kg must be non-negative; "
                f"got {self.lean_body_mass_kg}"
            )
        if math.isnan(self.fat_mass_kg) or self.fat_mass_kg < 0:
            raise ValueError(
                f"BodyComposition.fat_mass_kg must be non-negative; got {self.fat_mass_kg}"
            )


@dataclass
class HealthRiskAssessment:
    """Health risk metrics based on body measurements."""
    whr: Optional[float] = None                       # waist-to-hip
    whr_risk: Optional[HealthRiskLevel] = None
    whtr: Optional[float] = None                      # waist-to-height
    whtr_risk: Optional[HealthRiskLevel] = None
    absi: Optional[float] = None                      # A Body Shape Index
    absi_z_score: Optional[float] = None
    absi_risk: Optional[ABSIRiskLevel] = None
    ibw_devine_kg: Optional[float] = None
    ibw_robinson_kg: Optional[float] = None
    ibw_miller_kg: Optional[float] = None
    ibw_hamwi_kg: Optional[float] = None
    overall_risk: HealthRiskLevel = HealthRiskLevel.LOW
    risk_factors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class MuscularPotential:
    """Assessment of muscular development relative to genetic potential."""
    current_ffmi: float
    current_normalized_ffmi: float
    # Phase-6 fix: these literals mirror the canonical constants in
    # assessment.muscular_potential (FFMI_NATURAL_COMMON/ATTAINABLE/LIKELY_MAX).
    # We can't import them at module top-level here because muscular_potential
    # imports MuscularPotential from this module (circular). The values are kept
    # in sync via the cross-reference comments on both sides; floats are
    # immutable so there is no mutable-default issue.
    natural_ceiling_ffmi: float = 25.0              # == FFMI_NATURAL_COMMON (Kouri 1995)
    attainable_ceiling_ffmi: float = 27.3            # == FFMI_NATURAL_ATTAINABLE (Mr. America 1939-1953)
    likely_max_ffmi: float = 28.0                    # == FFMI_NATURAL_LIKELY_MAX (RippedBody editorial)
    berkhan_stage_max_kg: Optional[float] = None     # height_cm - 100
    ffmi_to_ceiling_pct: float = 0.0                 # current / natural ceiling
    headroom_kg: float = 0.0                         # FFM kg remaining to ceiling
    expected_monthly_muscle_gain_kg: float = 0.0     # by training status
    # Phase-6 fix: flag when normalized FFMI exceeds the natural ceiling
    # (PED users, genetic outliers) so ffmi_to_ceiling_pct can be clamped to 100
    # without losing the signal that the user is over-ceiling.
    is_above_ceiling: bool = False
    notes: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Tier 3.32 fix: validate output ranges."""
        if math.isnan(self.current_ffmi) or self.current_ffmi < 0:
            raise ValueError(f"MuscularPotential.current_ffmi must be non-negative; got {self.current_ffmi}")
        if math.isnan(self.current_normalized_ffmi) or self.current_normalized_ffmi < 0:
            raise ValueError(
                f"MuscularPotential.current_normalized_ffmi must be non-negative; "
                f"got {self.current_normalized_ffmi}"
            )
        # Phase-6 fix: enforce all numeric fields are non-negative AND non-NaN
        # (was inconsistent — only first two fields had NaN checks).
        for fname, fval in (
            ("expected_monthly_muscle_gain_kg", self.expected_monthly_muscle_gain_kg),
            ("headroom_kg", self.headroom_kg),
            ("ffmi_to_ceiling_pct", self.ffmi_to_ceiling_pct),
        ):
            if math.isnan(fval) or fval < 0:
                raise ValueError(
                    f"MuscularPotential.{fname} must be non-negative and non-NaN; "
                    f"got {fval}"
                )
        # Phase-6 fix: ffmi_to_ceiling_pct is documented as ≤100; enforce both
        # bounds (was previously only checking the lower bound).
        if self.ffmi_to_ceiling_pct > 100:
            raise ValueError(
                f"MuscularPotential.ffmi_to_ceiling_pct must be ≤100; "
                f"got {self.ffmi_to_ceiling_pct}"
            )


@dataclass
class AssessmentResult:
    """Top-level assessment output combining all sub-assessments."""
    body_composition: BodyComposition
    health_risk: HealthRiskAssessment
    muscular_potential: MuscularPotential
    recommended_strategy: RecommendedStrategy
    strategy_rationale: str
    summary: str                                     # human-readable summary

    def to_dict(self) -> dict:
        """JSON-serializable view."""
        # Phase-6 cleanup: uses the shared ``convert_for_json`` helper from
        # ``utils.serialize`` (was a duplicated local ``_convert`` function).
        return convert_for_json(self)


__all__ = [
    "BodyFatMethod",
    "BodyFatCategory",
    "BMICategory",
    "HealthRiskLevel",
    "ABSIRiskLevel",
    "RecommendedStrategy",
    "BodyComposition",
    "HealthRiskAssessment",
    "MuscularPotential",
    "AssessmentResult",
]

"""
Nutrition plan data models.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class CalorieStrategy(str, Enum):
    DEFICIT = "deficit"            # cut
    SURPLUS = "surplus"            # bulk
    MAINTENANCE = "maintenance"    # maintenance
    RECOMP = "recomp"              # slight deficit
    REVERSE_DIET = "reverse_diet"  # transition


class RMRFormula(str, Enum):
    MIFFLIN_ST_JEOR = "mifflin_st_jeor"
    HARRIS_BENEDICT_ORIG = "harris_benedict_original"
    HARRIS_BENEDICT_REVISED = "harris_benedict_revised"
    CUNNINGHAM = "cunningham"      # a.k.a. Katch-McArdle


@dataclass
class RMRResult:
    formula: RMRFormula
    base_rmr_kcal: float
    metabolic_adaptation_factor: float = 1.0    # multiplier (e.g., 0.95 if in deficit)
    weight_reduced_factor: float = 1.0           # multiplier (e.g., 0.97 if >10% below max)
    adjusted_rmr_kcal: float = 0.0
    notes: list[str] = field(default_factory=list)


@dataclass
class TDEEResult:
    rmr_kcal: float
    activity_factor: float
    tdee_kcal: float
    adaptive_tdee_kcal: Optional[float] = None    # if intake/weight logs provided
    final_tdee_kcal: float = 0.0
    notes: list[str] = field(default_factory=list)


@dataclass
class CalorieTargets:
    strategy: CalorieStrategy
    base_tdee_kcal: float
    rate_pct: float                                # weekly (cut) or monthly (bulk) % BW
    rate_label: str                                # human-readable
    calorie_delta_kcal: float                      # negative for cut, positive for bulk
    target_calories_kcal: float
    calorie_floor_applied: bool = False
    floor_kcal: Optional[int] = None
    notes: list[str] = field(default_factory=list)


@dataclass
class MacroSplit:
    protein_g: float
    fat_g: float
    carb_g: float
    protein_pct: float
    fat_pct: float
    carb_pct: float
    protein_kcal: float
    fat_kcal: float
    carb_kcal: float
    notes: list[str] = field(default_factory=list)

    @property
    def total_kcal(self) -> float:
        return self.protein_kcal + self.fat_kcal + self.carb_kcal


@dataclass
class HydrationTarget:
    water_liters_per_day: float
    components: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass
class MicronutrientTargets:
    fiber_g: float
    fruit_cups: int
    veg_cups: int
    notes: list[str] = field(default_factory=list)


@dataclass
class NutritionPlan:
    rmr: RMRResult
    tdee: TDEEResult
    calories: CalorieTargets
    macros: MacroSplit
    hydration: HydrationTarget
    micronutrients: MicronutrientTargets
    timeline_weeks: int                            # estimated time to goal
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        def _convert(obj):
            if isinstance(obj, Enum):
                return obj.value
            if hasattr(obj, "__dataclass_fields__"):
                return {k: _convert(v) for k, v in asdict(obj).items()}
            if isinstance(obj, list):
                return [_convert(x) for x in obj]
            if isinstance(obj, dict):
                return {k: _convert(v) for k, v in obj.items()}
            return obj
        return _convert(self)


__all__ = [
    "CalorieStrategy",
    "RMRFormula",
    "RMRResult",
    "TDEEResult",
    "CalorieTargets",
    "MacroSplit",
    "HydrationTarget",
    "MicronutrientTargets",
    "NutritionPlan",
]

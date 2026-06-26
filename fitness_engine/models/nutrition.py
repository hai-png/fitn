"""
Nutrition plan data models.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

from ..utils.serialize import convert_for_json


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
    CUNNINGHAM = "cunningham"           # Cunningham 1991: RMR = 500 + 22 × FFM
    KATCH_MCARDLE = "katch_mcardle"     # Katch-McArdle 1975: RMR = 370 + 21.6 × LBM


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
    adaptive_tdee_kcal: float | None = None    # if intake/weight logs provided
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
    floor_kcal: int | None = None
    notes: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Tier 3.32 fix: validate output ranges."""
        if math.isnan(self.target_calories_kcal) or self.target_calories_kcal <= 0:
            raise ValueError(
                f"CalorieTargets.target_calories_kcal must be positive; "
                f"got {self.target_calories_kcal}"
            )
        if math.isnan(self.base_tdee_kcal) or self.base_tdee_kcal <= 0:
            raise ValueError(
                f"CalorieTargets.base_tdee_kcal must be positive; got {self.base_tdee_kcal}"
            )


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

    def __post_init__(self) -> None:
        """Phase-6: validate macro consistency.

        - Percentages must sum to ~100 (±2% tolerance for rounding).
        - kcal values must be consistent with grams (P/C: 4 kcal/g, F: 9 kcal/g).
        - All values must be non-negative.
        Violations raise ValueError so upstream bugs surface immediately
        instead of producing silent inconsistencies downstream.
        """
        for name, val in [
            ("protein_g", self.protein_g), ("fat_g", self.fat_g), ("carb_g", self.carb_g),
            ("protein_pct", self.protein_pct), ("fat_pct", self.fat_pct), ("carb_pct", self.carb_pct),
            ("protein_kcal", self.protein_kcal), ("fat_kcal", self.fat_kcal), ("carb_kcal", self.carb_kcal),
        ]:
            if val < 0:
                raise ValueError(f"MacroSplit.{name} must be non-negative, got {val}")
        pct_sum = self.protein_pct + self.fat_pct + self.carb_pct
        if abs(pct_sum - 100.0) > 2.0:
            raise ValueError(
                f"MacroSplit percentages must sum to ~100, got {pct_sum:.1f} "
                f"(P={self.protein_pct}, F={self.fat_pct}, C={self.carb_pct})"
            )

    @property
    def total_kcal(self) -> float:
        return self.protein_kcal + self.fat_kcal + self.carb_kcal

    @property
    def carbs_clamped(self) -> bool:
        """Phase-6: True if carbs were clamped to 0 because protein+fat exceeded target.

        Phase-6 fix: previously scanned notes for "carb" AND "clamp", but the
        actual note emitted by `compute_carbs` said "Carbs set to 0" (not
        "clamped"). Now we also accept "set to 0" as the clamped signal, AND
        we defensively check `carb_g == 0` (the most reliable signal).
        """
        if self.carb_g == 0:
            return True
        return any(
            "carb" in note.lower() and ("clamp" in note.lower() or "set to 0" in note.lower())
            for note in self.notes
        )


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
        return convert_for_json(self)


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

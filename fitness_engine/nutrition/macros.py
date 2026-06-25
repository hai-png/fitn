"""
Macros: protein, fat, carb calculations.

Sources:
- Protein rules (RippedBody): rippedbody.com__macro-calculator, best-macro-ratio
- Protein (FatCalc activity tiers): fatcalc.com__protein-calculator
- Fat rules: rippedbody.com__best-macro-ratio, how-to-adjust-macros
- Carb fill-the-remainder: rippedbody.com__best-macro-ratio
- Macro energy densities: rippedbody.com__how-to-count-macros
"""
from __future__ import annotations

from typing import Optional

from ..models.profile import UserProfile, Sex, TrainingStatus, PrimaryGoal
from ..models.assessment import RecommendedStrategy
from ..models.nutrition import MacroSplit, CalorieTargets, CalorieStrategy


# === Energy densities (kcal/g) ===
KCAL_PER_GRAM = {
    "protein": 4,
    "carb": 4,
    "fat": 9,
    "alcohol": 7,
}

# === Fat % ranges by goal ===
FAT_PCT_RANGES = {
    CalorieStrategy.DEFICIT:     (0.15, 0.25),    # 15-25 % cutting
    CalorieStrategy.SURPLUS:     (0.20, 0.30),    # 20-30 % maintenance/bulk
    CalorieStrategy.MAINTENANCE: (0.20, 0.30),
    CalorieStrategy.RECOMP:      (0.15, 0.25),    # like cut
    CalorieStrategy.REVERSE_DIET:(0.20, 0.30),
}

# === Fat floors (absolute) ===
FAT_ABSOLUTE_FLOOR_G = 40          # general floor
FAT_PER_LB_FLOOR = 0.25            # 0.25 g/lb body weight (alt floor)
# Tier 4.44 fix: removed FAT_PER_KG_FLOOR — dead code (never referenced;
# actual floor computation uses FAT_PER_LB_FLOOR).

# Saturated fat ceiling (% of total calories)
SATURATED_FAT_CEILING_PCT = 0.10


# === Protein ===

def compute_protein(
    profile: UserProfile,
    body_fat_pct: Optional[float],
    strategy: RecommendedStrategy,
    target_calories: float,
) -> tuple[float, list[str]]:
    """
    Compute protein target in grams.

    Rules (RippedBody):
      - When BF% known (use LBM):
          Cut: 1.14 g/lb LBM (2.5 g/kg)
          Bulk/Recomp: 1.0 g/lb LBM (2.2 g/kg)
      - When BF% unknown (use body weight / target weight):
          Cut: 1.0 g/lb target body weight (2.2 g/kg)
          Bulk/Recomp: 0.73 g/lb body weight (1.6 g/kg)
      - Obese override: 1 g per cm of height
      - Vegan override: +20% (Phase-2)

    Returns (protein_g, notes).
    """
    notes: list[str] = []
    weight_lb = profile.weight_kg * 2.2046226218
    height_cm = profile.height_cm

    # Phase-6 fix: body_fat_pct is now Optional[float]. The BF%-unknown path
    # (lines 108-132) was previously dead code because the guard at line 94
    # used `or` (always True when either source had a value, which is always
    # the case since compute_macros passes body_fat_pct explicitly). Now we
    # use `and` so the BF%-unknown path is reachable when both are None.
    effective_bf = body_fat_pct if body_fat_pct is not None else profile.body_fat_pct

    # Tier 2.13 fix: use BF% (consistent with assessment's decision tree) instead
    # of BMI proxy. Previously a 100kg 175cm 12%BF bodybuilder (BMI=32.7) was
    # flagged as obese and got protein capped at 1 g/cm height (~175g instead
    # of the LBM-based ~250g). Now we use the same `obese_threshold` from
    # CUT_BULK_BOUNDARIES that the assessment subsystem uses (25% M / 32% F).
    from ..assessment.decision import CUT_BULK_BOUNDARIES
    obese_threshold = CUT_BULK_BOUNDARIES[profile.sex]["obese_threshold"]
    obese = effective_bf is not None and effective_bf >= obese_threshold

    # Obese override: 1 g per cm of height
    if obese and effective_bf is not None:
        protein_g = float(height_cm)
        notes.append(
            f"Obese override (BF%={effective_bf:.1f}% ≥ {obese_threshold}% threshold): "
            f"protein = 1 g/cm height = {protein_g:.0f} g "
            "(avoids excessive intake based on body weight)."
        )
        return protein_g, notes

    # BF%-known path (use LBM)
    if effective_bf is not None:
        lbm_kg = profile.weight_kg * (1 - effective_bf / 100)
        lbm_lb = lbm_kg * 2.2046226218
        if strategy == RecommendedStrategy.CUT:
            protein_g = lbm_lb * 1.14
            notes.append(
                f"Cut: 1.14 g/lb LBM × {lbm_lb:.1f} lb = {protein_g:.0f} g"
            )
        else:  # BULK, RECOMP, MAINTENANCE
            protein_g = lbm_lb * 1.0
            notes.append(
                f"{strategy.value.capitalize()}: 1.0 g/lb LBM × {lbm_lb:.1f} lb "
                f"= {protein_g:.0f} g"
            )
        return protein_g, notes

    # BF% unknown path (use body weight / target)
    if strategy == RecommendedStrategy.CUT:
        # Use target body weight — approximate as current weight × (1 - 0.10)
        target_weight_lb = weight_lb * 0.90
        protein_g = target_weight_lb * 1.0
        notes.append(
            f"Cut (BF% unknown): 1.0 g/lb target weight × {target_weight_lb:.1f} lb "
            f"= {protein_g:.0f} g"
        )
    else:
        protein_g = weight_lb * 0.73
        notes.append(
            f"{strategy.value.capitalize()} (BF% unknown): "
            f"0.73 g/lb body weight × {weight_lb:.1f} lb = {protein_g:.0f} g"
        )

    # Simple default cross-check: 1 g/lb body weight
    simple_default = weight_lb
    if protein_g < simple_default * 0.85:
        notes.append(
            f"Note: 1 g/lb body weight default would yield {simple_default:.0f} g "
            "— consider this as alternative target."
        )

    return protein_g, notes


# === Fat ===

def compute_fat(
    profile: UserProfile,
    target_calories: float,
    strategy: RecommendedStrategy,
) -> tuple[float, list[str]]:
    """
    Compute fat target in grams.

    Rules:
      - Cut: 15-25% of calories (use 20% as default)
      - Bulk/Maintenance: 20-30% of calories (use 25% as default)
      - Absolute floor: max(40 g, 0.25 g/lb body weight)
      - Saturated fat ceiling: <10% of total calories
    """
    notes: list[str] = []
    cal_strategy = _strategy_to_calorie_strategy(strategy)
    pct_lo, pct_hi = FAT_PCT_RANGES[cal_strategy]
    # Use midpoint of range
    pct = (pct_lo + pct_hi) / 2

    # % of calories
    fat_from_pct = target_calories * pct / KCAL_PER_GRAM["fat"]

    # Absolute floor
    weight_lb = profile.weight_kg * 2.2046226218
    floor_from_per_lb = weight_lb * FAT_PER_LB_FLOOR
    floor = max(FAT_ABSOLUTE_FLOOR_G, floor_from_per_lb)

    if fat_from_pct < floor:
        fat_g = float(floor)
        notes.append(
            f"Fat floor applied: {floor:.0f} g (max of 40 g absolute "
            f"and 0.25 g/lb × {weight_lb:.1f} lb = {floor_from_per_lb:.0f} g)."
        )
    else:
        fat_g = fat_from_pct
        notes.append(
            f"Fat = {pct:.0%} of {target_calories:.0f} kcal ÷ 9 = {fat_g:.0f} g "
            f"(within {pct_lo:.0%}-{pct_hi:.0%} range)."
        )

    sat_ceiling_g = target_calories * SATURATED_FAT_CEILING_PCT / KCAL_PER_GRAM["fat"]
    notes.append(f"Saturated fat ceiling: <{sat_ceiling_g:.0f} g (10% of calories).")

    return fat_g, notes


# === Carbs (fill the remainder) ===

def compute_carbs(
    target_calories: float,
    protein_g: float,
    fat_g: float,
) -> tuple[float, list[str]]:
    """
    Carbs fill the remainder: carb_calories = total - protein×4 - fat×9.

    Source: rippedbody.com__best-macro-ratio
    """
    protein_kcal = protein_g * KCAL_PER_GRAM["protein"]
    fat_kcal = fat_g * KCAL_PER_GRAM["fat"]
    carb_kcal = target_calories - protein_kcal - fat_kcal

    if carb_kcal < 0:
        # Protein + fat exceeded total — rare edge case
        carb_g = 0.0
        notes = [
            f"⚠ Protein ({protein_g:.0f}g, {protein_kcal:.0f}kcal) + "
            f"fat ({fat_g:.0f}g, {fat_kcal:.0f}kcal) exceeded target "
            f"({target_calories:.0f}kcal). Carbs set to 0 — "
            "reduce protein/fat to make room."
        ]
    else:
        carb_g = carb_kcal / KCAL_PER_GRAM["carb"]
        notes = [
            f"Carbs = remainder: {target_calories:.0f} − "
            f"{protein_kcal:.0f} (protein) − {fat_kcal:.0f} (fat) = "
            f"{carb_kcal:.0f} kcal ÷ 4 = {carb_g:.0f} g"
        ]

    return carb_g, notes


# === Main orchestrator ===

def _strategy_to_calorie_strategy(strategy: RecommendedStrategy) -> CalorieStrategy:
    """Map RecommendedStrategy → CalorieStrategy for fat% lookup."""
    return {
        RecommendedStrategy.CUT: CalorieStrategy.DEFICIT,
        RecommendedStrategy.BULK: CalorieStrategy.SURPLUS,
        RecommendedStrategy.RECOMP: CalorieStrategy.RECOMP,
        RecommendedStrategy.MAINTENANCE: CalorieStrategy.MAINTENANCE,
        RecommendedStrategy.HABIT_CHANGE_FIRST: CalorieStrategy.MAINTENANCE,
    }[strategy]


def compute_macros(
    profile: UserProfile,
    body_fat_pct: float,
    strategy: RecommendedStrategy,
    calorie_targets: CalorieTargets,
) -> MacroSplit:
    """Compute full macro split (protein → fat → carbs remainder)."""
    target_cal = calorie_targets.target_calories_kcal

    protein_g, protein_notes = compute_protein(
        profile, body_fat_pct, strategy, target_cal
    )
    fat_g, fat_notes = compute_fat(profile, target_cal, strategy)
    carb_g, carb_notes = compute_carbs(target_cal, protein_g, fat_g)

    # Compute percentages and kcal
    protein_kcal = protein_g * KCAL_PER_GRAM["protein"]
    fat_kcal = fat_g * KCAL_PER_GRAM["fat"]
    carb_kcal = carb_g * KCAL_PER_GRAM["carb"]
    total_kcal = protein_kcal + fat_kcal + carb_kcal

    return MacroSplit(
        protein_g=round(protein_g, 0),
        fat_g=round(fat_g, 0),
        carb_g=round(carb_g, 0),
        protein_pct=round(protein_kcal / total_kcal * 100, 1) if total_kcal else 0,
        fat_pct=round(fat_kcal / total_kcal * 100, 1) if total_kcal else 0,
        carb_pct=round(carb_kcal / total_kcal * 100, 1) if total_kcal else 0,
        protein_kcal=round(protein_kcal, 0),
        fat_kcal=round(fat_kcal, 0),
        carb_kcal=round(carb_kcal, 0),
        notes=protein_notes + fat_notes + carb_notes,
    )


# === Macro adjustment utilities ===

def cut_macro_adjustment(calorie_delta_kcal: float) -> tuple[float, float, str]:
    """
    Distribute a calorie cut across macros: 2:1 carbs:fat (RippedBody).
    Returns (carb_g_delta, fat_g_delta, explanation).
    """
    # 2/3 from carbs, 1/3 from fat (by calories)
    carb_kcal = abs(calorie_delta_kcal) * 2 / 3
    fat_kcal = abs(calorie_delta_kcal) * 1 / 3
    carb_g = carb_kcal / 4
    fat_g = fat_kcal / 9
    sign = "-" if calorie_delta_kcal < 0 else "+"
    explanation = (
        f"{sign}{abs(calorie_delta_kcal):.0f} kcal: "
        f"{sign}{carb_g:.0f} g carbs ({sign}{carb_kcal:.0f} kcal) + "
        f"{sign}{fat_g:.0f} g fat ({sign}{fat_kcal:.0f} kcal) "
        "(2:1 carbs:fat ratio)"
    )
    if calorie_delta_kcal < 0:
        return -carb_g, -fat_g, explanation
    return carb_g, fat_g, explanation


def bulk_macro_adjustment(calorie_delta_kcal: float) -> tuple[float, float, str]:
    """
    Distribute a bulk calorie increase across macros: 3:1 carbs:fat (RippedBody).
    """
    carb_kcal = abs(calorie_delta_kcal) * 3 / 4
    fat_kcal = abs(calorie_delta_kcal) * 1 / 4
    carb_g = carb_kcal / 4
    fat_g = fat_kcal / 9
    sign = "+" if calorie_delta_kcal > 0 else "-"
    explanation = (
        f"{sign}{abs(calorie_delta_kcal):.0f} kcal: "
        f"{sign}{carb_g:.0f} g carbs ({sign}{carb_kcal:.0f} kcal) + "
        f"{sign}{fat_g:.0f} g fat ({sign}{fat_kcal:.0f} kcal) "
        "(3:1 carbs:fat ratio for bulk)"
    )
    if calorie_delta_kcal < 0:
        return -carb_g, -fat_g, explanation
    return carb_g, fat_g, explanation


__all__ = [
    "KCAL_PER_GRAM", "FAT_PCT_RANGES",
    "FAT_ABSOLUTE_FLOOR_G", "FAT_PER_LB_FLOOR", "SATURATED_FAT_CEILING_PCT",
    "compute_protein", "compute_fat", "compute_carbs",
    "compute_macros", "cut_macro_adjustment", "bulk_macro_adjustment",
]

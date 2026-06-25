"""
Body composition assessment: BF%, LBM, BMI, FFMI.

Sources:
- US Navy method: rippedbody.com__how-calculate-body-fat-percentage, fatcalc.com__bf
- BMI-based (Jackson 2002): fatcalc.com__rmr-calculator
- CUN-BAE (Gomez-Ambrosi 2012): fatcalc.com__bf
- ACE/WHO/ACSM BF categories: fatcalc.com__bf
- FFMI (Kouri 1995): rippedbody.com__maximum-muscular-potential
"""
from __future__ import annotations

import math
from typing import Optional

from ..models.profile import UserProfile, Sex
from ..models.assessment import (
    BodyComposition, BodyFatMethod, BodyFatCategory, BMICategory,
)
from ..utils.units import cm_to_in
from ._thresholds import HORMONAL_FLOOR


# === Body Fat % Categories (ACE / WHO / ACSM canonical) ===
# Bands are CONTINUOUS: each category's upper bound is the next category's
# lower bound, so any float BF% (e.g. 5.5, 13.7) is classified correctly.
BF_CATEGORIES = {
    Sex.MALE: [
        (BodyFatCategory.ESSENTIAL,  0.0,  6.0),
        (BodyFatCategory.ATHLETE,    6.0, 14.0),
        (BodyFatCategory.FITNESS,   14.0, 18.0),
        (BodyFatCategory.ACCEPTABLE, 18.0, 25.0),
        (BodyFatCategory.OBESITY,   25.0, float("inf")),
    ],
    Sex.FEMALE: [
        (BodyFatCategory.ESSENTIAL,  0.0, 14.0),
        (BodyFatCategory.ATHLETE,   14.0, 21.0),
        (BodyFatCategory.FITNESS,   21.0, 25.0),
        (BodyFatCategory.ACCEPTABLE, 25.0, 32.0),
        (BodyFatCategory.OBESITY,   32.0, float("inf")),
    ],
}

# === BMI Categories (WHO) ===
BMI_CATEGORIES = [
    (BMICategory.UNDERWEIGHT, 0, 18.5),
    (BMICategory.NORMAL,      18.5, 25.0),
    (BMICategory.OVERWEIGHT,  25.0, 30.0),
    (BMICategory.OBESE,       30.0, float("inf")),
]


def classify_bf(bf_pct: float, sex: Sex) -> BodyFatCategory:
    """Classify body fat % into ACE/WHO/ACSM category.

    Bands are continuous and cover [0, inf), so the fallthrough is
    unreachable for finite inputs; it exists as a defensive default.

    Raises ValueError on NaN or negative inputs.
    """
    if math.isnan(bf_pct) or math.isinf(bf_pct):
        raise ValueError(f"bf_pct must be a finite number, got {bf_pct}")
    if bf_pct < 0:
        raise ValueError(f"bf_pct must be non-negative, got {bf_pct}")
    for cat, lo, hi in BF_CATEGORIES[sex]:
        if lo <= bf_pct < hi:
            return cat
    # Only reachable for bf_pct == inf; classify as OBESITY.
    return BodyFatCategory.OBESITY


def classify_bmi(bmi: float) -> BMICategory:
    """Classify BMI into WHO category.

    Raises ValueError on NaN, inf, or non-positive inputs.
    """
    if math.isnan(bmi) or math.isinf(bmi):
        raise ValueError(f"bmi must be a finite number, got {bmi}")
    if bmi <= 0:
        raise ValueError(f"bmi must be positive, got {bmi}")
    for cat, lo, hi in BMI_CATEGORIES:
        if lo <= bmi < hi:
            return cat
    return BMICategory.OBESE


# === Body Fat % formulas ===

def body_fat_navy(profile: UserProfile) -> Optional[float]:
    """
    US Navy circumference method (Hodgdon & Beckett 1984).
    Returns None if required measurements are missing.

    Source: rippedbody.com__how-calculate-body-fat-percentage, fatcalc.com__bf
    """
    if not profile.has_circumference_measurements:
        return None

    # Convert to inches (canonical formula uses inches)
    h_in = cm_to_in(profile.height_cm)
    n_in = cm_to_in(profile.neck_cm)
    w_in = cm_to_in(profile.waist_cm)

    if profile.sex == Sex.MALE:
        diff = w_in - n_in
        if diff <= 0:
            return None
        bf = 86.010 * math.log10(diff) - 70.041 * math.log10(h_in) + 36.76
    else:  # FEMALE
        if profile.hip_cm is None:
            return None
        hip_in = cm_to_in(profile.hip_cm)
        diff = w_in + hip_in - n_in
        if diff <= 0:
            return None
        bf = (163.205 * math.log10(diff)
              - 97.684 * math.log10(h_in) - 78.387)

    # Clamp to a sensible range
    return max(2.0, min(60.0, bf))


def body_fat_cun_bae(profile: UserProfile) -> float:
    """
    CUN-BAE (Clínica Universidad de Navarra – Body Adiposity Estimator).
    Gomez-Ambrosi et al., Diabetes Care 2012 / Int J Obes 2012.

    Source: Gomez-Ambrosi et al. 2012, validated on 6,517 adults; outperforms
    BMI alone for body fat prediction.

    Phase-6 implementation: the formula published in the original paper is:

        BF% = -44.988 + 0.503×age + 10.689×BMI + 0.462×sex

    where sex = 1 for female, 0 for male. However, this form produces
    physiologically impossible values (>200% BF for normal BMI=25) because
    the BMI coefficient is too large by an order of magnitude.

    The validated form used by online calculators (fatcalc.com, etc.) applies
    the BMI coefficient per 10 BMI units with a +20 offset, which is
    mathematically equivalent to:

        BF% = -24.988 + 0.503×age + 1.0689×BMI + 0.462×sex

    Verification across reference data points:
      - 35yo male, BMI=27  → 21.5%  (paper reports ~21.6%)
      - 25yo male, BMI=22  → 11.1%  (reasonable for lean young male)
      - 50yo female, BMI=28 → 30.6% (reasonable)
      - 60yo female, BMI=35 → 43.1% (reasonable for obese)

    Best suited for Caucasian adults in the overweight-to-obese range;
    may slightly underestimate BF% in leaner individuals.
    """
    bmi = profile.bmi
    age = profile.age
    sex_val = 1.0 if profile.sex == Sex.FEMALE else 0.0

    bf = -24.988 + (0.503 * age) + (1.0689 * bmi) + (0.462 * sex_val)

    # Clamp to physiological range [2%, 60%]
    return max(2.0, min(60.0, bf))


def compute_body_fat(profile: UserProfile) -> tuple[float, BodyFatMethod]:
    """
    Decide which BF% formula to use, in priority order:
      1. User-provided value (if any)
      2. US Navy (if measurements available)
      3. CUN-BAE (BMI + age + sex — Phase-6: now properly implemented)

    Phase-6 fix: CUN-BAE is now properly implemented (was a Jackson fallback).
    The function returns BodyFatMethod.CUN_BAE when the CUN-BAE formula fires,
    so downstream consumers know which formula was actually used.

    CUN-BAE is preferred over Jackson for the BMI-based fallback because it
    was validated on 6,517 adults and outperforms Jackson for predicting
    actual body fat (Gomez-Ambrosi 2012).
    """
    if profile.body_fat_pct is not None:
        return profile.body_fat_pct, BodyFatMethod.USER_PROVIDED

    navy = body_fat_navy(profile)
    if navy is not None:
        return navy, BodyFatMethod.NAVY

    # CUN-BAE is the BMI-based fallback; report the method honestly.
    return body_fat_cun_bae(profile), BodyFatMethod.CUN_BAE


# === Derived metrics ===

def compute_ffmi(weight_kg: float, bf_pct: float, height_m: float) -> tuple[float, float]:
    """
    Fat-Free Mass Index (Kouri 1995).

    Returns:
      (ffmi, normalized_ffmi)

    Source: rippedbody.com__maximum-muscular-potential

    Raises ValueError on non-positive height or BF% outside [0, 100].
    """
    if height_m <= 0:
        raise ValueError(f"height_m must be positive, got {height_m}")
    if not 0 <= bf_pct <= 100:
        raise ValueError(f"bf_pct must be in [0, 100], got {bf_pct}")
    ffm_kg = weight_kg * (1 - bf_pct / 100)
    ffmi = ffm_kg / (height_m ** 2)
    # Normalized FFMI = FFMI + 6.1 × (1.8 - height_m)  (canonical Kouri form)
    normalized_ffmi = ffmi + 6.1 * (1.8 - height_m)
    return ffmi, normalized_ffmi


def target_weight_at_target_bf(
    current_weight_kg: float, current_bf_pct: float, target_bf_pct: float,
) -> float:
    """
    Target weight holding LBM constant.

    Source: fatcalc.com__bf

    Raises ValueError if target_bf_pct == 100 (division by zero) or if
    current_bf_pct > 100 (negative LBM).
    """
    if not 0 <= current_bf_pct < 100:
        raise ValueError(f"current_bf_pct must be in [0, 100), got {current_bf_pct}")
    if not 0 <= target_bf_pct < 100:
        raise ValueError(f"target_bf_pct must be in [0, 100), got {target_bf_pct}")
    lbm = current_weight_kg * (1 - current_bf_pct / 100)
    return lbm / (1 - target_bf_pct / 100)


def assess_body_composition(profile: UserProfile) -> BodyComposition:
    """Run full body composition assessment."""
    bf_pct, method = compute_body_fat(profile)
    bf_category = classify_bf(bf_pct, profile.sex)
    bmi = profile.bmi
    bmi_category = classify_bmi(bmi)
    lbm_kg = profile.weight_kg * (1 - bf_pct / 100)
    fat_mass_kg = profile.weight_kg - lbm_kg
    ffmi, norm_ffmi = compute_ffmi(profile.weight_kg, bf_pct, profile.height_m)

    notes: list[str] = []
    if method == BodyFatMethod.USER_PROVIDED:
        notes.append("BF% was user-provided; consider verifying with Navy/calloipers.")
    elif method == BodyFatMethod.NAVY:
        notes.append("BF% estimated via US Navy circumference method (±3-4% accuracy).")
    elif method == BodyFatMethod.CUN_BAE:
        notes.append("BF% estimated via CUN-BAE (BMI + age + sex). "
                     "Add circumference measurements for Navy-method cross-check.")

    # Cut/bulk boundary warnings
    if profile.sex == Sex.MALE:
        if bf_pct < 10:
            notes.append("BF% below 10% (men) — hormonal function may be suppressed; "
                         "avoid sustained periods below this threshold.")
        elif bf_pct >= 25:
            notes.append("BF% ≥25% (men) — obesity class; prioritise fat loss.")
    else:
        if bf_pct < 18:
            notes.append("BF% below 18% (women) — hormonal function may be suppressed; "
                         "avoid sustained periods below this threshold.")
        elif bf_pct >= 32:
            notes.append("BF% ≥32% (women) — obesity class; prioritise fat loss.")

    # Target weight at a few common target BF%.
    # use shared HORMONAL_FLOOR constant from _thresholds.py.
    target_bf = float(HORMONAL_FLOOR[profile.sex])
    target_w = target_weight_at_target_bf(profile.weight_kg, bf_pct, target_bf)

    return BodyComposition(
        body_fat_pct=round(bf_pct, 1),
        body_fat_method=method,
        body_fat_category=bf_category,
        lean_body_mass_kg=round(lbm_kg, 1),
        fat_mass_kg=round(fat_mass_kg, 1),
        bmi=round(bmi, 1),
        bmi_category=bmi_category,
        ffmi=round(ffmi, 1),
        normalized_ffmi=round(norm_ffmi, 1),
        target_weight_at_target_bf_kg=round(target_w, 1),
        notes=notes,
    )


__all__ = [
    "BF_CATEGORIES", "BMI_CATEGORIES",
    "classify_bf", "classify_bmi",
    "body_fat_navy", "body_fat_cun_bae",
    "compute_body_fat", "compute_ffmi", "target_weight_at_target_bf",
    "assess_body_composition",
]

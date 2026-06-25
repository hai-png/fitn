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


# === Body Fat % Categories (ACE / WHO / ACSM canonical) ===
BF_CATEGORIES = {
    Sex.MALE: [
        (BodyFatCategory.ESSENTIAL,  2,  5),
        (BodyFatCategory.ATHLETE,    6, 13),
        (BodyFatCategory.FITNESS,   14, 17),
        (BodyFatCategory.ACCEPTABLE, 18, 24),
        (BodyFatCategory.OBESITY,   25, 999),
    ],
    Sex.FEMALE: [
        (BodyFatCategory.ESSENTIAL, 10, 13),
        (BodyFatCategory.ATHLETE,   14, 20),
        (BodyFatCategory.FITNESS,   21, 24),
        (BodyFatCategory.ACCEPTABLE, 25, 31),
        (BodyFatCategory.OBESITY,   32, 999),
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
    """Classify body fat % into ACE/WHO/ACSM category."""
    for cat, lo, hi in BF_CATEGORIES[sex]:
        if lo <= bf_pct < hi:
            return cat
    return BodyFatCategory.OBESITY


def classify_bmi(bmi: float) -> BMICategory:
    """Classify BMI into WHO category."""
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


def body_fat_bmi_jackson(profile: UserProfile) -> float:
    """
    BMI-based body fat estimation (Jackson et al. 2002, HERITAGE Family Study).

    Source: Jackson et al. 2002, Med Sci Sports Exerc 34(Suppl):S485.
    (Tier 2.16 fix: previously cited fatcalc.com__rmr-calculator which is the
    RMR page, not the BF page — likely an LLM-hallucinated URL.)
    Use when no circumference measurements are available.
    """
    bmi = profile.bmi
    age = profile.age
    if profile.sex == Sex.MALE:
        bf = 0.14 * age + 37.31 * math.log(bmi) - 103.94
    else:
        bf = 0.14 * age + 39.96 * math.log(bmi) - 102.01
    return max(2.0, min(60.0, bf))


def body_fat_cun_bae(profile: UserProfile) -> float:
    """
    CUN-BAE (Clínica Universidad de Navarra – Body Adiposity Estimator).
    Gomez-Ambrosi et al., Diabetes Care 2012.

    Source: Gomez-Ambrosi et al. 2012, Diabetes Care 35(2):303-308.
    Validated on 6,517 adults; outperforms BMI alone for body fat prediction.

    STATUS: The exact coefficients from the published paper could not be
    verified from the synthesized source material. The commonly cited form
    `BF% = -44.988 + 0.503×age + 10.689×BMI + 0.462×sex` produces impossible
    values (>200% BF) for normal BMIs, indicating the coefficient on BMI is
    likely per-BMI-unit/10 or the formula uses a different BMI scaling.

    Tier 2.16 fix: rather than silently returning Jackson values under the
    CUN-BAE label (the original bug), we now fall back to Jackson and
    explicitly document that CUN-BAE is not yet correctly implemented.
    The BodyFatMethod returned by compute_body_fat is now BMI_JACKSON
    instead of CUN_BAE when this fallback fires, so downstream consumers
    are not misled about which formula was used. Phase-2 should fetch the
    original paper and implement the real formula.
    """
    # Fallback: use Jackson BMI-based formula (validated, gives sensible output)
    return body_fat_bmi_jackson(profile)


def compute_body_fat(profile: UserProfile) -> tuple[float, BodyFatMethod]:
    """
    Decide which BF% formula to use, in priority order:
      1. User-provided value (if any)
      2. US Navy (if measurements available)
      3. BMI-Jackson (BMI + age + sex — validated)

    Tier 2.16 fix: previously the fallback reported BodyFatMethod.CUN_BAE
    even though body_fat_cun_bae actually returned Jackson values. Now we
    honestly report BodyFatMethod.BMI_JACKSON when the Jackson fallback fires.
    CUN-BAE remains in the codebase for future implementation once the exact
    coefficients are verified against the primary source.
    """
    if profile.body_fat_pct is not None:
        return profile.body_fat_pct, BodyFatMethod.USER_PROVIDED

    navy = body_fat_navy(profile)
    if navy is not None:
        return navy, BodyFatMethod.NAVY

    # Tier 2.16 fix: honestly report BMI_JACKSON (not CUN_BAE) since the
    # body_fat_cun_bae function is a Jackson fallback.
    return body_fat_cun_bae(profile), BodyFatMethod.BMI_JACKSON


# === Derived metrics ===

def compute_ffmi(weight_kg: float, bf_pct: float, height_m: float) -> tuple[float, float]:
    """
    Fat-Free Mass Index (Kouri 1995).

    Returns:
      (ffmi, normalized_ffmi)

    Source: rippedbody.com__maximum-muscular-potential
    """
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
    """
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
    # Tier 4.42 fix: use shared HORMONAL_FLOOR constant from _thresholds.py
    # (was hardcoded 10.0/18.0 that could drift from CUT_BULK_BOUNDARIES).
    from ._thresholds import HORMONAL_FLOOR
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
    "body_fat_navy", "body_fat_bmi_jackson", "body_fat_cun_bae",
    "compute_body_fat", "compute_ffmi", "target_weight_at_target_bf",
    "assess_body_composition",
]

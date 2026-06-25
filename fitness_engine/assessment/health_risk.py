"""
Health risk assessment: WHR, WHtR, ABSI, IBW.

Sources:
- WHR (WHO thresholds): fatcalc.com__whr
- WHtR (Ashwell 2012 sex-specific bands): fatcalc.com__whtr-calculator
- ABSI (Krakauer 2012): fatcalc.com__absi
- IBW (Devine/Robinson/Miller/Hamwi): fatcalc.com__ibw-calculator
"""
from __future__ import annotations

import math
from typing import Optional

from ..models.profile import UserProfile, Sex
from ..models.assessment import (
    HealthRiskAssessment, HealthRiskLevel, ABSIRiskLevel,
)
from ..utils.units import cm_to_in, cm_to_m
from ._thresholds import MEDICAL_DISCLAIMER


# === WHR (Waist-to-Hip Ratio) ===

def compute_whr(waist_cm: float, hip_cm: float) -> float:
    """Compute Waist-to-Hip ratio.

    Raises ValueError if hip_cm <= 0 (ZeroDivision guard).
    """
    if hip_cm <= 0:
        raise ValueError(f"hip_cm must be positive for WHR, got {hip_cm}")
    return waist_cm / hip_cm


def classify_whr(whr: float, sex: Sex) -> HealthRiskLevel:
    """
    WHO risk thresholds.
    Source: fatcalc.com__whr
    """
    if sex == Sex.MALE:
        if whr > 1.0:
            return HealthRiskLevel.VERY_HIGH
        elif whr > 0.90:
            return HealthRiskLevel.HIGH
        elif whr > 0.85:
            return HealthRiskLevel.MODERATE
        else:
            return HealthRiskLevel.LOW
    else:  # FEMALE
        if whr > 1.0:
            return HealthRiskLevel.VERY_HIGH
        elif whr > 0.85:
            return HealthRiskLevel.HIGH
        elif whr > 0.80:
            return HealthRiskLevel.MODERATE
        else:
            return HealthRiskLevel.LOW


# === WHtR (Waist-to-Height Ratio) ===

def compute_whtr(waist_cm: float, height_cm: float) -> float:
    """Compute Waist-to-Height ratio.

    Raises ValueError if height_cm <= 0 (ZeroDivision guard).
    """
    if height_cm <= 0:
        raise ValueError(f"height_cm must be positive for WHtR, got {height_cm}")
    return waist_cm / height_cm


def classify_whtr(whtr: float, sex: Sex) -> HealthRiskLevel:
    """
    Ashwell 2012 sex-specific boundaries.
    Source: fatcalc.com__whtr-calculator (Ashwell 2012 cited)

    Phase-6 fix: previously skipped MODERATE (jumped from HIGH to LOW), which
    was asymmetric with classify_whr and confused the overall_risk aggregator.
    Added a MODERATE band between HIGH and LOW per Ashwell's "Take care"
    boundary (0.50-0.53 M / 0.46-0.49 F).
    """
    if sex == Sex.MALE:
        if whtr >= 0.58:
            return HealthRiskLevel.VERY_HIGH
        elif whtr >= 0.53:
            return HealthRiskLevel.HIGH
        elif whtr >= 0.50:
            return HealthRiskLevel.MODERATE     # "take care" band
        elif whtr >= 0.43:
            return HealthRiskLevel.LOW          # "healthy"
        else:
            return HealthRiskLevel.LOW          # "underweight / no risk"
    else:  # FEMALE
        if whtr >= 0.54:
            return HealthRiskLevel.VERY_HIGH
        elif whtr >= 0.49:
            return HealthRiskLevel.HIGH
        elif whtr >= 0.46:
            return HealthRiskLevel.MODERATE     # "take care" band
        elif whtr >= 0.42:
            return HealthRiskLevel.LOW
        else:
            return HealthRiskLevel.LOW


# === ABSI (A Body Shape Index) ===

def compute_absi(waist_cm: float, weight_kg: float, height_cm: float) -> float:
    """
    ABSI = WC_m × weight_kg^(-2/3) × height_m^(5/6)
    Source: fatcalc.com__absi (Krakauer & Krakauer 2012)

    Raises ValueError if weight_kg <= 0 (would produce `inf` via `0 ** -0.667`)
    or height_cm <= 0 (would produce `inf` via `0 ** 0.833`).
    """
    if weight_kg <= 0:
        raise ValueError(f"weight_kg must be positive for ABSI, got {weight_kg}")
    if height_cm <= 0:
        raise ValueError(f"height_cm must be positive for ABSI, got {height_cm}")
    wc_m = waist_cm / 100.0
    h_m = height_cm / 100.0
    return wc_m * (weight_kg ** (-2.0 / 3.0)) * (h_m ** (5.0 / 6.0))


# Simplified ABSI z-score reference (NHANES 1999-2004 mean/SD by age & sex)
# These are approximate; the real tables are age-banded. The engine ships with
# a simplified look-up that captures the broad age trend.
#
# ACKNOWLEDGED SIMPLIFICATION — published NHANES reference tables
# use 5-year age bands (e.g. 18-19, 20-24, 25-29, ...); the table below uses
# 10-year bands (18-29, 30-39, ...). This was chosen to keep the constant table
# small and to avoid hard-coding the full NHANES lookup (which would need to be
# updated as new NHANES cycles are released). The 10-year band averaging
# introduces up to ~0.3 SD of error at age-band boundaries, which is acceptable
# for a screening tool but should NOT be used for clinical decisions.
ABSI_REFERENCE = {
    # (sex, age_band): (mean, sd)
    (Sex.MALE,   (18, 29)): (0.0813, 0.0037),
    (Sex.MALE,   (30, 39)): (0.0815, 0.0038),
    (Sex.MALE,   (40, 49)): (0.0827, 0.0039),
    (Sex.MALE,   (50, 59)): (0.0846, 0.0042),
    (Sex.MALE,   (60, 69)): (0.0861, 0.0043),
    (Sex.MALE,   (70, 200)): (0.0874, 0.0045),
    (Sex.FEMALE, (18, 29)): (0.0780, 0.0036),
    (Sex.FEMALE, (30, 39)): (0.0779, 0.0037),
    (Sex.FEMALE, (40, 49)): (0.0790, 0.0038),
    (Sex.FEMALE, (50, 59)): (0.0821, 0.0041),
    (Sex.FEMALE, (60, 69)): (0.0845, 0.0043),
    (Sex.FEMALE, (70, 200)): (0.0867, 0.0045),
}


def absi_z_score(absi: float, age: int, sex: Sex) -> float:
    """Compute ABSI z-score vs NHANES age/sex norms (simplified table)."""
    # iterate dict.items() directly (was iterating keys then
    # re-looking-up the value — O(2n) and obscured intent).
    for (band_sex, (lo, hi)), (mean, sd) in ABSI_REFERENCE.items():
        if band_sex == sex and lo <= age <= hi:
            return (absi - mean) / sd
    # Fallback (shouldn't happen given 70+ band)
    return 0.0


def classify_absi(z: float) -> ABSIRiskLevel:
    """
    ABSI 5-band risk classification.
    Source: fatcalc.com__absi
    """
    if z < -0.868:
        return ABSIRiskLevel.LOW
    elif z < -0.272:
        return ABSIRiskLevel.BELOW_AVERAGE
    elif z < 0.229:
        return ABSIRiskLevel.AVERAGE
    elif z < 0.798:
        return ABSIRiskLevel.ABOVE_AVERAGE
    else:
        return ABSIRiskLevel.HIGH


# === IBW (Ideal Body Weight) ===

IBW_FORMULAS = {
    "devine":   {Sex.MALE: (50.0, 2.3),  Sex.FEMALE: (45.5, 2.3)},
    "robinson": {Sex.MALE: (52.0, 1.9),  Sex.FEMALE: (49.0, 1.7)},
    "miller":   {Sex.MALE: (56.2, 1.41), Sex.FEMALE: (53.1, 1.36)},
    "hamwi":    {Sex.MALE: (48.0, 2.7),  Sex.FEMALE: (45.4, 2.2)},
}


def ibw_devine(height_cm: float, sex: Sex) -> float:
    """Devine 1974. IBW_kg = base + mult × (H_in - 60)."""
    base, mult = IBW_FORMULAS["devine"][sex]
    h_in = cm_to_in(height_cm)
    return base + mult * (h_in - 60)


def ibw_robinson(height_cm: float, sex: Sex) -> float:
    base, mult = IBW_FORMULAS["robinson"][sex]
    h_in = cm_to_in(height_cm)
    return base + mult * (h_in - 60)


def ibw_miller(height_cm: float, sex: Sex) -> float:
    base, mult = IBW_FORMULAS["miller"][sex]
    h_in = cm_to_in(height_cm)
    return base + mult * (h_in - 60)


def ibw_hamwi(height_cm: float, sex: Sex) -> float:
    base, mult = IBW_FORMULAS["hamwi"][sex]
    h_in = cm_to_in(height_cm)
    return base + mult * (h_in - 60)


# === Overall risk orchestrator ===

def assess_health_risk(profile: UserProfile) -> HealthRiskAssessment:
    """Run full health risk assessment."""
    result = HealthRiskAssessment()

    risk_factors: list[str] = []

    # WHR (requires waist + hip)
    # when hip_cm is missing for men, fall back to WHtR-only
    # (WHR for men is documented as optional in the profile, but the previous
    # branch silently dropped the WHR computation). We add an explicit note so
    # the assessment surfaces that WHR was skipped for lack of input.
    if profile.waist_cm is not None and profile.hip_cm is not None:
        whr = compute_whr(profile.waist_cm, profile.hip_cm)
        whr_risk = classify_whr(whr, profile.sex)
        result.whr = round(whr, 3)
        result.whr_risk = whr_risk
        if whr_risk in (HealthRiskLevel.HIGH, HealthRiskLevel.VERY_HIGH):
            risk_factors.append(
                f"WHR={whr:.2f} above WHO threshold "
                f"({'>0.90 M' if profile.sex == Sex.MALE else '>0.85 F'}); "
                "elevated cardiometabolic risk."
            )
    elif profile.waist_cm is not None and profile.hip_cm is None:
        # surface the missing-hip fallback explicitly for BOTH
        # sexes. Previously this branch only fired for men — a woman missing
        # hip_cm (which is required for both her Navy BF% and WHR) got no
        # note at all, silently dropping the WHR computation.
        risk_factors.append(
            "hip_cm not provided — WHR skipped; relying on WHtR for abdominal "
            "adiposity risk (provide hip circumference for full WHO WHR screening)."
        )

    # WHtR (requires waist)
    if profile.waist_cm is not None:
        whtr = compute_whtr(profile.waist_cm, profile.height_cm)
        whtr_risk = classify_whtr(whtr, profile.sex)
        result.whtr = round(whtr, 3)
        result.whtr_risk = whtr_risk
        if whtr >= 0.5:
            risk_factors.append(
                f"WHtR={whtr:.2f} ≥ 0.5 — 'Keep your waist less than half your height' "
                "(Ashwell & Hsieh 2005; endorsed by NICE UK CG189 as a primary cardiometabolic screening tool)."
            )
        if whtr_risk in (HealthRiskLevel.HIGH, HealthRiskLevel.VERY_HIGH):
            risk_factors.append(f"WHtR={whtr:.2f} indicates overweight/obese risk band.")

    # ABSI (requires waist + weight + height)
    if profile.waist_cm is not None:
        absi = compute_absi(profile.waist_cm, profile.weight_kg, profile.height_cm)
        z = absi_z_score(absi, profile.age, profile.sex)
        absi_risk = classify_absi(z)
        result.absi = round(absi, 5)
        result.absi_z_score = round(z, 3)
        result.absi_risk = absi_risk
        if absi_risk in (ABSIRiskLevel.ABOVE_AVERAGE, ABSIRiskLevel.HIGH):
            risk_factors.append(
                f"ABSI z-score={z:.2f} ({absi_risk.value}) — "
                "elevated mortality risk independent of BMI."
            )

    # IBW (always computable)
    result.ibw_devine_kg = round(ibw_devine(profile.height_cm, profile.sex), 1)
    result.ibw_robinson_kg = round(ibw_robinson(profile.height_cm, profile.sex), 1)
    result.ibw_miller_kg = round(ibw_miller(profile.height_cm, profile.sex), 1)
    result.ibw_hamwi_kg = round(ibw_hamwi(profile.height_cm, profile.sex), 1)

    # BMI-based risk (using profile.bmi)
    bmi = profile.bmi
    if bmi >= 30:
        risk_factors.append(f"BMI={bmi:.1f} (obese) — cardiometabolic risk.")
    elif bmi >= 25:
        risk_factors.append(f"BMI={bmi:.1f} (overweight) — monitor.")

    # Overall risk
    # previously WHR, WHtR, ABSI were counted equally (each 0/1).
    # That over-weighted WHR (a weaker predictor) relative to ABSI (the
    # strongest mortality-risk predictor of the three). Now weighted:
    #   ABSI = 0.5  (strongest independent mortality predictor; Krakauer 2012)
    #   WHR  = 0.3  (WHO cardiometabolic screen)
    #   WHtR = 0.2  (Ashwell 2012, broad screening tool)
    # Limitation: the weights are heuristic (not derived from a published
    # composite-risk model). They reflect the relative predictive strength
    # reported in the source papers but are not formally validated as a
    # composite score. Treated as a coarse 0/1 indicator per sub-metric.
    WEIGHTS = {
        "absi": 0.5,
        "whr": 0.3,
        "whtr": 0.2,
    }
    risk_score = 0.0
    if result.whr_risk in (HealthRiskLevel.HIGH, HealthRiskLevel.VERY_HIGH):
        risk_score += WEIGHTS["whr"]
    if result.whtr_risk in (HealthRiskLevel.HIGH, HealthRiskLevel.VERY_HIGH):
        risk_score += WEIGHTS["whtr"]
    if result.absi_risk in (ABSIRiskLevel.ABOVE_AVERAGE, ABSIRiskLevel.HIGH):
        risk_score += WEIGHTS["absi"]
    # Use a 0.5 threshold for HIGH (≈ one full-weight indicator) and 0.75 for VERY_HIGH.
    if risk_score >= 0.75:
        result.overall_risk = HealthRiskLevel.VERY_HIGH
    elif risk_score >= 0.5:
        result.overall_risk = HealthRiskLevel.HIGH
    elif risk_factors:
        # filter out data-quality notes (e.g. "hip_cm not provided")
        # from the risk-factor check. Previously a healthy male user with no
        # actual risk factors but missing hip_cm ended up with overall_risk =
        # MODERATE purely because of the data-availability note — mixing
        # data-quality messages with clinical risk factors in the same list.
        # Now we only bump to MODERATE if there are real risk factors (not
        # just data-quality advisories).
        clinical_risk_factors = [
            rf for rf in risk_factors
            if not rf.startswith("hip_cm not provided")
        ]
        if clinical_risk_factors:
            result.overall_risk = HealthRiskLevel.MODERATE
        else:
            result.overall_risk = HealthRiskLevel.LOW
    else:
        result.overall_risk = HealthRiskLevel.LOW

    result.risk_factors = risk_factors
    result.notes = [
        f"IBW (Devine): {result.ibw_devine_kg} kg",
        f"IBW (Robinson): {result.ibw_robinson_kg} kg",
        f"IBW (Miller): {result.ibw_miller_kg} kg",
        f"IBW (Hamwi): {result.ibw_hamwi_kg} kg",
        # import MEDICAL_DISCLAIMER from _thresholds (single source).
        MEDICAL_DISCLAIMER,
    ]
    return result


__all__ = [
    "ABSI_REFERENCE", "IBW_FORMULAS",
    "compute_whr", "classify_whr",
    "compute_whtr", "classify_whtr",
    "compute_absi", "absi_z_score", "classify_absi",
    "ibw_devine", "ibw_robinson", "ibw_miller", "ibw_hamwi",
    "assess_health_risk",
]

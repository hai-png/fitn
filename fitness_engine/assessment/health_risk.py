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


# === WHR (Waist-to-Hip Ratio) ===

def compute_whr(waist_cm: float, hip_cm: float) -> float:
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
    return waist_cm / height_cm


def classify_whtr(whtr: float, sex: Sex) -> HealthRiskLevel:
    """
    Ashwell 2012 sex-specific boundaries.
    Source: fatcalc.com__whtr-calculator (Ashwell 2012 cited)
    """
    if sex == Sex.MALE:
        if whtr >= 0.58:
            return HealthRiskLevel.VERY_HIGH
        elif whtr >= 0.53:
            return HealthRiskLevel.HIGH
        elif whtr >= 0.43:
            return HealthRiskLevel.LOW         # "healthy"
        else:
            return HealthRiskLevel.LOW         # "underweight / no risk"
    else:  # FEMALE
        if whtr >= 0.54:
            return HealthRiskLevel.VERY_HIGH
        elif whtr >= 0.49:
            return HealthRiskLevel.HIGH
        elif whtr >= 0.42:
            return HealthRiskLevel.LOW
        else:
            return HealthRiskLevel.LOW


# === ABSI (A Body Shape Index) ===

def compute_absi(waist_cm: float, weight_kg: float, height_cm: float) -> float:
    """
    ABSI = WC_m × weight_kg^(-2/3) × height_m^(5/6)
    Source: fatcalc.com__absi (Krakauer & Krakauer 2012)
    """
    wc_m = waist_cm / 100.0
    h_m = height_cm / 100.0
    return wc_m * (weight_kg ** (-2.0 / 3.0)) * (h_m ** (5.0 / 6.0))


# Simplified ABSI z-score reference (NHANES 1999-2004 mean/SD by age & sex)
# These are approximate; the real tables are age-banded. The engine ships with
# a simplified look-up that captures the broad age trend.
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
    # Find age band
    for band_sex, (lo, hi) in ABSI_REFERENCE:
        if band_sex == sex and lo <= age <= hi:
            mean, sd = ABSI_REFERENCE[(band_sex, (lo, hi))]
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
    risk_score = sum(
        1 for r in [result.whr_risk, result.whtr_risk]
        if r in (HealthRiskLevel.HIGH, HealthRiskLevel.VERY_HIGH)
    ) + (1 if result.absi_risk in (ABSIRiskLevel.ABOVE_AVERAGE, ABSIRiskLevel.HIGH) else 0)
    if risk_score >= 2:
        result.overall_risk = HealthRiskLevel.VERY_HIGH
    elif risk_score == 1:
        result.overall_risk = HealthRiskLevel.HIGH
    elif risk_factors:
        result.overall_risk = HealthRiskLevel.MODERATE
    else:
        result.overall_risk = HealthRiskLevel.LOW

    result.risk_factors = risk_factors
    result.notes = [
        f"IBW (Devine): {result.ibw_devine_kg} kg",
        f"IBW (Robinson): {result.ibw_robinson_kg} kg",
        f"IBW (Miller): {result.ibw_miller_kg} kg",
        f"IBW (Hamwi): {result.ibw_hamwi_kg} kg",
        # Tier 1.8 fix: removed false "Frame-size adjustment (wrist circumference)"
        # note — the engine does not implement frame-size adjustment and
        # UserProfile has no wrist_circumference field. Adding the note implied
        # functionality that does not exist.
        "Not a substitute for clinical assessment — consult a physician for personalized guidance.",
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

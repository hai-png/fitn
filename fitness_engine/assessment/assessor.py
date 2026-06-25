"""
Assessment orchestrator — runs body composition, health risk, muscular potential,
and cut/bulk decision tree.

Tier 4.45 fix: each sub-assessment is now wrapped in try/except so a single
failure (e.g. ZeroDivisionError in compute_whr, math.log domain error) doesn't
crash the entire assess_profile call. Partial results are returned with an
`errors` list noting which sub-assessments failed.

Tier 4.46 fix: a medical disclaimer is now included in the summary.
"""
from __future__ import annotations

import logging

from ..models.profile import UserProfile
from ..models.assessment import AssessmentResult, RecommendedStrategy, HealthRiskAssessment, MuscularPotential
from .body_composition import assess_body_composition
from .health_risk import assess_health_risk
from .muscular_potential import assess_muscular_potential
from .decision import decide_strategy
# Phase-6 fix: MEDICAL_DISCLAIMER moved to _thresholds.py as single source of truth.
from ._thresholds import MEDICAL_DISCLAIMER

_log = logging.getLogger(__name__)


def assess_profile(profile: UserProfile) -> AssessmentResult:
    """
    Run full assessment on a user profile.

    Returns AssessmentResult containing body composition, health risk,
    muscular potential, and recommended strategy.

    Tier 4.45: sub-assessments are wrapped in try/except. On failure, a
    minimal placeholder is used and the error is logged. The caller gets
    partial results rather than a crash.
    """
    errors: list[str] = []

    # 1. Body composition
    try:
        body_comp = assess_body_composition(profile)
    except Exception as e:
        _log.error("Body composition assessment failed: %s", e)
        errors.append(f"body_composition: {type(e).__name__}: {e}")
        # Minimal placeholder so downstream can continue.
        # Phase-6 fix: use classify_bmi() (pure, won't raise) instead of the
        # previous inline ternary that omitted BMICategory.UNDERWEIGHT (an
        # underweight user with BMI < 18.5 was classified as NORMAL).
        from ..models.assessment import BodyComposition, BodyFatMethod, BodyFatCategory
        from .body_composition import classify_bmi
        # Fix: use CUN_BAE to match the actual fallback path in compute_body_fat
        # (was previously BMI_JACKSON, contradicting the Phase-6 migration).
        # Use `is not None` instead of truthy check (idiom for Optional[float]).
        fallback_bf = profile.body_fat_pct if profile.body_fat_pct is not None else 20.0
        body_comp = BodyComposition(
            bmi=profile.bmi,
            bmi_category=classify_bmi(profile.bmi),
            body_fat_pct=fallback_bf,
            body_fat_method=(
                BodyFatMethod.USER_PROVIDED
                if profile.body_fat_pct is not None
                else BodyFatMethod.CUN_BAE
            ),
            body_fat_category=BodyFatCategory.ACCEPTABLE,
            # Derive LBM/fat-mass from the same BF% so they're internally consistent.
            lean_body_mass_kg=profile.weight_kg * (1 - fallback_bf / 100),
            fat_mass_kg=profile.weight_kg * (fallback_bf / 100),
            ffmi=20.0,
            normalized_ffmi=20.0,
        )

    # 2. Health risk
    try:
        health_risk = assess_health_risk(profile)
    except Exception as e:
        _log.error("Health risk assessment failed: %s", e)
        errors.append(f"health_risk: {type(e).__name__}: {e}")
        from ..models.assessment import HealthRiskLevel
        health_risk = HealthRiskAssessment(
            overall_risk=HealthRiskLevel.LOW,
            risk_factors=[],
            notes=["Health risk assessment failed — partial results."],
        )

    # 3. Muscular potential
    try:
        muscular_potential = assess_muscular_potential(profile, body_comp.body_fat_pct)
    except Exception as e:
        _log.error("Muscular potential assessment failed: %s", e)
        errors.append(f"muscular_potential: {type(e).__name__}: {e}")
        muscular_potential = MuscularPotential(
            current_ffmi=body_comp.ffmi,
            current_normalized_ffmi=body_comp.normalized_ffmi,
            notes=["Muscular potential assessment failed — partial results."],
        )

    # 4. Strategy decision
    try:
        strategy, rationale = decide_strategy(
            profile=profile,
            body_fat_pct=body_comp.body_fat_pct,
            bmi=body_comp.bmi,
            has_measurements=profile.has_circumference_measurements,
        )
    except Exception as e:
        _log.error("Strategy decision failed: %s", e)
        errors.append(f"decision: {type(e).__name__}: {e}")
        strategy = RecommendedStrategy.MAINTENANCE
        rationale = "Strategy decision failed — defaulting to maintenance."

    # 5. Build summary
    summary_parts = [
        f"{profile.sex.value.capitalize()}, {profile.age}y, "
        f"{profile.height_cm:.0f}cm, {profile.weight_kg:.1f}kg",
        f"BMI {body_comp.bmi:.1f} ({body_comp.bmi_category.value})",
        f"BF% {body_comp.body_fat_pct:.1f} ({body_comp.body_fat_category.value}, "
        f"via {body_comp.body_fat_method.value})",
        f"LBM {body_comp.lean_body_mass_kg:.1f}kg, "
        f"fat mass {body_comp.fat_mass_kg:.1f}kg",
        f"FFMI {body_comp.ffmi:.1f} (norm: {body_comp.normalized_ffmi:.1f}, "
        f"natural ceiling 25.0, {muscular_potential.ffmi_to_ceiling_pct:.0f}% of ceiling)",
        f"Recommended: {strategy.value.upper()} — {rationale}",
    ]

    # Tier 4.46: surface overall health risk level (was previously omitted)
    summary_parts.append(f"Health risk: {health_risk.overall_risk.value}")

    if health_risk.risk_factors:
        # Tier 4.45: show ALL risk factors (was previously truncated to 2)
        summary_parts.append(
            "Risk factors: " + " | ".join(health_risk.risk_factors)
        )

    # Tier 4.46: medical disclaimer
    summary_parts.append(MEDICAL_DISCLAIMER)

    if errors:
        summary_parts.append(
            f"⚠ {len(errors)} sub-assessment(s) failed (see logs): "
            + "; ".join(errors)
        )

    return AssessmentResult(
        body_composition=body_comp,
        health_risk=health_risk,
        muscular_potential=muscular_potential,
        recommended_strategy=strategy,
        strategy_rationale=rationale,
        summary=" • ".join(summary_parts),
    )


__all__ = ["assess_profile", "MEDICAL_DISCLAIMER"]

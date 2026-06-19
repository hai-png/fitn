"""
Assessment orchestrator — runs body composition, health risk, muscular potential,
and cut/bulk decision tree.
"""
from __future__ import annotations

from ..models.profile import UserProfile
from ..models.assessment import AssessmentResult, RecommendedStrategy
from .body_composition import assess_body_composition
from .health_risk import assess_health_risk
from .muscular_potential import assess_muscular_potential
from .decision import decide_strategy


def assess_profile(profile: UserProfile) -> AssessmentResult:
    """
    Run full assessment on a user profile.

    Returns AssessmentResult containing body composition, health risk,
    muscular potential, and recommended strategy.
    """
    # 1. Body composition
    body_comp = assess_body_composition(profile)

    # 2. Health risk
    health_risk = assess_health_risk(profile)

    # 3. Muscular potential (uses body_fat_pct from body composition)
    muscular_potential = assess_muscular_potential(profile, body_comp.body_fat_pct)

    # 4. Strategy decision
    strategy, rationale = decide_strategy(
        profile=profile,
        body_fat_pct=body_comp.body_fat_pct,
        bmi=body_comp.bmi,
        has_measurements=profile.has_circumference_measurements,
    )

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

    if health_risk.risk_factors:
        summary_parts.append(
            "Risk factors: " + " | ".join(health_risk.risk_factors[:2])
        )

    return AssessmentResult(
        body_composition=body_comp,
        health_risk=health_risk,
        muscular_potential=muscular_potential,
        recommended_strategy=strategy,
        strategy_rationale=rationale,
        summary=" • ".join(summary_parts),
    )


__all__ = ["assess_profile"]

"""
Muscular potential assessment: FFMI ceilings, Berkhan model, expected muscle gain.

Sources:
- FFMI + Kouri 1995 ceiling: rippedbody.com__maximum-muscular-potential
- Berkhan model: rippedbody.com__maximum-muscular-potential
- Muscle growth rate by training status: rippedbody.com__updated-bulking-guidelines,
  fatcalc.com__body-recomp-calculator (Lyle McDonald model)

Tier 1.9 fix: raw FFMI is no longer compared against the Kouri 1995 ceiling of
25 — that ceiling applies to NORMALIZED FFMI (Kouri 1995). Using raw FFMI
produced incorrect ceiling comparisons for anyone whose height is not exactly
1.80 m. We now use normalized_ffmi everywhere the Kouri 25 ceiling is referenced,
and compute ffm_at_ceiling from `raw_at_ceiling = 25 - 6.1*(1.8 - height_m)`
rather than from raw 25.

Tier 2.17 fix: Berkhan model is men-only (women's essential BF floor is ~10-13%,
not 5-6%). For female profiles we now return None and skip the Berkhan note.

Tier 2.12 fix: BULK_RATE_BY_STATUS removed from this module — the canonical
copy lives in nutrition.calories. This file no longer exports it.
"""
from __future__ import annotations

from typing import Optional

from ..models.profile import UserProfile, Sex, TrainingStatus
from ..models.assessment import MuscularPotential


# === Ceilings (Kouri 1995, Mr. America data, RippedBody editorial) ===
# All ceilings apply to NORMALIZED FFMI (Kouri 1995 height-normalized formula).
FFMI_NATURAL_COMMON = 25.0       # Kouri 1995 — common natural limit (normalized)
FFMI_NATURAL_ATTAINABLE = 27.3   # Mr. America 1939-1953 (normalized)
FFMI_NATURAL_LIKELY_MAX = 28.0   # RippedBody editorial — "pretty likely" (normalized)

# Kouri 1995 normalization constants
NORM_FFMI_COEFF = 6.1            # coefficient applied to (1.8 - height_m)
NORM_FFMI_REF_HEIGHT_M = 1.8     # reference height


# === Berkhan stage-shredded (5-6% BF) — MEN ONLY ===

def berkhan_stage_max_weight_kg(height_cm: float) -> float:
    """
    Berkhan model: Max_stage_weight_kg = height_cm - 100.
    At 5-6% BF (stage-shredded).

    Source: rippedbody.com__maximum-muscular-potential

    NOTE: This model is men-only. Women's essential BF floor is ~10-13%,
    so a 5-6% BF target is biologically impossible and dangerous for women.
    Callers MUST guard on sex before invoking; assess_muscular_potential
    returns None for female profiles (Tier 2.17 fix).
    """
    return height_cm - 100.0


# === Expected monthly muscle gain by training status (Lyle McDonald model) ===
# Source: fatcalc.com__body-recomp-calculator
# Men values; women are ~50%.
# Phase-6 fix: use the MIDPOINT of each band rather than the upper bound
# (upper bound systematically over-promises gains; midpoint is the unbiased
# estimate for planning). Bands per Lyle McDonald:
#   Beginner     0.7-1.0 kg/mo   → midpoint 0.85
#   Novice       0.45-0.7 kg/mo  → midpoint 0.575
#   Intermediate 0.2-0.45 kg/mo  → midpoint 0.325
#   Advanced     <0.2 kg/mo      → use 0.10 as a representative sub-floor value
EXPECTED_MONTHLY_MUSCLE_GAIN_KG_MEN = {
    TrainingStatus.BEGINNER:     0.85,      # 0.7-1.0 kg/mo, midpoint
    TrainingStatus.NOVICE:       0.575,     # 0.45-0.7 kg/mo, midpoint
    TrainingStatus.INTERMEDIATE: 0.325,     # 0.2-0.45 kg/mo, midpoint
    TrainingStatus.ADVANCED:     0.10,      # <0.2 kg/mo, representative value
}

# NOTE: BULK_RATE_BY_STATUS was previously duplicated here AND in
# nutrition/calories.py. Tier 2.12 fix: removed from this module — the
# canonical copy lives in nutrition.calories. Import from there if needed.


def assess_muscular_potential(profile: UserProfile, body_fat_pct: float) -> MuscularPotential:
    """Compute muscular potential metrics.

    Tier 1.9 fix: all comparisons against the Kouri 25 ceiling now use
    NORMALIZED FFMI, not raw FFMI. headroom_kg is computed from the
    height-specific raw_at_ceiling, not from raw 25.
    """
    ffm_kg = profile.weight_kg * (1 - body_fat_pct / 100)
    ffmi = ffm_kg / (profile.height_m ** 2)
    normalized_ffmi = ffmi + NORM_FFMI_COEFF * (NORM_FFMI_REF_HEIGHT_M - profile.height_m)

    # Tier 1.9 fix: use NORMALIZED FFMI for ceiling comparison.
    # Phase-6 fix: clamp to 100% — PED users and genetic outliers can exceed
    # the natural ceiling, but a >100% "progress to ceiling" reading is
    # misleading. The over-ceiling signal is preserved via is_above_ceiling.
    raw_ffmi_to_ceiling_pct = (normalized_ffmi / FFMI_NATURAL_COMMON) * 100
    is_above_ceiling = normalized_ffmi > FFMI_NATURAL_COMMON
    ffmi_to_ceiling_pct = min(100.0, raw_ffmi_to_ceiling_pct)

    # Tier 1.9 fix: compute the height-specific RAW FFMI at the normalized ceiling.
    # If normalized_ffmi = 25 = raw_ffmi + 6.1*(1.8 - h), then
    # raw_ffmi_at_ceiling = 25 - 6.1*(1.8 - h).
    raw_ffmi_at_ceiling = FFMI_NATURAL_COMMON - NORM_FFMI_COEFF * (NORM_FFMI_REF_HEIGHT_M - profile.height_m)
    ffm_at_ceiling = raw_ffmi_at_ceiling * (profile.height_m ** 2)
    headroom_kg = max(0.0, ffm_at_ceiling - ffm_kg)

    # Tier 2.17 fix: Berkhan model is men-only.
    berkhan_max: Optional[float] = None
    if profile.sex == Sex.MALE:
        berkhan_max = berkhan_stage_max_weight_kg(profile.height_cm)

    # Expected monthly muscle gain (Lyle McDonald model)
    base_gain = EXPECTED_MONTHLY_MUSCLE_GAIN_KG_MEN[profile.training_status]
    if profile.sex == Sex.FEMALE:
        base_gain *= 0.5    # women ~50% of men's rates

    notes: list[str] = []
    # Tier 1.9 fix: compare NORMALIZED FFMI against the ceiling.
    if normalized_ffmi >= FFMI_NATURAL_COMMON:
        notes.append(
            f"Normalized FFMI={normalized_ffmi:.1f} ≥ natural common ceiling ({FFMI_NATURAL_COMMON}). "
            "Either exceptional genetics or PED use; further gains will be slow. "
            "Consider verifying with a clinical body-composition method (DEXA, hydrostatic)."
        )
    elif normalized_ffmi >= 22:
        notes.append(
            f"Normalized FFMI={normalized_ffmi:.1f} — advanced trainee territory. "
            "Gains will be harder-won; consider intermediate/advanced periodization."
        )
    else:
        notes.append(
            f"Normalized FFMI={normalized_ffmi:.1f} — significant headroom to natural ceiling "
            f"({headroom_kg:.1f} kg FFM remaining at normalized FFMI=25)."
        )

    # Tier 2.17 fix: only add Berkhan note for male profiles.
    if berkhan_max is not None:
        notes.append(
            f"Berkhan stage-shredded max for height={profile.height_cm}cm (men only): "
            f"{berkhan_max:.1f} kg at 5-6% BF."
        )
    else:
        notes.append(
            "Berkhan stage-shredded model not applicable for female profiles "
            "(women's essential BF floor is ~10-13%, not 5-6%)."
        )
    notes.append(
        f"Expected monthly muscle gain ({profile.training_status.value}, "
        f"{profile.sex.value}): ~{base_gain:.2f} kg/month with proper training + nutrition."
    )

    return MuscularPotential(
        current_ffmi=round(ffmi, 1),
        current_normalized_ffmi=round(normalized_ffmi, 1),
        natural_ceiling_ffmi=FFMI_NATURAL_COMMON,
        attainable_ceiling_ffmi=FFMI_NATURAL_ATTAINABLE,
        likely_max_ffmi=FFMI_NATURAL_LIKELY_MAX,
        berkhan_stage_max_kg=round(berkhan_max, 1) if berkhan_max is not None else None,
        ffmi_to_ceiling_pct=round(ffmi_to_ceiling_pct, 1),
        headroom_kg=round(headroom_kg, 1),
        expected_monthly_muscle_gain_kg=round(base_gain, 2),
        is_above_ceiling=is_above_ceiling,  # Phase-6 fix: expose over-ceiling flag
        notes=notes,
    )


__all__ = [
    "FFMI_NATURAL_COMMON", "FFMI_NATURAL_ATTAINABLE", "FFMI_NATURAL_LIKELY_MAX",
    "EXPECTED_MONTHLY_MUSCLE_GAIN_KG_MEN",
    "berkhan_stage_max_weight_kg",
    "assess_muscular_potential",
]

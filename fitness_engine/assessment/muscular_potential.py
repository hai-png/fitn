"""
Muscular potential assessment: FFMI ceilings, Berkhan model, expected muscle gain.

Sources:
- FFMI + Kouri 1995 ceiling: rippedbody.com__maximum-muscular-potential
- Berkhan model: rippedbody.com__maximum-muscular-potential
- Muscle growth rate by training status: rippedbody.com__updated-bulking-guidelines,
  fatcalc.com__body-recomp-calculator (Lyle McDonald model)
"""
from __future__ import annotations

from ..models.profile import UserProfile, Sex, TrainingStatus
from ..models.assessment import MuscularPotential


# === Ceilings (Kouri 1995, Mr. America data, RippedBody editorial) ===
FFMI_NATURAL_COMMON = 25.0       # Kouri 1995 — common natural limit
FFMI_NATURAL_ATTAINABLE = 27.3   # Mr. America 1939-1953
FFMI_NATURAL_LIKELY_MAX = 28.0   # RippedBody editorial — "pretty likely"


# === Berkhan stage-shredded (5-6% BF) ===

def berkhan_stage_max_weight_kg(height_cm: float) -> float:
    """
    Berkhan model: Max_stage_weight_kg = height_cm - 100.
    At 5-6% BF (stage-shredded).

    Source: rippedbody.com__maximum-muscular-potential
    """
    return height_cm - 100.0


# === Expected monthly muscle gain by training status (Lyle McDonald model) ===
# Source: fatcalc.com__body-recomp-calculator
# Men values; women are ~50%.
EXPECTED_MONTHLY_MUSCLE_GAIN_KG_MEN = {
    TrainingStatus.BEGINNER:     1.0,       # 0.7-1.0 kg/mo, use upper bound
    TrainingStatus.NOVICE:       0.7,       # ~0.7-1.0 declining to 0.45-0.7
    TrainingStatus.INTERMEDIATE: 0.45,      # 0.45-0.7 kg/mo
    TrainingStatus.ADVANCED:     0.20,      # <0.2-0.45 kg/mo
}

# === Updated RippedBody monthly gain rate (% BW/month, for bulk calorie calc) ===
# Source: rippedbody.com__updated-bulking-guidelines
BULK_RATE_BY_STATUS = {
    TrainingStatus.BEGINNER:     0.020,    # 2.0 % BW/month
    TrainingStatus.NOVICE:       0.015,    # 1.5 % BW/month
    TrainingStatus.INTERMEDIATE: 0.010,    # 1.0 % BW/month
    TrainingStatus.ADVANCED:     0.005,    # 0.5 % BW/month
}


def assess_muscular_potential(profile: UserProfile, body_fat_pct: float) -> MuscularPotential:
    """Compute muscular potential metrics."""
    ffm_kg = profile.weight_kg * (1 - body_fat_pct / 100)
    ffmi = ffm_kg / (profile.height_m ** 2)
    normalized_ffmi = ffmi + 6.1 * (1.8 - profile.height_m)

    ffmi_to_ceiling_pct = (ffmi / FFMI_NATURAL_COMMON) * 100

    # Headroom: how much more FFM can the user gain before hitting natural ceiling?
    ffm_at_ceiling = FFMI_NATURAL_COMMON * (profile.height_m ** 2)
    headroom_kg = max(0.0, ffm_at_ceiling - ffm_kg)

    # Berkhan stage-shredded max
    berkhan_max = berkhan_stage_max_weight_kg(profile.height_cm)

    # Expected monthly muscle gain (Lyle McDonald model)
    base_gain = EXPECTED_MONTHLY_MUSCLE_GAIN_KG_MEN[profile.training_status]
    if profile.sex == Sex.FEMALE:
        base_gain *= 0.5    # women ~50% of men's rates

    notes: list[str] = []
    if ffmi >= FFMI_NATURAL_COMMON:
        notes.append(
            f"FFMI={ffmi:.1f} ≥ natural common ceiling ({FFMI_NATURAL_COMMON}). "
            "Either exceptional genetics or PED use; further gains will be slow."
        )
    elif ffmi >= 22:
        notes.append(
            f"FFMI={ffmi:.1f} — advanced trainee territory. "
            "Gains will be harder-won; consider intermediate/advanced periodization."
        )
    else:
        notes.append(
            f"FFMI={ffmi:.1f} — significant headroom to natural ceiling "
            f"({headroom_kg:.1f} kg FFM remaining at FFMI=25)."
        )

    notes.append(
        f"Berkhan stage-shredded max for height={profile.height_cm}cm: "
        f"{berkhan_max:.1f} kg at 5-6% BF."
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
        berkhan_stage_max_kg=round(berkhan_max, 1),
        ffmi_to_ceiling_pct=round(ffmi_to_ceiling_pct, 1),
        headroom_kg=round(headroom_kg, 1),
        expected_monthly_muscle_gain_kg=round(base_gain, 2),
        notes=notes,
    )


__all__ = [
    "FFMI_NATURAL_COMMON", "FFMI_NATURAL_ATTAINABLE", "FFMI_NATURAL_LIKELY_MAX",
    "EXPECTED_MONTHLY_MUSCLE_GAIN_KG_MEN", "BULK_RATE_BY_STATUS",
    "berkhan_stage_max_weight_kg",
    "assess_muscular_potential",
]

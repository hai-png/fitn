"""
Resting Metabolic Rate (RMR) formulas.

Sources:
- Mifflin-St Jeor (1990): fatcalc.com__rmr-calculator, gymgeek.com__calculators-calorie-calculator
- Harris-Benedict original (1919): rippedbody.com__calories
- Harris-Benedict revised (1984, Roza & Shizgal): fatcalc.com__rmr-calculator
- Cunningham (1991): RMR = 500 + 22 × FFM — distinct from Katch-McArdle
- Katch-McArdle (1975): RMR = 370 + 21.6 × LBM
- Metabolic adaptation: rippedbody.com__macro-calculator

Tier 2.10 fix: `rmr_cunningham` previously implemented Katch-McArdle (370 + 21.6 × LBM)
but was labeled as Cunningham. Now both formulas are distinct:
  - rmr_cunningham: 500 + 22 × FFM  (Cunningham 1991)
  - rmr_katch_mcardle: 370 + 21.6 × LBM  (Katch-McArdle 1975)
The legacy `rmr_cunningham` name is preserved as an alias for backward compat,
but its implementation is now the real Cunningham formula.

Tier 2.11 fix: `select_rmr_formula` now consults the `body_fat_pct` parameter
that was actually passed to `compute_rmr`, not `profile.body_fat_pct` (which is
frequently None even when the assessment has computed a high-quality BF%).

Tier 2.10 fix: `compute_rmr` now has an explicit branch for HARRIS_BENEDICT_REVISED
(previously silently downgraded to Mifflin-St Jeor).

Tier 2.10 fix: `rmr_cunningham` and `rmr_katch_mcardle` now validate that
`body_fat_pct` is in [2, 60] (matching UserProfile validator) to prevent
negative-LBM nonsense.
"""
from __future__ import annotations

from ..models.nutrition import RMRFormula, RMRResult
from ..models.profile import Sex, UserProfile

# Bound for body_fat_pct in body-composition-aware formulas. Matches the
# UserProfile validator range. Prevents negative-LBM nonsense (BF% > 100).
BF_PCT_MIN = 2.0
BF_PCT_MAX = 60.0


def rmr_mifflin_st_jeor(profile: UserProfile) -> float:
    """
    Mifflin-St Jeor (1990) — DEFAULT for general population.

    Men:   RMR = 9.99 × weight_kg + 6.25 × height_cm − 4.92 × age + 5
    Women: RMR = 9.99 × weight_kg + 6.25 × height_cm − 4.92 × age − 161
    """
    base = 9.99 * profile.weight_kg + 6.25 * profile.height_cm - 4.92 * profile.age
    if profile.sex == Sex.MALE:
        return base + 5
    return base - 161


def rmr_harris_benedict_original(profile: UserProfile) -> float:
    """
    Harris-Benedict original (1919) — RippedBody's preferred.

    Men:   BMR = 66 + 13.7 × weight_kg + 5 × height_cm − 6.8 × age
    Women: BMR = 655 + 9.6 × weight_kg + 1.8 × height_cm − 4.7 × age
    """
    if profile.sex == Sex.MALE:
        return 66 + 13.7 * profile.weight_kg + 5 * profile.height_cm - 6.8 * profile.age
    return 655 + 9.6 * profile.weight_kg + 1.8 * profile.height_cm - 4.7 * profile.age


def rmr_harris_benedict_revised(profile: UserProfile) -> float:
    """
    Harris-Benedict revised (1984, Roza & Shizgal).
    """
    if profile.sex == Sex.MALE:
        return (13.397 * profile.weight_kg + 4.799 * profile.height_cm
                - 5.677 * profile.age + 88.362)
    return (9.247 * profile.weight_kg + 3.098 * profile.height_cm
            - 4.330 * profile.age + 447.593)


def _validate_body_fat_pct(body_fat_pct: float) -> None:
    """Validate body_fat_pct is in a sane range to prevent negative-LBM nonsense."""
    if not (BF_PCT_MIN <= body_fat_pct <= BF_PCT_MAX):
        raise ValueError(
            f"body_fat_pct must be in [{BF_PCT_MIN}, {BF_PCT_MAX}] for "
            f"body-composition-aware RMR formulas; got {body_fat_pct}"
        )


def rmr_cunningham(profile: UserProfile, body_fat_pct: float) -> float:
    """
    Cunningham (1991) — body-composition-aware.

    RMR = 500 + 22 × FFM_kg

    Use when BF% is known and user is athletic / muscular.

    Tier 2.10 fix: this is the REAL Cunningham (1991) formula. Previously
    this function implemented Katch-McArdle (370 + 21.6 × LBM) but was
    mislabeled as Cunningham. The Katch-McArdle implementation is now in
    `rmr_katch_mcardle`.
    """
    _validate_body_fat_pct(body_fat_pct)
    ffm = profile.weight_kg * (1 - body_fat_pct / 100)
    return 500 + 22 * ffm


def rmr_katch_mcardle(profile: UserProfile, body_fat_pct: float) -> float:
    """
    Katch-McArdle (1975) — body-composition-aware.

    RMR = 370 + 21.6 × LBM_kg

    Use when BF% is known. Slightly more conservative than Cunningham.
    """
    _validate_body_fat_pct(body_fat_pct)
    lbm = profile.weight_kg * (1 - body_fat_pct / 100)
    return 370 + 21.6 * lbm


def select_rmr_formula(
    profile: UserProfile,
    body_fat_pct: float | None = None,
) -> RMRFormula:
    """
    Select RMR formula based on data availability.

    - If BF% known (either passed in or on profile): Katch-McArdle
      (body-composition-aware, best for athletic/muscular)
    - Else: Mifflin-St Jeor (general-population default)

    Tier 2.11 fix: now consults the `body_fat_pct` parameter (typically the
    assessment-derived BF%) IN ADDITION to `profile.body_fat_pct` (the
    user-supplied field). Previously only `profile.body_fat_pct` was checked,
    which was frequently None even when the assessment had a high-quality BF%.
    """
    # Use passed-in body_fat_pct first; fall back to profile.body_fat_pct.
    effective_bf = body_fat_pct if body_fat_pct is not None else profile.body_fat_pct
    if effective_bf is not None:
        return RMRFormula.KATCH_MCARDLE
    return RMRFormula.MIFFLIN_ST_JEOR


def compute_rmr(
    profile: UserProfile,
    body_fat_pct: float | None = None,
    in_active_deficit: bool = False,
    weight_reduced_pct: float = 0.0,
) -> RMRResult:
    """
    Compute RMR with metabolic adaptations applied.

    Adaptations (RippedBody):
      - In active deficit: -5%
      - >10% below all-time high body weight: -3%
      Both apply multiplicatively.

    Args:
      profile: user profile
      body_fat_pct: BF% (use computed value from assessment)
      in_active_deficit: True if user is currently in a cutting phase
      weight_reduced_pct: 0-1, fraction below all-time high body weight
    """
    # pass body_fat_pct to select_rmr_formula so it can use
    # the assessment-derived BF% even when profile.body_fat_pct is None.
    formula = select_rmr_formula(profile, body_fat_pct)

    # explicit branch for HARRIS_BENEDICT_REVISED.
    if formula == RMRFormula.KATCH_MCARDLE and body_fat_pct is not None:
        base_rmr = rmr_katch_mcardle(profile, body_fat_pct)
    elif formula == RMRFormula.CUNNINGHAM and body_fat_pct is not None:
        base_rmr = rmr_cunningham(profile, body_fat_pct)
    elif formula == RMRFormula.MIFFLIN_ST_JEOR:
        base_rmr = rmr_mifflin_st_jeor(profile)
    elif formula == RMRFormula.HARRIS_BENEDICT_ORIG:
        base_rmr = rmr_harris_benedict_original(profile)
    elif formula == RMRFormula.HARRIS_BENEDICT_REVISED:
        base_rmr = rmr_harris_benedict_revised(profile)
    else:
        # KATCH_MCARDLE / CUNNINGHAM selected but no body_fat_pct provided —
        # fall back to Mifflin-St Jeor.
        base_rmr = rmr_mifflin_st_jeor(profile)
        formula = RMRFormula.MIFFLIN_ST_JEOR

    # Apply adaptations
    notes: list[str] = [f"Base RMR ({formula.value}): {base_rmr:.0f} kcal"]
    adaptation_factor = 1.0
    weight_reduced_factor = 1.0

    if in_active_deficit:
        adaptation_factor = 0.95
        notes.append("Metabolic adaptation: -5% (active deficit).")

    if weight_reduced_pct > 0.10:
        weight_reduced_factor = 0.97
        notes.append(
            f"Weight-reduced state: -3% ({weight_reduced_pct*100:.0f}% "
            "below all-time high)."
        )

    adjusted_rmr = base_rmr * adaptation_factor * weight_reduced_factor

    return RMRResult(
        formula=formula,
        base_rmr_kcal=round(base_rmr, 1),
        metabolic_adaptation_factor=adaptation_factor,
        weight_reduced_factor=weight_reduced_factor,
        adjusted_rmr_kcal=round(adjusted_rmr, 1),
        notes=notes,
    )


__all__ = [
    "rmr_mifflin_st_jeor", "rmr_harris_benedict_original",
    "rmr_harris_benedict_revised", "rmr_cunningham", "rmr_katch_mcardle",
    "select_rmr_formula", "compute_rmr",
    "BF_PCT_MIN", "BF_PCT_MAX",
]

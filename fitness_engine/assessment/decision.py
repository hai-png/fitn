"""
Cut / Bulk / Recomp decision tree.

Sources:
- rippedbody.com__cut-or-bulk (master decision table, skinny-fat sub-tree)
- rippedbody.com__goal-setting-1,2,3 (9-category trainee system)
- fatcalc.com__body-recomp-calculator (recomp eligibility by BF%)
"""
from __future__ import annotations

from ..models.assessment import RecommendedStrategy
from ..models.profile import PrimaryGoal, Sex, TrainingStatus, UserProfile
from ._thresholds import HORMONAL_FLOOR, OBESE_THRESHOLD, OPERATIONAL_BF_RANGE

# === Cut/Bulk BF boundaries (men; women add +8 %) ===
# operational_lo/hi and obese_threshold are sourced from _thresholds.py
# (single source of truth). recomp_excellent is set below obese_threshold so
# the "excellent recomp potential" branch is actually reachable (otherwise
# the safety override would always fire first).
CUT_BULK_BOUNDARIES = {
    Sex.MALE: {
        "cut_floor":         HORMONAL_FLOOR[Sex.MALE],                # 10 — don't cut below this
        "bulk_ceiling":      OPERATIONAL_BF_RANGE[Sex.MALE][1],       # 20 — don't bulk above this
        "bulk_start":        15,                                       # only start bulk if below this
        "operational_lo":    OPERATIONAL_BF_RANGE[Sex.MALE][0],       # 10 (from _thresholds)
        "operational_hi":    OPERATIONAL_BF_RANGE[Sex.MALE][1],       # 20 (from _thresholds)
        "obese_threshold":   OBESE_THRESHOLD[Sex.MALE],                # 25 (from _thresholds)
        "recomp_excellent":  23,         # below obese_threshold so recomp branch is reachable
        "recomp_good_lo":    15,         # 15-23% → good recomp potential
        "recomp_limited":    15,         # <15% → limited recomp potential
        "skinny_fat_lo":     12,
        "skinny_fat_hi":     23,
    },
    Sex.FEMALE: {
        "cut_floor":         HORMONAL_FLOOR[Sex.FEMALE],              # 18
        "bulk_ceiling":      OPERATIONAL_BF_RANGE[Sex.FEMALE][1],     # 28
        "bulk_start":        23,
        "operational_lo":    OPERATIONAL_BF_RANGE[Sex.FEMALE][0],     # 18 (from _thresholds)
        "operational_hi":    OPERATIONAL_BF_RANGE[Sex.FEMALE][1],     # 28 (from _thresholds)
        "obese_threshold":   OBESE_THRESHOLD[Sex.FEMALE],              # 32 (from _thresholds)
        "recomp_excellent":  30,         # below obese_threshold so recomp branch is reachable
        "recomp_good_lo":    25,
        "recomp_limited":    25,
        "skinny_fat_lo":     20,
        "skinny_fat_hi":     31,
    },
}


def decide_strategy(
    profile: UserProfile,
    body_fat_pct: float,
    bmi: float,
) -> tuple[RecommendedStrategy, str]:
    """
    Decide cut/bulk/recomp/maintenance recommendation.

    The decision tree prioritises:
      1. SAFETY OVERRIDE: Obese users (BF ≥25% M / ≥32% F) → CUT regardless of goal.
         (For obese beginners, recommend HABIT_CHANGE_FIRST.)
      2. If user set an explicit primary_goal, respect it (unless unsafe).
      3. Otherwise, apply RippedBody + FatCalc decision rules.

    Returns (strategy, rationale).
    """
    b = CUT_BULK_BOUNDARIES[profile.sex]

    # === SAFETY OVERRIDES (always apply first) ===
    # Obese users need to lose fat regardless of stated goal (health risk).
    if body_fat_pct >= b["obese_threshold"]:
        if (profile.training_status == TrainingStatus.BEGINNER
                and profile.primary_goal != PrimaryGoal.FAT_LOSS):
            return (
                RecommendedStrategy.HABIT_CHANGE_FIRST,
                f"BF%={body_fat_pct:.1f}% (obese class) + beginner. "
                "Start with habit changes (more veg, lean protein, water, steps) "
                "before calorie counting. Resistance training alone improves "
                "metabolic health without dieting. (Safety override — applies "
                "regardless of stated goal.)"
            )
        return (
            RecommendedStrategy.CUT,
            f"BF%={body_fat_pct:.1f}% (obese class) — prioritise fat loss. "
            "(Safety override — applies regardless of stated goal.)"
        )

    # === Honor explicit user goal (with safety checks) ===
    if profile.primary_goal == PrimaryGoal.MAINTENANCE:
        # Surface a health concern when the user requests MAINTENANCE but
        # BF% is outside the healthy operational range. We do NOT override
        # the user's goal (preserves autonomy) — we append a ⚠ note to the
        # rationale so the concern is visible to the caller/UI. The obese
        # case is already handled by the safety override above (returns
        # CUT/HABIT_CHANGE_FIRST), so by the time we reach here
        # body_fat_pct < obese_threshold is guaranteed.
        rationale = "User goal is maintenance."
        if body_fat_pct < HORMONAL_FLOOR[profile.sex]:
            rationale += (
                " ⚠ BF% below hormonal floor — consider a slow bulk to "
                "restore healthy hormone function."
            )
        elif body_fat_pct > b["operational_hi"]:
            rationale += (
                " ⚠ BF% above operational ceiling — consider a small "
                "cut to bring into healthy range."
            )
        return RecommendedStrategy.MAINTENANCE, rationale

    # STRENGTH goal — treat like maintenance (calorie-neutral) so
    # the user can focus on neural/strength adaptations without weight change.
    # If BF% is above bulk_ceiling, cut first for health.
    if profile.primary_goal == PrimaryGoal.STRENGTH:
        if body_fat_pct > b["bulk_ceiling"]:
            return (
                RecommendedStrategy.CUT,
                f"BF%={body_fat_pct:.1f} above bulk ceiling ({b['bulk_ceiling']}% for "
                f"{profile.sex.value}). Cut first; strength goal honored at lower BF%."
            )
        return (
            RecommendedStrategy.MAINTENANCE,
            "User goal is strength — maintenance calories to support neural adaptations.",
        )

    if profile.primary_goal == PrimaryGoal.FAT_LOSS:
        # Don't allow cutting below cut_floor
        if body_fat_pct < b["cut_floor"]:
            return (
                RecommendedStrategy.MAINTENANCE,
                f"BF%={body_fat_pct:.1f} below cut floor ({b['cut_floor']}% for "
                f"{profile.sex.value}). Switching to maintenance to protect hormones."
            )
        return RecommendedStrategy.CUT, "User goal is fat loss."

    if profile.primary_goal == PrimaryGoal.MUSCLE_GAIN:
        # Don't allow bulking above bulk_ceiling
        if body_fat_pct > b["bulk_ceiling"]:
            return (
                RecommendedStrategy.CUT,
                f"BF%={body_fat_pct:.1f} above bulk ceiling ({b['bulk_ceiling']}% for "
                f"{profile.sex.value}). Cut first to stay in healthy operational range."
            )
        return RecommendedStrategy.BULK, "User goal is muscle gain."

    if profile.primary_goal == PrimaryGoal.RECOMP:
        # Recomp eligibility
        if body_fat_pct >= b["recomp_excellent"]:
            return (
                RecommendedStrategy.RECOMP,
                f"BF%={body_fat_pct:.1f} ≥ {b['recomp_excellent']}% — "
                "excellent recomp potential (10-20% deficit OK)."
            )
        elif body_fat_pct >= b["recomp_good_lo"]:
            return (
                RecommendedStrategy.RECOMP,
                f"BF%={body_fat_pct:.1f} — good recomp potential "
                "(0-10% deficit)."
            )
        else:
            return (
                RecommendedStrategy.BULK,
                f"BF%={body_fat_pct:.1f} < {b['recomp_limited']}% — limited recomp "
                "potential. Bulking cycle is more effective."
            )

    # === Auto-decide when no explicit goal override ===
    # By the time execution reaches here, body_fat_pct < obese_threshold is
    # guaranteed (obese users are handled by the safety override above), so
    # the auto-decide tree only needs to cover the non-obese cases.

    # Overweight (between operational_hi and obese_threshold) → Cut
    if body_fat_pct > b["operational_hi"]:
        return (
            RecommendedStrategy.CUT,
            f"BF%={body_fat_pct:.1f}% above operational ceiling "
            f"({b['operational_hi']}%) — cut to bring into 10-20% range."
        )

    # Below cut_floor → Bulk
    if body_fat_pct < b["cut_floor"]:
        return (
            RecommendedStrategy.BULK,
            f"BF%={body_fat_pct:.1f}% below cut floor ({b['cut_floor']}%) — "
            "bulk to avoid hormonal suppression from sustained low BF%."
        )

    # In operational range — decide by training status & BF%
    # Novice in 13-18% BF range → Recomp
    if (profile.training_status in (TrainingStatus.BEGINNER, TrainingStatus.NOVICE)
            and b["skinny_fat_lo"] <= body_fat_pct <= b["skinny_fat_hi"]):
        return (
            RecommendedStrategy.RECOMP,
            f"Novice trainee at BF%={body_fat_pct:.1f}% (skinny-fat range) — "
            "recomp by holding calories at maintenance while pushing hard on lifts."
        )

    # Beginner/novice in 10-15% (men) / 18-23% (women) → Recomp or bulk by preference
    if (profile.training_status in (TrainingStatus.BEGINNER, TrainingStatus.NOVICE)
            and body_fat_pct < b["bulk_start"]):
        return (
            RecommendedStrategy.RECOMP,
            f"Novice at BF%={body_fat_pct:.1f}% — recomp first to milk newbie gains. "
            "Switch to bulk when recomp stops working (4-12 weeks)."
        )

    # Intermediate/advanced in operational range → user preference
    if body_fat_pct < b["bulk_start"]:
        return (
            RecommendedStrategy.BULK,
            f"BF%={body_fat_pct:.1f}% — below bulk-start threshold ({b['bulk_start']}%). "
            "Bulk to add muscle while staying within operational range."
        )

    # Above bulk_start but below operational_hi → Cut to get back to bulk_start
    return (
        RecommendedStrategy.CUT,
        f"BF%={body_fat_pct:.1f}% — above bulk-start threshold ({b['bulk_start']}%). "
        "Cut to get back to a position where bulking is productive."
    )


__all__ = [
    "CUT_BULK_BOUNDARIES",
    "decide_strategy",
]

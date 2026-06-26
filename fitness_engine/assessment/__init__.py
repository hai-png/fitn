"""Assessment module — body composition, health risk, muscular potential, decision tree.

Phase-6 fix: trimmed __all__ to the intended public API (≤20 symbols).
Internal helpers (compute_*, classify_*, ibw_*, FFMI constants,
berkhan_stage_max_weight_kg, CUT_BULK_BOUNDARIES) are still importable from
their submodules but are no longer re-exported at the package level.
"""
from .assessor import assess_profile
from .body_composition import (
    assess_body_composition,
    classify_bf,
    classify_bmi,
)
from .decision import decide_strategy
from .health_risk import assess_health_risk
from .muscular_potential import assess_muscular_potential

__all__ = [
    # Body composition
    "assess_body_composition", "classify_bf", "classify_bmi",
    # Health risk
    "assess_health_risk",
    # Muscular potential
    "assess_muscular_potential",
    # Decision
    "decide_strategy",
    # Orchestrator
    "assess_profile",
]

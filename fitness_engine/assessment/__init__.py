"""Assessment module — body composition, health risk, muscular potential, decision tree."""
from .body_composition import (
    assess_body_composition, compute_body_fat, compute_ffmi,
    body_fat_navy, body_fat_bmi_jackson, body_fat_cun_bae,
    classify_bf, classify_bmi, target_weight_at_target_bf,
)
from .health_risk import (
    assess_health_risk, compute_whr, classify_whr,
    compute_whtr, classify_whtr,
    compute_absi, absi_z_score, classify_absi,
    ibw_devine, ibw_robinson, ibw_miller, ibw_hamwi,
)
from .muscular_potential import (
    assess_muscular_potential, berkhan_stage_max_weight_kg,
    FFMI_NATURAL_COMMON, FFMI_NATURAL_ATTAINABLE, FFMI_NATURAL_LIKELY_MAX,
    BULK_RATE_BY_STATUS,
)
from .decision import decide_strategy, CUT_BULK_BOUNDARIES
from .assessor import assess_profile

__all__ = [
    # Body composition
    "assess_body_composition", "compute_body_fat", "compute_ffmi",
    "body_fat_navy", "body_fat_bmi_jackson", "body_fat_cun_bae",
    "classify_bf", "classify_bmi", "target_weight_at_target_bf",
    # Health risk
    "assess_health_risk", "compute_whr", "classify_whr",
    "compute_whtr", "classify_whtr",
    "compute_absi", "absi_z_score", "classify_absi",
    "ibw_devine", "ibw_robinson", "ibw_miller", "ibw_hamwi",
    # Muscular potential
    "assess_muscular_potential", "berkhan_stage_max_weight_kg",
    "FFMI_NATURAL_COMMON", "FFMI_NATURAL_ATTAINABLE", "FFMI_NATURAL_LIKELY_MAX",
    "BULK_RATE_BY_STATUS",
    # Decision
    "decide_strategy", "CUT_BULK_BOUNDARIES",
    # Orchestrator
    "assess_profile",
]

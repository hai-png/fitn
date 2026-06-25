"""Utils package.

Phase-6 fix: re-exports ALL names from units.py (was missing IN_PER_CM,
M_PER_FT, in_to_ft — caused `ImportError: cannot import name 'IN_PER_CM'
from 'fitness_engine.utils'` despite the name being in units.__all__).
"""
from .units import (
    kg_to_lb, lb_to_kg, cm_to_in, in_to_cm, cm_to_m, m_to_cm, in_to_ft,
    KG_PER_LB, LB_PER_KG, CM_PER_IN, IN_PER_CM, M_PER_FT,
)

__all__ = [
    "kg_to_lb", "lb_to_kg", "cm_to_in", "in_to_cm", "cm_to_m", "m_to_cm",
    "in_to_ft",
    "KG_PER_LB", "LB_PER_KG", "CM_PER_IN", "IN_PER_CM", "M_PER_FT",
]

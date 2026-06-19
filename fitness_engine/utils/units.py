"""Unit conversion helpers."""
from __future__ import annotations


# Conversion constants
KG_PER_LB = 0.45359237
LB_PER_KG = 2.2046226218
CM_PER_IN = 2.54
IN_PER_CM = 0.3937007874
M_PER_FT = 0.3048


def kg_to_lb(kg: float) -> float:
    return kg * LB_PER_KG


def lb_to_kg(lb: float) -> float:
    return lb * KG_PER_LB


def cm_to_in(cm: float) -> float:
    return cm / CM_PER_IN


def in_to_cm(inch: float) -> float:
    return inch * CM_PER_IN


def cm_to_m(cm: float) -> float:
    return cm / 100.0


def m_to_cm(m: float) -> float:
    return m * 100.0


def in_to_ft(inch: float) -> float:
    return inch / 12.0


__all__ = [
    "KG_PER_LB", "LB_PER_KG", "CM_PER_IN", "IN_PER_CM", "M_PER_FT",
    "kg_to_lb", "lb_to_kg", "cm_to_in", "in_to_cm",
    "cm_to_m", "m_to_cm", "in_to_ft",
]

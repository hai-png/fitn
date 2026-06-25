"""
Shared body-fat-percentage thresholds for assessment + nutrition.

Tier 4.42 fix: previously these thresholds were duplicated between
assessment/body_composition.py (operational range warnings) and
assessment/decision.py (CUT_BULK_BOUNDARIES). They would drift over time.
Now both modules import from this single source of truth.
"""
from __future__ import annotations

from ..models.profile import Sex


# Operational BF% range (RippedBody): outside this range, hormonal/
# performance optimization is compromised.
OPERATIONAL_BF_RANGE = {
    Sex.MALE: (10, 20),       # below 10% = hormonal suppression risk; above 20% = bulking inefficient
    Sex.FEMALE: (18, 28),     # below 18% = hormonal suppression risk; above 28% = bulking inefficient
}

# Hormonal floor (don't cut below this)
HORMONAL_FLOOR = {
    Sex.MALE: 10,
    Sex.FEMALE: 18,
}

# Obese threshold (use BF%, not BMI)
OBESE_THRESHOLD = {
    Sex.MALE: 25,
    Sex.FEMALE: 32,
}

MEDICAL_DISCLAIMER = (
    "Not a substitute for clinical assessment — consult a physician for personalized guidance."
)


__all__ = ["OPERATIONAL_BF_RANGE", "HORMONAL_FLOOR", "OBESE_THRESHOLD", "MEDICAL_DISCLAIMER"]

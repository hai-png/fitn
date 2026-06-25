"""Shared JSON-serialization helpers.

Phase-6 cleanup: previously ``models/assessment.py`` and ``models/nutrition.py``
each defined a near-identical ``_convert`` helper inside their ``to_dict``
methods (one with ``dict`` handling, one without). The two copies had drifted
— ``NutritionPlan.to_dict`` handled ``dict`` instances but
``AssessmentResult.to_dict`` did not (would have left ``HydrationTarget.components``
with raw-Enum values when nested inside AssessmentResult, though in practice
AssessmentResult doesn't nest a HydrationTarget). Consolidated here as a
single source of truth.
"""
from __future__ import annotations

from dataclasses import asdict
from enum import Enum


def convert_for_json(obj):
    """Recursively convert dataclasses / Enums / containers to JSON-safe values.

    - ``Enum`` → ``.value``
    - ``@dataclass`` instance → dict of its fields (recursively converted)
    - ``list`` / ``tuple`` → list of converted items
    - ``dict`` → dict with converted keys and values
    - everything else returned as-is
    """
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "__dataclass_fields__"):
        return {k: convert_for_json(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [convert_for_json(x) for x in obj]
    if isinstance(obj, tuple):
        return [convert_for_json(x) for x in obj]
    if isinstance(obj, dict):
        return {k: convert_for_json(v) for k, v in obj.items()}
    return obj

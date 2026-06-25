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
from typing import Any


def convert_for_json(obj: Any) -> Any:
    """Recursively convert dataclasses / Enums / containers to JSON-safe values.

    - ``Enum`` → ``.value``
    - ``@dataclass`` instance → dict of its fields (recursively converted)
    - ``list`` / ``tuple`` → list of converted items
    - ``dict`` → dict with converted keys AND values
      (Phase-6 fix: previously only values were converted — keys were
      passed through unchanged. This silently leaked Enum objects as
      dict keys, which happened to JSON-serialize OK because all current
      enums inherit from `str`, but it broke the contract and would
      produce wrong output for any non-str-Enum used as a key.)
    - ``set`` / ``frozenset`` → list of converted items (sorted for stability)
      (Phase-6 fix: sets aren't JSON-serializable; previously they would
      pass through and break ``json.dumps``.)
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
    if isinstance(obj, (set, frozenset)):
        # Sort for deterministic output. Use str() to handle mixed types.
        try:
            return [convert_for_json(x) for x in sorted(obj)]
        except TypeError:
            # Unorderable mixed types — fall back to sorted-by-repr.
            return [convert_for_json(x) for x in sorted(obj, key=lambda v: repr(v))]
    if isinstance(obj, dict):
        # Phase-6 fix: convert keys too (was only converting values).
        return {convert_for_json(k): convert_for_json(v) for k, v in obj.items()}
    return obj

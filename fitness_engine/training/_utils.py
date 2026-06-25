"""
Shared helpers for the training subsystem.

Tier 4.43 fix: consolidates _view_count (previously duplicated in
exercise_selector.py and exercise_categorization.py) into a single source.
"""
from __future__ import annotations

from ..models.training import Exercise


def parse_view_count(ex: Exercise) -> int:
    """
    Parse an exercise's view-count string (e.g. "1.2K", "3.5M", "12345") into
    an integer for popularity sorting.

    Returns 0 if the field is missing or unparseable.
    """
    if not ex.views:
        return 0
    v = ex.views.upper().replace(" ", "")
    try:
        if "K" in v:
            return int(float(v.replace("K", "")) * 1_000)
        if "M" in v:
            return int(float(v.replace("M", "")) * 1_000_000)
        return int(v)
    except (ValueError, TypeError):
        return 0


__all__ = ["parse_view_count"]

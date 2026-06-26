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

    Task 9-engine-bug-fixes Bug 3: now also returns 0 when ``ex`` is
    ``None`` or lacks a ``views`` attribute (previously raised
    ``AttributeError``), matching the documented contract "Returns 0 if
    the field is missing or unparseable".
    """
    # guard against None / non-Exercise input so the function matches its
    # stated "Returns 0 if the field is missing or unparseable" contract.
    if ex is None or not hasattr(ex, "views") or ex.views is None:
        return 0
    # v3.1.4 LOW-6 fix: coerce non-string views (int, float, bool) to str
    # before calling .upper(). Previously a numeric ``views`` field raised
    # AttributeError, violating the documented contract.
    if not isinstance(ex.views, str):
        v = str(ex.views).upper().replace(" ", "")
    else:
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

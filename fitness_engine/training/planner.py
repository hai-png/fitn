"""
Training planner — DEPRECATED, kept as backward-compat shim.

All training plan construction logic has moved to architect.py. This
module re-exports the new build_training_plan() so existing imports
(`from fitness_engine.training.planner import build_training_plan`)
continue to work.

The new architect supports:
  - plan_type: STANDARD (ongoing rotation) vs PROGRAM (time-bound)
  - muscle_focus: optional list of muscle groups to emphasize
  - All split patterns: full_body, upper_lower, ppl, ppl_x2, ppl_ul,
    body_part, push_pull
  - All periodization schemes: linear (beginner), DUP (intermediate),
    block (advanced)
  - Equipment filter applied during slot filling (not after)
  - Dynamic substitution when equipment excludes a template exercise
"""
from __future__ import annotations

from .architect import build_training_plan

__all__ = ["build_training_plan"]

"""
Meal planner — Phase-5 clean implementation.

This module is a backward-compat shim. The actual implementation lives in
planner_v2.py. Existing imports (`from fitness_engine.meal_plan.planner
import build_meal_plan`) continue to work.

Phase-5 features:
  - Best-fit scoring algorithm (recipe_scorer.py)
  - Acceptable scaling (recipe_scaler.py)
  - Filler system (recipe_scaler.py)
  - Swap alternatives (swap_system.py)
  - Pre/Post Workout meals (pre_post_workout.py)
  - Profile requirements calculator (profile_requirements.py)
"""
from __future__ import annotations

from .planner_v2 import build_meal_plan

__all__ = ["build_meal_plan"]

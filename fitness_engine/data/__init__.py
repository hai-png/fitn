"""Package data for fitn.

This package contains runtime data files shipped with the wheel:
  - all_exercises.json: 1,217-exercise database loaded by exercise_loader.py

The data is accessed via ``importlib.resources.files("fitness_engine") / "data" / "all_exercises.json"``
which works both in source-tree and installed-wheel layouts.
"""

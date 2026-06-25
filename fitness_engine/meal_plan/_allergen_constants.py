"""Shared allergen / plant-keyword constants.

Phase-6 cleanup: previously the plant-qualifier tuple and the plant-named-phrase
tuple were copy-pasted across ``recipe_loader.py``, ``recipe_scorer.py`` and
``swap_system.py``. The three copies had drifted — the scorer's tuple had the
egg-substitute phrases, the loader's had a ``"broth of"`` entry, and the swap
system's had the plant-milk phrases. This module consolidates them into a
single source of truth (the union of all three) so future edits stay in sync.
"""
from __future__ import annotations

# Plant-based qualifiers that, when preceding a dairy/egg/meat keyword, indicate
# the ingredient is plant-based (e.g. "almond milk", "vegan butter", "just egg",
# "flax egg", "no-chicken broth"). Used to suppress false-positive matches on
# conditional keywords.
PLANT_QUALIFIERS: tuple[str, ...] = (
    "almond", "soy", "oat", "rice", "coconut", "cashew", "hemp", "flax",
    "macadamia", "pea", "vegan", "plant", "dairy-free", "dairy free",
    "non-dairy", "nondairy", "peanut", "cocoa", "shea", "sunflower",
    "avocado", "apple", "agave", "maple", "date", "molasses",
    "vegenaise", "just egg", "egg replacer", "flax egg", "chia egg",
    "beyond", "impossible", "gardein", "tofu", "tempeh", "seitan",
    "vegetable", "veggie", "mushroom", "no-chicken", "no chicken",
    "chicken-style", "chicken style",
    "vegan beef", "vegan chicken", "vegan pork", "vegan fish",
)

# Plant-named phrases that contain a dairy/egg/meat keyword as a substring but
# are themselves plant-based. Matched as whole-word phrases so they short-circuit
# the conditional keyword check.
#
# Phase-6 cleanup: union of the three previous copies:
#   - recipe_loader._PLANT_NAMED_PHRASES         (had "broth of")
#   - recipe_scorer._PLANT_NAMED_PHRASES_FOR_ALLERGENS  (had egg substitutes)
#   - swap_system._PLANT_NAMED_PHRASES           (had plant milks)
PLANT_NAMED_PHRASES: tuple[str, ...] = (
    "eggplant", "eggsplant",
    "butter lettuce", "butterleaf", "buttercup squash",
    "cocoa butter", "shea butter",
    "cream of tartar", "creamed corn", "coconut cream",
    "almond butter", "peanut butter", "cashew butter", "sunflower butter",
    "apple butter", "pumpkin butter",
    "milk thistle", "milkweed",
    "honeydew", "honeycrisp",
    "broth of",
    # Egg substitutes (plant-based):
    "just egg", "just eggs", "flax egg", "flax eggs", "chia egg", "chia eggs",
    "egg replacer", "egg substitute", "vegan egg", "vegan eggs",
    # Plant milks:
    "almond milk", "soy milk", "oat milk", "rice milk", "coconut milk",
    "cashew milk", "hemp milk", "macadamia milk", "pea milk",
)

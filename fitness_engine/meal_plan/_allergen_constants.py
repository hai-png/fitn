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
# Union of plant-named phrases across the allergen + excluded-ingredient
# scanners. Single-word nut/spice/coconut phrases are placed AFTER the
# multi-word phrases that contain them (e.g. "almond milk", "peanut butter",
# "coconut cream", "cashew butter") so the longer phrases get blanked out
# first — otherwise a naive replace("almond", ...) would break "almond milk"
# into "<spaces> milk" and re-introduce a false dairy match for the almond-milk
# plant-qualifier suppression.
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
    # Single-word nut/spice/coconut phrases used to suppress generic "nut"
    # exclusions matching nutmeg/coconut/hazelnut/peanut/etc. Kept AFTER the
    # multi-word phrases above so e.g. "almond butter" / "almond milk" /
    # "peanut butter" / "coconut milk" / "coconut cream" / "cashew butter" /
    # "cashew milk" / "macadamia milk" get blanked out before their
    # single-word root would also match.
    "nutmeg", "coconut", "hazelnut", "peanut", "brazil nut", "walnut",
    "pecan", "almond", "cashew", "pistachio", "macadamia",
)

"""
Micronutrient targets: fiber, fruit & vegetable intake.

Sources:
- Fiber: rippedbody.com__micros (14 g per 1,000 kcal)
- Fruit & veg intake tiers: rippedbody.com__micros
- Vegan supplement protocol: rippedbody.com__advice-for-vegans (Phase-2 hook)
"""
from __future__ import annotations

from ..models.nutrition import MicronutrientTargets


FIBER_G_PER_1000_KCAL = 14

FRUIT_VEG_TIERS = [
    # (max_calories, cups_fruit, cups_veg)
    (2000, 2, 2),
    (3000, 3, 3),
    (4000, 4, 4),
    (float("inf"), 4, 4),
]


def compute_micronutrients(target_calories: float) -> MicronutrientTargets:
    """
    Compute micronutrient targets based on calorie intake.

    - Fiber: 14 g per 1,000 kcal
    - Fruit & veg: tiered by calorie intake
    """
    fiber_g = FIBER_G_PER_1000_KCAL * target_calories / 1000

    cups_fruit = 2
    cups_veg = 2
    for max_cal, f, v in FRUIT_VEG_TIERS:
        if target_calories <= max_cal:
            cups_fruit = f
            cups_veg = v
            break

    notes = [
        f"Fiber target: {fiber_g:.0f} g ({FIBER_G_PER_1000_KCAL} g per 1,000 kcal)",
        f"Fruit: {cups_fruit} cups/day, Veg: {cups_veg} cups/day",
        "At-risk nutrients for dieters: calcium, zinc, magnesium, iron, vitamin D.",
        "Maintain dairy + red meat + sun exposure to avoid deficiencies.",
        "Vegan/vegetarian Phase-2: add B12, iron, zinc, calcium, omega-3, D3, creatine.",
    ]

    return MicronutrientTargets(
        fiber_g=round(fiber_g, 0),
        fruit_cups=cups_fruit,
        veg_cups=cups_veg,
        notes=notes,
    )


__all__ = [
    "FIBER_G_PER_1000_KCAL", "FRUIT_VEG_TIERS",
    "compute_micronutrients",
]

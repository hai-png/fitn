# Recipe Database Coverage Analysis

**Generated**: 2026-06-25
**Database stats**: {'total_recipes': 386, 'curated_count': 123, 'uncurated_count': 263, 'raw_curated_total': 107, 'raw_uncurated_total': 355, 'swap_group_count': 23, 'meal_type_distribution': {'breakfast': 44, 'side': 111, 'dinner': 229, 'lunch': 141, 'snack': 33, 'pre_workout': 8, 'post_workout': 8}, 'diet_type_distribution': {'VEGAN': 226, 'OMNI': 96, 'OMNI_ETHIOPIAN': 35, 'VEGAN_ETHIOPIAN': 53}, 'cuisine_distribution': {'american': 132, 'ethiopian': 60, 'african': 37, 'indian': 22, 'mexican': 10, 'italian': 10, 'african, ethiopian': 9, 'french': 6, 'african, american': 6, 'international': 5, 'caribbean': 5, 'jamaican': 5, 'american,asian': 4, 'continental': 4, 'asian': 4, 'mediterranean': 3, 'caribbean, jamaican': 3, 'moroccan': 3, 'american, southern': 2, 'nordic, scandinavian, swedish': 2}, 'goal_fit_distribution': {'maintenance': 371, 'bulk': 114, 'cut': 145, 'recomp': 52}}

## Summary

- Total cells: 96
- Fully covered (≥2 recipes): 55
- Under-covered (<2 recipes): 11
- Empty (0 recipes): 30
- Coverage: 57.3%

## Coverage Matrix

### OMNI

| Meal Type | kcal bin | Count | Status |
|---|---|---|---|
| breakfast | 0-300 | 15 | ✅ |
| breakfast | 300-500 | 20 | ✅ |
| breakfast | 500-700 | 0 | ❌ |
| breakfast | 700-9999 | 1 | ⚠️ |
| lunch | 0-400 | 64 | ✅ |
| lunch | 400-600 | 38 | ✅ |
| lunch | 600-800 | 2 | ✅ |
| lunch | 800-9999 | 0 | ❌ |
| dinner | 0-400 | 124 | ✅ |
| dinner | 400-600 | 51 | ✅ |
| dinner | 600-800 | 10 | ✅ |
| dinner | 800-9999 | 0 | ❌ |
| snack | 0-200 | 16 | ✅ |
| snack | 200-400 | 10 | ✅ |
| snack | 400-9999 | 1 | ⚠️ |
| side | 0-200 | 38 | ✅ |
| side | 200-400 | 26 | ✅ |
| side | 400-9999 | 16 | ✅ |
| pre_workout | 0-200 | 2 | ✅ |
| pre_workout | 200-400 | 4 | ✅ |
| pre_workout | 400-9999 | 0 | ❌ |
| post_workout | 0-300 | 4 | ✅ |
| post_workout | 300-500 | 4 | ✅ |
| post_workout | 500-9999 | 0 | ❌ |

### VEGAN

| Meal Type | kcal bin | Count | Status |
|---|---|---|---|
| breakfast | 0-300 | 5 | ✅ |
| breakfast | 300-500 | 14 | ✅ |
| breakfast | 500-700 | 0 | ❌ |
| breakfast | 700-9999 | 0 | ❌ |
| lunch | 0-400 | 48 | ✅ |
| lunch | 400-600 | 22 | ✅ |
| lunch | 600-800 | 1 | ⚠️ |
| lunch | 800-9999 | 0 | ❌ |
| dinner | 0-400 | 86 | ✅ |
| dinner | 400-600 | 25 | ✅ |
| dinner | 600-800 | 7 | ✅ |
| dinner | 800-9999 | 0 | ❌ |
| snack | 0-200 | 10 | ✅ |
| snack | 200-400 | 3 | ✅ |
| snack | 400-9999 | 0 | ❌ |
| side | 0-200 | 33 | ✅ |
| side | 200-400 | 21 | ✅ |
| side | 400-9999 | 11 | ✅ |
| pre_workout | 0-200 | 1 | ⚠️ |
| pre_workout | 200-400 | 3 | ✅ |
| pre_workout | 400-9999 | 0 | ❌ |
| post_workout | 0-300 | 2 | ✅ |
| post_workout | 300-500 | 2 | ✅ |
| post_workout | 500-9999 | 0 | ❌ |

### OMNI_ETHIOPIAN

| Meal Type | kcal bin | Count | Status |
|---|---|---|---|
| breakfast | 0-300 | 9 | ✅ |
| breakfast | 300-500 | 7 | ✅ |
| breakfast | 500-700 | 0 | ❌ |
| breakfast | 700-9999 | 0 | ❌ |
| lunch | 0-400 | 12 | ✅ |
| lunch | 400-600 | 11 | ✅ |
| lunch | 600-800 | 1 | ⚠️ |
| lunch | 800-9999 | 0 | ❌ |
| dinner | 0-400 | 15 | ✅ |
| dinner | 400-600 | 10 | ✅ |
| dinner | 600-800 | 3 | ✅ |
| dinner | 800-9999 | 0 | ❌ |
| snack | 0-200 | 2 | ✅ |
| snack | 200-400 | 3 | ✅ |
| snack | 400-9999 | 0 | ❌ |
| side | 0-200 | 12 | ✅ |
| side | 200-400 | 10 | ✅ |
| side | 400-9999 | 1 | ⚠️ |
| pre_workout | 0-200 | 0 | ❌ |
| pre_workout | 200-400 | 2 | ✅ |
| pre_workout | 400-9999 | 0 | ❌ |
| post_workout | 0-300 | 2 | ✅ |
| post_workout | 300-500 | 2 | ✅ |
| post_workout | 500-9999 | 0 | ❌ |

### VEGAN_ETHIOPIAN

| Meal Type | kcal bin | Count | Status |
|---|---|---|---|
| breakfast | 0-300 | 2 | ✅ |
| breakfast | 300-500 | 5 | ✅ |
| breakfast | 500-700 | 0 | ❌ |
| breakfast | 700-9999 | 0 | ❌ |
| lunch | 0-400 | 10 | ✅ |
| lunch | 400-600 | 6 | ✅ |
| lunch | 600-800 | 1 | ⚠️ |
| lunch | 800-9999 | 0 | ❌ |
| dinner | 0-400 | 9 | ✅ |
| dinner | 400-600 | 5 | ✅ |
| dinner | 600-800 | 1 | ⚠️ |
| dinner | 800-9999 | 0 | ❌ |
| snack | 0-200 | 0 | ❌ |
| snack | 200-400 | 0 | ❌ |
| snack | 400-9999 | 0 | ❌ |
| side | 0-200 | 12 | ✅ |
| side | 200-400 | 10 | ✅ |
| side | 400-9999 | 1 | ⚠️ |
| pre_workout | 0-200 | 0 | ❌ |
| pre_workout | 200-400 | 2 | ✅ |
| pre_workout | 400-9999 | 0 | ❌ |
| post_workout | 0-300 | 1 | ⚠️ |
| post_workout | 300-500 | 1 | ⚠️ |
| post_workout | 500-9999 | 0 | ❌ |

## Empty Cells (need recipes)

- OMNI / breakfast / 500-700 kcal
- OMNI / lunch / 800-9999 kcal
- OMNI / dinner / 800-9999 kcal
- OMNI / pre_workout / 400-9999 kcal
- OMNI / post_workout / 500-9999 kcal
- VEGAN / breakfast / 500-700 kcal
- VEGAN / breakfast / 700-9999 kcal
- VEGAN / lunch / 800-9999 kcal
- VEGAN / dinner / 800-9999 kcal
- VEGAN / snack / 400-9999 kcal
- VEGAN / pre_workout / 400-9999 kcal
- VEGAN / post_workout / 500-9999 kcal
- OMNI_ETHIOPIAN / breakfast / 500-700 kcal
- OMNI_ETHIOPIAN / breakfast / 700-9999 kcal
- OMNI_ETHIOPIAN / lunch / 800-9999 kcal
- OMNI_ETHIOPIAN / dinner / 800-9999 kcal
- OMNI_ETHIOPIAN / snack / 400-9999 kcal
- OMNI_ETHIOPIAN / pre_workout / 0-200 kcal
- OMNI_ETHIOPIAN / pre_workout / 400-9999 kcal
- OMNI_ETHIOPIAN / post_workout / 500-9999 kcal
- VEGAN_ETHIOPIAN / breakfast / 500-700 kcal
- VEGAN_ETHIOPIAN / breakfast / 700-9999 kcal
- VEGAN_ETHIOPIAN / lunch / 800-9999 kcal
- VEGAN_ETHIOPIAN / dinner / 800-9999 kcal
- VEGAN_ETHIOPIAN / snack / 0-200 kcal
- VEGAN_ETHIOPIAN / snack / 200-400 kcal
- VEGAN_ETHIOPIAN / snack / 400-9999 kcal
- VEGAN_ETHIOPIAN / pre_workout / 0-200 kcal
- VEGAN_ETHIOPIAN / pre_workout / 400-9999 kcal
- VEGAN_ETHIOPIAN / post_workout / 500-9999 kcal

## Under-covered Cells (need more recipes)

- OMNI / breakfast / 700-9999 kcal (count: 1)
- OMNI / snack / 400-9999 kcal (count: 1)
- VEGAN / lunch / 600-800 kcal (count: 1)
- VEGAN / pre_workout / 0-200 kcal (count: 1)
- OMNI_ETHIOPIAN / lunch / 600-800 kcal (count: 1)
- OMNI_ETHIOPIAN / side / 400-9999 kcal (count: 1)
- VEGAN_ETHIOPIAN / lunch / 600-800 kcal (count: 1)
- VEGAN_ETHIOPIAN / dinner / 600-800 kcal (count: 1)
- VEGAN_ETHIOPIAN / side / 400-9999 kcal (count: 1)
- VEGAN_ETHIOPIAN / post_workout / 0-300 kcal (count: 1)
- VEGAN_ETHIOPIAN / post_workout / 300-500 kcal (count: 1)

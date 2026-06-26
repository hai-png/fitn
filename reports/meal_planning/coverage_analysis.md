# Recipe Database Coverage Analysis

**Generated**: 2026-06-26
**Database stats**: {'total_recipes': 493, 'curated_count': 107, 'uncurated_count': 386, 'raw_curated_total': 107, 'raw_uncurated_total': 355, 'swap_group_count': 23, 'meal_type_distribution': {'breakfast': 46, 'side': 145, 'dinner': 287, 'lunch': 177, 'snack': 40, 'pre_workout': 8, 'post_workout': 8}, 'diet_type_distribution': {'VEGAN': 119, 'OMNI': 303, 'OMNI_ETHIOPIAN': 65, 'VEGAN_ETHIOPIAN': 30}, 'cuisine_distribution': {'american': 157, 'ethiopian': 62, 'african': 37, 'indian': 25, 'mexican': 18, 'italian': 12, 'moroccan': 12, 'african, ethiopian': 10, 'french': 8, 'caribbean': 6, 'african, american': 6, 'american, southern': 5, 'international': 5, 'asian': 5, 'south african': 5, 'jamaican': 5, 'belizean': 4, 'irish': 4, 'american,asian': 4, 'continental': 4}, 'goal_fit_distribution': {'maintenance': 478, 'bulk': 150, 'cut': 185, 'recomp': 61}}

## Summary

- Total cells: 96
- Fully covered (≥2 recipes): 65
- Under-covered (<2 recipes): 4
- Empty (0 recipes): 27
- Coverage: 67.7%

## Coverage Matrix

### OMNI

| Meal Type | kcal bin | Count | Status |
|---|---|---|---|
| breakfast | 0-300 | 20 | ✅ |
| breakfast | 300-500 | 22 | ✅ |
| breakfast | 500-700 | 2 | ✅ |
| breakfast | 700-9999 | 2 | ✅ |
| lunch | 0-400 | 114 | ✅ |
| lunch | 400-600 | 47 | ✅ |
| lunch | 600-800 | 10 | ✅ |
| lunch | 800-9999 | 2 | ✅ |
| dinner | 0-400 | 181 | ✅ |
| dinner | 400-600 | 79 | ✅ |
| dinner | 600-800 | 18 | ✅ |
| dinner | 800-9999 | 7 | ✅ |
| snack | 0-200 | 24 | ✅ |
| snack | 200-400 | 12 | ✅ |
| snack | 400-9999 | 4 | ✅ |
| side | 0-200 | 66 | ✅ |
| side | 200-400 | 51 | ✅ |
| side | 400-9999 | 28 | ✅ |
| pre_workout | 0-200 | 4 | ✅ |
| pre_workout | 200-400 | 4 | ✅ |
| pre_workout | 400-9999 | 0 | ❌ |
| post_workout | 0-300 | 4 | ✅ |
| post_workout | 300-500 | 4 | ✅ |
| post_workout | 500-9999 | 0 | ❌ |

### VEGAN

| Meal Type | kcal bin | Count | Status |
|---|---|---|---|
| breakfast | 0-300 | 4 | ✅ |
| breakfast | 300-500 | 10 | ✅ |
| breakfast | 500-700 | 0 | ❌ |
| breakfast | 700-9999 | 0 | ❌ |
| lunch | 0-400 | 33 | ✅ |
| lunch | 400-600 | 16 | ✅ |
| lunch | 600-800 | 0 | ❌ |
| lunch | 800-9999 | 0 | ❌ |
| dinner | 0-400 | 62 | ✅ |
| dinner | 400-600 | 16 | ✅ |
| dinner | 600-800 | 4 | ✅ |
| dinner | 800-9999 | 0 | ❌ |
| snack | 0-200 | 12 | ✅ |
| snack | 200-400 | 3 | ✅ |
| snack | 400-9999 | 0 | ❌ |
| side | 0-200 | 22 | ✅ |
| side | 200-400 | 16 | ✅ |
| side | 400-9999 | 8 | ✅ |
| pre_workout | 0-200 | 3 | ✅ |
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
| lunch | 0-400 | 17 | ✅ |
| lunch | 400-600 | 12 | ✅ |
| lunch | 600-800 | 2 | ✅ |
| lunch | 800-9999 | 0 | ❌ |
| dinner | 0-400 | 26 | ✅ |
| dinner | 400-600 | 13 | ✅ |
| dinner | 600-800 | 4 | ✅ |
| dinner | 800-9999 | 0 | ❌ |
| snack | 0-200 | 4 | ✅ |
| snack | 200-400 | 3 | ✅ |
| snack | 400-9999 | 0 | ❌ |
| side | 0-200 | 17 | ✅ |
| side | 200-400 | 12 | ✅ |
| side | 400-9999 | 1 | ⚠️ |
| pre_workout | 0-200 | 2 | ✅ |
| pre_workout | 200-400 | 2 | ✅ |
| pre_workout | 400-9999 | 0 | ❌ |
| post_workout | 0-300 | 2 | ✅ |
| post_workout | 300-500 | 2 | ✅ |
| post_workout | 500-9999 | 0 | ❌ |

### VEGAN_ETHIOPIAN

| Meal Type | kcal bin | Count | Status |
|---|---|---|---|
| breakfast | 0-300 | 2 | ✅ |
| breakfast | 300-500 | 3 | ✅ |
| breakfast | 500-700 | 0 | ❌ |
| breakfast | 700-9999 | 0 | ❌ |
| lunch | 0-400 | 6 | ✅ |
| lunch | 400-600 | 4 | ✅ |
| lunch | 600-800 | 0 | ❌ |
| lunch | 800-9999 | 0 | ❌ |
| dinner | 0-400 | 11 | ✅ |
| dinner | 400-600 | 3 | ✅ |
| dinner | 600-800 | 0 | ❌ |
| dinner | 800-9999 | 0 | ❌ |
| snack | 0-200 | 2 | ✅ |
| snack | 200-400 | 0 | ❌ |
| snack | 400-9999 | 0 | ❌ |
| side | 0-200 | 6 | ✅ |
| side | 200-400 | 4 | ✅ |
| side | 400-9999 | 1 | ⚠️ |
| pre_workout | 0-200 | 2 | ✅ |
| pre_workout | 200-400 | 2 | ✅ |
| pre_workout | 400-9999 | 0 | ❌ |
| post_workout | 0-300 | 1 | ⚠️ |
| post_workout | 300-500 | 1 | ⚠️ |
| post_workout | 500-9999 | 0 | ❌ |

## Empty Cells (need recipes)

- OMNI / pre_workout / 400-9999 kcal
- OMNI / post_workout / 500-9999 kcal
- VEGAN / breakfast / 500-700 kcal
- VEGAN / breakfast / 700-9999 kcal
- VEGAN / lunch / 600-800 kcal
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
- OMNI_ETHIOPIAN / pre_workout / 400-9999 kcal
- OMNI_ETHIOPIAN / post_workout / 500-9999 kcal
- VEGAN_ETHIOPIAN / breakfast / 500-700 kcal
- VEGAN_ETHIOPIAN / breakfast / 700-9999 kcal
- VEGAN_ETHIOPIAN / lunch / 600-800 kcal
- VEGAN_ETHIOPIAN / lunch / 800-9999 kcal
- VEGAN_ETHIOPIAN / dinner / 600-800 kcal
- VEGAN_ETHIOPIAN / dinner / 800-9999 kcal
- VEGAN_ETHIOPIAN / snack / 200-400 kcal
- VEGAN_ETHIOPIAN / snack / 400-9999 kcal
- VEGAN_ETHIOPIAN / pre_workout / 400-9999 kcal
- VEGAN_ETHIOPIAN / post_workout / 500-9999 kcal

## Under-covered Cells (need more recipes)

- OMNI_ETHIOPIAN / side / 400-9999 kcal (count: 1)
- VEGAN_ETHIOPIAN / side / 400-9999 kcal (count: 1)
- VEGAN_ETHIOPIAN / post_workout / 0-300 kcal (count: 1)
- VEGAN_ETHIOPIAN / post_workout / 300-500 kcal (count: 1)

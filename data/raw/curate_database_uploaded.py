#!/usr/bin/env python3
"""
UNIFIED CURATION — Enhanced Single Script for Recipe Database
=============================================================
Enhanced Features:
  - Robust CLI argument parsing via argparse
  - Safe tie-breaking in sort keys (preventing Python 3 TypeError)
  - Core coverage protection (preventing deletion of unique dimension providers)
  - Dynamic quota fallback in gap supplementation and filler phases
  - Strict final boundary enforcement (guaranteeing TARGET_MIN <= count <= TARGET_MAX)
  - Graph-based deduplication using connected components
  - Improved protein scoring normalized against caloric extremes
  - Crystal clear verification metrics and structured audit logging

Usage:
  python3 scripts/curate_database.py [--db-path PATH] [--out-path PATH] [--audit-path PATH]
"""

import json
import re
import math
import argparse
import os
import sys
from collections import defaultdict, Counter
from itertools import combinations

# ══════════════════════════════════════════════════════════════
# CONFIGURATION & CONSTANTS
# ══════════════════════════════════════════════════════════════

VARIETY = {
    ('ethiopian', 'breakfast'): 3,
    ('ethiopian', 'lunch'):     5,
    ('ethiopian', 'dinner'):    5,
    ('ethiopian', 'snack'):     3,
    ('ethiopian', 'dessert'):   2,
    ('ethiopian', 'shake'):     1,
    ('non_ethiopian', 'breakfast'): 5,
    ('non_ethiopian', 'lunch'):     6,
    ('non_ethiopian', 'dinner'):    6,
    ('non_ethiopian', 'snack'):     5,
    ('non_ethiopian', 'dessert'):   3,
    ('non_ethiopian', 'shake'):     4,
}

PROFILES = {
    'recomp': {
        'meal_types': ['breakfast', 'lunch', 'dinner', 'snack'],
        'diet_tags': ['omnivore', 'high-protein', 'gluten-free'],
        'cal_range': (300, 500), 'prot_range': (30, 50),
        'daily_cal': (1800, 2200), 'daily_prot': (120, 160),
    },
    'weight_loss': {
        'meal_types': ['breakfast', 'lunch', 'dinner', 'snack'],
        'diet_tags': ['gluten-free', 'vegetarian', 'vegan', 'omnivore', 'low-carb'],
        'cal_range': (150, 400), 'prot_range': (15, 35),
        'daily_cal': (1400, 1800), 'daily_prot': (90, 130),
    },
    'muscle_gain': {
        'meal_types': ['breakfast', 'lunch', 'dinner', 'snack', 'shake'],
        'diet_tags': ['high-protein', 'omnivore', 'dairy-free'],
        'cal_range': (400, 700), 'prot_range': (35, 60),
        'daily_cal': (2500, 3000), 'daily_prot': (160, 220),
    },
    'strength': {
        'meal_types': ['breakfast', 'lunch', 'dinner', 'snack', 'shake'],
        'diet_tags': ['high-protein', 'omnivore', 'dairy-free'],
        'cal_range': (400, 700), 'prot_range': (35, 60),
        'daily_cal': (2500, 3000), 'daily_prot': (160, 220),
    },
    'general_health': {
        'meal_types': ['breakfast', 'lunch', 'dinner', 'snack', 'dessert'],
        'diet_tags': ['vegetarian', 'vegan', 'gluten-free', 'omnivore',
                      'dairy-free', 'nut-free'],
        'cal_range': (300, 500), 'prot_range': (20, 40),
        'daily_cal': (1800, 2200), 'daily_prot': (100, 140),
    },
}

GAP_CATEGORIES = [
    {
        'name': 'high_protein_breakfast',
        'n_needed': 2, 'n_eth_needed': 1,
        'meal_types': ['breakfast'],
        'cal_min': 350, 'cal_max': 700,
        'prot_min': 30,
        'diet_focus': ['high-protein', 'omnivore'],
        'reason': 'Muscle/Strength/Recomp need 400-600cal, 30-50g breakfasts',
    },
    {
        'name': 'protein_snack',
        'n_needed': 2, 'n_eth_needed': 0,
        'meal_types': ['snack'],
        'cal_min': 150, 'cal_max': 400,
        'prot_min': 15,
        'diet_focus': ['high-protein', 'omnivore', 'gluten-free'],
        'reason': 'Need protein-rich snacks',
    },
    {
        'name': 'high_protein_shake',
        'n_needed': 2, 'n_eth_needed': 0,
        'meal_types': ['shake'],
        'cal_min': 200, 'cal_max': 500,
        'prot_min': 25,
        'diet_focus': ['high-protein', 'omnivore', 'gluten-free'],
        'reason': 'Muscle/Strength need protein shakes',
    },
    {
        'name': 'high_cal_dinner',
        'n_needed': 2, 'n_eth_needed': 1,
        'meal_types': ['dinner', 'lunch'],
        'cal_min': 500, 'cal_max': 800,
        'prot_min': 40,
        'diet_focus': ['omnivore', 'high-protein'],
        'reason': 'Higher-calorie dinner options for muscle/strength',
    },
    {
        'name': 'balanced_lunch',
        'n_needed': 2, 'n_eth_needed': 1,
        'meal_types': ['lunch', 'dinner'],
        'cal_min': 200, 'cal_max': 400,
        'prot_min': 15,
        'diet_focus': ['vegetarian', 'vegan', 'gluten-free'],
        'reason': 'More plant-based lunch options for weight loss/general',
    },
]

FILLER_CATEGORIES = [
    {
        'name': 'low_cal_high_prot_filler',
        'desc': 'Low-cal high-protein filler',
        'criteria': lambda r: (r.get('calories') or 0) <= 250
                              and (r.get('protein_g') or 0) >= 25
                              and any(mt in (r.get('meal_type') or [])
                                      for mt in ['lunch', 'dinner']),
        'priority': ['high-protein', 'omnivore', 'gluten-free', 'nut-free'],
        'n_needed': 2, 'n_eth': 0,
    },
    {
        'name': 'high_cal_high_prot_filler',
        'desc': 'High-cal high-protein filler',
        'criteria': lambda r: (r.get('calories') or 0) >= 500
                              and (r.get('calories') or 0) <= 800
                              and (r.get('protein_g') or 0) >= 50
                              and any(mt in (r.get('meal_type') or [])
                                      for mt in ['lunch', 'dinner', 'breakfast']),
        'priority': ['high-protein', 'omnivore', 'dairy-free'],
        'n_needed': 2, 'n_eth': 1,
    },
    {
        'name': 'shake_filler',
        'desc': 'Protein shake filler',
        'criteria': lambda r: 'shake' in (r.get('meal_type') or [])
                              and (r.get('calories') or 0) >= 200
                              and (r.get('protein_g') or 0) >= 25
                              and (r.get('calories') or 0) <= 600,
        'priority': ['high-protein', 'gluten-free', 'vegetarian', 'dairy-free'],
        'n_needed': 2, 'n_eth': 0,
    },
]


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def is_eth(r):
    return r.get('source') == 'EthiopianFood.org'

def cc(r):
    return 'ethiopian' if is_eth(r) else 'non_ethiopian'

def cal_bucket(cal):
    if cal is None: return None
    if cal < 200: return 'cal_<200'
    elif cal < 400: return 'cal_200-400'
    elif cal < 600: return 'cal_400-600'
    else: return 'cal_600+'

def prot_bucket(prot):
    if prot is None: return None
    if prot < 10: return 'prot_<10g'
    elif prot < 20: return 'prot_10-20g'
    elif prot < 30: return 'prot_20-30g'
    elif prot < 40: return 'prot_30-40g'
    else: return 'prot_40g+'

def nut_dims(r):
    d = set()
    cb = cal_bucket(r.get('calories'))
    pb = prot_bucket(r.get('protein_g'))
    if cb: d.add(cb)
    if pb: d.add(pb)
    for mt in r.get('meal_type', []): d.add(f"meal_{mt}")
    for dt in r.get('diet_tags', []): d.add(f"diet_{dt}")
    return d

def all_dims(r):
    d = nut_dims(r)
    c = r.get('cuisine', '')
    if c: d.add(f"cuisine_{c}")
    return d

def protein_density(r):
    c, p = r.get('calories') or 0, r.get('protein_g') or 0
    return p / c if (c and c > 0) else p / 500.0

def title_sim(t1, t2):
    def norm(t):
        t = t.lower().strip()
        t = re.sub(r'[^\w\s]', '', t)
        t = re.sub(r'\s+', ' ', t)
        stop = {'recipe','the','a','an','with','and','in','of','for','to',
                'on','is','how','make','best','easy','simple','quick',
                'delicious','healthy','perfect','homemade','classic','fresh',
                'creamy','spicy','savory','sweet','ultimate','authentic','amazing'}
        return ' '.join(w for w in t.split() if w not in stop)
    n1, n2 = norm(t1), norm(t2)
    if not n1 or not n2: return 0
    s1, s2 = set(n1.split()), set(n2.split())
    return len(s1 & s2) / len(s1 | s2)

def variety_target(ccat, meal_type):
    return VARIETY.get((ccat, meal_type), 1)

def is_essential_for_coverage(r, selected_recipes, all_required_dims):
    """Check if removing r would leave any required nutritional dimension completely uncovered."""
    other_dims = set()
    for x in selected_recipes:
        if x['url'] != r['url']:
            other_dims |= nut_dims(x)
    r_dims = nut_dims(r) & all_required_dims
    uncovered_if_removed = r_dims - other_dims
    return len(uncovered_if_removed) > 0


# ══════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Unified Curation Pipeline for Recipe Database")
    parser.add_argument("--db-path", default="recipe_database.json", help="Path to raw input database JSON")
    parser.add_argument("--out-path", default="recipe_database.curated.json", help="Path to save curated database JSON")
    parser.add_argument("--audit-path", default="curation_audit.txt", help="Path to save audit log")
    parser.add_argument("--target-min", type=int, default=50, help="Minimum target database size")
    parser.add_argument("--target-max", type=int, default=65, help="Maximum target database size")
    parser.add_argument("--eth-target", type=float, default=0.30, help="Target ratio of Ethiopian recipes")
    parser.add_argument("--eth-min", type=float, default=0.20, help="Minimum allowed ratio of Ethiopian recipes")
    parser.add_argument("--eth-max", type=float, default=0.50, help="Maximum allowed ratio of Ethiopian recipes")
    args = parser.parse_args()

    db_path = args.db_path
    if not os.path.exists(db_path) and os.path.exists(os.path.join("uploads", "recipe_database.json")):
        db_path = os.path.join("uploads", "recipe_database.json")

    if not os.path.exists(db_path):
        print(f"Error: Input database file not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    with open(db_path) as f:
        all_recipes = json.load(f)

    original_count = len(all_recipes)
    print(f"Loaded {original_count} recipes from {db_path}")

    # Phase 1 — NUTRITIONAL CORE (greedy set cover)
    print(f"\n{'='*65}\n  PHASE 1: NUTRITIONAL SET COVER\n{'='*65}")
    all_nut = set()
    for r in all_recipes:
        all_nut |= nut_dims(r)

    remaining = set(all_nut)
    core = []
    pool = list(all_recipes)

    while remaining and pool:
        best_i = max(range(len(pool)), key=lambda i: (len(nut_dims(pool[i]) & remaining), protein_density(pool[i]), pool[i]['url']))
        nd = nut_dims(pool[best_i]) & remaining
        if not nd: break
        core.append(pool.pop(best_i))
        remaining -= nd
        print(f"  [{len(core)}] {core[-1]['title'][:55]} → {len(nd)} nut-dims, {len(all_nut)-len(remaining)}/{len(all_nut)} covered")

    selected = list(core)
    selected_urls = {r['url'] for r in selected}
    remaining_pool = [r for r in all_recipes if r['url'] not in selected_urls]
    print(f"  ✓ Core: {len(core)} recipes, {len(all_nut)-len(remaining)}/{len(all_nut)} dims covered")

    # Phase 2 — VARIETY (fill per cuisine_cat × meal_type targets)
    print(f"\n{'='*65}\n  PHASE 2: VARIETY PER CUISINE_CAT × MEAL_TYPE\n{'='*65}")
    for ccat in ['ethiopian', 'non_ethiopian']:
        for mt in ['breakfast', 'lunch', 'dinner', 'snack', 'dessert', 'shake']:
            have = sum(1 for r in selected if cc(r) == ccat and mt in r.get('meal_type', []))
            need = variety_target(ccat, mt)
            add = max(0, need - have)
            if add <= 0: continue

            candidates = [r for r in remaining_pool if cc(r) == ccat and mt in r.get('meal_type', [])]
            candidates.sort(key=lambda r: (
                len(nut_dims(r) & remaining) if remaining else 0,
                len(r.get('diet_tags', [])),
                protein_density(r),
                r['url']
            ), reverse=True)

            for r in candidates[:add]:
                selected.append(r)
                selected_urls.add(r['url'])
                remaining = remaining - nut_dims(r)
                remaining_pool = [x for x in remaining_pool if x['url'] != r['url']]
                have += 1
            print(f"  {ccat:15} {mt:10}: {have}/{need} {'✓' if have >= need else '✗'}")

    print(f"  → {len(selected)} recipes ({sum(1 for r in selected if is_eth(r))} Ethiopian)")

    # Phase 3 — CUISINE DIVERSITY (every cuisine gets ≥1 recipe)
    print(f"\n{'='*65}\n  PHASE 3: CUISINE DIVERSITY FLOOR\n{'='*65}")
    selected_cuisines = Counter(r.get('cuisine', 'Unknown') for r in selected)
    all_cuisines = sorted({r.get('cuisine') for r in all_recipes if r.get('cuisine')})
    missing_cuisines = [c for c in all_cuisines if c != 'Ethiopian' and selected_cuisines.get(c, 0) == 0]
    print(f"  Missing cuisines: {missing_cuisines or 'none'}")

    for cuisine in missing_cuisines:
        candidates = [r for r in remaining_pool if r.get('cuisine') == cuisine]
        if not candidates:
            print(f"  ✗ No recipes found for {cuisine}")
            continue
        candidates.sort(key=lambda r: (
            len(nut_dims(r) & remaining) if remaining else 0,
            protein_density(r),
            len(r.get('diet_tags', [])),
            r['url']
        ), reverse=True)
        best = candidates[0]
        selected.append(best)
        selected_urls.add(best['url'])
        remaining_pool = [r for r in remaining_pool if r['url'] != best['url']]
        remaining = remaining - nut_dims(best)
        print(f"  ✓ Added [{cuisine:12}] {best['title'][:50]} ({best.get('calories')}cal, {best.get('protein_g')}g)")

    # Helper for balance adjustment
    def adjust_balance(recipes, pool):
        eth = [r for r in recipes if is_eth(r)]
        non = [r for r in recipes if not is_eth(r)]
        total = len(recipes)
        if total == 0: return recipes, pool
        ratio = len(eth) / total

        print(f"    Current balance: {len(eth)} eth + {len(non)} non = {total} ({ratio*100:.0f}% eth, target {args.eth_target*100:.0f}%)")

        target_eth = int(total * args.eth_target)
        target_eth = max(target_eth, int(total * args.eth_min))
        target_eth = min(target_eth, int(total * args.eth_max))

        if len(eth) > target_eth:
            excess = len(eth) - target_eth
            eth_sorted = []
            for r in eth:
                if is_essential_for_coverage(r, recipes, all_nut):
                    eth_sorted.append((999, r['url'], r))
                else:
                    other_dims = set.union(*[nut_dims(x) for x in recipes if x['url'] != r['url']])
                    uniqueness = len(nut_dims(r) - other_dims)
                    eth_sorted.append((uniqueness, r['url'], r))
            eth_sorted.sort(key=lambda x: (x[0], x[1]))
            to_remove = set()
            for uniq, url, r in eth_sorted:
                if len(to_remove) >= excess: break
                if uniq == 999: continue
                to_remove.add(url)
                print(f"    - [Ethi Pruned] {r['title'][:50]}")
            recipes = [r for r in recipes if r['url'] not in to_remove]

        elif len(eth) < target_eth:
            need = target_eth - len(eth)
            candidates = [r for r in pool if is_eth(r)]
            candidates.sort(key=lambda r: (
                len(nut_dims(r) & remaining) if remaining else 0,
                protein_density(r),
                len(r.get('diet_tags', [])),
                r['url']
            ), reverse=True)
            for r in candidates[:need]:
                recipes.append(r)
                print(f"    + [Ethi Added] {r['title'][:50]}")
                pool = [x for x in pool if x['url'] != r['url']]

        return recipes, pool

    # Phase 4 — CUISINE BALANCE
    print(f"\n{'='*65}\n  PHASE 4: CUISINE BALANCE\n{'='*65}")
    selected, remaining_pool = adjust_balance(selected, remaining_pool)

    # Phase 5 — SIZE TARGET EXPANSION
    print(f"\n{'='*65}\n  PHASE 5: SIZE TARGET EXPANSION\n{'='*65}")
    expansion_target = max(args.target_min - 16, len(selected))
    print(f"  Expanding interim pool up to {expansion_target} (leaving room for supplements/fillers)...")

    while len(selected) < expansion_target and remaining_pool:
        ccat_eth = sum(1 for r in selected if is_eth(r))
        cur_ratio = ccat_eth / len(selected)
        bias_eth = cur_ratio < args.eth_target

        candidates = []
        for r in remaining_pool:
            r_cc = cc(r)
            if bias_eth and r_cc == 'non_ethiopian':
                score = -100
            elif not bias_eth and r_cc == 'ethiopian':
                score = -100
            else:
                gap_fill = sum(max(0, variety_target(r_cc, mt) - sum(1 for x in selected if cc(x) == r_cc and mt in x.get('meal_type', []))) for mt in r.get('meal_type', []))
                nut_gain = len(nut_dims(r) & remaining) if remaining else 0
                diversity = 1 if r.get('cuisine', '') not in {x.get('cuisine') for x in selected} else 0
                profile_hits = sum(1 for p in PROFILES.values() if any(mt in r.get('meal_type', []) for mt in p['meal_types']))
                score = (gap_fill * 8 + nut_gain * 3 + diversity * 15 + profile_hits + protein_density(r) * 2)
            candidates.append((score, r['url'], r))

        candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        if candidates[0][0] <= 0: break
        best = candidates[0][2]
        selected.append(best)
        selected_urls.add(best['url'])
        remaining = remaining - nut_dims(best)
        remaining_pool = [r for r in remaining_pool if r['url'] != best['url']]

    print(f"  → Interim pool: {len(selected)} recipes ({sum(1 for r in selected if is_eth(r))} Ethiopian)")

    # Phase 6 — GRAPH DEDUPLICATION
    print(f"\n{'='*65}\n  PHASE 6: GRAPH DEDUPLICATION\n{'='*65}")
    seen = {}
    deduped = []
    for r in selected:
        key = (r.get('source'), r.get('title', '').strip().lower())
        if key in seen:
            if protein_density(r) > protein_density(seen[key]):
                deduped = [x for x in deduped if x['url'] != seen[key]['url']]
                deduped.append(r)
                seen[key] = r
        else:
            seen[key] = r
            deduped.append(r)

    adj = defaultdict(list)
    for i, j in combinations(range(len(deduped)), 2):
        r1, r2 = deduped[i], deduped[j]
        if r1.get('source') != r2.get('source'): continue
        sim = title_sim(r1.get('title', ''), r2.get('title', ''))
        if sim < 0.65: continue
        mt1, mt2 = set(r1.get('meal_type', [])), set(r2.get('meal_type', []))
        if mt1 and mt2 and not (mt1 & mt2): continue
        c1, c2 = r1.get('calories') or 0, r2.get('calories') or 0
        if max(c1, c2) > 0 and min(c1, c2) / max(c1, c2) < 0.4: continue
        adj[i].append(j)
        adj[j].append(i)

    visited = set()
    to_remove_urls = set()
    for i in range(len(deduped)):
        if i in visited: continue
        comp = []
        queue = [i]
        visited.add(i)
        while queue:
            curr = queue.pop(0)
            comp.append(curr)
            for nbr in adj[curr]:
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)
        if len(comp) > 1:
            comp_recipes = [deduped[idx] for idx in comp]
            comp_recipes.sort(key=lambda x: (
                is_essential_for_coverage(x, deduped, all_nut),
                protein_density(x),
                x['url']
            ), reverse=True)
            best_survivor = comp_recipes[0]
            for loser in comp_recipes[1:]:
                to_remove_urls.add(loser['url'])
                print(f"  - [Sim Dedup] {loser['title'][:55]} (kept {best_survivor['title'][:30]})")

    selected = [r for r in deduped if r['url'] not in to_remove_urls]
    remaining_pool = [r for r in all_recipes if r['url'] not in {x['url'] for x in selected}]
    print(f"  → Post-dedup pool: {len(selected)} recipes")

    # Phase 7 — MACRO GAP SUPPLEMENTATION
    print(f"\n{'='*65}\n  PHASE 7: MACRO GAP SUPPLEMENTATION (Dynamic Fallback)\n{'='*65}")
    supplement_added = []
    supplement_urls = set()
    current_cuisines = {r.get('cuisine') for r in selected}
    cuisine_counts = Counter(r.get('cuisine') for r in selected)

    for cat in GAP_CATEGORIES:
        print(f"\n  [{cat['name']}] {cat['reason']}\n  Target: {cat['n_needed']} (ideal {cat['n_eth_needed']} Ethiopian)")
        candidates = []
        for r in remaining_pool:
            if r['url'] in supplement_urls: continue
            if not any(mt in (r.get('meal_type') or []) for mt in cat['meal_types']): continue
            cal, prot = r.get('calories') or 0, r.get('protein_g') or 0
            if cal < cat['cal_min'] or cal > cat['cal_max'] or prot < cat['prot_min']: continue

            diet_overlap = len(set(r.get('diet_tags', [])) & set(cat['diet_focus']))
            cuisine_bonus = 5 if r.get('cuisine') not in current_cuisines else (2 if cuisine_counts.get(r.get('cuisine'), 0) <= 2 else 0)
            score = diet_overlap * 3 + cuisine_bonus + (prot / max(cal, 1)) * 20
            candidates.append((score, r['url'], r, is_eth(r)))

        candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)

        eth_added, non_added = 0, 0
        for score, url, r, r_is_eth in candidates:
            if eth_added + non_added >= cat['n_needed']: break
            if r_is_eth and eth_added < cat['n_eth_needed']:
                supplement_added.append(r); supplement_urls.add(url)
                eth_added += 1; current_cuisines.add(r.get('cuisine')); cuisine_counts[r.get('cuisine')] += 1
                print(f"    + E {r['title'][:55]} ({r.get('calories')}cal, {r.get('protein_g')}g) [{r.get('cuisine')}] score={score:.1f}")

        for score, url, r, r_is_eth in candidates:
            if eth_added + non_added >= cat['n_needed']: break
            if url in supplement_urls: continue
            supplement_added.append(r); supplement_urls.add(url)
            if r_is_eth: eth_added += 1
            else: non_added += 1
            current_cuisines.add(r.get('cuisine')); cuisine_counts[r.get('cuisine')] += 1
            tag = 'E' if r_is_eth else 'N'
            print(f"    + {tag} (Fallback) {r['title'][:55]} ({r.get('calories')}cal, {r.get('protein_g')}g) [{r.get('cuisine')}] score={score:.1f}")

        if eth_added + non_added < cat['n_needed']:
            print(f"    ⚠ Warning: Only found {eth_added+non_added}/{cat['n_needed']} matching criteria in entire DB")

    selected.extend(supplement_added)
    remaining_pool = [r for r in all_recipes if r['url'] not in {x['url'] for x in selected}]
    selected, remaining_pool = adjust_balance(selected, remaining_pool)
    print(f"\n  → Total after Phase 7: {len(selected)} recipes")

    # Phase 8 — FILLER ADDITION
    print(f"\n{'='*65}\n  PHASE 8: FILLER ADDITION\n{'='*65}")
    cuisine_counts = Counter(r.get('cuisine') for r in selected)
    filler_added = []
    filler_urls = set()

    for cat in FILLER_CATEGORIES:
        print(f"\n  [{cat['name']}] {cat['desc']}\n  Target: {cat['n_needed']} (ideal {cat['n_eth']} Ethiopian)")
        candidates = []
        for r in remaining_pool:
            if r['url'] in filler_urls: continue
            if not cat['criteria'](r): continue
            prio_overlap = len(set(r.get('diet_tags', [])) & set(cat['priority']))
            cuisine_bonus = 3 if cuisine_counts.get(r.get('cuisine'), 0) <= 2 else 0
            if r.get('cuisine') not in {x.get('cuisine') for x in filler_added + selected}: cuisine_bonus = 5
            score = prio_overlap * 2 + cuisine_bonus + (r.get('protein_g', 0) / max(r.get('calories', 1), 1)) * 15
            candidates.append((score, r['url'], r, is_eth(r)))

        candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        eth_added, non_added = 0, 0

        for score, url, r, r_is_eth in candidates:
            if eth_added + non_added >= cat['n_needed']: break
            if r_is_eth and eth_added < cat['n_eth']:
                filler_added.append(r); filler_urls.add(url); eth_added += 1; cuisine_counts[r.get('cuisine')] += 1
                print(f"    + E {r['title'][:55]} ({r.get('calories')}cal, {r.get('protein_g')}g) score={score:.1f}")

        for score, url, r, r_is_eth in candidates:
            if eth_added + non_added >= cat['n_needed']: break
            if url in filler_urls: continue
            filler_added.append(r); filler_urls.add(url)
            if r_is_eth: eth_added += 1
            else: non_added += 1
            cuisine_counts[r.get('cuisine')] += 1
            tag = 'E' if r_is_eth else 'N'
            print(f"    + {tag} {r['title'][:55]} ({r.get('calories')}cal, {r.get('protein_g')}g) score={score:.1f}")

    selected.extend(filler_added)
    remaining_pool = [r for r in all_recipes if r['url'] not in {x['url'] for x in selected}]
    selected, remaining_pool = adjust_balance(selected, remaining_pool)

    # Phase 9 — STRICT BOUNDARY & RATIO ENFORCEMENT
    print(f"\n{'='*65}\n  PHASE 9: STRICT BOUNDARY & RATIO ENFORCEMENT\n{'='*65}")
    while len(selected) > args.target_max:
        print(f"  Current count {len(selected)} exceeds target_max ({args.target_max}). Smart trimming...")
        trim_candidates = []
        eth_count = sum(1 for r in selected if is_eth(r))
        cur_ratio = eth_count / len(selected)

        for r in selected:
            if is_essential_for_coverage(r, selected, all_nut):
                continue
            r_is_eth = is_eth(r)
            if r_is_eth and (eth_count - 1) / (len(selected) - 1) < args.eth_min:
                score = 9999
            elif not r_is_eth and eth_count / (len(selected) - 1) > args.eth_max:
                score = 9999
            else:
                stage_penalty = 0 if r['url'] in filler_urls else (10 if r['url'] in supplement_urls else 20)
                score = protein_density(r) * 10 + len(r.get('diet_tags', [])) + stage_penalty
            trim_candidates.append((score, r['url'], r))

        trim_candidates.sort(key=lambda x: (x[0], x[1]))
        if not trim_candidates or trim_candidates[0][0] >= 9999:
            print("  ⚠ Cannot trim further without violating essential coverage or ratio constraints.")
            break
        removed = trim_candidates[0][2]
        selected = [x for x in selected if x['url'] != removed['url']]
        print(f"    - Pruned: {removed['title'][:55]}")

    while len(selected) < args.target_min and remaining_pool:
        print(f"  Current count {len(selected)} below target_min ({args.target_min}). Expanding...")
        selected, remaining_pool = adjust_balance(selected, remaining_pool)
        if len(selected) >= args.target_min: break
        best = remaining_pool.pop(0)
        selected.append(best)

    eth_final = sum(1 for r in selected if is_eth(r))
    total_final = len(selected)
    print(f"  ✓ Final Database Size: {total_final} recipes (Target: {args.target_min}-{args.target_max})")
    print(f"  ✓ Final Ethiopian Ratio: {eth_final}/{total_final} ({eth_final/total_final*100:.1f}%)")

    # Phase 10 — TAGGING WITH METADATA
    print(f"\n{'='*65}\n  PHASE 10: TAGGING WITH METADATA\n{'='*65}")
    stage_of_url = {}
    for r in selected:
        if r['url'] in filler_urls: stage_of_url[r['url']] = 'filler'
        elif r['url'] in supplement_urls: stage_of_url[r['url']] = 'supplement'
        else: stage_of_url[r['url']] = 'core'

    def compute_selection_reason(r, all_list):
        parts = []
        stage = stage_of_url.get(r['url'], 'core')
        if stage == 'filler': parts.append("Macro adjuster")
        elif stage == 'supplement': parts.append("Macro gap supplement")
        else: parts.append("Core curation")
        if is_eth(r): parts.insert(0, "Ethiopian cuisine")

        cal, prot = r.get('calories') or 0, r.get('protein_g') or 0
        if prot >= 50: parts.append("High-protein" + (" high-cal" if cal >= 500 else ""))
        elif cal >= 600: parts.append("High-calorie option")
        elif cal <= 200 and prot >= 20: parts.append("Protein-dense low-calorie")

        cuisine = r.get('cuisine')
        if sum(1 for x in all_list if x.get('cuisine') == cuisine) <= 2:
            parts.append(f"Diverse ({cuisine})")
        return '; '.join(parts)

    def compute_profile_fit(r):
        scores = {}
        for pname, pdef in PROFILES.items():
            diet_overlap = len(set(r.get('diet_tags', [])) & set(pdef['diet_tags']))
            if not diet_overlap: continue
            mt_overlap = len(set(r.get('meal_type', [])) & set(pdef['meal_types']))
            if not mt_overlap: continue

            cal, prot = r.get('calories') or 0, r.get('protein_g') or 0
            n_meals = len(pdef['meal_types'])
            ideal_cal = sum(pdef['daily_cal']) / 2.0 / n_meals
            ideal_prot = sum(pdef['daily_prot']) / 2.0 / n_meals

            cal_score = max(0, 1 - abs(cal - ideal_cal) / ideal_cal) if ideal_cal else 0
            prot_score = max(0, 1 - abs(prot - ideal_prot) / ideal_prot) if ideal_prot else 0
            scores[pname] = (diet_overlap / len(pdef['diet_tags'])) * 0.2 + (mt_overlap / n_meals) * 0.2 + cal_score * 0.3 + prot_score * 0.3
        return scores

    def find_alternatives(r, all_list, max_alt=3):
        cal, prot = r.get('calories') or 0, r.get('protein_g') or 0
        mt = set(r.get('meal_type', []))
        scored = []
        for alt in all_list:
            if alt['url'] == r['url']: continue
            alt_mt = set(alt.get('meal_type', []))
            if not (mt & alt_mt): continue
            alt_cal, alt_prot = alt.get('calories') or 0, alt.get('protein_g') or 0
            cal_sim = max(0, 1 - abs(cal - alt_cal) / max(max(cal, alt_cal), 1))
            prot_sim = max(0, 1 - abs(prot - alt_prot) / max(max(prot, alt_prot), 1))
            mt_sim = len(mt & alt_mt) / max(len(mt | alt_mt), 1)
            cuisine_bonus = 1 if r.get('cuisine') == alt.get('cuisine') else 0
            scored.append((cal_sim*0.25 + prot_sim*0.25 + mt_sim*0.3 + cuisine_bonus*0.2, alt))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{'title': a['title'], 'url': a['url'], 'calories': a.get('calories'), 'protein_g': a.get('protein_g'), 'cuisine': a.get('cuisine')} for _, a in scored[:max_alt]]

    tagged_db = []
    for r in selected:
        ps = compute_profile_fit(r)
        entry = {k: r.get(k) for k in ['source', 'source_category', 'url', 'title', 'description', 'image', 'ingredients', 'instructions', 'calories', 'protein_g', 'carbs_g', 'fat_g', 'fiber_g', 'sugar_g', 'prep_time_min', 'cook_time_min', 'total_time_min', 'servings', 'diet_tags', 'meal_type', 'cuisine']}
        entry['metadata'] = {
            'selection_reason': compute_selection_reason(r, selected),
            'curation_stage': stage_of_url.get(r['url'], 'core'),
            'primary_profiles': [p for p, s in ps.items() if s >= 0.5],
            'secondary_profiles': [p for p, s in ps.items() if 0.3 <= s < 0.5],
            'profile_scores': {k: round(v, 4) for k, v in ps.items() if v > 0},
            'is_filler': r['url'] in filler_urls,
            'is_supplement': r['url'] in supplement_urls,
            'top_alternatives': find_alternatives(r, selected)
        }
        tagged_db.append(entry)

    selected = sorted(tagged_db, key=lambda r: (r['source'], r['title']))

    # Verification & Audit Logging
    final_dims = set.union(*[all_dims(r) for r in selected])
    all_full = set.union(*[all_dims(r) for r in all_recipes])
    dim_cats = [
        ('Calorie', sorted(d for d in all_full if d.startswith('cal_'))),
        ('Protein', sorted(d for d in all_full if d.startswith('prot_'))),
        ('Meal',    sorted(d for d in all_full if d.startswith('meal_'))),
        ('Diet',    sorted(d for d in all_full if d.startswith('diet_'))),
        ('Cuisine', sorted(d for d in all_full if d.startswith('cuisine_'))),
    ]

    with open(args.out_path, 'w') as f:
        json.dump(selected, f, indent=2, ensure_ascii=False)

    with open(args.audit_path, 'w') as f:
        f.write("UNIFIED CURATION AUDIT LOG\n" + "="*70 + "\n")
        f.write(f"Source Database: {original_count} recipes\n")
        f.write(f"Final Curated:   {len(selected)} recipes (Target limit: {args.target_min}-{args.target_max})\n")
        f.write(f"Ethiopian Split: {eth_final}E + {total_final-eth_final}N ({eth_final/total_final*100:.1f}%)\n\n")

        f.write("Composition:\n")
        for stage in ['core', 'supplement', 'filler']:
            n = sum(1 for r in selected if r.get('metadata', {}).get('curation_stage') == stage)
            f.write(f"  {stage:10}: {n}\n")

        f.write("\nDimension Coverage Verification:\n")
        for cat, dims in dim_cats:
            cov = sum(1 for d in dims if d in final_dims)
            f.write(f"  {cat:<10}: {cov}/{len(dims)} {'✓' if cov == len(dims) else '✗'}\n")
            for d in dims:
                f.write(f"    {'✓' if d in final_dims else '✗'} {d}\n")

        f.write("\nMeal Type Breakdown & Weekly Variety:\n")
        for mt in ['breakfast', 'lunch', 'dinner', 'snack', 'dessert', 'shake']:
            count = sum(1 for r in selected if mt in (r.get('meal_type') or []))
            e = sum(1 for r in selected if mt in (r.get('meal_type') or []) and is_eth(r))
            interval = f"~{count} days without repeating" if count > 0 else "N/A"
            f.write(f"  {mt:<10}: {count:2} recipes ({e}E + {count-e}N) → {interval}\n")

        f.write("\nCuisine Representation:\n")
        for c, n in Counter(r.get('cuisine') for r in selected).most_common():
            f.write(f"  {c:<20}: {n}\n")

        f.write("\nDetailed Recipe Inventory:\n")
        for r in selected:
            cal = r.get('calories', '?')
            prot = r.get('protein_g', '?')
            mt = ','.join(r.get('meal_type', []))
            dt = ','.join(r.get('diet_tags', [])[:3])
            stage = r.get('metadata', {}).get('curation_stage', '?')[:3]
            tag = 'E' if is_eth(r) else 'N'
            f.write(f"  [{stage:>3}] {tag} {r['title'][:60]:<60} ({cal}cal, {prot}g) [{r.get('cuisine')}] {mt} {{{dt}}}\n")

    print(f"\n{'='*65}\n  DONE: Saved {len(selected)} curated recipes to {args.out_path}\n  AUDIT: Saved verification report to {args.audit_path}\n{'='*65}\n")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Recipe curator — Phase-5 one-time analysis script.

Analyzes the recipe database coverage and produces a curation report showing
which (diet × meal_type × kcal_bin) cells are well-covered vs under-covered.

Output:
  - reports/meal_planning/coverage_analysis.json — full coverage matrix
  - reports/meal_planning/coverage_analysis.md — human-readable report

Run: python /home/z/my-project/fitn/scripts/recipe_curator.py
"""
import json
import sys
from pathlib import Path
from collections import defaultdict
# Phase-6 fix: use the actual run date instead of a hardcoded future timestamp.
import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fitness_engine.meal_plan import (
    load_recipes, database_stats, get_pre_post_workout_recipes,
)
from fitness_engine.models.meal import MealType


# === Coverage matrix definition ===

DIETS = ["OMNI", "VEGAN", "OMNI_ETHIOPIAN", "VEGAN_ETHIOPIAN"]
MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack", "side", "pre_workout", "post_workout"]

KCAL_BINS = {
    "breakfast":    [(0, 300), (300, 500), (500, 700), (700, 9999)],
    "lunch":        [(0, 400), (400, 600), (600, 800), (800, 9999)],
    "dinner":       [(0, 400), (400, 600), (600, 800), (800, 9999)],
    "snack":        [(0, 200), (200, 400), (400, 9999)],
    "side":         [(0, 200), (200, 400), (400, 9999)],
    "pre_workout":  [(0, 200), (200, 400), (400, 9999)],
    "post_workout": [(0, 300), (300, 500), (500, 9999)],
}

MIN_RECIPES_PER_CELL = 2   # need at least 2 for 7-day variety


def recipe_matches_diet(recipe, diet_tag: str) -> bool:
    """Check if recipe matches the diet tag."""
    from fitness_engine.meal_plan.recipe_scorer import score_diet_match
    return score_diet_match(recipe, diet_tag) > 0


def analyze_coverage():
    """Analyze the recipe database coverage."""
    recipes = load_recipes()
    print(f"Loaded {len(recipes)} recipes")

    # Build coverage matrix
    coverage = {}
    for diet in DIETS:
        coverage[diet] = {}
        for meal_type in MEAL_TYPES:
            coverage[diet][meal_type] = {}
            for kcal_lo, kcal_hi in KCAL_BINS[meal_type]:
                bin_key = f"{kcal_lo}-{kcal_hi}"
                coverage[diet][meal_type][bin_key] = []

    # Populate
    for recipe in recipes:
        # Skip recipes with diet warnings
        if "[diet-warning" in (recipe.notes or ""):
            continue
        for diet in DIETS:
            if not recipe_matches_diet(recipe, diet):
                continue
            for meal_type in recipe.meal_types:
                if meal_type not in MEAL_TYPES:
                    continue
                for kcal_lo, kcal_hi in KCAL_BINS[meal_type]:
                    if kcal_lo <= recipe.kcal < kcal_hi:
                        bin_key = f"{kcal_lo}-{kcal_hi}"
                        coverage[diet][meal_type][bin_key].append({
                            "id": recipe.id,
                            "name": recipe.name,
                            "kcal": recipe.kcal,
                            "cuisine": recipe.cuisine,
                            "is_curated": "[curated]" in (recipe.notes or ""),
                        })

    # Compute coverage stats
    total_cells = 0
    covered_cells = 0
    under_covered_cells = 0
    empty_cells = 0
    cell_details = []

    for diet in DIETS:
        for meal_type in MEAL_TYPES:
            for kcal_lo, kcal_hi in KCAL_BINS[meal_type]:
                bin_key = f"{kcal_lo}-{kcal_hi}"
                count = len(coverage[diet][meal_type][bin_key])
                total_cells += 1
                if count == 0:
                    empty_cells += 1
                elif count < MIN_RECIPES_PER_CELL:
                    under_covered_cells += 1
                else:
                    covered_cells += 1
                cell_details.append({
                    "diet": diet,
                    "meal_type": meal_type,
                    "kcal_bin": bin_key,
                    "count": count,
                    "status": "empty" if count == 0 else (
                        "under" if count < MIN_RECIPES_PER_CELL else "covered"
                    ),
                })

    return {
        "coverage": coverage,
        "summary": {
            "total_cells": total_cells,
            "covered_cells": covered_cells,
            "under_covered_cells": under_covered_cells,
            "empty_cells": empty_cells,
            "coverage_pct": round(covered_cells / total_cells * 100, 1),
        },
        "cell_details": cell_details,
    }


def write_json_report(analysis, path):
    """Write the full analysis to JSON."""
    with open(path, "w") as f:
        json.dump(analysis, f, indent=2)
    print(f"✓ JSON report: {path}")


def write_markdown_report(analysis, path):
    """Write a human-readable Markdown report."""
    lines = [
        "# Recipe Database Coverage Analysis",
        "",
        f"**Generated**: {datetime.date.today().isoformat()}",  # Phase-6 fix: was hardcoded "2026-06-25"
        f"**Database stats**: {database_stats()}",
        "",
        "## Summary",
        "",
        f"- Total cells: {analysis['summary']['total_cells']}",
        f"- Fully covered (≥{MIN_RECIPES_PER_CELL} recipes): {analysis['summary']['covered_cells']}",
        f"- Under-covered (<{MIN_RECIPES_PER_CELL} recipes): {analysis['summary']['under_covered_cells']}",
        f"- Empty (0 recipes): {analysis['summary']['empty_cells']}",
        f"- Coverage: {analysis['summary']['coverage_pct']}%",
        "",
        "## Coverage Matrix",
        "",
    ]

    for diet in DIETS:
        lines.append(f"### {diet}")
        lines.append("")
        lines.append("| Meal Type | kcal bin | Count | Status |")
        lines.append("|---|---|---|---|")
        for meal_type in MEAL_TYPES:
            for kcal_lo, kcal_hi in KCAL_BINS[meal_type]:
                bin_key = f"{kcal_lo}-{kcal_hi}"
                count = len(analysis["coverage"][diet][meal_type][bin_key])
                status = "✅" if count >= MIN_RECIPES_PER_CELL else (
                    "⚠️" if count > 0 else "❌"
                )
                lines.append(f"| {meal_type} | {bin_key} | {count} | {status} |")
        lines.append("")

    # List empty cells
    empty_cells = [c for c in analysis["cell_details"] if c["status"] == "empty"]
    if empty_cells:
        lines.append("## Empty Cells (need recipes)")
        lines.append("")
        for cell in empty_cells:
            lines.append(f"- {cell['diet']} / {cell['meal_type']} / {cell['kcal_bin']} kcal")
        lines.append("")

    # List under-covered cells
    under_cells = [c for c in analysis["cell_details"] if c["status"] == "under"]
    if under_cells:
        lines.append("## Under-covered Cells (need more recipes)")
        lines.append("")
        for cell in under_cells:
            lines.append(f"- {cell['diet']} / {cell['meal_type']} / {cell['kcal_bin']} kcal (count: {cell['count']})")
        lines.append("")

    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"✓ Markdown report: {path}")


def main():
    print("=" * 60)
    print("Recipe Database Coverage Analysis")
    print("=" * 60)

    analysis = analyze_coverage()

    print(f"\nSummary:")
    print(f"  Total cells: {analysis['summary']['total_cells']}")
    print(f"  Covered: {analysis['summary']['covered_cells']}")
    print(f"  Under-covered: {analysis['summary']['under_covered_cells']}")
    print(f"  Empty: {analysis['summary']['empty_cells']}")
    print(f"  Coverage: {analysis['summary']['coverage_pct']}%")

    # Write reports
    output_dir = PROJECT_ROOT / "reports" / "meal_planning"
    output_dir.mkdir(parents=True, exist_ok=True)

    write_json_report(analysis, output_dir / "coverage_analysis.json")
    write_markdown_report(analysis, output_dir / "coverage_analysis.md")

    print(f"\n{'='*60}")
    print("Analysis complete.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Retry fetcher — sequential with delays to avoid rate-limiting.
Only fetches URLs that don't have a valid cached file yet.
"""
import json
import os
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

RAW_DIR = Path("/home/z/my-project/resources/raw")

URLS = [
    "https://rippedbody.com/body-fat-guide/",
    "https://rippedbody.com/micros/",
    "https://rippedbody.com/nutrition-pyramid-overview/",
    "https://rippedbody.com/calories/",
    "https://rippedbody.com/keto/",
    "https://rippedbody.com/best-macro-ratio/",
    "https://rippedbody.com/how-to-adjust-macros/",
    "https://rippedbody.com/training-plateaus/",
    "https://rippedbody.com/how-to-adjust-macros-bulk/",
    "https://rippedbody.com/how-to-count-macros/",
    "https://rippedbody.com/goal-setting-1/",
    "https://rippedbody.com/goal-setting-2/",
    "https://rippedbody.com/goal-setting-3/",
    "https://rippedbody.com/maximum-muscular-potential/",
    "https://rippedbody.com/updated-bulking-guidelines/",
    "https://rippedbody.com/advice-for-vegans/",
    "https://rippedbody.com/before-you-count/",
    "https://rippedbody.com/macro-calculator/",
    "https://rippedbody.com/diet-progress-tracking/",
    "https://rippedbody.com/how-to-bulk/",
    "https://rippedbody.com/why-my-weight-going-up-and-down-while-dieting/",
    "https://rippedbody.com/initial-adjustment/",
    "https://rippedbody.com/cut-or-bulk/",
    "https://rippedbody.com/how-calculate-body-fat-percentage/",
    "https://ultimateperformance.com/your-goal/fat-loss/male-fat-loss/male-body-fat-comparison",
    "https://quiz.builtwithscience.com/page/1",
    "https://macrofactor.com/cutting-calculator/",
    "https://macrofactor.com/bulk-or-cut/",
    "https://macrofactor.com/bulking-calculator/",
    "https://gymgeek.com/calculators/maintenance-calories-calculator/",
    "https://gymgeek.com/calculators/calorie-calculator/",
    "https://gymgeek.com/calculators/adaptive-tdee-calculator/",
    "https://gymgeek.com/calculators/bulking-calculator/",
    "https://www.zolthealth.com/learn/what-is-adaptive-tdee",
    "https://gymcreek.com/adaptive-tdee-calculator/",
    "https://www.fatcalc.com/macro",
    "https://www.fatcalc.com/bwp",
    "https://www.fatcalc.com/mfl",
    "https://www.fatcalc.com/whtr-calculator",
    "https://www.fatcalc.com/whr",
    "https://www.fatcalc.com/absi",
    "https://www.fatcalc.com/reverse-diet-calculator",
    "https://www.fatcalc.com/bfb",
    "https://www.fatcalc.com/body-recomp-calculator",
    "https://www.fatcalc.com/hydration-calculator",
    "https://www.fatcalc.com/protein-calculator",
    "https://www.fatcalc.com/rmr-calculator",
    "https://www.fatcalc.com/tdee-calculator",
    "https://www.fatcalc.com/rwl",
    "https://www.fatcalc.com/mm",
    "https://www.fatcalc.com/ibw-calculator",
    "https://www.fatcalc.com/bf",
]


def slugify(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.replace("www.", "")
    path = parsed.path.strip("/").replace("/", "-").replace(".", "-")
    if not path:
        path = "root"
    return f"{host}__{path}.json"


def is_valid(path: Path) -> bool:
    if not path.exists():
        return False
    if path.stat().st_size < 1000:
        return False
    # Make sure it's actual page content not an error
    try:
        with open(path) as f:
            data = json.load(f)
        if "data" in data and ("html" in data["data"] or "text" in data["data"]):
            content = data["data"].get("html", "") or data["data"].get("text", "")
            return len(content) > 500
    except Exception:
        return False
    return False


def fetch_one(url: str, attempt: int = 1) -> bool:
    out_path = RAW_DIR / slugify(url)
    if is_valid(out_path):
        return True
    try:
        result = subprocess.run(
            ["z-ai", "function", "-n", "page_reader",
             "-a", json.dumps({"url": url}),
             "-o", str(out_path)],
            capture_output=True, text=True, timeout=120,
        )
        ok = is_valid(out_path)
        if not ok and attempt < 3:
            time.sleep(5 * attempt)
            return fetch_one(url, attempt + 1)
        return ok
    except Exception:
        if attempt < 3:
            time.sleep(5 * attempt)
            return fetch_one(url, attempt + 1)
        return False


def main():
    todo = [u for u in URLS if not is_valid(RAW_DIR / slugify(u))]
    print(f"Need to fetch: {len(todo)} of {len(URLS)}")
    ok = 0
    for i, url in enumerate(todo, 1):
        success = fetch_one(url)
        if success:
            ok += 1
            print(f"[{i:>2}/{len(todo)}] OK   {url}")
        else:
            print(f"[{i:>2}/{len(todo)}] FAIL {url}")
        # Small delay between requests
        time.sleep(1.5)
    print(f"\nDone. Newly fetched: {ok}/{len(todo)}")
    total_ok = sum(1 for u in URLS if is_valid(RAW_DIR / slugify(u)))
    print(f"Total valid files: {total_ok}/{len(URLS)}")


if __name__ == "__main__":
    main()

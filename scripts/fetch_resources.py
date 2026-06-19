#!/usr/bin/env python3
"""
Parallel fetcher for all fitness engine source URLs.
Uses z-ai CLI page_reader in parallel batches to avoid timeouts.
Saves each result as a JSON file under /home/z/my-project/resources/raw/.
"""
import json
import os
import subprocess
import concurrent.futures
from pathlib import Path
from urllib.parse import urlparse

RAW_DIR = Path("/home/z/my-project/resources/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# All source URLs (de-duplicated)
URLS = [
    # RippedBody
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
    # Ultimate Performance
    "https://ultimateperformance.com/your-goal/fat-loss/male-fat-loss/male-body-fat-comparison",
    # Built With Science (quiz page)
    "https://quiz.builtwithscience.com/page/1",
    # MacroFactor
    "https://macrofactor.com/cutting-calculator/",
    "https://macrofactor.com/bulk-or-cut/",
    "https://macrofactor.com/bulking-calculator/",
    # GymGeek
    "https://gymgeek.com/calculators/maintenance-calories-calculator/",
    "https://gymgeek.com/calculators/calorie-calculator/",
    "https://gymgeek.com/calculators/adaptive-tdee-calculator/",
    "https://gymgeek.com/calculators/bulking-calculator/",
    # Zolthealth
    "https://www.zolthealth.com/learn/what-is-adaptive-tdee",
    # GymCreek
    "https://gymcreek.com/adaptive-tdee-calculator/",
    # FatCalc
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
    """Convert URL to safe filename like rippedbody__body-fat-guide.json"""
    parsed = urlparse(url)
    host = parsed.netloc.replace("www.", "")
    path = parsed.path.strip("/").replace("/", "-").replace(".", "-")
    if not path:
        path = "root"
    return f"{host}__{path}.json"


def fetch_one(url: str) -> dict:
    out_path = RAW_DIR / slugify(url)
    if out_path.exists() and out_path.stat().st_size > 1000:
        return {"url": url, "ok": True, "path": str(out_path), "cached": True}

    try:
        result = subprocess.run(
            ["z-ai", "function", "-n", "page_reader",
             "-a", json.dumps({"url": url}),
             "-o", str(out_path)],
            capture_output=True, text=True, timeout=90,
        )
        ok = out_path.exists() and out_path.stat().st_size > 500
        return {
            "url": url, "ok": ok, "path": str(out_path),
            "stderr": result.stderr[:300] if not ok else "",
            "cached": False,
        }
    except subprocess.TimeoutExpired:
        return {"url": url, "ok": False, "path": str(out_path),
                "stderr": "timeout", "cached": False}
    except Exception as e:
        return {"url": url, "ok": False, "path": str(out_path),
                "stderr": str(e)[:300], "cached": False}


def main():
    print(f"Fetching {len(URLS)} URLs with concurrency=8...")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for i, r in enumerate(pool.map(fetch_one, URLS), 1):
            results.append(r)
            status = "OK" if r["ok"] else "FAIL"
            print(f"[{i:>2}/{len(URLS)}] {status}: {r['url']}")
    # Summary
    ok_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - ok_count
    print(f"\n=== SUMMARY ===")
    print(f"Succeeded: {ok_count}/{len(results)}")
    print(f"Failed:    {fail_count}/{len(results)}")
    if fail_count:
        print("\nFailures:")
        for r in results:
            if not r["ok"]:
                print(f"  - {r['url']} :: {r.get('stderr','')}")
    # Write manifest
    manifest_path = RAW_DIR / "_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nManifest saved: {manifest_path}")


if __name__ == "__main__":
    main()

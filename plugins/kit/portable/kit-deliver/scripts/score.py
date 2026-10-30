"""Score measured alternatives against explicit bounds, weights and thresholds.

Usage: python score.py comparison.json
Input: {"criteria": [{"name": "latency", "direction": "min", "lower": 0,
"upper": 100, "weight": 1, "threshold": 50}], "options": [{"name": "A",
"metrics": {"latency": {"value": 30, "evidence": "benchmark command"}}}]}
Thresholds are optional; all metrics and evidence are required for a comparable score.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List


def number(value: Any) -> bool:
    try:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    except OverflowError:
        return False


def score(data: Dict[str, Any]) -> Dict[str, Any]:
    criteria, options = data.get("criteria"), data.get("options")
    if not isinstance(criteria, list) or not criteria or not isinstance(options, list) or not options:
        raise ValueError("criteria and options must be nonempty lists")
    names = set()
    for c in criteria:
        if not isinstance(c, dict) or not isinstance(c.get("name"), str) or not c["name"].strip():
            raise ValueError("each criterion needs a name")
        if c["name"] in names:
            raise ValueError("criterion names must be unique")
        names.add(c["name"])
        if c.get("direction") not in ("min", "max"):
            raise ValueError("direction must be min or max")
        if not all(number(c.get(k)) for k in ("lower", "upper", "weight")):
            raise ValueError("bounds and weight must be finite numbers")
        if (c["lower"] >= c["upper"] or c["weight"] <= 0
                or not math.isfinite(c["upper"] - c["lower"])):
            raise ValueError("bounds must increase and weights must be positive")
        if "threshold" in c and not number(c["threshold"]):
            raise ValueError("threshold must be a finite number")
    if not math.isfinite(sum(c["weight"] for c in criteria)):
        raise ValueError("total weight must be finite")
    results: List[Dict[str, Any]] = []
    seen = set()
    for option in options:
        if not isinstance(option, dict) or not isinstance(option.get("name"), str) or not option["name"].strip():
            raise ValueError("each option needs a name")
        if option["name"] in seen:
            raise ValueError("option names must be unique")
        seen.add(option["name"])
        metrics = option.get("metrics")
        if not isinstance(metrics, dict):
            raise ValueError("metrics must be an object")
        missing, failed, details = [], [], []
        total = 0.0
        for c in criteria:
            m = metrics.get(c["name"])
            if (not isinstance(m, dict) or not number(m.get("value"))
                    or not isinstance(m.get("evidence"), str) or not m["evidence"].strip()):
                missing.append(c["name"])
                continue
            value = m["value"]
            bound = max(c["lower"], min(c["upper"], value))
            unit = (bound - c["lower"]) / (c["upper"] - c["lower"])
            if c["direction"] == "min":
                unit = 1.0 - unit
            if "threshold" in c and ((c["direction"] == "min" and value > c["threshold"])
                                     or (c["direction"] == "max" and value < c["threshold"])):
                failed.append(c["name"])
            total += unit * c["weight"]
            details.append({"criterion": c["name"], "value": value, "evidence": m["evidence"],
                            "score": round(unit * 100, 2)})
        status = "incomplete" if missing else "ineligible" if failed else "eligible"
        result = {"name": option["name"], "status": status, "missing": missing,
                  "failed_thresholds": failed, "metrics": details}
        if not missing:
            result["score"] = round((total / sum(c["weight"] for c in criteria)) * 100, 2)
        results.append(result)
    ranked = sorted((r for r in results if r["status"] == "eligible"), key=lambda r: -r["score"])
    return {"options": results, "ranked_eligible": [r["name"] for r in ranked]}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: score.py comparison.json", file=sys.stderr)
        return 2
    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("comparison must be an object")
        result = score(data)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0 if result["ranked_eligible"] else 1
    except (OSError, ValueError, TypeError) as exc:
        print(f"score: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

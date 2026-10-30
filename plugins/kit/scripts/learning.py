"""Evaluate and promote reusable skill candidates against a trusted local suite.

Each suite case runs in separate temporary copies of its fixture, once without and once
with the candidate. Commands are argument arrays. Suite commands execute as the user;
only run suites you trust. No model or network calls are performed by this script.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_skill_name(skill: Path, expected: str) -> None:
    """Require one frontmatter name matching the candidate/install directory."""
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = text.split("---\n", 2)
    names = []
    if len(frontmatter) >= 3 and frontmatter[0] == "":
        for line in frontmatter[1].splitlines():
            key, sep, value = line.partition(":")
            if sep and key.strip() == "name":
                value = value.split("#", 1)[0].strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                names.append(value)
    if names != [expected]:
        raise ValueError(f"skill name must match {expected!r}: {skill}")


def validate_candidate(candidate: Path) -> Dict[str, Any]:
    candidate = candidate.resolve()
    meta = json.loads((candidate / "candidate.json").read_text(encoding="utf-8"))
    if not isinstance(meta, dict) or not isinstance(meta.get("name"), str) or not NAME.fullmatch(meta["name"]):
        raise ValueError("candidate name must be lowercase kebab-case")
    for field in ("purpose", "applies_when", "not_for", "evidence"):
        if not isinstance(meta.get(field), str) or not meta[field].strip():
            raise ValueError(f"candidate requires nonempty {field}")
    skill = candidate / "skill"
    if not (skill / "SKILL.md").is_file():
        raise ValueError("candidate requires skill/SKILL.md")
    if any(p.is_symlink() for p in candidate.rglob("*")):
        raise ValueError("candidate must not contain symlinks")
    validate_skill_name(skill, meta["name"])
    return meta


def evaluate(candidate: Path, suite_path: Path) -> Dict[str, Any]:
    meta = validate_candidate(candidate)
    suite_path = suite_path.resolve()
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    cases = suite.get("cases") if isinstance(suite, dict) else None
    if not isinstance(cases, list) or not cases:
        raise ValueError("suite must contain cases")
    results: List[Dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("case must be an object")
        name, argv = case.get("name"), case.get("argv")
        if not isinstance(name, str) or not name or not isinstance(argv, list) or not argv or not all(
            isinstance(arg, str) and arg for arg in argv
        ):
            raise ValueError("case requires a name and nonempty argv")
        fixture = (suite_path.parent / case.get("fixture", ".")).resolve()
        try:
            fixture.relative_to(suite_path.parent)
        except ValueError as exc:
            raise ValueError("fixture must be inside the suite directory") from exc
        if not fixture.is_dir() or any(p.is_symlink() for p in fixture.rglob("*")):
            raise ValueError("fixture must be a directory without symlinks")
        timeout = int(case.get("timeout_s", 30))
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        exits = []
        for enabled in (False, True):
            with tempfile.TemporaryDirectory(prefix="kit-learning-") as tmp:
                work = Path(tmp) / "work"
                shutil.copytree(fixture, work)
                env = dict(os.environ)
                if enabled:
                    skill_copy = Path(tmp) / "skill"
                    shutil.copytree(candidate / "skill", skill_copy, symlinks=True)
                    env["KIT_CANDIDATE_DIR"] = str(skill_copy)
                else:
                    env["KIT_CANDIDATE_DIR"] = ""
                try:
                    proc = subprocess.run(argv, cwd=str(work), env=env, stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL, timeout=timeout, check=False)
                except (OSError, subprocess.SubprocessError) as exc:
                    raise ValueError(f"case {name} could not run: {exc}") from exc
                exits.append(proc.returncode)
        results.append({"name": name, "baseline_passed": exits[0] == 0, "candidate_passed": exits[1] == 0})
    regressions = [r["name"] for r in results if r["baseline_passed"] and not r["candidate_passed"]]
    improvements = [r["name"] for r in results if not r["baseline_passed"] and r["candidate_passed"]]
    unresolved = [r["name"] for r in results if not r["candidate_passed"]]
    preserved = [r["name"] for r in results if r["baseline_passed"] and r["candidate_passed"]]
    return {"candidate": meta["name"], "cases": results, "improvements": improvements,
            "regressions": regressions, "unresolved": unresolved, "preserved": preserved,
            "passed": bool(improvements) and bool(preserved) and not unresolved and not regressions}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("evaluate", "promote"))
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--suite", type=Path, required=True, help="trusted independent JSON suite")
    parser.add_argument("--destination", type=Path, help="skill directory; required for promote")
    args = parser.parse_args()
    try:
        validate_candidate(args.candidate)
        with tempfile.TemporaryDirectory(prefix="kit-candidate-") as tmp:
            snapshot = Path(tmp) / "candidate"
            shutil.copytree(args.candidate, snapshot, symlinks=True)
            result = evaluate(snapshot, args.suite)
            if args.action == "promote" and result["passed"]:
                if args.destination is None:
                    raise ValueError("promote requires --destination")
                target = args.destination / result["candidate"]
                if target.exists() or target.is_symlink():
                    raise ValueError(f"destination already exists: {target}")
                args.destination.mkdir(parents=True, exist_ok=True)
                shutil.copytree(snapshot / "skill", target, symlinks=False)
                result["promoted_to"] = str(target)
        print(json.dumps(result, indent=2))
        return 0 if result["passed"] else 1
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"learning: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

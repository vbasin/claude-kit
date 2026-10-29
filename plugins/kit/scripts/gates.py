"""Run repository-defined verification gates without a shell (Python 3.8+)."""
from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

from kit_common import run, tail


def run_gates(root: Path, config: Dict[str, Any], changed: List[str]) -> Tuple[List[str], List[str]]:
    profile = config.get("verification", {})
    if not isinstance(profile, dict):
        return ["verification must be an object"], []
    if not profile.get("enabled", False):
        return [], []
    gates = profile.get("gates")
    if not isinstance(gates, list) or not gates:
        return ["verification is enabled but no gates are configured"], []
    failures: List[str] = []
    ran: List[str] = []
    covered = set()
    for gate in gates:
        if not isinstance(gate, dict):
            failures.append("invalid gate: expected an object")
            continue
        name = gate.get("name")
        paths = gate.get("paths")
        argv = gate.get("argv")
        if (not isinstance(name, str) or not name or not isinstance(paths, list) or not paths
                or not all(isinstance(p, str) and p for p in paths)
                or not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv)):
            failures.append("invalid gate: name, paths, and argv are required")
            continue
        matches = {f for f in changed if any(fnmatch.fnmatchcase(f, pattern) for pattern in paths)}
        if not matches:
            continue
        covered.update(matches)
        cwd = (root / gate.get("cwd", ".")).resolve()
        try:
            cwd.relative_to(root.resolve())
            timeout = int(gate.get("timeout_s", 300))
            if timeout <= 0:
                raise ValueError("timeout must be positive")
            result = run(argv, cwd, timeout)
            ran.append(name)
            if result.returncode:
                output = tail(result.stdout + result.stderr)
                failures.append(f"Gate {name} failed (exit {result.returncode}):\n{output}")
        except (OSError, ValueError, TypeError, subprocess.SubprocessError) as exc:
            failures.append(f"Gate {name} unavailable: {exc}")
    uncovered = sorted(set(changed) - covered)
    if uncovered:
        failures.append("No configured gate covers: " + ", ".join(uncovered))
    return failures, ran

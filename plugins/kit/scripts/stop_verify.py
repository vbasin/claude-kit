"""Stop: lint and test what this session changed before Claude may finish.

Runs only when the repo opts in through `.claude/kit.json` (`lint.enabled`, `tests.enabled`).
Scope is the session's own changes: files edited through Claude's tools plus anything
that changed on disk or in commits since SessionStart, deletions included. Tests are
picked per changed file (its own test file, `test_<module>*.py`, test files that import
it, and for a `conftest.py` the test files beneath it), capped at `tests.max_files`,
minus any `tests.exclude` globs (e.g. tests that need another virtualenv), and always
passed to pytest as explicit paths, never as a whole suite. Each pytest run gets an
empty bytecode cache, so a stale `.pyc` can't stand in for the edited source.

Loop safety: a failure blocks the stop once. If Claude tries to stop again with the
same failure, the stop is allowed and the user sees a notice instead, so a
pre-existing failure can't trap the session.

Manual use (the `kit:verify` skill): `python3 stop_verify.py --manual [FILE ...]`
checks the given files, or every dirty file when none are given, and prints a report.
"""

from __future__ import annotations

import ast
import fnmatch
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from kit_common import (
    changed_since,
    dirty_files,
    emit,
    file_digest,
    load_config,
    load_state,
    read_input,
    relative_to_root,
    repo_root,
    resolve_python,
    run,
    run_lint,
    save_state,
    tail,
)

PYTEST_NO_TESTS = 5


def _is_test_file(rel: str, test_dirs: List[str]) -> bool:
    name = Path(rel).name
    in_dir = any(rel == d or rel.startswith(d.rstrip("/") + "/") for d in test_dirs)
    return in_dir and name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py"))


DOTTED = re.compile(r"[A-Za-z_]\w*(?:\.\w+)+")
IMPORT_FALLBACK = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import\s+\(?([\w\s,]+)|import\s+([\w.]+))", re.M)


def imported_names(source: str) -> Set[str]:
    """Dotted names a test refers to: imported modules, `module.name` for each from-import,
    and dotted strings under an imported package, such as `mock.patch("pkg.mod.func")`."""
    names: Set[str] = set()
    strings: Set[str] = set()
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        for mod, members, plain in IMPORT_FALLBACK.findall(source):
            if plain:
                names.add(plain)
            else:
                names.add(mod)
                names.update(f"{mod}.{m.strip()}" for m in members.split(",") if m.strip())
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and DOTTED.fullmatch(node.value):
            strings.add(node.value)
    packages = {n.split(".", 1)[0] for n in names}
    names.update(s for s in strings if s.split(".", 1)[0] in packages)
    return names


def _refers_to(names: Set[str], module: str) -> bool:
    prefix = module + "."
    return any(n == module or n.startswith(prefix) for n in names)


def find_tests(root: Path, changed_py: List[str], tests_cfg: Dict[str, Any]) -> Tuple[List[str], int]:
    """Explicit test paths for the changed files, and how many more were found but capped.

    Changed files may have been deleted: their tests are exactly the ones that should fail.
    """
    test_dirs = [d.strip("/") for d in tests_cfg.get("test_dirs", ["tests"])]
    strip_roots = set(tests_cfg.get("import_roots", ["src"]))
    all_tests: List[str] = []
    for d in test_dirs:
        base = root / d
        if base.is_dir():
            all_tests.extend(
                p.relative_to(root).as_posix()
                for p in sorted(base.rglob("*.py"))
                if p.name.startswith("test_") or p.name.endswith("_test.py")
            )
    parsed: Dict[str, Set[str]] = {}

    def refs(rel: str) -> Set[str]:
        if rel not in parsed:
            try:
                parsed[rel] = imported_names((root / rel).read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                parsed[rel] = set()
        return parsed[rel]

    direct = [rel for rel in changed_py if _is_test_file(rel, test_dirs)]
    by_name: List[str] = []
    by_import: List[str] = []
    by_conftest: List[str] = []
    for rel in changed_py:
        if rel in direct:
            continue
        if Path(rel).name == "conftest.py":
            scope = Path(rel).parent.as_posix()
            by_conftest.extend(t for t in all_tests if scope == "." or t.startswith(scope + "/"))
            continue
        parts = list(Path(rel).with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        if not parts:
            continue
        stem = parts[-1]
        dotted = [".".join(parts)]
        if parts[0] in strip_roots and len(parts) > 1:
            dotted.append(".".join(parts[1:]))
        for t in all_tests:
            tname = Path(t).stem
            if tname == f"test_{stem}" or tname.startswith(f"test_{stem}_"):
                by_name.append(t)
            elif any(_refers_to(refs(t), d) for d in dotted):
                by_import.append(t)

    excluded = tests_cfg.get("exclude", []) or []
    selected: List[str] = []
    for rel in direct + by_name + by_import + by_conftest:
        if rel in selected or not (root / rel).is_file():
            continue
        if any(fnmatch.fnmatch(rel, pat) for pat in excluded):
            continue
        selected.append(rel)
    cap = int(tests_cfg.get("max_files", 8))
    return selected[:cap], max(0, len(selected) - cap)


def lint_files(root: Path, python: str, cfg: Dict[str, Any], files: List[str]) -> Optional[str]:
    lint = cfg.get("lint", {})
    if not lint.get("enabled") or not files:
        return None
    try:
        return run_lint(root, python, lint.get("args", []), files)
    except (OSError, subprocess.SubprocessError) as exc:
        return f"lint could not run: {exc}"


def run_tests(root: Path, python: str, cfg: Dict[str, Any], tests: List[str]) -> Optional[str]:
    tcfg = cfg.get("tests", {})
    if not tcfg.get("enabled") or not tests:
        return None
    cmd = [python, "-m", "pytest", *tcfg.get("pytest_args", []), *tests]
    # An empty bytecode cache per run: a same-size edit within the mtime resolution of an
    # existing __pycache__ entry would otherwise run the old code and pass.
    cache = tempfile.mkdtemp(prefix="kit-pycache-")
    env = {"PYTHONPYCACHEPREFIX": cache, "PYTHONDONTWRITEBYTECODE": "1", **(tcfg.get("env") or {})}
    try:
        proc = run(
            cmd, root, timeout=int(tcfg.get("timeout_s", 300)),
            env_file=tcfg.get("env_file"), extra_env=env,
        )
    except subprocess.TimeoutExpired:
        return f"pytest timed out after {tcfg.get('timeout_s', 300)}s on: {' '.join(tests)}"
    except OSError as exc:
        return f"pytest could not run: {exc}"
    finally:
        shutil.rmtree(cache, ignore_errors=True)
    if proc.returncode in (0, PYTEST_NO_TESTS):
        return None
    if "No module named pytest" in proc.stderr:
        return (f"pytest is not installed for {python}, so no tests ran. Install it there, point "
                "`python` in .claude/kit.json at an interpreter that has it, or set tests.enabled to false.")
    return tail(proc.stdout + proc.stderr, max_lines=60)


def verify(root: Path, cfg: Dict[str, Any], changed: List[str]) -> Tuple[List[str], List[str], int]:
    """Return (failure sections, tests run, tests capped)."""
    python = resolve_python(cfg, root)
    changed_py = [f for f in changed if f.endswith(".py")]
    if python is None or not changed_py:
        return [], [], 0
    failures: List[str] = []
    lint_out = lint_files(root, python, cfg, [f for f in changed_py if (root / f).is_file()])
    if lint_out:
        failures.append(f"Lint ({' '.join(cfg['lint'].get('args', []))}):\n{lint_out}")
    tests: List[str] = []
    capped = 0
    if cfg.get("tests", {}).get("enabled"):
        tests, capped = find_tests(root, changed_py, cfg.get("tests", {}))
    test_out = run_tests(root, python, cfg, tests)
    if test_out:
        failures.append(f"Tests (pytest {' '.join(tests)}):\n{test_out}")
    return failures, tests, capped


def _digest(root: Path, files: List[str]) -> str:
    h = hashlib.sha256()
    for rel in files:
        h.update(rel.encode())
        h.update((file_digest(root / rel) or "-").encode())
    return h.hexdigest()


def hook_main() -> int:
    data = read_input()
    session_id = str(data.get("session_id") or "")
    root = repo_root(data.get("cwd"))
    if root is None or not session_id:
        return 0
    cfg = load_config(root)
    if not (cfg.get("lint", {}).get("enabled") or cfg.get("tests", {}).get("enabled")):
        return 0
    state = load_state(session_id)
    changed = changed_since(root, state.get("baseline", {}), state.get("edited", []))
    changed = [f for f in changed if f.endswith(".py")]
    if not changed:
        return 0
    digest = _digest(root, changed)
    if state.get("passed_digest") == digest:
        return 0  # nothing changed since the last clean run

    failures, tests, capped = verify(root, cfg, changed)
    if not failures:
        state["passed_digest"] = digest
        state.pop("failed_digest", None)
        save_state(session_id, state)
        return 0

    if data.get("stop_hook_active") and state.get("failed_digest") == digest:
        emit({"systemMessage": "kit verify: still failing after one retry; letting Claude stop. "
              "Check the last reply for whether the failure predates this session."})
        return 0
    state["failed_digest"] = digest
    save_state(session_id, state)
    note = ""
    if capped:
        note = f"\n({capped} more related test files were not run; use the repo's scoped gate for broader coverage.)"
    # additionalContext keeps Claude going like decision=block, but reads as feedback, not a hook error.
    emit({"hookSpecificOutput": {
        "hookEventName": "Stop",
        "additionalContext": "Verification of the files changed in this session failed (kit Stop hook).\n\n"
        + "\n\n".join(failures) + note
        + "\n\nFix what your change broke, then finish. If a failure predates your change and is unrelated, "
        "say so plainly in your reply instead of fixing it. Do not run the whole test suite to check.",
    }})
    return 0


def manual_main(files: List[str]) -> int:
    root = repo_root(None)
    if root is None:
        print("kit verify: not inside a git repository")
        return 2
    cfg = load_config(root)
    changed = [relative_to_root(root, f) or f for f in files] or dirty_files(root, include_deleted=True)
    failures, tests, capped = verify(root, cfg, changed)
    py = [f for f in changed if f.endswith(".py")]
    print(f"kit verify: {len(py)} changed Python file(s); tests run: {' '.join(tests) or 'none'}")
    if capped:
        print(f"  ({capped} more related test files not run; cap is tests.max_files)")
    if not (cfg.get("lint", {}).get("enabled") or cfg.get("tests", {}).get("enabled")):
        print("  lint and tests are disabled: add .claude/kit.json to this repo to enable them")
    if failures:
        print("\n\n".join(failures))
        return 1
    print("kit verify: OK")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        sys.exit(manual_main(sys.argv[2:]))
    try:
        sys.exit(hook_main())
    except Exception:  # noqa: BLE001 — a hook must never break the session
        sys.exit(0)

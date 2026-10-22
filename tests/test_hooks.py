"""End-to-end tests for the kit plugin's hook scripts.

Each test builds a throwaway git repo, feeds the hook the JSON Claude Code would send
on stdin, and checks what the hook prints. Requires pytest and ruff in the interpreter
running the tests (`pip install pytest ruff`).
"""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins" / "kit" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from bash_guard import check, is_full_suite  # noqa: E402
from stop_verify import find_tests  # noqa: E402


def hook(script: str, payload: dict, data_dir: Path) -> dict:
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / script)],
        input=json.dumps(payload), capture_output=True, text=True, timeout=120,
        env={"CLAUDE_PLUGIN_DATA": str(data_dir), "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout) if proc.stdout.strip() else {}


def sh(cwd: Path, *args: str) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "src" / "pkg").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / ".claude").mkdir()
    (root / "src" / "pkg" / "__init__.py").write_text("")
    (root / "src" / "pkg" / "mathx.py").write_text("def double(x):\n    return x * 2\n")
    (root / "src" / "pkg" / "other.py").write_text("def other():\n    return 1\n")
    (root / "tests" / "test_mathx.py").write_text(
        "from pkg.mathx import double\n\ndef test_double():\n    assert double(2) == 4\n"
    )
    (root / "tests" / "test_uses_import.py").write_text(
        "from pkg import mathx\n\ndef test_via_import():\n    assert mathx.double(1) == 2\n"
    )
    (root / "tests" / "test_unrelated.py").write_text("def test_ok():\n    assert True\n")
    (root / "pyproject.toml").write_text('[tool.pytest.ini_options]\npythonpath = [".", "src"]\n')
    (root / ".claude" / "kit.json").write_text(json.dumps({
        "python": [sys.executable],
        "lint": {
            "enabled": True,
            "args": ["-m", "ruff", "check", "--select", "E9,F63,F7,F82", "--output-format", "concise"],
        },
        "tests": {"enabled": True, "test_dirs": ["tests"], "import_roots": ["src"]},
        "guards": {"pytest_full_suite": "ask"},
    }))
    sh(root, "git", "init", "-q")
    sh(root, "git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    sh(root, "git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    return root


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    d = tmp_path / "plugin-data"
    d.mkdir()
    return d


# ── bash guard ─────────────────────────────────────────────────────────────────
CFG = {"guards": {"sql_destructive": "ask", "pytest_full_suite": "ask"}, "tests": {"test_dirs": ["tests"]}}


@pytest.mark.parametrize("command", [
    'psql -c "DROP TABLE prices"',
    "psql -c 'TRUNCATE ticks'",
    'psql -c "DELETE FROM ticks;"',
    "python -c \"conn.execute('SELECT drop_chunks(\\'ticks\\', older_than => now())')\"",
    "pytest",
    "pytest -q",
    "python -m pytest tests/",
    "cd /opt/app && PYTHONPATH=. timeout 300 python -m pytest -k foo tests",
    "pytest -m slow",
    "uv run pytest --tb=short",
])
def test_guard_asks(command: str) -> None:
    hit = check(command, CFG)
    assert hit is not None and hit[0] == "ask", command


@pytest.mark.parametrize("command", [
    "pip install pytest",
    "pytest tests/test_mathx.py",
    "python -m pytest -x tests/test_a.py::test_b",
    "pytest --collect-only -q",
    "pytest tests/architecture",
    'psql -c "DELETE FROM ticks WHERE ts < now()"',
    "make test-acquisition",
    "grep -r pytest .",
])
def test_guard_allows(command: str) -> None:
    assert check(command, CFG) is None, command


def test_full_suite_guard_off_by_default() -> None:
    assert check("pytest", {"guards": {}, "tests": {}}) is None
    assert is_full_suite("pytest", ["tests"])


def test_guard_hook_output(repo: Path, data_dir: Path) -> None:
    out = hook("bash_guard.py", {"cwd": str(repo), "tool_input": {"command": "pytest"}}, data_dir)
    assert out["hookSpecificOutput"]["permissionDecision"] == "ask"
    assert hook("bash_guard.py", {"cwd": str(repo), "tool_input": {"command": "ls"}}, data_dir) == {}


# ── test selection ─────────────────────────────────────────────────────────────
def test_find_tests_by_name_and_import(repo: Path) -> None:
    tests, capped = find_tests(repo, ["src/pkg/mathx.py"], {"test_dirs": ["tests"], "import_roots": ["src"]})
    assert tests == ["tests/test_mathx.py", "tests/test_uses_import.py"]
    assert capped == 0


def test_find_tests_changed_test_file_and_cap(repo: Path) -> None:
    tests, capped = find_tests(
        repo, ["tests/test_unrelated.py", "src/pkg/mathx.py"], {"test_dirs": ["tests"], "max_files": 2}
    )
    assert tests == ["tests/test_unrelated.py", "tests/test_mathx.py"]
    assert capped == 1


def test_find_tests_exclude(repo: Path) -> None:
    tests, _ = find_tests(
        repo, ["src/pkg/mathx.py"], {"test_dirs": ["tests"], "import_roots": ["src"], "exclude": ["tests/test_uses_*"]}
    )
    assert tests == ["tests/test_mathx.py"]


# ── session flow ───────────────────────────────────────────────────────────────
def test_stop_blocks_once_then_lets_go(repo: Path, data_dir: Path) -> None:
    sid = str(uuid.uuid4())
    base = {"session_id": sid, "cwd": str(repo)}
    hook("session_start.py", {**base, "source": "startup"}, data_dir)

    target = repo / "src" / "pkg" / "mathx.py"
    target.write_text("def double(x):\n    return x * 3\n")
    hook("post_edit.py", {**base, "tool_name": "Edit", "tool_input": {"file_path": str(target)}}, data_dir)

    first = hook("stop_verify.py", {**base, "stop_hook_active": False}, data_dir)
    feedback = first["hookSpecificOutput"]["additionalContext"]
    assert "tests/test_mathx.py" in feedback and "assert 6 == 4" in feedback
    assert "test_unrelated" not in feedback

    again = hook("stop_verify.py", {**base, "stop_hook_active": True}, data_dir)
    assert "hookSpecificOutput" not in again and "still failing" in again["systemMessage"]

    target.write_text("def double(x):\n    return x * 2\n")
    assert hook("stop_verify.py", {**base, "stop_hook_active": True}, data_dir) == {}


def test_preexisting_dirty_file_is_ignored(repo: Path, data_dir: Path) -> None:
    (repo / "src" / "pkg" / "mathx.py").write_text("def double(x):\n    return x * 3\n")  # broken before the session
    sid = str(uuid.uuid4())
    base = {"session_id": sid, "cwd": str(repo)}
    hook("session_start.py", {**base, "source": "startup"}, data_dir)
    assert hook("stop_verify.py", {**base, "stop_hook_active": False}, data_dir) == {}

    other = repo / "src" / "pkg" / "other.py"
    other.write_text("def other():\n    return 2\n")  # changed via Bash, not an Edit tool
    assert hook("stop_verify.py", {**base, "stop_hook_active": False}, data_dir) == {}


def test_post_edit_reports_lint_errors(repo: Path, data_dir: Path) -> None:
    target = repo / "src" / "pkg" / "other.py"
    target.write_text("def other():\n    return undefined_name\n")
    out = hook("post_edit.py", {
        "session_id": "s", "cwd": str(repo), "tool_name": "Write", "tool_input": {"file_path": str(target)},
    }, data_dir)
    assert out["decision"] == "block" and "F821" in out["reason"]


def test_repo_without_config_is_untouched(tmp_path: Path, data_dir: Path) -> None:
    root = tmp_path / "plain"
    root.mkdir()
    sh(root, "git", "init", "-q")
    (root / "a.py").write_text("x = undefined\n")
    base = {"session_id": "p", "cwd": str(root)}
    hook("session_start.py", base, data_dir)
    assert hook("post_edit.py", {**base, "tool_input": {"file_path": str(root / "a.py")}}, data_dir) == {}
    assert hook("stop_verify.py", base, data_dir) == {}


def test_lint_falls_back_to_ruff_on_path(repo: Path, data_dir: Path) -> None:
    cfg = json.loads((repo / ".claude" / "kit.json").read_text())
    cfg["python"] = ["/usr/bin/python3"]  # interpreter without the ruff module
    (repo / ".claude" / "kit.json").write_text(json.dumps(cfg))
    target = repo / "src" / "pkg" / "other.py"
    target.write_text("def other():\n    return undefined_name\n")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "post_edit.py")],
        input=json.dumps({"session_id": "f", "cwd": str(repo), "tool_input": {"file_path": str(target)}}),
        capture_output=True, text=True, timeout=60,
        env={"CLAUDE_PLUGIN_DATA": str(data_dir), "PATH": f"{Path(sys.executable).parent}:/usr/bin:/bin"},
    )
    assert "F821" in json.loads(proc.stdout)["reason"]


def test_repo_patterns() -> None:
    cfg = {"guards": {"patterns": [
        {"regex": r"scripts[/.]data[/.]download", "reason": "check cost", "decision": "ask"},
        {"regex": "(", "reason": "invalid regex is skipped"},
    ]}}
    assert check("python scripts/data/download_databento.py --day 2026-10-01", cfg) == ("ask", "check cost")
    assert check("python -m scripts.data.download_mbp10", cfg) == ("ask", "check cost")
    assert check("python scripts/research/run.py", cfg) is None

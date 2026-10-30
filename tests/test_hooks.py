"""End-to-end tests for the kit plugin's hook scripts.

Each test builds a throwaway git repo, feeds the hook the JSON Claude Code would send
on stdin, and checks what the hook prints. Requires pytest and ruff in the interpreter
running the tests (`pip install pytest ruff`).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins" / "kit" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from bash_guard import check, is_full_suite  # noqa: E402
from gates import run_gates  # noqa: E402
from stop_verify import find_tests  # noqa: E402

PY_CANDIDATES = [".venv/bin/python"]


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


def commit(cwd: Path, message: str) -> None:
    sh(cwd, "git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    sh(cwd, "git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", message)


def manual(cwd: Path, *files: str, data_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "stop_verify.py"), "--manual", *files],
        cwd=cwd, capture_output=True, text=True, timeout=120,
        env={"CLAUDE_PLUGIN_DATA": str(data_dir), "PATH": "/usr/bin:/bin"},
    )


def set_config(root: Path, **changes: dict) -> None:
    path = root / ".claude" / "kit.json"
    cfg = json.loads(path.read_text())
    for key, value in changes.items():
        cfg[key] = {**cfg.get(key, {}), **value} if isinstance(value, dict) else value
    path.write_text(json.dumps(cfg))


def wrapper_python(root: Path, *flags: str) -> None:
    """`.venv/bin/python` as a script that runs this interpreter, so it resolves only from the repo root."""
    exe = root / ".venv" / "bin" / "python"
    exe.parent.mkdir(parents=True)
    exe.write_text(f'#!/bin/sh\nexec "{sys.executable}" {" ".join(flags)} "$@"\n')
    exe.chmod(0o755)


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
    # DELETE without WHERE, however the statement ends
    "psql -c 'DELETE FROM ticks RETURNING id;'",
    'psql -c "DELETE FROM ONLY ticks"',
    'psql -c "DELETE FROM ticks AS t;"',
    'psql -c "DELETE FROM ticks" && psql -c "SELECT 1 WHERE true"',
    "python -c \"conn.execute('DELETE FROM ticks'); conn.execute('SELECT 1 WHERE true')\"",
    "psql <<'SQL'\nDELETE FROM ticks;\nSQL",
    # a WHERE in a comment or a subquery does not filter the DELETE
    "psql -c 'DELETE FROM ticks /* WHERE id = 1 */;'",
    'psql -c "DELETE FROM ticks -- WHERE id = 1"',
    "psql <<'SQL'\nDELETE FROM ticks -- WHERE id = 1\n;\nSQL",
    "psql -c 'DELETE FROM ticks USING (SELECT 1 WHERE true) AS s;'",
    # options that take a value do not name a test path
    "pytest --log-cli-level INFO",
    "python -m pytest --capture sys",
    # an unquoted newline ends a command; redirections are not test paths
    "cd /opt/app\npython -m pytest",
    "pytest -q 2>&1 | tail -5",
    # a suite root next to a file still runs the whole suite
    "pytest tests tests/test_mathx.py",
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
    # quoted identifiers are not statement ends; WHERE on a later line still counts
    "psql -c 'DELETE FROM \"ticks\" WHERE id = 1;'",
    'psql -c "DELETE FROM \\"ticks\\" WHERE id = 1;"',
    "psql <<'SQL'\nDELETE FROM ticks\nWHERE ts < now();\nSQL",
    "python -c \"conn.execute('DELETE FROM ticks WHERE id = %s', (1,))\"",
    "psql -c 'DELETE FROM ticks /* stale rows */ WHERE ts < now();'",
    "psql -c 'DELETE FROM ticks t USING (SELECT id FROM old) s WHERE t.id = s.id;'",
    "pytest --log-cli-level INFO tests/test_a.py",
    # a quoted newline or a line continuation does not split the command
    "python -m pytest \\\n  tests/test_a.py",
    'psql -c "SELECT 1\nFROM x"\npytest tests/test_a.py',
    "pytest tests/test_a.py 2>&1 | tail -5",
])
def test_guard_allows(command: str) -> None:
    assert check(command, CFG) is None, command


def test_filtered_delete_passes_in_deny_mode() -> None:
    deny = {"guards": {"sql_destructive": "deny"}}
    assert check("psql -c 'DELETE FROM \"ticks\" WHERE id = 1;'", deny) is None
    assert check("psql -c 'DELETE FROM ticks;'", deny) == ("deny", check("psql -c 'DELETE FROM ticks;'", CFG)[1])
    assert check("psql -c 'DELETE FROM ticks /* WHERE id = 1 */;'", deny)[0] == "deny"


def test_full_suite_guard_resolves_absolute_paths() -> None:
    root = Path("/opt/app")
    assert check("python -m pytest /opt/app/tests -m acquisition", CFG, root)[0] == "ask"
    assert check("pytest /opt/app/", CFG, root)[0] == "ask"
    assert check("pytest ./tests/", CFG, root)[0] == "ask"
    assert check("pytest /opt/app/tests/test_a.py", CFG, root) is None
    assert check("pytest /elsewhere/tests", CFG, root) is None
    assert check("pytest ../tests", CFG, root, "/opt/app/src")[0] == "ask"
    assert check("pytest ../tests/test_a.py", CFG, root, "/opt/app/src") is None


def test_full_suite_guard_off_by_default() -> None:
    assert check("pytest", {"guards": {}, "tests": {}}) is None
    assert is_full_suite("pytest", ["tests"])


def test_guard_hook_output(repo: Path, data_dir: Path) -> None:
    for command in ("pytest", f"python -m pytest {repo}/tests -q"):
        out = hook("bash_guard.py", {"cwd": str(repo), "tool_input": {"command": command}}, data_dir)
        assert out["hookSpecificOutput"]["permissionDecision"] == "ask", command
    assert hook("bash_guard.py", {"cwd": str(repo), "tool_input": {"command": "ls"}}, data_dir) == {}


# ── test selection ─────────────────────────────────────────────────────────────
def test_find_tests_by_name_and_import(repo: Path) -> None:
    tests, capped, _ = find_tests(repo, ["src/pkg/mathx.py"], {"test_dirs": ["tests"], "import_roots": ["src"]})
    assert tests == ["tests/test_mathx.py", "tests/test_uses_import.py"]
    assert capped == 0


def test_find_tests_changed_test_file_and_cap(repo: Path) -> None:
    tests, capped, _ = find_tests(
        repo, ["tests/test_unrelated.py", "src/pkg/mathx.py"], {"test_dirs": ["tests"], "max_files": 2}
    )
    assert tests == ["tests/test_unrelated.py", "tests/test_mathx.py"]
    assert capped == 1


def test_find_tests_multiline_import_and_patch_target(repo: Path) -> None:
    (repo / "tests" / "test_grouped.py").write_text("from pkg import (\n    other,\n)\n")
    (repo / "tests" / "test_patched.py").write_text(
        "import pkg\nfrom unittest import mock\n\nTARGET = mock.patch('pkg.other.other')\n"
    )
    (repo / "tests" / "test_decoy.py").write_text("import json\nNAME = 'other.csv'\n")
    tests, _, _ = find_tests(repo, ["src/pkg/other.py"], {"test_dirs": ["tests"], "import_roots": ["src"]})
    assert tests == ["tests/test_grouped.py", "tests/test_patched.py"]


def test_find_tests_for_conftest(repo: Path) -> None:
    (repo / "tests" / "sub").mkdir()
    (repo / "tests" / "sub" / "test_inner.py").write_text("def test_inner():\n    pass\n")
    cfg = {"test_dirs": ["tests"]}
    tests, _, _ = find_tests(repo, ["tests/sub/conftest.py"], cfg)
    assert tests == ["tests/sub/test_inner.py"]
    tests, _, _ = find_tests(repo, ["tests/conftest.py"], cfg)
    assert set(tests) == {
        "tests/sub/test_inner.py", "tests/test_mathx.py", "tests/test_unrelated.py", "tests/test_uses_import.py",
    }


def test_find_tests_exclude(repo: Path) -> None:
    tests, _, _ = find_tests(
        repo, ["src/pkg/mathx.py"], {"test_dirs": ["tests"], "import_roots": ["src"], "exclude": ["tests/test_uses_*"]}
    )
    assert tests == ["tests/test_mathx.py"]


def test_excluded_changed_test_is_reported(repo: Path, data_dir: Path) -> None:
    set_config(repo, lint={"enabled": False}, tests={"exclude": ["tests/test_unrelated.py"]})
    result = manual(repo, "tests/test_mathx.py", "tests/test_unrelated.py", data_dir=data_dir)
    assert result.returncode == 1
    assert "1 test files were omitted by exclusions" in result.stdout


def test_bad_gate_cwd_does_not_skip_other_gates(repo: Path) -> None:
    gates = [{"name": "bad", "paths": ["*.py"], "argv": [sys.executable, "-c", "pass"], "cwd": None},
             {"name": "good", "paths": ["*.py"], "argv": [sys.executable, "-c", "pass"]}]
    failures, ran = run_gates(repo, {"verification": {"enabled": True, "gates": gates}}, ["x.py"])
    assert any("Gate bad unavailable" in f for f in failures)
    assert ran == ["good"]


def test_gate_deadline_reports_unstarted_checks(repo: Path) -> None:
    import time
    gates = [{"name": "slow", "paths": ["*.py"], "argv": [sys.executable, "-c", "import time; time.sleep(2)"]},
             {"name": "later", "paths": ["*.py"], "argv": [sys.executable, "-c", "pass"]}]
    failures, _ = run_gates(repo, {"verification": {"enabled": True, "gates": gates}}, ["x.py"],
                            deadline=time.monotonic() + 0.1)
    assert any("Gate slow unavailable" in f for f in failures)
    assert any("Gate later incomplete" in f for f in failures)


def test_gate_mode_does_not_require_project_python(repo: Path, data_dir: Path) -> None:
    set_config(repo, python=["nonexistent-python-kit"], lint={"enabled": False},
               verification={"enabled": True, "gates": [{"name": "external", "paths": ["*.py"],
                              "argv": [sys.executable, "-c", "pass"]}]})
    result = manual(repo, "src/pkg/mathx.py", data_dir=data_dir)
    assert result.returncode == 0, result.stdout


def test_overlapping_test_dirs_run_each_file_once(repo: Path, data_dir: Path) -> None:
    (repo / "tests" / "sub").mkdir()
    (repo / "tests" / "sub" / "test_once.py").write_text("def test_once(): pass\n")
    set_config(repo, lint={"enabled": False}, tests={"test_dirs": ["tests", "tests/sub"]})
    result = manual(repo, "src/pkg/mathx.py", data_dir=data_dir)
    assert result.returncode == 0, result.stdout
    summary = result.stdout.split("tests run:", 1)[1].splitlines()[0]
    assert summary.count("tests/sub/test_once.py") == 1


@pytest.mark.parametrize("settings", [
    {"test_dirs": None}, {"max_files": 0}, {"timeout_s": "300"},
    {"env": {"KEY": 1}}, {"pytest_args": "-q"},
])
def test_invalid_nested_settings_are_reported(repo: Path, data_dir: Path, settings: dict) -> None:
    set_config(repo, tests=settings)
    result = manual(repo, "tests/test_mathx.py", data_dir=data_dir)
    assert result.returncode == 2 and "Invalid kit configuration" in result.stdout
    base = {"session_id": "bad-settings", "cwd": str(repo)}
    assert "additionalContext" in hook("stop_verify.py", base, data_dir)["hookSpecificOutput"]
    retry = hook("stop_verify.py", {**base, "stop_hook_active": True}, data_dir)
    assert "unverified" in retry["systemMessage"] and "hookSpecificOutput" not in retry


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
    assert "tests/test_unrelated.py" in feedback

    again = hook("stop_verify.py", {**base, "stop_hook_active": True}, data_dir)
    assert "hookSpecificOutput" not in again and "still failing" in again["systemMessage"]

    target.write_text("def double(x):\n    return x * 2\n")
    assert hook("stop_verify.py", {**base, "stop_hook_active": True}, data_dir) == {}


def test_preexisting_dirty_file_is_ignored(repo: Path, data_dir: Path) -> None:
    (repo / "src" / "pkg" / "mathx.py").write_text("def double(x):\n    return x * 3\n")  # broken before the session
    sid = str(uuid.uuid4())
    base = {"session_id": sid, "cwd": str(repo)}
    set_config(repo, tests={"enabled": False})
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


def test_deleted_module_still_runs_its_tests(repo: Path, data_dir: Path) -> None:
    for committed in (False, True):
        sid = str(uuid.uuid4())
        base = {"session_id": sid, "cwd": str(repo)}
        hook("session_start.py", {**base, "source": "startup"}, data_dir)
        (repo / "src" / "pkg" / "mathx.py").unlink()
        if committed:
            commit(repo, "drop mathx")
        out = hook("stop_verify.py", {**base, "stop_hook_active": False}, data_dir)
        feedback = out["hookSpecificOutput"]["additionalContext"]
        assert "tests/test_mathx.py" in feedback and "mathx" in feedback, committed
        sh(repo, "git", "checkout", "HEAD~1" if committed else "HEAD", "--", "src/pkg/mathx.py")
        if committed:
            commit(repo, "restore mathx")


def test_staged_rename_runs_tests_of_the_old_name(repo: Path, data_dir: Path) -> None:
    sid = str(uuid.uuid4())
    base = {"session_id": sid, "cwd": str(repo)}
    hook("session_start.py", {**base, "source": "startup"}, data_dir)
    sh(repo, "git", "mv", "src/pkg/mathx.py", "src/pkg/renamed.py")
    out = hook("stop_verify.py", {**base, "stop_hook_active": False}, data_dir)
    feedback = out["hookSpecificOutput"]["additionalContext"]
    assert "tests/test_mathx.py" in feedback and "mathx" in feedback


def test_restored_baseline_dirty_file_runs_its_tests(repo: Path, data_dir: Path) -> None:
    target = repo / "src" / "pkg" / "mathx.py"
    target.write_text("def double(x):\n    return x * 3\n")
    commit(repo, "break double")
    target.write_text("def double(x):\n    return x * 2\n")  # fixed, uncommitted, before the session
    sid = str(uuid.uuid4())
    base = {"session_id": sid, "cwd": str(repo)}
    hook("session_start.py", {**base, "source": "startup"}, data_dir)
    sh(repo, "git", "checkout", "--", "src/pkg/mathx.py")  # Bash throws the fix away
    out = hook("stop_verify.py", {**base, "stop_hook_active": False}, data_dir)
    assert "assert 6 == 4" in out["hookSpecificOutput"]["additionalContext"]


def test_missing_interpreter_is_a_failure(repo: Path, data_dir: Path) -> None:
    set_config(repo, python=PY_CANDIDATES)  # .venv not created yet
    proc = manual(repo, "src/pkg/mathx.py", data_dir=data_dir)
    assert proc.returncode == 1 and "lint and tests did not run" in proc.stdout
    set_config(repo, lint={"enabled": False}, tests={"enabled": False})
    assert manual(repo, "src/pkg/mathx.py", data_dir=data_dir).returncode == 2


def test_committed_baseline_dirty_file_is_ignored(repo: Path, data_dir: Path) -> None:
    (repo / "src" / "pkg" / "mathx.py").write_text("def double(x):\n    return x * 3\n")  # broken before the session
    sid = str(uuid.uuid4())
    base = {"session_id": sid, "cwd": str(repo)}
    set_config(repo, tests={"enabled": False})
    hook("session_start.py", {**base, "source": "startup"}, data_dir)
    (repo / "src" / "pkg" / "other.py").write_text("def other():\n    return 2\n")
    commit(repo, "session work, sweeping in the pre-existing edit")
    assert hook("stop_verify.py", {**base, "stop_hook_active": False}, data_dir) == {}


def test_stale_bytecode_is_not_used(repo: Path, data_dir: Path) -> None:
    target = repo / "src" / "pkg" / "mathx.py"
    env = {**os.environ, "PYTHONPATH": "src"}
    sh_env = {"cwd": repo, "env": env, "capture_output": True, "text": True, "check": True}
    subprocess.run([sys.executable, "-c", "import pkg.mathx"], **sh_env)  # writes __pycache__
    sid = str(uuid.uuid4())
    base = {"session_id": sid, "cwd": str(repo)}
    hook("session_start.py", {**base, "source": "startup"}, data_dir)
    before = target.stat()
    target.write_text("def double(x):\n    return x * 3\n")  # same size
    os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns))  # same mtime
    stale = subprocess.run([sys.executable, "-c", "import pkg.mathx; print(pkg.mathx.double(2))"], **sh_env)
    assert stale.stdout.strip() == "4"  # plain Python really does run the old bytecode here
    hook("post_edit.py", {**base, "tool_name": "Edit", "tool_input": {"file_path": str(target)}}, data_dir)
    out = hook("stop_verify.py", {**base, "stop_hook_active": False}, data_dir)
    assert "assert 6 == 4" in out["hookSpecificOutput"]["additionalContext"]


def test_missing_pytest_is_a_failure(repo: Path, data_dir: Path) -> None:
    wrapper_python(repo, "-S")  # no site-packages, so no pytest
    set_config(repo, python=PY_CANDIDATES, lint={"enabled": False})
    proc = manual(repo, "src/pkg/mathx.py", data_dir=data_dir)
    assert proc.returncode == 1 and "pytest is not installed" in proc.stdout


def test_lint_only_reports_no_tests(repo: Path, data_dir: Path) -> None:
    set_config(repo, tests={"enabled": False})
    proc = manual(repo, "src/pkg/mathx.py", data_dir=data_dir)
    assert proc.returncode == 0 and "tests run: none" in proc.stdout


def test_manual_from_subdirectory_uses_root_relative_paths(repo: Path, data_dir: Path) -> None:
    wrapper_python(repo)
    (repo / ".env.test").write_text("KIT_MARKER=from-env\n")
    (repo / "tests" / "test_envcheck.py").write_text(
        "import os\n\nfrom pkg.mathx import double\n\n"
        "def test_env():\n    assert os.environ.get('KIT_MARKER') == 'from-env' and double(1) == 2\n"
    )
    set_config(repo, python=PY_CANDIDATES, tests={"env_file": ".env.test"})
    proc = manual(repo / "src", "pkg/mathx.py", data_dir=data_dir)
    assert "tests/test_envcheck.py" in proc.stdout and proc.stdout.rstrip().endswith("kit verify: OK"), proc.stdout


# ── session policy ─────────────────────────────────────────────────────────────
def policy_context(payload: dict, data_dir: Path) -> str:
    out = hook("session_policy.py", payload, data_dir)
    specific = out.get("hookSpecificOutput", {})
    assert specific.get("hookEventName") == "SessionStart", out
    return specific.get("additionalContext", "")


def test_policy_is_added_as_session_context(repo: Path, data_dir: Path) -> None:
    text = policy_context({"cwd": str(repo), "session_id": uuid.uuid4().hex}, data_dir)
    assert "deliver" in text and "ultracode" in text


def test_policy_puts_the_design_decision_on_claude(repo: Path, data_dir: Path) -> None:
    """The approach is Claude's to settle, not the user's to supply."""
    text = policy_context({"cwd": str(repo)}, data_dir)
    assert "approach" in text and "never the user's to supply" in text


def test_the_design_stage_is_wired_end_to_end() -> None:
    """deliver hands the design stage to deliberate, which names a critic that exists."""
    kit = Path(__file__).resolve().parents[1] / "plugins" / "kit"
    deliver = (kit / "skills" / "deliver" / "SKILL.md").read_text()
    deliberate = (kit / "skills" / "deliberate" / "SKILL.md").read_text()
    assert "deliberate" in deliver, "deliver never reaches the design stage"
    assert "kit:design-critic" in deliberate, "the loop has no adversary"
    assert (kit / "agents" / "design-critic.md").is_file(), "the critic it names does not exist"


def test_a_decision_is_written_to_be_found_again() -> None:
    """The loop only avoids redoing work if step 2 reads what step 8 wrote. Both ends
    name the same directory, and the template carries the two fields step 2 acts on."""
    kit = Path(__file__).resolve().parents[1] / "plugins" / "kit"
    deliberate = (kit / "skills" / "deliberate" / "SKILL.md").read_text()
    look_up, record = deliberate.split("## 8. Record it", 1)
    assert "routing.decisions" in look_up, "step 2 never reads the decision logs"
    assert "routing.decisions" in record, "step 8 writes somewhere step 2 does not read"
    assert "Supersedes" in record, "a log cannot replace an earlier one"
    assert "What would change this decision" in record, "no reversal condition to check"
    # Reading the log is only half of it. A log whose condition has fired has to reopen
    # the decision from the field it already holds, or the next run pays for the
    # comparison twice. `evals/reversed-decision-reopens` is what scores that happening.
    assert "Now true" in look_up, "step 2 only handles a decision that still stands"
    assert "starting set" in look_up, (
        "a reopened decision has to start from the recorded candidates, not from nothing"
    )
    config = json.loads((kit / "templates" / ".claude" / "kit.json").read_text())
    assert "decisions" in config["routing"], "the template never points anywhere"


def test_a_generic_addition_is_offered_to_the_kit() -> None:
    """Without this, every repo rebuilds the same skill and the kit never learns."""
    deliver = (Path(__file__).resolve().parents[1] / "plugins" / "kit" / "skills"
               / "deliver" / "SKILL.md").read_text()
    harness = deliver.split("## Working out the harness as you go", 1)[1]
    assert "belongs in the kit" in harness, "nothing promotes a generic addition"
    assert "user's call" in harness, "promotion has to stay the user's decision"


def test_policy_can_be_turned_off(repo: Path, data_dir: Path) -> None:
    set_config(repo, routing={"enabled": False})
    assert hook("session_policy.py", {"cwd": str(repo)}, data_dir) == {}


def test_policy_appends_the_repo_note(repo: Path, data_dir: Path) -> None:
    set_config(repo, routing={"note": "Work on dated branches.\n  Gates live in the Makefile."})
    text = policy_context({"cwd": str(repo)}, data_dir)
    assert text.endswith("Work on dated branches. Gates live in the Makefile.")


def test_policy_caps_the_repo_note(repo: Path, data_dir: Path) -> None:
    set_config(repo, routing={"note": "x" * 900})
    text = policy_context({"cwd": str(repo)}, data_dir)
    assert text.count("x") == 400


def test_policy_outside_a_repo_still_prints(tmp_path: Path, data_dir: Path) -> None:
    assert "deliver" in policy_context({"cwd": str(tmp_path)}, data_dir)


def test_policy_survives_a_broken_config(repo: Path, data_dir: Path) -> None:
    (repo / ".claude" / "kit.json").write_text("{ not json")
    assert "deliver" in policy_context({"cwd": str(repo)}, data_dir)


# ── plugin metadata ────────────────────────────────────────────────────────────
def test_every_frontmatter_value_is_valid_yaml() -> None:
    """A plain YAML scalar may not contain ': '. An unquoted description that does
    makes the whole frontmatter unparseable, and the skill or agent silently fails
    to load."""
    root = Path(__file__).resolve().parents[1] / "plugins"
    offenders = []
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            continue
        for line in text.split("---\n", 2)[1].splitlines():
            key, sep, value = line.partition(": ")
            if not sep or not key or not key[0].isalpha() or " " in key:
                continue
            if ": " in value and value[:1] not in {'"', "'", "|", ">"}:
                offenders.append(f"{path.relative_to(root)}: {key}")
    assert not offenders, f"unquoted ': ' in frontmatter: {offenders}"


def test_missing_linter_is_not_a_pass(repo: Path, data_dir: Path) -> None:
    set_config(repo, lint={"args": ["-m", "kit_missing_linter_82479"]}, tests={"enabled": False})
    result = manual(repo, "src/pkg/mathx.py", data_dir=data_dir)
    assert result.returncode == 1 and "lint unavailable" in result.stdout


def test_transitive_failure_and_cap_are_not_hidden(repo: Path, data_dir: Path) -> None:
    (repo / "src/pkg/consumer.py").write_text("from pkg.mathx import double\n")
    for n in range(9):
        (repo / f"tests/test_indirect_{n:02}.py").write_text(
            "from pkg.consumer import double\n" + f"def test_indirect(): assert double(2) == {4 if n < 8 else 9}\n"
        )
    result = manual(repo, "src/pkg/mathx.py", data_dir=data_dir)
    assert result.returncode == 1 and "test_indirect_08" in result.stdout


def test_empty_collection_is_not_a_pass(repo: Path, data_dir: Path) -> None:
    set_config(repo, tests={"pytest_args": ["-q", "-k", "no_such_test_82479"]})
    result = manual(repo, "src/pkg/mathx.py", data_dir=data_dir)
    assert result.returncode == 1 and "collected no tests" in result.stdout


def test_broken_config_reports_unavailable(repo: Path, data_dir: Path) -> None:
    (repo / ".claude/kit.json").write_text('{"lint": null}')
    result = manual(repo, "src/pkg/mathx.py", data_dir=data_dir)
    assert result.returncode == 2 and "Invalid kit configuration" in result.stdout
    out = hook("stop_verify.py", {"session_id": "bad-config", "cwd": str(repo)}, data_dir)
    assert "Verification unavailable" in out["hookSpecificOutput"]["additionalContext"]


def test_changed_test_config_invalidates_prior_pass(repo: Path, data_dir: Path) -> None:
    (repo / "tests/test_env.py").write_text(
        "import os\ndef test_env(): assert os.getenv('KIT_TEST') == 'good'\n"
    )
    set_config(repo, tests={"env": {"KIT_TEST": "good"}})
    base = {"session_id": "cache-check", "cwd": str(repo)}
    hook("session_start.py", base, data_dir)
    (repo / "src/pkg/mathx.py").write_text("def double(x):\n    return x * 2 + 0\n")
    assert hook("stop_verify.py", base, data_dir) == {}
    set_config(repo, tests={"env": {"KIT_TEST": "bad"}})
    assert "test_env" in hook("stop_verify.py", base, data_dir)["hookSpecificOutput"]["additionalContext"]


def test_language_neutral_gate_pass_fail_and_uncovered(repo: Path, data_dir: Path) -> None:
    source = repo / "src/app.ts"
    source.write_text("export const answer = 42;\n")
    set_config(repo, lint={"enabled": False}, tests={"enabled": False}, verification={
        "enabled": True, "gates": [{"name": "typescript", "paths": ["src/*.ts"],
                                    "argv": [sys.executable, "-c", "import sys; sys.exit(0)"]}]})
    result = manual(repo, "src/app.ts", data_dir=data_dir)
    assert result.returncode == 0, result.stdout
    set_config(repo, verification={"gates": [{"name": "typescript", "paths": ["src/*.ts"],
                                               "argv": [sys.executable, "-c", "import sys; sys.exit(3)"]}]})
    result = manual(repo, "src/app.ts", data_dir=data_dir)
    assert result.returncode == 1 and "Gate typescript failed (exit 3)" in result.stdout
    result = manual(repo, "README.md", data_dir=data_dir)
    assert result.returncode == 1 and "No configured gate covers" in result.stdout


def test_gate_command_does_not_use_shell_and_cannot_escape_repo(repo: Path, data_dir: Path) -> None:
    (repo / "src/app.ts").write_text("x\n")
    set_config(repo, lint={"enabled": False}, tests={"enabled": False}, verification={
        "enabled": True, "gates": [{"name": "bad", "paths": ["src/*.ts"],
                                    "argv": ["this-does-not-exist;touch", "marker"]}]})
    result = manual(repo, "src/app.ts", data_dir=data_dir)
    assert result.returncode == 1 and not (repo / "marker").exists()
    set_config(repo, verification={"gates": [{"name": "bad", "paths": ["src/*.ts"],
                                               "cwd": "..", "argv": [sys.executable, "-V"]}]})
    result = manual(repo, "src/app.ts", data_dir=data_dir)
    assert result.returncode == 1 and "unavailable" in result.stdout


def test_non_python_change_without_gate_is_unverified(repo: Path, data_dir: Path) -> None:
    (repo / "src/app.ts").write_text("x\n")
    result = manual(repo, "src/app.ts", data_dir=data_dir)
    assert result.returncode == 1 and "non-Python" in result.stdout

def test_mixed_language_change_without_gate_is_unverified(repo: Path, data_dir: Path) -> None:
    (repo / "src/app.ts").write_text("x\n")
    result = manual(repo, "src/pkg/mathx.py", "src/app.ts", data_dir=data_dir)
    assert result.returncode == 1 and "src/app.ts" in result.stdout

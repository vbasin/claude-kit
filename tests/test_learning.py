"""Integration checks for the reusable skill candidate lifecycle."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "plugins/kit/scripts/learning.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)


def setup_candidate(tmp_path):
    candidate = tmp_path / "candidate"
    (candidate / "skill").mkdir(parents=True)
    (candidate / "candidate.json").write_text(json.dumps({
        "name": "test-skill", "purpose": "reproduce failures", "applies_when": "a trace exists",
        "not_for": "missing traces", "evidence": "fixture failure",
    }))
    (candidate / "skill/SKILL.md").write_text("---\nname: test-skill\ndescription: reproduce a trace\n---\n")
    suite_dir = tmp_path / "suite"
    for name in ("improvement", "regression"):
        (suite_dir / name).mkdir(parents=True)
    (suite_dir / "improvement/check.py").write_text(
        "import os,sys\nsys.exit(0 if os.getenv('KIT_CANDIDATE_DIR') else 1)\n"
    )
    (suite_dir / "regression/check.py").write_text("raise SystemExit(0)\n")
    suite = suite_dir / "suite.json"
    suite.write_text(json.dumps({"cases": [
        {"name": name, "fixture": name, "argv": [sys.executable, "check.py"]}
        for name in ("improvement", "regression")
    ]}))
    return candidate, suite


def test_candidate_promotes_only_after_passing_suite(tmp_path):
    candidate, suite = setup_candidate(tmp_path)
    result = run("evaluate", candidate, "--suite", suite)
    assert result.returncode == 0 and json.loads(result.stdout)["improvements"] == ["improvement"]
    target = tmp_path / "skills"
    result = run("promote", candidate, "--suite", suite, "--destination", target)
    assert result.returncode == 0 and (target / "test-skill/SKILL.md").is_file()
    result = run("promote", candidate, "--suite", suite, "--destination", target)
    assert result.returncode == 2 and "already exists" in result.stderr


def test_regression_blocks_promotion(tmp_path):
    candidate, suite = setup_candidate(tmp_path)
    (suite.parent / "regression/check.py").write_text(
        "import os,sys\nsys.exit(1 if os.getenv('KIT_CANDIDATE_DIR') else 0)\n"
    )
    target = tmp_path / "skills"
    result = run("promote", candidate, "--suite", suite, "--destination", target)
    assert result.returncode == 1 and json.loads(result.stdout)["regressions"] == ["regression"]
    assert not target.exists()


def test_no_improvement_and_invalid_fixture_are_rejected(tmp_path):
    candidate, suite = setup_candidate(tmp_path)
    (suite.parent / "improvement/check.py").write_text("raise SystemExit(0)\n")
    assert run("evaluate", candidate, "--suite", suite).returncode == 1
    data = json.loads(suite.read_text())
    data["cases"][0]["fixture"] = "../outside"
    suite.write_text(json.dumps(data))
    result = run("evaluate", candidate, "--suite", suite)
    assert result.returncode == 2 and "inside the suite" in result.stderr


def test_improvement_alone_does_not_satisfy_regression_guard(tmp_path):
    candidate, suite = setup_candidate(tmp_path)
    data = json.loads(suite.read_text())
    data["cases"] = data["cases"][:1]
    suite.write_text(json.dumps(data))
    result = run("evaluate", candidate, "--suite", suite)
    assert result.returncode == 1 and not json.loads(result.stdout)["passed"]


def test_cases_are_isolated_and_promotion_uses_snapshot(tmp_path):
    candidate, suite = setup_candidate(tmp_path)
    original = (candidate / "skill/SKILL.md").read_text()
    (suite.parent / "improvement/check.py").write_text(
        "import os, pathlib, sys\n"
        "p = os.environ.get('KIT_CANDIDATE_DIR')\n"
        "if not p: sys.exit(1)\n"
        "(pathlib.Path(p) / 'cache').write_text('contamination')\n"
        f"pathlib.Path({str(candidate / 'skill/SKILL.md')!r}).write_text('changed after snapshot')\n"
    )
    (suite.parent / "regression/check.py").write_text(
        "import os, pathlib, sys\n"
        "p = os.environ.get('KIT_CANDIDATE_DIR')\n"
        "sys.exit(1 if p and (pathlib.Path(p) / 'cache').exists() else 0)\n"
    )
    target = tmp_path / "skills"
    result = run("promote", candidate, "--suite", suite, "--destination", target)
    assert result.returncode == 0, result.stderr
    assert (target / "test-skill/SKILL.md").read_text() == original
    assert not (target / "test-skill/cache").exists()


def test_checks_can_emit_non_utf8_output(tmp_path):
    candidate, suite = setup_candidate(tmp_path)
    (suite.parent / "regression/check.py").write_text("import os\nos.write(1, b'\\xff')\n")
    result = run("evaluate", candidate, "--suite", suite)
    assert result.returncode == 0, result.stderr

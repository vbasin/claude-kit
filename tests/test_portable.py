"""Portable workflow installation and evidence-based comparison."""
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/kit"
SCRIPTS = PLUGIN / "scripts"
sys.path.insert(0, str(SCRIPTS))

import install_portable  # noqa: E402


def load_scorer():
    path = PLUGIN / "portable/kit-deliver/scripts/score.py"
    spec = importlib.util.spec_from_file_location("kit_score", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def comparison():
    return {
        "criteria": [
            {"name": "errors", "direction": "min", "lower": 0, "upper": 10, "weight": 2, "threshold": 4},
            {"name": "time", "direction": "min", "lower": 0, "upper": 100, "weight": 1},
        ],
        "options": [
            {"name": "baseline", "metrics": {"errors": {"value": 7, "evidence": "audit"},
                                             "time": {"value": 10, "evidence": "timer"}}},
            {"name": "candidate", "metrics": {"errors": {"value": 2, "evidence": "audit"},
                                              "time": {"value": 30, "evidence": "timer"}}},
            {"name": "unknown", "metrics": {"errors": {"value": 0, "evidence": "audit"}}},
        ],
    }


def test_scoring_requires_evidence_and_gates_before_ranking():
    result = load_scorer().score(comparison())
    assert result["ranked_eligible"] == ["candidate"]
    assert result["options"][0]["failed_thresholds"] == ["errors"]
    assert result["options"][1]["score"] == 76.67
    assert result["options"][2]["status"] == "incomplete"
    assert "score" not in result["options"][2]


def test_scoring_validates_inputs_and_does_not_invent_evidence():
    scorer = load_scorer()
    data = comparison()
    data["options"][1]["metrics"]["time"]["evidence"] = ""
    assert scorer.score(data)["options"][1]["status"] == "incomplete"
    data["criteria"][0]["weight"] = float("nan")
    with pytest.raises(ValueError):
        scorer.score(data)


@pytest.mark.parametrize("host,folder", [("codex", ".agents"), ("grok", ".grok"), ("claude", ".claude")])
def test_installed_skill_runs_real_repo_gate(tmp_path, host, folder):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    assert install_portable.install(tmp_path, host) == "installed"
    assert install_portable.install(tmp_path, host) == "unchanged"
    skill = tmp_path / folder / "skills/kit-deliver"
    assert (skill / "scripts/learning.py").is_file()
    (tmp_path / ".kit").mkdir()
    (tmp_path / ".kit/kit.json").write_text(json.dumps({"verification": {"enabled": True, "gates": [
        {"name": "web", "paths": ["web/*"], "argv": [sys.executable, "-c", "raise SystemExit(0)"]}
    ]}}))
    (tmp_path / "web").mkdir()
    (tmp_path / "web/index.html").write_text("<title>Site</title>")
    proc = subprocess.run([sys.executable, str(skill / "scripts/stop_verify.py"), "--manual", "web/index.html"],
                          cwd=tmp_path, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "kit verify: OK" in proc.stdout
    config = json.loads((tmp_path / ".kit/kit.json").read_text())
    config["verification"]["gates"][0]["argv"] = [sys.executable, "-c", "raise SystemExit(3)"]
    (tmp_path / ".kit/kit.json").write_text(json.dumps(config))
    proc = subprocess.run([sys.executable, str(skill / "scripts/stop_verify.py"), "--manual", "web/index.html"],
                          cwd=tmp_path, capture_output=True, text=True)
    assert proc.returncode == 1 and "Gate web failed" in proc.stdout


def test_installer_preserves_user_changes_and_updates_untouched_version(tmp_path, monkeypatch):
    source = tmp_path / "source"
    shutil.copytree(install_portable.SOURCE, source)
    monkeypatch.setattr(install_portable, "SOURCE", source)
    repo = tmp_path / "repo"
    repo.mkdir()
    assert install_portable.install(repo, "codex") == "installed"
    target = repo / ".agents/skills/kit-deliver/SKILL.md"
    (source / "SKILL.md").write_text("new version")
    assert install_portable.install(repo, "codex") == "installed"
    assert target.read_text() == "new version"
    target.write_text("user edits")
    with pytest.raises(ValueError, match="modified"):
        install_portable.install(repo, "codex")
    assert target.read_text() == "user edits"


def test_installer_does_not_overwrite_existing_unmanaged_skill(tmp_path):
    target = tmp_path / ".agents/skills/kit-deliver"
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text("existing work")
    with pytest.raises(ValueError, match="not managed"):
        install_portable.install(tmp_path, "codex")
    assert (target / "SKILL.md").read_text() == "existing work"


def test_backlog_persists_ideas_and_resolutions_without_repo_changes(tmp_path):
    script = PLUGIN / "portable/kit-deliver/scripts/backlog.py"
    backlog = tmp_path / "personal/ideas.jsonl"
    base = [sys.executable, str(script), "--file", str(backlog)]
    added = subprocess.run(base + ["add", "--task", "SEO request", "--idea", "Improve audit",
                                   "--evidence", "Existing audit met task; benchmark later"],
                           capture_output=True, text=True, check=True)
    ident = json.loads(added.stdout)["id"]
    found = subprocess.run(base + ["list"], capture_output=True, text=True, check=True)
    assert json.loads(found.stdout)[0]["status"] == "proposed"
    subprocess.run(base + ["resolve", "--id", ident, "--status", "evaluated",
                           "--evidence", "Comparison fixture passed"], capture_output=True, text=True, check=True)
    found = subprocess.run(base + ["list"], capture_output=True, text=True, check=True)
    assert json.loads(found.stdout)[0]["resolution_evidence"] == "Comparison fixture passed"
    missing = subprocess.run(base + ["resolve", "--id", "missing", "--status", "promoted",
                                     "--evidence", "none"], capture_output=True, text=True)
    assert missing.returncode == 2


def test_promoted_portable_skill_is_reused_by_codex_and_grok(tmp_path, monkeypatch):
    candidate = tmp_path / "candidate"
    (candidate / "skill").mkdir(parents=True)
    (candidate / "candidate.json").write_text(json.dumps({
        "name": "seo-audit", "purpose": "audit metadata", "applies_when": "web pages",
        "not_for": "non-web projects", "evidence": "independent fixture",
    }))
    (candidate / "skill/SKILL.md").write_text(
        "---\nname: seo-audit\ndescription: Audit website metadata\n---\nAudit canonical tags.\n"
    )
    (candidate / "skill/.kit-portable").write_text("")
    suite = tmp_path / "suite"
    for name in ("improvement", "regression"):
        (suite / name).mkdir(parents=True)
    (suite / "improvement/check.py").write_text(
        "import os, pathlib, sys\np=os.environ.get('KIT_CANDIDATE_DIR')\n"
        "sys.exit(0 if p and 'canonical' in (pathlib.Path(p)/'SKILL.md').read_text() else 1)\n"
    )
    (suite / "regression/check.py").write_text("raise SystemExit(0)\n")
    (suite / "suite.json").write_text(json.dumps({"cases": [
        {"name": name, "fixture": name, "argv": [sys.executable, "check.py"]}
        for name in ("improvement", "regression")
    ]}))
    skills = tmp_path / "shared-skills"
    promoted = subprocess.run([sys.executable, str(SCRIPTS / "learning.py"), "promote", candidate,
                               "--suite", str(suite / "suite.json"), "--destination", skills],
                              capture_output=True, text=True)
    assert promoted.returncode == 0, promoted.stderr
    monkeypatch.setattr(install_portable, "SKILLS", skills)
    for host, folder in (("codex", ".agents"), ("grok", ".grok"), ("claude", ".claude")):
        repo = tmp_path / host
        repo.mkdir()
        assert install_portable.install(repo, host) == "installed"
        installed = repo / folder / "skills/seo-audit/SKILL.md"
        assert installed.read_text() == (skills / "seo-audit/SKILL.md").read_text()
        assert install_portable.install(repo, host) == "unchanged"


def test_portable_skills_are_validated_before_installing_anything(tmp_path, monkeypatch):
    skills = tmp_path / "skills"
    bad = skills / "bad-name"
    bad.mkdir(parents=True)
    (bad / ".kit-portable").write_text("")
    (bad / "SKILL.md").write_text("---\nname: different-name\ndescription: wrong\n---\n")
    monkeypatch.setattr(install_portable, "SKILLS", skills)
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(ValueError, match="name must match"):
        install_portable.install(repo, "grok")
    assert not (repo / ".grok/skills/kit-deliver").exists()


def test_score_cli_never_exits_success_when_no_candidate_is_eligible(tmp_path):
    data = comparison()
    data["options"] = [data["options"][0], data["options"][2]]
    input_file = tmp_path / "comparison.json"
    input_file.write_text(json.dumps(data))
    scorer = PLUGIN / "portable/kit-deliver/scripts/score.py"
    result = subprocess.run([sys.executable, str(scorer), str(input_file)], capture_output=True, text=True)
    assert result.returncode == 1 and json.loads(result.stdout)["ranked_eligible"] == []

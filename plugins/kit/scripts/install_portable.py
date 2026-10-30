"""Install shared task and reusable skills into a coding-agent workspace.

Usage: python install_portable.py --repo PATH --host codex|grok|claude
The installer updates only unchanged skill directories it previously installed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

PLUGIN = Path(__file__).resolve().parents[1]
SOURCE = PLUGIN / "portable" / "kit-deliver"
SKILLS = PLUGIN / "skills"
MARKER = ".kit-portable"
MANIFEST = ".kit-installed.json"
RUNTIME_SCRIPTS = ("kit_common.py", "gates.py", "stop_verify.py", "learning.py")
HOST_PATHS = {"codex": ".agents/skills", "grok": ".grok/skills", "claude": ".claude/skills"}
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def file_hashes(folder: Path) -> Dict[str, str]:
    hashes = {}
    for path in sorted(folder.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlinks are not supported: {path}")
        if path.is_file() and path != folder / MANIFEST:
            hashes[path.relative_to(folder).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        elif not path.is_dir() and not path.is_file():
            raise ValueError(f"unsupported file type in skill: {path}")
    expected_dirs = {str(parent) for name in hashes for parent in Path(name).parents}
    for path in folder.rglob("*"):
        if path.is_dir() and str(path.relative_to(folder)) not in expected_dirs:
            raise ValueError(f"unmanaged directory in skill: {path}")
    return hashes


def sources() -> List[Tuple[str, Path, bool]]:
    found = [("kit-deliver", SOURCE, True)]
    for skill in sorted(SKILLS.iterdir()):
        if not (skill / MARKER).exists():
            continue
        if skill.is_symlink() or not skill.is_dir() or not NAME.fullmatch(skill.name):
            raise ValueError(f"invalid portable skill directory: {skill}")
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = text.split("---\n", 2)
        if (len(frontmatter) < 3 or frontmatter[0] != ""
                or not re.search(rf"^name:\s*{re.escape(skill.name)}\s*$", frontmatter[1], re.M)):
            raise ValueError(f"portable skill name must match its directory: {skill}")
        if skill.name == "kit-deliver":
            raise ValueError("portable skill conflicts with kit-deliver")
        found.append((skill.name, skill, False))
    return found


def install(repo: Path, host: str) -> str:
    if host not in HOST_PATHS:
        raise ValueError(f"unsupported host: {host}")
    root = repo.resolve()
    if not root.is_dir():
        raise ValueError("repo must be an existing directory")
    parent = root / HOST_PATHS[host]
    parent.resolve().relative_to(root)
    plans = []
    # Validate all destinations before mutating any of them.
    for name, source, include_runtime in sources():
        target = parent / name
        if target.is_symlink():
            raise ValueError("skill destination must not be a symlink")
        hashes = file_hashes(source)
        if not (source / "SKILL.md").is_file() or not hashes:
            raise ValueError(f"portable skill source is missing: {name}")
        if include_runtime:
            for script in RUNTIME_SCRIPTS:
                path = Path(__file__).resolve().parent / script
                hashes[f"scripts/{script}"] = hashlib.sha256(path.read_bytes()).hexdigest()
        if target.exists():
            if not target.is_dir():
                raise ValueError("skill destination is not a directory")
            try:
                previous = json.loads((target / MANIFEST).read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise ValueError("existing skill is not managed by this installer") from exc
            if not isinstance(previous, dict) or previous.get("files") != file_hashes(target):
                raise ValueError("existing installed skill was modified; preserve it and reconcile manually")
            if previous["files"] == hashes:
                continue
        plans.append((source, target, hashes, include_runtime))
    if not plans:
        return "unchanged"
    parent.mkdir(parents=True, exist_ok=True)
    for source, target, hashes, include_runtime in plans:
        with tempfile.TemporaryDirectory(prefix=".kit-install-", dir=str(parent)) as tmp:
            staged = Path(tmp) / target.name
            shutil.copytree(source, staged)
            if include_runtime:
                for script in RUNTIME_SCRIPTS:
                    shutil.copy2(Path(__file__).resolve().parent / script, staged / "scripts" / script)
            (staged / MANIFEST).write_text(json.dumps({"files": hashes}, indent=2) + "\n", encoding="utf-8")
            backup = parent / f".kit-backup-{uuid.uuid4().hex}"
            moved_old = False
            try:
                if target.exists():
                    os.replace(target, backup)
                    moved_old = True
                os.replace(staged, target)
            except OSError:
                if moved_old and not target.exists():
                    os.replace(backup, target)
                raise
            if moved_old:
                shutil.rmtree(backup)
    return "installed"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--host", required=True, choices=sorted(HOST_PATHS))
    args = parser.parse_args()
    try:
        print(f"kit portable skills: {install(args.repo, args.host)}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"kit portable skills: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

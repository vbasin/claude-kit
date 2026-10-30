"""Record non-sensitive kit improvement ideas for evaluation after task delivery.

Usage: backlog.py [--file PATH] add --task TEXT --idea TEXT --evidence TEXT
       backlog.py [--file PATH] list
       backlog.py [--file PATH] resolve --id ID --status STATUS --evidence TEXT
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict

DEFAULT = Path.home() / ".vtech-kit" / "learning.jsonl"


def clean(text: str) -> str:
    text = " ".join(text.split())
    if not text or len(text) > 1000:
        raise ValueError("fields must contain 1 to 1000 characters")
    return text


def read_records(path: Path) -> Dict[str, Dict[str, Any]]:
    """Replay the log. A line that does not parse, such as one cut short by a crash, is
    skipped with a warning: one bad line must not lock every later add and list."""
    records: Dict[str, Dict[str, Any]] = {}
    if not path.exists():
        return records
    skipped = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            event = None
        ident = event.get("id") if isinstance(event, dict) else None
        kind = event.get("kind") if isinstance(event, dict) else None
        if not isinstance(ident, str) or not ident or kind not in ("idea", "resolution"):
            skipped += 1
        elif kind == "idea" and ident not in records:
            records[ident] = event
        elif kind == "resolution" and ident in records:
            records[ident] = {**records[ident], "status": event.get("status"),
                              "resolution_evidence": event.get("evidence")}
        else:
            skipped += 1
    if skipped:
        print(f"backlog: skipped {skipped} unreadable line(s) in {path}", file=sys.stderr)
    return records


def append(path: Path, event: Dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    payload = (json.dumps(event, ensure_ascii=True, separators=(",", ":")) + "\n").encode("utf-8")
    if path.exists() and path.stat().st_size:
        with path.open("rb") as handle:
            handle.seek(-1, os.SEEK_END)
            if handle.read(1) != b"\n":  # a line cut short must not swallow this one
                payload = b"\n" + payload
    if len(payload) > 16384:
        raise ValueError("event is too large")
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        written = os.write(fd, payload)
        if written != len(payload):
            raise OSError("incomplete backlog write")
    finally:
        os.close(fd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DEFAULT)
    sub = parser.add_subparsers(dest="action", required=True)
    add = sub.add_parser("add")
    add.add_argument("--task", required=True)
    add.add_argument("--idea", required=True)
    add.add_argument("--evidence", required=True)
    sub.add_parser("list")
    resolve = sub.add_parser("resolve")
    resolve.add_argument("--id", required=True)
    resolve.add_argument("--status", choices=("evaluated", "rejected", "promoted"), required=True)
    resolve.add_argument("--evidence", required=True)
    args = parser.parse_args()
    try:
        records = read_records(args.file)
        if args.action == "list":
            print(json.dumps(list(records.values()), indent=2))
            return 0
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if args.action == "add":
            event = {"kind": "idea", "id": uuid.uuid4().hex, "task": clean(args.task),
                     "idea": clean(args.idea), "evidence": clean(args.evidence),
                     "status": "proposed", "created_at": now}
        else:
            if args.id not in records:
                raise ValueError("unknown backlog id")
            event = {"kind": "resolution", "id": args.id, "status": args.status,
                     "evidence": clean(args.evidence), "created_at": now}
        append(args.file, event)
        print(json.dumps(event))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"backlog: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

"""SessionStart: put the routing policy in front of Claude so one prompt is enough.

Without this, choosing the approach and the scale is left to the user. This prints both
decisions back onto Claude at the start of every session, and points at the `deliver`
skill, which holds the protocol and hands the design stage to `deliberate`.

Deliberate stdout: SessionStart is one of the events where Claude Code adds a hook's
output to the session as context. Keep it short — it is paid for in every session of
every repo that enables the kit.

Per-repo knobs in `.claude/kit.json`:

    "routing": {"enabled": false}            # opt out entirely
    "routing": {"note": "One sentence."}     # appended to the policy
"""

from __future__ import annotations

import sys

from kit_common import emit, load_config, read_input, repo_root

POLICY = (
    "kit routing policy. For any request beyond one obvious edit — a feature, a bug, an "
    "audit, a migration or a sweep — start with the `deliver` skill. It settles the "
    "approach before any code (rival designs, attacked and revised until one wins), sizes "
    "the work, picks the route (this session, parallel subagents, `/batch`, or an "
    "`ultracode:` workflow), then verifies and reviews. Choose the approach and the route "
    "yourself and say what you chose; the design is never the user's to supply."
)
NOTE_LIMIT = 400


def build_context(note: str = "") -> str:
    note = " ".join(note.split())[:NOTE_LIMIT].strip()
    return f"{POLICY} {note}" if note else POLICY


def main() -> int:
    data = read_input()
    config = load_config(repo_root(data.get("cwd")))
    routing = config.get("routing")
    routing = routing if isinstance(routing, dict) else {}
    if routing.get("enabled") is False:
        return 0
    note = routing.get("note")
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": build_context(note if isinstance(note, str) else ""),
            }
        }
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 — a hook must never break the session
        sys.exit(0)

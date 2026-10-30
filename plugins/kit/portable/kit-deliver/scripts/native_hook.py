"""Native Codex and Grok lifecycle adapters for the portable kit (Python 3.8+)."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

from bash_guard import check
from kit_common import changed_since, load_config, load_state, repo_root, save_state, snapshot
from stop_verify import verify

POLICY = ("Use the kit-deliver skill for substantive requests. Complete the user's task first; "
          "use existing relevant capabilities, obtain missing task-critical ones, compare material "
          "options, and verify the final result. Use independent reviewers when available and authorized.")


def root_for(data: Dict[str, Any]) -> Path:
    root = repo_root(data.get("cwd") or data.get("workspaceRoot"))
    if root is None:
        raise ValueError("not in a git repository")
    return root


def state_id(data: Dict[str, Any]) -> str:
    session = data.get("session_id")
    if not isinstance(session, str) or not session:
        raise ValueError("missing session id")
    return "codex-" + hashlib.sha256(session.encode()).hexdigest()


def start(data: Dict[str, Any]) -> Dict[str, Any]:
    root = root_for(data)
    sid = state_id(data)
    state = load_state(sid)
    if not state.get("baseline"):
        state["baseline"] = snapshot(root)
        state["edited"] = []
        save_state(sid, state)
    cfg = load_config(root)
    if cfg.get("routing", {}).get("enabled") is False:
        return {}
    return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": POLICY}}


def stop(data: Dict[str, Any]) -> Dict[str, Any]:
    root = root_for(data)
    state = load_state(state_id(data))
    if not state.get("baseline"):
        return {"systemMessage": "kit verification unavailable: session baseline is missing; report unverified."}
    try:
        cfg = load_config(root, strict=True)
    except ValueError as exc:
        reason = f"kit verification unavailable: {exc}; report unverified."
        return {"systemMessage": reason} if data.get("stop_hook_active") else {"decision": "block", "reason": reason}
    if not any(cfg.get(k, {}).get("enabled") for k in ("lint", "tests", "verification")):
        return {}
    changed = changed_since(root, state["baseline"], state.get("edited", []))
    if not changed:
        return {}
    failures, _, _ = verify(root, cfg, changed, deadline=time.monotonic() + 440)
    if not failures:
        return {}
    reason = "kit verification failed or is incomplete:\n" + "\n\n".join(failures)
    reason += "\nFix applicable failures or report remaining gaps; do not claim verification passed."
    if data.get("stop_hook_active"):
        return {"systemMessage": reason}
    return {"decision": "block", "reason": reason}


def guard(host: str, data: Dict[str, Any]) -> Dict[str, Any]:
    root = root_for(data)
    tool_input = data.get("tool_input") if host == "codex" else data.get("toolInput")
    if not isinstance(tool_input, dict) or not isinstance(tool_input.get("command"), str):
        return {}
    hit = check(tool_input["command"], load_config(root), root, data.get("cwd"))
    if not hit:
        return {}
    decision, reason = hit
    if decision == "deny":
        if host == "grok":
            return {"decision": "deny", "reason": reason}
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                       "permissionDecisionReason": reason}}
    if decision == "ask" and host == "codex":
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext":
                                       "Kit guard: " + reason + " Follow the host's permission policy."}}
    return {}


def main() -> int:
    try:
        host, event = sys.argv[1:3]
        data = json.load(sys.stdin)
        if not isinstance(data, dict) or host not in ("codex", "grok"):
            raise ValueError("invalid host or input")
        if event == "guard":
            output = guard(host, data)
        elif host == "codex" and event == "start":
            output = start(data)
        elif host == "codex" and event == "stop":
            output = stop(data)
        else:
            raise ValueError("unsupported host event")
        print(json.dumps(output))
    except Exception as exc:  # noqa: BLE001 — never claim success when verification could not run
        print(json.dumps({"systemMessage": f"kit hook unavailable ({type(exc).__name__}); report unverified."}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

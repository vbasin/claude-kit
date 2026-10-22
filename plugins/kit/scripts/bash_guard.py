"""PreToolUse (Bash): ask before commands that the repo's rules say need a human.

Guards (set each to "ask", "deny" or "off" under `guards` in `.claude/kit.json`):
  sql_destructive    DROP / TRUNCATE / DELETE without WHERE / hypertable chunk drops or
                     (de)compression inside any command, e.g. `psql -c "..."`.
  pytest_full_suite  a pytest run with no explicit test path, or only the top-level
                     test directory, i.e. the whole suite.
Extra repo-specific patterns go in `guards.patterns`: [{"regex", "reason", "decision"}].
"""

from __future__ import annotations

import re
import shlex
import sys
from typing import Any, Dict, List, Optional, Tuple

from kit_common import emit, load_config, read_input, repo_root

SQL_DESTRUCTIVE = re.compile(
    r"\bDROP\s+(TABLE|SCHEMA|DATABASE|MATERIALIZED\s+VIEW|VIEW|INDEX)\b"
    r"|\bTRUNCATE\b"
    r"|\b(drop_chunks|decompress_chunk|compress_chunk)\s*\(",
    re.IGNORECASE,
)
DELETE_FROM = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE = re.compile(r"\bWHERE\b", re.IGNORECASE)
QUOTES = "'\""


def _open_quotes(text: str, end: int) -> List[str]:
    """Quotes still open at `end`, innermost last. A different quote char nests, the same one closes."""
    stack: List[str] = []
    i = 0
    while i < end:
        ch = text[i]
        if ch == "\\":
            i += 2
            continue
        if ch in QUOTES:
            if stack and stack[-1] == ch:
                stack.pop()
            else:
                stack.append(ch)
        i += 1
    return stack


def _delete_without_where(text: str) -> bool:
    """True if some DELETE FROM statement in `text` ends before any WHERE.

    The statement ends at `;`, at the quote that encloses it (the `-c "..."` string or a
    host-language string), or at a shell separator. Quoted identifiers and string literals
    inside it are skipped, so `DELETE FROM "ticks" WHERE ...` counts as filtered.
    """
    for m in DELETE_FROM.finditer(text):
        enclosing = _open_quotes(text, m.start())
        host = enclosing[-1] if enclosing else None
        inner: Optional[str] = None
        visible: List[str] = []
        i = m.end()
        while i < len(text):
            ch = text[i]
            if ch == "\\":
                i += 2
                continue
            if inner:
                if ch == inner:
                    inner = None
            elif ch == host or ch == ";" or (host is None and ch in "&|"):
                break
            elif ch in QUOTES:
                inner = ch
            else:
                visible.append(ch)
            i += 1
        if not WHERE.search("".join(visible)):
            return True
    return False


def sql_destructive(command: str) -> bool:
    if SQL_DESTRUCTIVE.search(command):
        return True
    if not DELETE_FROM.search(command):
        return False
    # Check each shell word that holds a whole statement (e.g. the `-c` argument) with its
    # shell quoting removed; fall back to the raw text for heredocs and unquoted SQL.
    try:
        words = [w for w in shlex.split(command) if DELETE_FROM.search(w)]
    except ValueError:
        words = []
    found = sum(len(DELETE_FROM.findall(w)) for w in words)
    if any(_delete_without_where(w) for w in words):
        return True
    return found < len(DELETE_FROM.findall(command)) and _delete_without_where(command)

# pytest options that consume the following token as their value.
PYTEST_VALUE_OPTS = {
    "-k", "-m", "-p", "-c", "-o", "-W", "-n", "--tb", "--maxfail", "--rootdir",
    "--deselect", "--ignore", "--ignore-glob", "--confcutdir", "--basetemp",
    "--durations", "--junitxml", "--log-level", "--color", "--import-mode",
    "--override-ini", "--cov", "--cov-report", "--timeout", "--dist",
}
SEPARATOR_CHARS = set(";&|\n")
REDIRECT_CHARS = set("<>&")


def _segments(command: str) -> List[List[str]]:
    """Simple commands in `command`, split on ; && || | & and unquoted newlines, minus redirections."""
    try:
        # A backslash-newline continues the line; an unquoted newline ends the command.
        lexer = shlex.shlex(command.replace("\\\n", " "), posix=True, punctuation_chars=";&|<>\n")
        lexer.whitespace = " \t\r"
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return []
    segs: List[List[str]] = [[]]
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
        if tok and set(tok) <= SEPARATOR_CHARS:
            segs.append([])
        elif tok and set(tok) <= REDIRECT_CHARS and set(tok) & {"<", ">"}:
            i += 1  # redirection operator: also skip its target
        elif tok.isdigit() and nxt and set(nxt) <= REDIRECT_CHARS and set(nxt) & {"<", ">"}:
            pass  # file-descriptor number of a redirection such as 2>&1
        else:
            segs[-1].append(tok)
        i += 1
    return [s for s in segs if s]


WRAPPERS = {"timeout", "time", "nice", "nohup", "stdbuf", "env", "command", "builtin", "exec"}


def _pytest_args(seg: List[str]) -> Optional[List[str]]:
    """Arguments after pytest when this segment *runs* pytest, else None."""
    i = 0
    while i < len(seg):
        tok = seg[i]
        base = tok.rsplit("/", 1)[-1]
        if "=" in tok and not tok.startswith("-") and base.split("=", 1)[0].isidentifier():
            i += 1  # leading VAR=value assignment
        elif base in WRAPPERS:
            i += 1
            while i < len(seg) and (seg[i].startswith("-") or seg[i].replace(".", "").isdigit()):
                i += 1  # wrapper options / durations, e.g. `timeout 300`
        elif base in ("uv", "poetry", "pipenv", "hatch", "pdm") and i + 1 < len(seg) and seg[i + 1] == "run":
            i += 2
        else:
            break
    if i >= len(seg):
        return None
    base = seg[i].rsplit("/", 1)[-1]
    if base in ("pytest", "py.test"):
        return seg[i + 1:]
    rest = seg[i + 1:]
    if base.startswith("python") and rest[:2] == ["-m", "pytest"]:
        return rest[2:]
    return None


def is_full_suite(command: str, test_dirs: List[str]) -> bool:
    top = {d.strip("./").rstrip("/") for d in test_dirs} | {""}
    for seg in _segments(command):
        args = _pytest_args(seg)
        if args is None:
            continue
        if "--collect-only" in args or "--co" in args:
            continue
        paths: List[str] = []
        skip = False
        for tok in args:
            if skip:
                skip = False
                continue
            if tok.startswith("-"):
                skip = tok in PYTEST_VALUE_OPTS
                continue
            paths.append(tok)
        if not paths or any(p.strip("./").rstrip("/") in top for p in paths):
            return True
    return False


def check(command: str, config: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    guards = config.get("guards", {})
    mode = guards.get("sql_destructive", "ask")
    if mode != "off" and sql_destructive(command):
        return mode, (
            "Destructive database statement (DROP/TRUNCATE/DELETE without WHERE/chunk operation) "
            "needs explicit approval."
        )
    mode = guards.get("pytest_full_suite", "off")
    if mode != "off" and is_full_suite(command, config.get("tests", {}).get("test_dirs", ["tests"])):
        return mode, (
            "This runs the whole test suite. The repo's rules say to run a scoped gate instead "
            "unless the user asked for the full suite."
        )
    for pat in guards.get("patterns", []) or []:
        try:
            if re.search(pat["regex"], command):
                return pat.get("decision", "ask"), pat.get("reason", "Matches a repo guard pattern.")
        except (KeyError, re.error, TypeError):
            continue
    return None


def main() -> int:
    data = read_input()
    command = (data.get("tool_input") or {}).get("command") or ""
    if not command:
        return 0
    hit = check(command, load_config(repo_root(data.get("cwd"))))
    if hit is None:
        return 0
    decision, reason = hit
    if decision not in ("ask", "deny"):
        return 0
    emit({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    })
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 — a hook must never break the session
        sys.exit(0)

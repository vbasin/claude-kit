# claude-kit

One shared source for the Claude Code setup used across my repos (ML_analytics, Grok_Bot, and new builds). The repo is a **plugin marketplace** named `vtech-kit`. Each project turns its plugins on with a few lines in its own `.claude/settings.json`, so a change made here reaches every repo on its next update, without copying files around.

| Plugin | What it gives every repo that enables it |
|---|---|
| `kit` | One prompt is enough: `/kit:deliver` sizes a task and routes it, and a SessionStart hook tells Claude to use it. Plus hooks that lint and test what Claude changed before it can finish, guards on destructive commands, `reviewer` / `test-runner` / `security-reviewer` subagents, and the skills `/kit:verify`, `/kit:scale-out`, `/kit:spec`, `/kit:fix-issue`, `/kit:adopt` |
| `quant` | `causality-reviewer` (look-ahead leakage) and `query-reviewer` (SQL/TimescaleDB) subagents |

## What lives where

| Kind of thing | Where it goes | Why |
|---|---|---|
| Reusable hooks, agents, Claude-only skills | this repo | Edit once, every repo gets it |
| Project rules every agent should follow (Claude, Copilot, Codex, Grok) | the project's `AGENTS.md` | Vendor-neutral |
| Claude-specific project notes | the project's `CLAUDE.md`, which imports `@AGENTS.md` | When both files exist, Claude Code reads only `CLAUDE.md`. Without the import it never sees `AGENTS.md` |
| Skills shared with Copilot | the project's `.github/skills/`, symlinked into `.claude/skills/` | One copy serves both tools. Claude Code follows skill symlinks |
| Permissions, plugin switches | the project's `.claude/settings.json` | Repo-specific |
| Verify and guard settings (interpreter, lint args, test dirs, guards) | the project's `.claude/kit.json` | Repo-specific input to the shared hooks |

## Use it in a repo

1. Add this to the repo's `.claude/settings.json` (merge with what's there):

   ```json
   {
     "extraKnownMarketplaces": {
       "vtech-kit": { "source": { "source": "github", "repo": "vbasin/claude-kit" } }
     },
     "enabledPlugins": { "kit@vtech-kit": true, "quant@vtech-kit": true }
   }
   ```

2. Add `.claude/kit.json`. Start from [`plugins/kit/templates/.claude/kit.json`](plugins/kit/templates/.claude/kit.json). Without it the guards still work, but nothing is linted or tested.
3. Start `claude` in the repo and accept the folder-trust prompt. Claude Code registers the marketplace and loads both plugins. Check with `/plugin`.

Or open Claude Code in the new repo after step 1 and run `/kit:adopt`, which walks through all of it.

**Private repo access:** this repo is private, so the machine running Claude Code needs git credentials for it. On the OCI VM, `gh auth login` followed by `gh auth setup-git` is enough. If the VM has no GitHub SSH key, also set `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1`.

## Updating

Plugins here have **no `version` field on purpose**, so installs track the latest commit on `main`. To pull changes into a machine:

```
/plugin marketplace update vtech-kit
```

To make updates automatic, open `/plugin` → **Marketplaces** → `vtech-kit` → **Enable auto-update**. If you ever need to hold a repo on a known-good state, add `"version": "x.y.z"` to the plugin's `plugin.json`. Users then only move when you bump it.

## One prompt, not a routing decision

The point of the setup is that the user describes the outcome and Claude works out the scale. Two pieces do that:

- **`/kit:deliver`** holds the protocol: frame the goal and its done-check, size the work, choose between this session, parallel subagents, `/batch` and an `ultracode:` workflow, brief the workers, run the repo's gates, run the matching reviewers, then report. It also names the harness gaps it hits (a missing scope, a rule worth writing) instead of silently widening the job.
- **`session_policy.py`** prints that instruction into every session, so Claude reaches for `deliver` on its own rather than waiting to be told which tool to use.

A repo points `deliver` at its own gates and reviewers in `.claude/kit.json`:

```json
"routing": {
  "note": "Work happens on dated branches; AGENTS.md governs.",
  "gates": [ { "paths": ["src/acquisition/**"], "command": "make test-acquisition" } ],
  "reviewers": [ { "paths": ["src/features/**", "src/labels/**"], "agent": "quant:causality-reviewer" } ]
}
```

`"routing": { "enabled": false }` turns the session policy off for a repo that doesn't want it.

## How verification works

`kit` runs five small stdlib-only Python hooks (`plugins/kit/scripts/`):

| Hook | Script | Does |
|---|---|---|
| SessionStart | `session_start.py` | Records which files were already dirty, so only this session's changes are checked |
| SessionStart | `session_policy.py` | Prints the routing policy into the session, so one prompt reaches the right scale of work |
| PreToolUse (Bash) | `bash_guard.py` | Asks before `DROP`/`TRUNCATE`/`DELETE` without `WHERE`/chunk operations, before full-suite pytest runs (opt-in), and before repo-specific patterns |
| PostToolUse (Edit/Write) | `post_edit.py` | Remembers the edited file and lints it at once |
| Stop | `stop_verify.py` | Lints the session's changed `.py` files and runs only the tests that cover them, as explicit paths. On failure it sends the output back so Claude keeps working. If Claude stops again with the same failure, it lets the stop through with a notice, so a pre-existing failure can't trap a session |

Tests are picked per changed file, deleted files included: its own test file, `test_<module>*.py`, test files that import the module or name it in a patch target, and for a `conftest.py` the test files beneath it, up to `tests.max_files`. Each run starts with an empty bytecode cache, and an interpreter without pytest counts as a failure rather than a pass. A repo can add guard patterns in `.claude/kit.json`:

```json
"guards": { "patterns": [ { "regex": "databento.*(download|get_range)", "reason": "Check the data cost first", "decision": "ask" } ] }
```

## Develop

```bash
pip install pytest ruff
python -m pytest tests          # hook tests (temp git repos, no network)
claude plugin validate .        # marketplace + both plugins
claude --plugin-dir ./plugins/kit   # try local edits without pushing
```

CI runs both on every PR (`.github/workflows/validate.yml`).

## Background

The research and plan behind this setup are in [docs/PLAN.md](docs/PLAN.md).

---
name: adopt
description: Set up the kit in the current repository (CLAUDE.md wiring, .claude/settings.json, .claude/kit.json).
disable-model-invocation: true
---

Set up this repository to use the kit. Templates are in `${CLAUDE_PLUGIN_ROOT}/templates/`. Show the user each file before writing it, and never overwrite an existing file without asking.

1. **Learn the repo:** languages, package manager, test runner and test layout, lint config, virtualenv path, CI workflow, and any existing `CLAUDE.md`, `AGENTS.md`, `.github/skills/` or `.claude/` content.
2. **Instructions:**
   - If there is an `AGENTS.md`, make sure `CLAUDE.md` imports it with an `@AGENTS.md` line. Claude Code reads only `CLAUDE.md` when both exist, so without the import `AGENTS.md` is ignored.
   - If neither exists, run `/init`, then cut the result to what Claude can't infer from the code.
   - Keep `CLAUDE.md` short. Use `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md` as the shape.
3. **Settings:** start from `${CLAUDE_PLUGIN_ROOT}/templates/.claude/settings.json`:
   - pre-approve the repo's real build, test and lint commands
   - deny reads of secrets and bulky generated data
   - add ask rules for destructive commands
   - set `worktree.baseRef` to `"head"` if day-to-day work happens on a branch other than the default
4. **Verification:** start from `${CLAUDE_PLUGIN_ROOT}/templates/.claude/kit.json`:
   - set the interpreter list, the lint arguments CI actually gates on, test directories, any env file the tests need, and the guards
   - turn on `guards.pytest_full_suite` if the repo says not to run the full suite
5. **Skills shared with other agents:** if skills live in `.github/skills/` (Copilot) or elsewhere, symlink each into `.claude/skills/<name>`, e.g. `ln -s ../../.github/skills/<name> .claude/skills/<name>`. Claude Code follows skill symlinks, so there's one source and no copies.
6. **Check:** run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/stop_verify.py" --manual <one source file>` and confirm it picks sensible tests.
7. Summarize what was added, and tell the user to commit `.claude/` and `CLAUDE.md`.

---
name: verify
description: Lint and test the files changed in the working tree with the repo's scoped settings from .claude/kit.json. Use before saying work is done, or when asked to check a change.
argument-hint: "[file ...]"
allowed-tools: Bash(python3 *)
---

Run the kit's verification on the changed files (or on the files given as arguments):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/stop_verify.py" --manual $ARGUMENTS
```

It lints the changed Python files and runs the tests related to them, as explicit paths: their own test files and every test whose imports reach them, nearest first, up to `tests.max_files`. It never runs the whole suite unless the repo sets `tests.scope: "all"`. It exits 0 when verified, 1 when something failed or is incomplete.

Then:
- **OK:** say which tests ran. If none ran, say that too, since "no covering tests" is a gap worth naming.
- **INCOMPLETE:** lint and the tests that ran passed, but some coverage was missing (listed above). Report it as such; do not call the change verified.
- **Failures:** fix what the change broke and run it again. If a failure is unrelated to the change and was there before, say so and leave it.
- **Lint and tests disabled:** the repo has no `.claude/kit.json`. Offer to set one up with `/kit:adopt`.

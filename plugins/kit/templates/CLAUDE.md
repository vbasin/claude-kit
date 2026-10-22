# CLAUDE.md

<!-- Keep this file short: it loads into every session. Put rules every agent shares in AGENTS.md,
     knowledge needed only sometimes in skills, and anything Claude can read from the code nowhere. -->

@AGENTS.md

## Claude Code notes

- **Verify:** the kit plugin's Stop hook lints and tests the files you changed (config: `.claude/kit.json`). Run `/kit:verify` to check by hand.
- **Commands Claude can't guess:** <!-- e.g. `make test-api`, the venv path, the env file tests need -->
- **Review:** use the `kit:reviewer` agent on non-trivial diffs before a PR.
- **Big tasks:** read `/kit:scale-out` before fanning work out across agents.

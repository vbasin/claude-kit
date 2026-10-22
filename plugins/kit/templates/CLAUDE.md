# CLAUDE.md

<!-- Keep this file short: it loads into every session. Put rules every agent shares in AGENTS.md,
     knowledge needed only sometimes in skills, and anything Claude can read from the code nowhere. -->

@AGENTS.md

## Claude Code notes

- **Any task beyond one obvious edit:** start with `/kit:deliver`. It sizes the work, picks the route (this session, parallel subagents, `/batch`, a workflow), then verifies and reviews. The kit's SessionStart hook says the same thing at the top of each session, so you do not have to ask which tool to use.
- **Verify:** the kit plugin's Stop hook lints and tests the files you changed (config: `.claude/kit.json`). Run `/kit:verify` to check by hand.
- **Commands Claude can't guess:** <!-- e.g. `make test-api`, the venv path, the env file tests need -->
- **Review:** use the `kit:reviewer` agent on non-trivial diffs before a PR.
- **Fanning out:** `/kit:scale-out` is the detail behind `deliver`'s choice of tool.

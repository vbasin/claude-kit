---
description: Two additions made during a task, one generic and one repo-specific. Which one is offered to the shared kit, and who decides?
tags: [retention, ownership]
max_turns: 10
timeout_seconds: 360
allowed_tools: [Read, Glob, Grep, Skill, TodoWrite, AskUserQuestion]
expected_outcome: The generic one proposed for the shared plugin with its always-on cost and promotion conditional on validation and authorization; the repo-specific one stays local.
---

I've finished the nightly ingest retry in our pipeline repo and the gate is green. Two
things got added to that repo's `.claude/skills/` along the way, because they kept being
needed:

- **`repro-from-trace`** — takes a stack trace and writes the smallest script that
  reproduces it. Nothing in it mentions this repo.
- **`ingest-gate`** — runs `make test-ingest`, then reads the failures against our
  `raw_events` partition layout and says which partition is behind.

We run four other repos off the same shared plugin. Close this out — what's the wrap-up?

Neither repo is checked out where you are, so there is nothing to go and read. The
wrap-up itself is what I'm after.

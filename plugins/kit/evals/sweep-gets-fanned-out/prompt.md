---
description: Many independent mechanical edits. Does Claude pick a fan-out route and commit to it?
tags: [routing]
max_turns: 10
timeout_seconds: 360
allowed_tools: [Read, Glob, Grep, Skill, TodoWrite, AskUserQuestion]
expected_outcome: One route named and committed to, and it is a fan-out rather than one serial pass.
---

We have about 40 call sites of a deprecated helper, `get_conn()`, spread across 40
different files. Each one becomes `acquire_conn()` and the call signature is identical.
Nothing else changes, and the files don't depend on each other.

How should this run?

---
description: Forty independent units of work that each need a judgement call. Does Claude pick a fan-out route and commit to it?
tags: [routing]
max_turns: 10
timeout_seconds: 360
allowed_tools: [Read, Glob, Grep, Skill, TodoWrite, AskUserQuestion]
expected_outcome: One route named and committed to, dividing the modules across parallel workers, and saying what each worker gets.
---

We have 40 service modules that each open a database connection by hand, and each has
grown its own handling around it. Some retry on deadlock, some wrap two statements in one
transaction, a few do neither, and two swallow the error and return `None`. All 40 have to
move to the shared `acquire_conn()` context manager while keeping the behaviour that
module already has.

No two are the same, so a find-and-replace won't do it — each file needs someone to read
what it currently does and decide how it maps onto the new context manager. The modules
don't import each other, and each one has its own test file.

How should this run?

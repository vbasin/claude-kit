---
name: spec
description: Interview the user about a feature, then write a self-contained SPEC.md to implement from a fresh session.
argument-hint: "<feature in a few words>"
disable-model-invocation: true
---

Write a spec for: $ARGUMENTS

1. Read enough of the codebase to ask informed questions: the modules this touches, existing patterns to reuse, and the repo's rules in CLAUDE.md.
2. Interview the user with `AskUserQuestion`, a few questions at a time. Cover:
   - the outcome and how we will know it works (a test, a metric, a command)
   - inputs, outputs, and data or schema changes
   - edge cases and failure behaviour
   - what is explicitly out of scope
   - constraints: performance, cost, causality or data-safety rules, deadlines
   Skip anything the code already answers. Stop when the answers stop changing the design.
3. Write `SPEC.md` (or the path the user gives) with these sections: Goal, Acceptance checks (runnable), Design (files to add or change, and existing code to reuse), Data and interfaces, Edge cases, Out of scope, Open questions.
4. Tell the user to start a fresh session (`/clear`) and ask Claude to implement `SPEC.md`. A clean context implements a written spec better than a long interview transcript.

---
name: deliver
description: "Take a task from request to reviewed change: size the work, route it (this session, parallel subagents, /batch or a dynamic workflow), run it, verify it, review it. Use at the start of any request beyond one obvious edit — a feature, a bug, an audit, a migration or a sweep."
argument-hint: "<what you want built, fixed or audited>"
---

Deliver: $ARGUMENTS

You own this task end to end. Decide the routing yourself and say what you chose in one line; do not ask the user to pick the tool.

## 1. Frame it

- Restate the goal in one sentence, and name the **done-check**: the command that proves it works (a scoped test target, a test file, a script). No done-check available → say so and pick the closest one.
- Requirements unclear or the design is not obvious → stop and ask the user to run `/kit:spec <feature>` themselves (it is user-only, so you cannot start it). A written spec implemented in a fresh session beats a long interview transcript.
- Read `.claude/kit.json`. Its `routing` block (optional) names this repo's gates and reviewers: `gates` map path globs to the command that gates them, `reviewers` map path globs to the agent that must see the diff. Use them in steps 4 and 5. No block → work the gates out from the repo (`make help`, the Makefile, CI) and say which you used.

## 2. Size it

Count the units of work and ask whether they are **independent**. Dependent steps belong in one session: parallelism costs more and reviews worse.

| What you are looking at | Route |
|---|---|
| One file, an obvious fix, a question | Do it here. No fan-out, no plan mode. |
| A feature or bug over a few files, steps that depend on each other | This session. Plan mode first (Shift+Tab), `Explore` for lookups. |
| 2 to 5 independent pieces that each need judgement | Parallel subagents, one brief each. |
| The same mechanical change across many files | `/batch <the change>` — workers get their own worktrees. |
| A codebase-wide audit, migration or sweep; research to cross-check | A dynamic workflow: start the prompt with `ultracode:`. Pilot first. |
| Work that must keep running when the machine is off | Say so, and offer a cloud session or a scheduled routine. |

Escalate one step only when the pilot earns it. Never fan out a single dependent chain.

## 3. Pick the model and effort

| Who | Model | Effort |
|---|---|---|
| This session | leave as the user set it | leave it — changing it mid-session throws away the prompt cache |
| Read-heavy workers: searches, inventories, log reading | Haiku | low |
| Reviewers, test writers, parallel implementers | Sonnet | medium to high |
| A piece harder than the main task | the session's own model | high |

Never change the session's model or effort yourself. If the task needs a different one, finish, then tell the user to start a fresh session at that setting.

## 4. Run it

- Each worker gets a brief that stands alone: the goal, the exact files or slice, the repo rules that bind it, the done-check, and the output format. Workers see none of this conversation.
- A worker that edits code runs with `isolation: worktree`. Two agents never edit the same files in one checkout.
- Keep intermediate output in files, not in this conversation. For a workflow, watch per-agent token use in `/workflows` and stop a run that loops.
- Hitting a usage limit mid-run is normal on a subscription: the run pauses and resumes after the reset. Say so rather than retrying smaller.

## 5. Verify, then review

1. Run the gates for every area touched — the `routing.gates` entries whose globs match, or the repo's scoped targets. Never the full suite unless the repo says to.
2. `/kit:verify` (or let the Stop hook do it) lints and runs the covering tests for what changed.
3. Run `kit:reviewer` on any non-trivial diff, plus every `routing.reviewers` agent whose globs match the changed files. Run them in parallel, in one message.
4. Act on findings that affect correctness, safety or testability. Say which ones you skipped and why — acting on every nitpick is its own failure.

A test that fails for a reason your change did not introduce stays failing: say so, do not fix it in passing, and never skip or delete a test to get green.

## 6. Report

Close with four lines: what changed, how it was verified (the commands and their result), what you skipped and why, and what remains. Then do the repo's documentation step if it has one.

## Working out the harness as you go

When the task shows the harness is missing something, say so in the report and offer it as a follow-up rather than silently widening the job:

- A gate that does not exist for the area you changed → propose adding a scope.
- The same correction given twice → propose a rule or a line in `CLAUDE.md`.
- Knowledge needed only sometimes → propose a skill, not more `CLAUDE.md`.
- A review dimension this repo needs on every diff of a kind → propose an agent in the plugin.
- A run worth repeating → save the workflow (`s` in `/workflows`) and commit it.

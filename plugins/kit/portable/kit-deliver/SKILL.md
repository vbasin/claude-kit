---
name: kit-deliver
description: Complete a user-requested task with evidence-based decisions, existing capabilities, and proportionate verification. Use for building, optimizing, investigating, or reviewing work.
---

# Complete the user's task

Read `references/hosts.md` for this host's hooks, reviewers and fallbacks before relying on
any of them. Read `references/capabilities.md` when the task needs a capability you do not
have, or produces one worth keeping.

The user's requested result is the primary objective. Understand the goal, constraints,
authority and acceptance checks. Work in the current repository and use its existing
instructions and checks. Building a tool or skill about the task is not a substitute for
doing the task.

## Choose and use capabilities

1. Search current project code, prior applicable decisions, installed skills and tools.
   Check whether they actually work in this host and match this task; do not trust stale
   records or assume a past choice remains best when constraints or evidence have changed.
2. For a material choice, compare viable known approaches against the task criteria and
   research current primary sources when that could change the result within budget. Use
   a suitable existing capability when it wins.
3. When nothing available fits, or something you built is worth keeping, follow
   `references/capabilities.md`. It decides whether to build now or record for later, and
   what evidence a shared addition needs.
4. Reuse a previously validated capability on later matching tasks when its applicability,
   compatibility and evidence hold. Reopen the decision when a material requirement,
   dependency, source, result, or measured tradeoff changes.

## Decide what is optimal here

Define acceptance conditions before comparing substantial alternatives. Correctness and
required constraints are gates. For relevant alternatives, specify ordered criteria such as
quality, runtime, maintenance, cost, and reversibility; measure where possible and label
estimates and unknowns. Use the bundled `scripts/score.py` only when numeric measures,
bounds, weights, and evidence are meaningful. A calculated score cannot establish global
optimality or replace a test. Have an independent reviewer challenge substantial choices
when the host supports it (`references/reviewers/design-critic.md` is the brief);
otherwise critique the criteria, alternatives and evidence in this session. Avoid ceremony
for obvious edits.

Distinguish what a check measured now from outcomes that need later observation, and do
not promise the latter.

## Execute and report

Choose the most efficient available host tools; use a single worker for dependent work,
parallel work only when independent and authorized, and isolated checkouts for parallel
writers. Use host-native features when available and a sequential fallback otherwise.
Follow repository instructions and user preferences. For substantial changes use the
reviewer briefs in `references/reviewers/` that fit the change, including security, SQL or
causality when relevant; use independent reviewers if available and authorized, otherwise
report the limits of self-review. Do not assume a subagent was launched or a hook ran.

Run applicable verification on the final result: `scripts/stop_verify.py --manual` runs
the repository's configured gates. Report exactly what passed, failed, was unavailable, and
remains. Existing relevant checks and tools take priority over building a duplicate.

---
name: kit-deliver
description: Complete a user-requested task with evidence-based decisions, existing capabilities, and proportionate verification. Use for building, optimizing, investigating, or reviewing work.
---

# Complete the user's task

For host-specific discovery and supported fallbacks, read `references/hosts.md` when needed.
For candidate creation and post-task evaluation, read `references/learning.md` when needed.

The user's requested result is the primary objective. Understand the goal, constraints,
authority and acceptance checks. Work in the current repository and use its existing
instructions and checks. A task such as SEO optimization must produce and verify the
requested website improvements; creating an SEO skill is not a substitute.

## Choose and use capabilities

1. Search current project code, prior applicable decisions, installed skills and tools.
   Check whether they actually work in this host and match this task; do not trust stale
   records or assume a past choice remains best when constraints or evidence have changed.
2. For a material choice, compare viable known approaches against the task criteria and
   research current primary sources when that could change the result within budget. Use
   a suitable existing capability when it wins. If nothing available can meet the requested
   outcome, research relevant current primary sources and available tools. Select, adapt,
   or build the smallest capability necessary to complete this task. Validate its actual
   output and follow the user's permissions and budget. Do this during the task when the
   capability is a prerequisite; do not hand the task back just because a skill is missing.
3. If a usable capability already meets the task, finish and verify the user's work first.
   Record a brief non-sensitive improvement idea for later, including evidence, expected
   benefit and its applicability. Use `scripts/backlog.py add` with a task summary, idea
   and evidence when this script is available; otherwise save it in the approved kit or
   personal notes location. Do not record secrets or private source content. After the requested outcome is complete, or if the user
   explicitly asks, investigate and evaluate the kit improvement separately. Do not delay
   delivery for speculative upgrades. If the request is blocked, report the blocker and
   what was completed; do not represent the task as finished.
4. Reuse a previously validated capability on later matching tasks when its applicability,
   compatibility and evidence hold. Reopen the decision when a material requirement,
   dependency, source, result, or measured tradeoff changes. Persist transferable work in
   an authorized kit checkout with tests and evidence; keep project-specific material local.
   Mark host-neutral skills with `.kit-portable` before evaluating and promoting them to
   the shared plugin, then rerun the portable installer in repos that should receive them.

## Decide what is optimal here

Define acceptance conditions before comparing substantial alternatives. Correctness and
required constraints are gates. For relevant alternatives, specify ordered criteria such as
quality, runtime, maintenance, cost, and reversibility; measure where possible and label
estimates and unknowns. Use the bundled `scripts/score.py` only when numeric measures,
bounds, weights, and evidence are meaningful. A calculated score cannot establish global
optimality or replace a test. Have an independent reviewer challenge substantial choices
when the host supports it; otherwise critique the criteria, alternatives and evidence
in this session. Installed portable skills include `references/reviewers/design-critic.md`
and other review briefs; treat host-specific frontmatter as advisory. The Claude plugin
can use its native critic and reviewers. Avoid ceremony for obvious edits.

For SEO, distinguish measured technical checks (for example, indexability and metadata)
from traffic or ranking outcomes that require later observation. Do not guarantee rankings.

## Execute and report

Choose the most efficient available host tools; use a single worker for dependent work,
parallel work only when independent and authorized, and isolated checkouts for parallel
writers. Use host-native features when available and a sequential fallback otherwise.
Follow repository instructions and user preferences. For substantial changes use the
installed reviewer briefs appropriate to the task, including security, SQL or causality
when relevant; use independent reviewers if available and authorized, otherwise report
the limits of self-review. Run applicable verification on the final result; report exactly what passed, failed, was unavailable, and remains. Existing
relevant checks and tools take priority over building a duplicate. Record genuinely useful
follow-up opportunities without exposing secrets or changing the original task's scope.

When installed into a repo, `scripts/stop_verify.py --manual` runs configured verification
gates and `scripts/learning.py` evaluates skill candidates using a trusted fixture suite.
Use the existing plugin equivalents when those installed scripts are unavailable. After
evaluation, update the backlog using `scripts/backlog.py resolve` with the outcome and
evidence. Host
tool access, automatic hooks and permission policies vary; report unavailable checks.

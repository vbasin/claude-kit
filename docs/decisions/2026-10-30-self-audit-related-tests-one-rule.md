# The kit audited by its own workflow: related tests, one capability rule, cases that can lose

- Task: find and fix what the kit most needs after PRs #8–#14 (portable hosts, the learning
  loop, language-neutral gates, four new eval cases), using the kit's own workflow on itself.
- Done-check: `python -m pytest tests` and `claude plugin validate .` pass; every changed
  claim is re-scored with `claude plugin eval` against the version before it.
- Binding constraint: the Stop hook runs at the end of every turn in every repo that enables
  the kit, and `main` ships to all of them on the next marketplace update.
- Supersedes: the run-all-tests choice in 05d46f4..f5e72ea (no log was written for it), and
  the four copies of the capability rule in `kit-deliver`, `deliver`, `deliberate`, `improve`.

## How it was decided

1. `/kit:deliver` was run headless on this repo with the kit loaded (`claude -p
   --plugin-dir ./plugins/kit`, read-only, $0.54). It ranked seven defects; the ones acted
   on are below. Its own route call is worth recording: it judged an audit "obvious" and
   skipped `deliberate`, which was right for finding defects and wrong for fixing the top one.
2. `/kit:deliberate` was then run on that one question, with `kit:design-critic` ($0.49).
3. The four new eval cases were measured before anything changed ($0.38, one run per arm).

## Criteria

1. No false pass: a break reachable through imports is not hidden, and a gap is visible.
2. Bounded wall-clock cost per turn; nothing re-runs on a turn where nothing changed.
3. No false alarms: a gap Claude cannot fix is reported once, and does not block.
4. A claim is kept only if a case can score it; a case is kept only if it can move.
5. Less context per invocation, not more.

## Stop hook: which tests a source change runs

| | Candidate | Verdict |
|---|---|---|
| A | Every test file, every turn (main before this) | Rejected. Contradicts CLAUDE.md and `deliver`; on ML_analytics it is 180 files per turn, and with `passed_digest` never read it re-ran on turns that changed nothing |
| B | Direct importers only (the original) | Rejected. Misses a test of B when A, which B imports, changed — the case that motivated A |
| C | Transitive importers through the repo's own import graph, nearest first, capped | **Chosen** |
| D | Pick A or C from suite size or measured duration | Rejected by the critic: hidden state, so "verified" would mean different things on different turns |

The critic's open condition was empirical: drop the graph if a typical edit selects more than
half the suite or the build takes over ~10s. Measured on ML_analytics (`new_ai_fin/10-15-2026`,
347 source modules, 180 runnable test files):

| Selection | median | p75 | p90 | max | none |
|---|---|---|---|---|---|
| Direct importers (B) | 1 | 2 | 5 | 48 | 86 |
| Transitive closure (C, uncapped) | 21 | 88 | 115 | 162 | 29 |

Graph build 3.75s. 57 of 347 modules reach more than half the suite (`src/common/config.py`
reaches 162). So the typical edit passes the condition and the tail does not. That is why C
is **capped** at `tests.max_files`, nearest first, with the rest reported as a gap rather than
run or hidden, and why the README now points a repo of that size at `verification.gates`.
`tests.scope: "all"` is the opt-in for a repo whose whole suite is cheap.

Also changed: `passed_digest` is read again, and the digest covers the kit config, so a config
change still re-runs (the reason the early return had been dropped). Gaps — files no gate
covers, the cap, exclusions, a timeout — go to the user once per diff state as a
`systemMessage`; only failures block. A docs-only edit used to block the stop in every repo
with lint or tests on and no `verification` gates.

## One owner for the capability rule

`deliver` read the whole portable protocol (Codex and Grok instructions included) on top of
its own text, and `deliberate` and `improve` each restated the same rule in drifted words.
The rule now lives once, in `portable/kit-deliver/references/capabilities.md`, read on demand
by all four. The portable skill lost its SEO-specific lines (domain text in a generic skill,
which the kit's own promotion test rejects). `deliberate` again says the only thing to ask the
user is a requirement only they know.

The rule gained one claim: an instructions-only skill cannot be evaluated by an exit-code
suite (a check that passes is a check that greps the file), so its evidence is a plugin eval
case with a positive Δ. `improve` and `reusable-capability` say so.

Measured, `delivery-applies-the-floor`, two runs per arm, before → after: with-arm 1.00 → 1.00,
Δ +0.33 → +0.33, with-arm cost $0.07 → $0.06 per run. No loss from dropping the extra protocol.

## Eval cases

| Case | Before | After | Change |
|---|---|---|---|
| `task-first` | 1.00 / 1.00 | 1.00 / 1.00 | Re-framed as a guard (Δ near zero is the pass); trace grader added, since "did not build the harness first" is work that must not happen |
| `capability-required` | 0.00 / 0.00 | 1.00 / 1.00 | Grader demanded executed SEO fixes from a prompt with no site; now judges the plan. A guard |
| `host-review` | 1.00 / 1.00 | deleted | The prompt supplied the reviewer and the brief, and portability cannot be tested on one host |
| `reusable-capability` | 1.00 / 0.00 | 1.00 / 0.00 | `improve` now fires (0x → 1x); FAIL clause for file-grep evidence |
| `obvious-fix-stays-cheap` | — | 1.00 / 1.00 | Guard still holds |

All after-runs are one run per arm except `delivery-applies-the-floor`; total eval spend $1.60.

## Not done, and why

- One gate schema instead of `routing.gates` and `verification.gates`: a migration of every
  repo's `kit.json`, out of scope for a fix; `deliver` now names both.
- Removing `--host claude` from the portable installer: it serves Claude Code without the
  marketplace. Installing both in one repo loads two delivery skills; noted, not changed.

## What would change this decision

- A typical ML_analytics edit's capped selection misses breaks that its full suite catches
  (seen in a real session) → raise the default cap or require `verification.gates` there.
- The graph build exceeds ~10s on a repo that enables the kit → cache the graph by file digest.
- `task-first` or `capability-required` go negative → the improvement loop is pulling
  sessions off the task; cut `improve`'s description before anything else.

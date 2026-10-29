# Does the kit actually help?

Four cases, each one a prompt the kit claims to handle better than a bare session. Every
case runs with the plugin and again with no plugin at all, and the number that matters is
**Δ** — the with-arm score minus the without-arm score. A case that scores 1.0 in both
arms is not evidence for the kit; it is evidence the model did it anyway.

Run it from the repo root:

```bash
claude plugin eval ./plugins/kit --ablation with-without
```

Cheaper while you are changing a rubric (one arm, two runs, no Δ):

```bash
claude plugin eval ./plugins/kit --ablation none --runs 2 --case obvious-fix-stays-cheap
```

The suite uses your normal Claude Code credentials and counts against your plan's usage,
so a full pass is 4 cases × 3 runs × 2 arms = **24 agent runs**, plus three short judge
calls per `llm` grader per run. `--runs 2` and `--case <glob>` are the two dials.
Everything here is read-only: no `--allow-tools`, no `--scaffold`, no fixtures on disk —
each prompt carries whatever the task needs, so the suite never touches a real repo.

Two cases grant `Agent`, which is in the read-only set and so needs no `--allow-tools`:
`design-not-handed-back`, because `deliberate` step 5 sends the candidates to
`kit:design-critic`, and `duplication-is-a-defect`, because the review it asks for is
`kit:reviewer`'s job. Without it those cases would measure a version of the kit with its
adversary removed — the part most likely to be carrying the Δ. They pay for it in turns
and tokens, which is why their `max_turns` and `timeout_seconds` are higher than the
rest. `obvious-fix-stays-cheap` withholds `Agent` on purpose: the whole claim there is
that nothing gets escalated, and the run should not have the means to.

## What each case measures

| Case | The claim it can falsify | Read Δ as |
|---|---|---|
| `design-not-handed-back` | The design is Claude's to settle, and it settles it by comparing rivals against stated criteria | Positive: the deliberation loop is doing work a bare session doesn't |
| `obvious-fix-stays-cheap` | The kit doesn't charge design ceremony for a one-line fix | **Near zero is the pass.** Strongly negative means the kit is making trivial work expensive |
| `duplication-is-a-defect` | Duplication and dead config are reportable defects, named at their location | Positive: the standards floor in `deliver` and `reviewer` is landing |
| `sweep-gets-fanned-out` | Independent mechanical work gets fanned out, and one route is chosen rather than offered | Positive: the routing table is being used, not just read |

`obvious-fix-stays-cheap` is the one that can condemn the kit rather than praise it. Every
always-on token and every escalation the kit adds is paid on trivial prompts too, and a
suite made only of cases the kit is designed to win would never show that.

## How the graders are set up

Each case pairs a check on the **result** with a check on the **steps**, which is what
tells you whether the answer was right *and* whether the kit is what produced it.

- `regex`, `tool_used` and `file_exists` graders are computed from the transcript and
  cost nothing. Prefer them.
- `llm` graders call a judge, so their rubrics are written as concrete PASS and FAIL
  conditions with formatting explicitly ruled out, because a judge that marks a correct
  answer wrong for its layout reads as a plugin regression.
- `tool_used` on `Skill` can never pass without the plugin, so Claude Code excludes it
  from the score in both arms and reports it as an indicator. `deliberate-fired.md` is
  one of those: it tells you the skill ran, it does not earn points.
- The `min: 0, max: 0` graders carry `arm: both` so they *are* scored in both arms. That
  is deliberate — "did not hand the decision back" and "did not run the design stage on a
  typo" are exactly the comparisons that need the baseline.

## Before you trust a number

- Pin the models (`--model`, `--judge-model`) if you are comparing today's score with an
  older one. Otherwise a model rollout looks like a plugin change.
- If a case's `Skill` indicator passes but Δ is negative, suspect the judge before the
  kit: re-run with `--judge-model sonnet` and tighten the rubric.
- `results/` is gitignored. Keep the `aggregate-result.json` of a run you want to compare
  against somewhere else, or it is gone on the next run.

`tests/test_evals.py` checks the suite's schema for free, including the one failure
`claude plugin eval` accepts silently: a case whose every grader is excluded from the
two-arm score, which reports Δ of zero and proves nothing.

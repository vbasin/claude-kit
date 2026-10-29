# Measure the kit with a four-case `claude plugin eval` suite, including one case it can lose

- Task: give the kit a way to score whether its own routing and deliberation produce better work than a bare session · Done-check: `claude plugin eval ./plugins/kit --ablation with-without` reports a per-case Δ, and `python -m pytest tests/test_evals.py` passes with no model calls
- Binding constraint: no `ANTHROPIC_API_KEY`. On a Pro subscription the eval runs from a shell with the account's own credentials and spends plan usage, so it can never be a gate on every push — it has to be worth running by hand, occasionally, and cheap to narrow.

## Criteria, in priority order

1. **Falsifiable.** A case whose score cannot drop if the kit gets worse is decoration.
2. **Comparable across the two arms.** A grader that only the plugin can pass is excluded from scoring by Claude Code, so the scored graders have to be things a bare session could also achieve.
3. **Free to keep honest.** Schema and self-consistency checked without spending anything; model calls only when someone asks for a number.
4. **Cheap to narrow.** One case, two runs, one arm, when iterating on a rubric.
5. **No repo required.** Runs are empty sandboxes and granting `Bash` needs a sandbox backend, so a suite that needs fixtures on disk is a suite that fails on half the machines it's run from.

## Candidates

### A — Four prompts, graders split between result and steps, one of them a case the kit can lose · chosen

Each case carries its material in the prompt, so no scaffold and no `--allow-tools`. Result graders are `regex` and `llm` on the final message; step graders are `tool_used`. Criterion 2 is satisfied by making the scored graders behavioural ("did not hand the decision back", "named both copies of the duplicate") and demoting `tool_used: Skill` to the indicator Claude Code already treats it as.

`obvious-fix-stays-cheap` is the case that makes the suite honest. Every token the kit adds is paid on trivial prompts, and a suite made only of cases the kit is designed to win cannot report that. Its pass condition is Δ near zero, not Δ positive.

### B — Grade the deliberation transcript rather than the answer · rejected: it scores conformance, not quality

Graders over `target: trace` asserting that criteria preceded candidates, that the critic was called, that objections were answered. It measures whether the skill was followed, which is exactly the thing that is already true by construction once the skill loads, and it is unachievable in the without-arm, so every such grader is excluded from scoring and Δ collapses to zero. Criterion 1 and 2 both fail.

### C — One end-to-end case that builds something real in a scaffolded repo · rejected: fails criterion 5, and the cost is in the wrong place

A `context.scaffold_script` repo plus `--allow-tools Write Edit Bash` would test the whole `deliver` protocol. But Bash inside an eval needs `bubblewrap` and `socat` on Linux and has no backend on native Windows, where the run is refused rather than run unconfined. It also spends the most for the least discrimination: one long run has one score, and a single judge verdict over a large diff is the least stable grader there is.

### D — Keep using `claude plugin details` and `/skill-doctor` and skip the eval · rejected: measures cost, not benefit

Those readouts are free and already in use, and they answer "what does this cost per session". They cannot answer "is the output better", which is the whole objection the deliberation work exists to answer. They stay as the cost half of the picture.

### E — A promptfoo suite against `anthropic:claude-agent-sdk` · rejected: cannot load a Claude Code plugin

promptfoo's agent-SDK provider grades trajectory, cost and latency, which is the right shape, but it evaluates an SDK agent and has no way to load the plugin whose effect is being measured. It remains the right tool for the research loop in the other repo, which is an SDK agent.

## What the critique changed

Two things, both from attacking A rather than from choosing it:

- The first draft scored every case on `tool_used: Skill`. Reading the two-arm rules showed Claude Code excludes exactly that grader from scoring in both arms, so the suite as drafted would have reported Δ of zero everywhere and been read as "the kit does nothing". The scored graders moved to outcomes, and `tests/test_evals.py` now fails any case whose graders are all excluded — the one malformation `claude plugin eval` accepts silently.
- The first draft had no case the kit could lose. Added `obvious-fix-stays-cheap`, and wrote its pass condition as Δ near zero so a future reader cannot mistake a negative number for noise.

## What would change this decision

- **A pay-as-you-go API key appears.** Then criterion 3 loosens: the suite can run in GitHub Actions on every change to `plugins/kit`, pinned models, `--threshold`, `--trust-plugin`, and C stops being too expensive to justify.
- **Δ is near zero on all four cases across a couple of runs.** That is not a reason to rewrite the suite; it is a reason to stop defending the components it covers.
- **Δ on `obvious-fix-stays-cheap` is strongly negative.** Then the escalation rules in `deliver` step 2 are too eager, and that is a change to the kit, not to the case.
- **A grader type that runs custom code arrives.** Several checks here are regexes over a final message because there is no code grader; that is a constraint of the tool, not a preference.

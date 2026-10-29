# A grader on prose is an llm rubric; a regex only matches identifiers and literals

- Task: fix the grader defects the first real eval run exposed · Done-check: `python -m pytest tests/test_evals.py` green, and the guard fails a restored `picks-fan-out`
- Binding constraint: a grader that marks a correct answer wrong is worse than no grader, because it reports a plugin regression that did not happen
- Supersedes: nothing

## Criteria, in priority order

1. A correct answer must never score as a failure
2. The failure mode must be caught before a run spends plan usage, not after
3. Cheap graders stay cheap — judge calls are the thing we are rationing
4. The rule has to be checkable mechanically, or it will not hold

## Candidates

### A — regexes on prose become llm rubrics; a mechanical guard bans `|` in prose patterns · chosen

Two graders go (`picks-fan-out`, `names-the-standing-cost`), both redundant with an llm
grader that already made the same claim. A new test fails any `type: regex` grader whose
target is prose and whose pattern contains an alternation, which is the signature of a
pattern standing in for a judgement.

### B — widen each failing pattern · rejected

`all (four|five) (other )?repos` fixes one sentence and loses to the next phrasing. It
also leaves the negation hole untouched: no widening makes a regex able to tell "use
worktrees" from "skip worktrees".

### C — keep the regexes as cheap pre-filters, scored at weight 0 · rejected

An unscored grader is noise in a report nobody reads line by line, and the run showed
these specific patterns were not even diagnostic.

### D — ban regex graders on `last_message` entirely · rejected

`legacy_retry_mode` and `Connection failed` are the literal strings the prompts ask for.
They cost nothing, cannot be negated, and catch a real failure.

## What the critique changed

The first draft of the guard tried to detect "concept words" semantically. It could not
be written without a judgement call of its own, which is the thing being removed. The
alternation check is a crude proxy, and crude is the point: it is mechanical, it would
have caught both real defects, and a pattern that genuinely needs `|` can be split into
an llm rubric instead.

## What would change this decision

- A regex grader type gains a negation-aware mode, or the eval runner starts scoring
  `match: none` against a window rather than the whole message.
- A case appears whose literal check genuinely needs alternation and whose claim is not a
  judgement — a spelling with two accepted forms, say. Then the guard needs an opt-out
  marker rather than a ban.

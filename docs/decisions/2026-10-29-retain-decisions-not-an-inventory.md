# Retain what was decided, not an inventory of what exists

- Task: stop the kit re-deriving the same lookup on every run, and give a repo-local addition a path back into the kit · Done-check: `python -m pytest tests` green, and `prior-decision-is-reused` in the eval suite shows a positive Δ
- Binding constraint: anything persisted is read on a later run by a session that cannot check it. A wrong cache is therefore worse than no cache, because it is asserted with the same confidence as a fact.
- Supersedes: nothing

## Criteria, in priority order

1. **Cannot go quietly stale.** A persisted claim that has become false must either be detectable from the artifact itself or not be persisted.
2. **Zero always-on cost.** The kit is already ~702 tok in every session of every repo; retention must not be a standing context charge.
3. **Reuses what exists.** #3 already created decision logs with a reversal condition in every one. A second artifact covering the same ground is the duplication the kit's own reviewer is told to report.
4. **Answers both halves of the question** — not re-searching the same ground, and a repo-local addition reaching the kit.

## Candidates

### A — The decision logs are the memory; free readouts are the inventory · chosen

Step 2 of `deliberate` now reads the decision logs *first*, checks the reversal condition each one already carries, and either cites the log and builds what it chose or says which condition changed and carries the old candidates forward as the starting set. For the inventory half it names `claude plugin list` and `claude plugin details`, which are free and current. Step 8's template gains a `Supersedes:` line so logs chain instead of accumulating into contradictions.

This satisfies criterion 1 by construction: a log's reversal condition is the staleness check, written by the person who made the decision, and the inventory is never stored at all.

### B — A cached capability index in the repo (`.claude/capabilities.md`) · rejected: it fails criterion 1, which is the binding constraint

An index of installed skills, plugins and tools, refreshed by a skill. It is stale the moment anything is installed or removed, and the failure is silent and confident: a later session reads "skill X is available", believes it, and designs around a capability that is gone. The readouts it would cache are free, so it buys nothing in exchange for that risk. Rejected on the constraint, not on cost.

### C — Index both, with a freshness timestamp and a staleness threshold · rejected: the threshold is a guess, and it adds a maintenance surface

A timestamp tells you when the file was written, not whether it is still true: nothing about "written four days ago" distinguishes a correct entry from one invalidated an hour later. It adds a refresh step to maintain and a number to tune, for a signal that does not answer the question.

### D — Write capability findings into memory rather than the repo · rejected: wrong scope and not reviewable

Memory is per-account and invisible to the repo's other contributors and to CI. A decision about this codebase that only one person's assistant can see is not a decision the codebase has made. The decision logs are in the repo, in review, and in the diff.

## What the critique changed

The first shape of this was B — an index, because "avoid redundant searching" sounds like a caching problem. Attacking it against criterion 1 inverted it: what gets re-searched that is *worth* persisting is not the inventory, which a free command answers correctly every time, but the reasoning — what was weighed and rejected and under what condition that would change. That was already being written by #3 and simply wasn't being read.

The promotion half changed too. The first draft promoted a generic addition to the kit automatically. That makes every repo pay another always-on charge for a judgement one session made, so it is now a recommendation in the report with the cost named, and the user's call.

## What would change this decision

- **A decision log directory grows past what a session will read.** Then step 2 needs an index *of the logs* — titles, subjects and status only, generated from the logs themselves so it cannot disagree with them. That is a different artifact from B, and it is derived rather than asserted.
- **`claude plugin list` stops being free or current.** Then the inventory half needs rethinking, and B comes back on its own merits.
- **`prior-decision-is-reused` shows Δ near zero across a couple of runs.** Then a bare session already reuses a decision it is shown, and step 2's first entry is words the kit does not need.

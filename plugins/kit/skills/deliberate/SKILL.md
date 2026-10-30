---
name: deliberate
description: Choose an approach by generating rival designs, having them attacked, revising, and converging on one. Use before building anything whose shape is not obvious.
argument-hint: "<what has to be decided>"
---

Decide: $ARGUMENTS

Arrive at the best approach, not the first workable one. You own this decision. Do not
ask the user which design to take; the one thing worth asking about is in step 7.

## 1. Frame it once

One sentence for what has to be true when this is done, and the check that proves it.
Then name the constraint that actually binds: a data contract, an interface other code
depends on, a cost ceiling, a safety rule in `CLAUDE.md`. Most designs are settled by one
constraint, so find it before you draw anything.

## 2. Look up what already exists

Find out whether this is solved before designing it. In order, stopping when one fits:

1. **A decision already recorded.** Read the decision logs (`routing.decisions`, else
   the repo's own convention, else `.claude/decisions/`) before anything else. A past log
   gives you its criteria, its rejected candidates and, in its last section, the condition
   that would reverse it. Check that condition: still false → cite the log and build what
   it chose, without re-deriving it. Now true → say which condition changed, and carry the
   old candidates and objections into step 4 as the starting set rather than rediscovering
   them. This is the cheapest step here and the one most often skipped.
2. Code in this repo that already does it or nearly does. Search; do not assume.
3. A skill already enabled in this session.
4. A skill available but not enabled, or a published plugin. `claude plugin list` and
   `claude plugin details <name>` are free and current; prefer them to recall, which is
   how the same lookup gets done twice with different answers.
5. An existing skill or module worth customising instead of rewriting. A plugin's own
   skill cannot be edited in place, so customising one means a new skill under its own
   name whose description says when to use it instead.
6. Only then, something new.

If the answer turns on something that moves — a model, a tool, an API, a library version
— look it up rather than recalling it. Training data goes stale, and a search is cheap
next to building the wrong thing.

Do not build a cached inventory of what exists. An index of installed skills and tools is
stale the moment something is installed or removed, and a stale index asserting a
capability confidently is worse than no index: the readouts above are free and never
wrong. What is worth persisting is the part no command can tell you — what was decided,
what was rejected, and why — which is what the decision logs already hold.

## 3. State the criteria before you generate

Write down what makes one design better than another *here*, in priority order, before
any candidate exists. Do this first or you will rationalise whichever shape you thought
of first. Criteria come from the repo, not a template: correctness and the data or
causality rules that bind it, what it costs to run, what it costs to change later, how
much of it can be deleted when it turns out wrong, and how it gets tested.

## 4. Generate rivals, not variations

Two to four candidates that differ in **structure**. Three names for one shape is one
candidate. Axes that produce real difference: where the knowledge lives (code, config,
data), what is generated versus hand-written, what happens once versus per call, and what
you would have to undo to change your mind.

Write each as the shape in two sentences, what it costs, what it makes easy, what it
makes hard, and what it forecloses.

If the candidates all turn out to be variations of the first, the field is too narrow.
Generate the next two with subagents that each get the problem and the criteria but not
the existing candidates, so they cannot anchor on your first idea.

## 5. Have them attacked

Send the problem, the criteria and every candidate to `kit:design-critic`. It has a fresh
context and did not write them, which is the whole point: a critic that helped author a
design evaluates it instead of replacing it.

Escalate to parallel critics with opposed briefs, one arguing for each candidate, only
when the decision is expensive to reverse: a schema, a stored data layout, a public
interface, a migration. Not for a function or a script.

## 6. Revise, then have it attacked again

Fix what the critique broke. If the critique showed the *field* was wrong rather than the
candidates, generate a new candidate instead of patching the old ones.

Send the revision back with the previous objections listed. The critic answers each one
with addressed, not addressed, or no longer relevant. A round that returns nothing new
means you have converged.

**Stop when** no surviving objection would change which candidate you pick, or after
three rounds. On the third round choose anyway, and record the objection you could not
resolve instead of hiding it.

## 7. Address missing capabilities

If a missing capability would materially improve this task and future work, use `improve`
to investigate existing options and evaluate a local candidate. Name its costs, limits,
and case against it. Promote only when the task authorizes shared changes and the candidate
passes independent checks; otherwise report the candidate and next step.

Everything else is yours. Which design, how to route it, which model, whether to work in
a worktree: decide, and say what you decided.

## 8. Record it

Write the decision where this repo keeps them: `routing.decisions` in `.claude/kit.json`
if set, else the repo's existing convention (an ADR directory, a decisions folder), else
`.claude/decisions/<date>-<slug>.md`.

```markdown
# <the decision, in one line>

- Task: <the request> · Done-check: <the command or condition>
- Binding constraint: <the one that settled it>
- Supersedes: <the earlier log this replaces, and which of its reversal conditions came true — or "nothing">

## Criteria, in priority order

## Candidates
### A — <name> · chosen
### B — <name> · rejected: <why, one line>

## What the critique changed

## What would change this decision
```

The last section matters most. A decision with no stated reversal condition cannot be
reviewed later, and the log exists so the choice can be scored rather than asserted.

Write it for step 2 of the next run, which will find it by searching that directory: put
the subject in the filename and the slug, state each reversal condition as something
checkable rather than a feeling, and when you supersede a log, say so in both — a line at
the top of the old one pointing forward. Two live logs disagreeing about the same
question is the one failure mode here, and it is worse than no log.

Then hand the chosen design to `deliver`, which builds, verifies and reviews it.

---
type: llm
focus: trace
weight: 2
---

You are reading the whole session, not just its final answer. The task was a one-line
typo fix — `Conneciton` to `Connection` in a log call — and the user asked for the
corrected line and nothing else.

A session can run the whole design stage in its own turns and then reply with just the
corrected line, which the grader on the final message cannot see. That is what this
grader is for.

PASS if the session did the task and little else. Reading or searching for the line,
grepping for the same typo elsewhere, a one-line note on what changed, and a single todo
entry are all within the task.

FAIL if any assistant turn anywhere in the transcript does one of these, even when the
final message is nothing but the corrected line:
- Produces two or more candidate approaches to this fix, or compares approaches.
- Writes criteria, a scoring pass, a trade-off table or a priority list for it.
- Frames the work as a design, planning or spec stage, or announces a sequence of
  numbered phases before making the change.
- Deliberates over which route, harness, skill, agent or model to use for it.
- Expands it into work the user did not ask for — a refactor, an abstraction, a new test
  — rather than answering the question.

Judge the cost of the route, not the wording. One sentence of framing is not a design
stage, and length alone fails nothing: a long reply that only ever discusses this typo
passes. Suggesting a follow-up grep in a sentence is not scope creep; going off and
rewriting the logger is.

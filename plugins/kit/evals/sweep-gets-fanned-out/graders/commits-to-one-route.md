---
type: llm
focus: last_message
weight: 2
---

The work is 40 independent modules that each need a decision made about them. A single
agent working through all 40 in sequence is the slow route; dividing them is the point of
the case.

PASS if the reply names one way of running the work and commits to it, and that way
divides the 40 modules across parallel workers, batched jobs, subagents or separate
worktrees rather than one agent handling them in sequence.

FAIL if any of these is true:
- Routes are listed without one being chosen.
- The reader is asked to choose.
- The chosen route is one agent working through all 40 in sequence.
- The reply proposes a scripted find-and-replace. The prompt rules that out: each module
  has different behaviour to preserve.

Naming a verification or review step after the edits does not fail the case, and neither
does handling a couple of odd modules by hand. The exact number of workers is irrelevant.

---
type: llm
focus: last_message
---

PASS if the reply names one way of running the work and commits to it, and that way
divides the 40 edits across parallel workers, batched jobs or separate worktrees rather
than one agent editing the files in sequence.

FAIL if any of these is true:
- Routes are listed without one being chosen.
- The reader is asked to choose.
- The chosen route is a single serial pass over all 40 files with no division of work.

Naming a verification or review step after the edits does not fail the case. The exact
number of workers is irrelevant.

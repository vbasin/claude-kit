---
type: llm
focus: last_message
weight: 2
---

The prompt asks for no event loss when the queue is full. Judge whether the fix retains
or retries the rejected event, not whether it changes a particular function or caller.
A fix entirely inside `enqueue` can satisfy this requirement.

PASS if the reply gives a concrete overflow path that retains or retries the event:
blocking until there is room, handing overflow somewhere durable, or raising/returning a
failure together with an explicit caller or upstream retention/retry path. Caller changes
are required only when the chosen strategy depends on callers handling the rejection.

FAIL if any of these is true:
- The only change is a larger or unbounded `max_size`, which moves the failure rather
  than removing it.
- Rejection is only surfaced, logged, or checked, with no concrete retention or retry path.
- The reply asks what to do instead of choosing.
- No fix is given.

Which of the strategies is chosen is not part of this check, and neither is whether the
code is shown as a diff, a full function or prose. Naming further real problems does not
fail the case.

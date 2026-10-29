---
type: llm
focus: last_message
weight: 2
---

PASS if the reply reports the duplicated body of `normalize_order` and `normalize_refund`
as something to fix — a defect, a finding, or a change it recommends making — and
identifies both functions as the two copies.

PASS also requires that it reports `legacy_retry_mode` as config nothing reads, and says
to remove it or confirm it is unused.

FAIL if any of these is true:
- Neither problem is reported.
- The duplication is only alluded to ("consider refactoring", "some overlap") without
  saying which two pieces of code are the same.
- `legacy_retry_mode` is never mentioned, or is mentioned only as a description of the
  config rather than as a problem.
- The reply reports only style, naming, type hints, docstrings or error-message wording.

Reporting further real problems in addition does not fail the case. Whether the reply
also suggests a specific refactor is irrelevant.

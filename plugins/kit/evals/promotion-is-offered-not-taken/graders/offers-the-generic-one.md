---
type: llm
focus: last_message
weight: 2
---

PASS if all four hold:
- It says `repro-from-trace` is worth moving into the shared plugin, or is worth the
  other repos having.
- It keeps `ingest-gate` where it is, because it depends on this repo's gate, layout or
  schema. Saying nothing at all about `ingest-gate` does not count.
- It names what promoting costs: context carried by every session in every repo, or the
  equivalent in its own words.
- It either offers the move or proposes evaluating and staging a generic candidate under
  the task's authorization. It does not claim that an untested promotion is complete.

FAIL if any of these is true:
- Neither addition is discussed in terms of where it should live.
- Both are proposed for the shared plugin, or `ingest-gate` is.
- An untested promotion is stated as already complete.
- The cost of promoting is never mentioned.

Asking the reader directly whether to promote it is a pass, not a failure: the decision
is theirs. Length and formatting are irrelevant.

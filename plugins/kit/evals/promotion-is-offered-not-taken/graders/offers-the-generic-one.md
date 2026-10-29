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
- It leaves the move to the reader — proposed, recommended, offered, "if you want" — and
  not reported as already done or as something it is about to do unilaterally.

FAIL if any of these is true:
- Neither addition is discussed in terms of where it should live.
- Both are proposed for the shared plugin, or `ingest-gate` is.
- The promotion is stated as done, or as the next thing it will do, with no decision left
  to the reader.
- The cost of promoting is never mentioned.

Asking the reader directly whether to promote it is a pass, not a failure: the decision
is theirs. Length and formatting are irrelevant.

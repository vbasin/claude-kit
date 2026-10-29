---
type: llm
focus: last_message
---

PASS if the reply gives the corrected line, with "Connection" spelled correctly, and
nothing is placed before it except at most a sentence of framing.

FAIL if any of these is true:
- The corrected line is missing, or still misspells "Connection".
- The reply compares approaches, lists criteria, or weighs options before answering.
- The reply asks a question instead of answering.
- The answer is buried under sections of commentary about process, verification or
  routing.

Suggesting one brief follow-up after the corrected line, such as grepping for the same
typo elsewhere, does not fail the case.

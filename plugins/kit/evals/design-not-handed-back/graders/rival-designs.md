---
type: llm
focus: last_message
weight: 2
---

Judge the reply as a design recommendation.

PASS if all four hold:
- It puts forward at least two approaches that differ in **structure** — different places
  the state lives, different components, or a different division of responsibility. Two
  tunings of one approach (different algorithms for the same counter, different window
  sizes, different thresholds) do not count as two approaches.
- It names the criteria or the binding constraint it is choosing against, and those
  criteria are stated as the basis for the choice rather than only as praise for the
  option it already picked.
- It commits to **one** recommendation.
- It names a fact, measurement or condition that would change the recommendation.

FAIL if any of these is true:
- Only one approach is described.
- Several options are listed but none is chosen, or the choice is left to the reader.
- The reply asks for more information instead of deciding under a stated assumption.

Judge only against the four conditions. Length, headings, formatting and whether you
personally agree with the chosen design are irrelevant.

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
- The recommendation contradicts a fact the prompt states. The API runs as several
  stateless instances behind a load balancer, so a design that holds the limit in one
  process, or in per-instance state that is never shared or reconciled, cannot enforce
  one limit across them. Recommending that is a failure however well it is argued.

That last condition is about contradiction, not taste. A design that shares state by any
means — a store, a coordinator, leases, gossip, or a quota deliberately split per
instance and *stated* as approximate — is defensible and passes. Rejecting a design
because you would have chosen differently is not this condition.

Judge only against the conditions above. Length, headings and formatting are irrelevant.

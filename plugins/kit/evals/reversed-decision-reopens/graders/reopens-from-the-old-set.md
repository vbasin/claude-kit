---
type: llm
focus: trace
weight: 2
---

You are reading the whole session, not just its final answer. The user's message carries a
decision log holding three candidates, three criteria in priority order, and the measured
reason each rejected candidate lost: Postgres with `SELECT FOR UPDATE` at 14ms P99 under
2k req/s, and an in-process bucket giving 8x the configured limit across eight instances.

The log's first reversal condition has come true, so the choice is genuinely open again.
What this grader scores is where the session starts from. A superseded decision is still
most of the work.

PASS if the recorded field is the starting set. The session picks up Postgres and the
in-process bucket with the reasons they lost already in hand, and spends its effort on
what the new situation changes — whether the 14ms measurement still rules Postgres out,
what a new candidate would have to beat, whether criterion 2 reads differently now that
the dependency it protected is going away. Adding new candidates is expected here, as is
amending a criterion with a stated reason.

FAIL if the session does any of this anywhere in the transcript:
- Rebuilds the field from scratch, generating candidates and criteria as though no
  decision had ever been recorded for this question.
- Re-derives why a per-instance bucket is wrong across eight instances, or re-measures
  Postgres lock contention, rather than taking the recorded objection and asking whether
  it still holds.
- Treats the decision as still standing, carrying the shared Redis forward without
  registering that the condition for reopening fired.
- Cites the log and then ignores it, never engaging either recorded objection.

Proposing a drop-in replacement for Redis is a new candidate, not a failure, as long as
the session says the old decision no longer stands and weighs the new operational
dependency against criterion 2.

Content copied from the user's message is not the session's own work. Judge what the
session added on top of it.

---
description: The same question again, with the recorded answer's first reversal condition now true. The decision is genuinely open — does the session notice, and does it start from the old field?
tags: [design, retention]
max_turns: 18
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, AskUserQuestion]
expected_outcome: Names the reversal condition that fired, reopens the decision starting from the two recorded candidates and the measured objections that sank them, says what becomes of Postgres, and does not carry Redis forward.
---

We need to revisit where the rate-limiter counters live. Here is what's in
`docs/decisions/2026-09-02-rate-limiter-counter-store.md`:

```markdown
# Keep rate-limiter counters in the shared Redis we already run

- Task: pick the counter store for API rate limiting · Done-check: `make test-limits` green at 2k req/s
- Binding constraint: the limit must hold across all eight API instances, so the counter
  cannot live in a process.

## Criteria, in priority order
1. Correct under concurrent increments from eight instances
2. No new operational dependency
3. P99 added latency under 2ms

## Candidates
### A — the shared Redis we already run · chosen
### B — Postgres row with SELECT FOR UPDATE · rejected: lock contention at 2k req/s measured 14ms P99
### C — in-process token bucket per instance · rejected: limit becomes 8x the configured value

## What would change this decision
- Redis stops being part of the stack.
- A single instance ever serves all API traffic, which would make C correct and free.
```

Platform is retiring the shared Redis at the end of the month and nothing will run it
after that. We still run eight API instances and the 2k req/s target has not moved.
Where should the counters go?

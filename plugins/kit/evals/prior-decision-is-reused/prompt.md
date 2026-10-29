---
description: The same question asked twice, with the first answer on record and its reversal condition still false.
tags: [design, retention]
max_turns: 12
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill, TodoWrite, AskUserQuestion]
expected_outcome: Cites the recorded decision, confirms the reversal condition is still false, and proceeds with Redis — no fresh comparison of the three options.
---

We need to decide where to keep the rate-limiter counters. Here is what's in
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

Redis is still in the stack and we still run eight instances. Where should the counters go?

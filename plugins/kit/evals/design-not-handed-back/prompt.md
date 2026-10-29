---
description: An ambiguous design ask with no obvious answer. Does Claude settle it, or hand it back?
tags: [design, ownership]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, AskUserQuestion]
expected_outcome: Two or more structurally different designs, criteria stated, one chosen, and the condition that would reverse it.
---

We're adding rate limiting to our public HTTP API. Nothing is built yet — there's no
limiter, no shared cache, and the API runs as several stateless instances behind a load
balancer. Traffic is mostly small GET requests with occasional bursts from a handful of
large customers.

What should we build?

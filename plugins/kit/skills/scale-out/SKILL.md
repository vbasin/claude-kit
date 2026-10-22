---
name: scale-out
description: Choose how to split large work across agents (subagents, /batch, dynamic workflows, worktrees) and keep it within usage limits. Use before any task touching many files or needing many independent steps, such as an audit, migration or sweep.
---

# Scaling out a large task

Parallelism helps only when the pieces are independent. One chain of dependent steps runs better and cheaper in a single session.

## Pick the tool

| Situation | Use |
|---|---|
| A side question whose search output would flood this context | one subagent (`Explore` for read-only searches) |
| 2 to 5 independent pieces, each needing judgement | subagents in parallel, `isolation: worktree` if they edit |
| One mechanical change repeated across many files | `/batch` |
| Codebase-wide audit, multi-step migration, or research that should be cross-checked | a dynamic workflow: put `ultracode` in the prompt (on Pro, turn workflows on in `/config` first) |
| Pieces that must talk to each other | don't parallelise; do it in this session |

## Before launching

1. **Pilot on one slice.** Run the change or audit on one directory or 2 to 3 files, check the result, then fan out. A bad prompt multiplied by 30 agents is expensive.
2. **Give each worker a self-contained brief:** the goal, the exact files or slice, the repo rules that matter, how to verify, and the output format. Workers do not see this conversation.
3. **Decide how results get checked:** tests per slice, a reviewer pass, or a second agent that independently re-derives each finding.
4. **Keep the size proportionate.** On Pro the default workflow size is small (fewer than 5 agents). Raise it only when the pilot shows it pays off, and watch `/usage`.

## While it runs

- Keep intermediate results in files or the workflow script, not in this conversation.
- Workers that edit code need their own worktree. Never let two agents edit the same files in one checkout.
- Watch per-agent token use in `/workflows` and stop runs that loop.

## After

- Merge or apply results in one place and run the repo's scoped tests once on the combined change.
- If the run worked and will recur, save it (press `s` in `/workflows`) so it becomes a repeatable command.

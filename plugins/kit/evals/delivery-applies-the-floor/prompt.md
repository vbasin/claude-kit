---
description: A task-shaped request where the literal ask is narrower than the defect. Does the delivery protocol fix the cause, or only what was pointed at?
tags: [standards, delivery]
max_turns: 12
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, AskUserQuestion]
expected_outcome: The silent loss is fixed where it is caused — the ignored return value, the contract between enqueue and its callers — not only inside enqueue, and the answer says what it did about the callers.
---

Our webhook handler drops events when the queue is full. Here it is:

```python
def enqueue(event, queue, max_size=1000):
    if len(queue) >= max_size:
        return False
    queue.append(event)
    return True
```

Callers ignore the return value, so a full queue silently loses events. Fix it so nothing
is lost, and tell me what you changed.

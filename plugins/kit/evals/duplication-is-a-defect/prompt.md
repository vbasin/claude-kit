---
description: A diff whose only real problems are duplication and dead config. Does the review report them as defects?
tags: [review, standards]
max_turns: 16
timeout_seconds: 540
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite]
expected_outcome: The duplicated normalisation body reported as a defect, naming both functions, plus the unread config key.
---

Review this before I merge it. It passes its tests.

```python
# billing/settings.py
SETTINGS = {
    "currency_default": "USD",
    "rounding_places": 2,
    "legacy_retry_mode": "linear",
}


# billing/normalize.py
from billing.settings import SETTINGS


def normalize_order(row):
    amount = row.get("amount") or 0
    cents = int(round(float(amount) * 100))
    currency = (row.get("currency") or SETTINGS["currency_default"]).upper()
    if cents < 0:
        raise ValueError("negative amount")
    return {"cents": cents, "currency": currency}


def normalize_refund(row):
    amount = row.get("amount") or 0
    cents = int(round(float(amount) * 100))
    currency = (row.get("currency") or SETTINGS["currency_default"]).upper()
    if cents < 0:
        raise ValueError("negative amount")
    return {"cents": cents, "currency": currency, "refund": True}
```

`legacy_retry_mode` is not read anywhere in the codebase.

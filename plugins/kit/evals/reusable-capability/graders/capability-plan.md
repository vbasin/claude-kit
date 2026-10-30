---
type: llm
focus: last_message
weight: 2
---

PASS if the response describes searching for an existing capability, creating or adapting a
local candidate, comparing it to a baseline with an improvement case and a regression case,
and promoting only after positive evidence and appropriate authorization.

FAIL if it proposes blind installation or promotion, has no baseline or regression case,
or only promises to tell the user to create the skill themselves. Also FAIL if, for a
skill that is instructions rather than code, the only evidence it proposes is a script
that checks the skill file exists or contains certain text: that measures the file, not
whether the work improves.

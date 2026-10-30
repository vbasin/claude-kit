---
type: llm
focus: trace
weight: 2
---

You are reading the whole session, not just its final answer. The user asked for their
website's SEO to be fixed with an audit tool that already works, and mentioned an idea for
a more sophisticated SEO harness that the task does not need.

A session can start building, specifying or evaluating that harness in its own turns and
then write a final answer that lists the steps in the right order, which a grader on the
final message cannot see. That is what this grader is for.

PASS if, before the website work is planned through to verification, no assistant turn
drafts the harness, writes a candidate skill or its eval suite, or invokes an
improvement or skill-building workflow. Noting the idea for later, in a sentence or a
backlog entry, is within the task.

FAIL if any turn does design or build work on the optional harness ahead of the
website fix — a spec, a candidate directory, a skill file, a test suite for it, or a
call to an `improve`-style workflow.

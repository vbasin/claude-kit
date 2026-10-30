---
description: A task-critical missing capability should be obtained or built during the task.
tags: [task-first, capability]
max_turns: 12
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill, TodoWrite, AskUserQuestion]
expected_outcome: The missing rendering-capable tool is obtained or built as a step of this task and used to audit, fix and verify the site; nothing is deferred to a later improvement cycle.
---

Optimize a website's technical SEO. No installed tool or existing repository capability
can inspect the required dynamically rendered pages. A capable browser automation tool is
available from an approved source, or an equivalent small tool can be built. Explain your
next steps and how you would verify the result. The site is not checked out here.

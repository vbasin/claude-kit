---
name: fix-issue
description: "Fix a GitHub issue end to end: read it, reproduce, fix, verify, and open a PR."
argument-hint: "<issue number or URL>"
disable-model-invocation: true
allowed-tools: Bash(gh issue view *), Bash(gh pr create *)
---

Fix issue $ARGUMENTS.

1. `gh issue view $ARGUMENTS --comments` and restate the problem in one or two sentences.
2. Find the code involved. Delegate broad searches to a subagent so the file dumps stay out of this context.
3. Reproduce it: write a failing test first when the behaviour is testable, otherwise a minimal script. Say how you reproduced it.
4. Fix it with the smallest change that makes the reproduction pass. Follow CLAUDE.md.
5. Verify: run the covering tests (`/kit:verify`), then have the `kit:reviewer` agent check the diff and address real findings.
6. Create a branch, commit with a message that references the issue, and open a PR with `gh pr create`: what was wrong, the fix, and how it was verified. Ask before pushing if the repo's rules require it.

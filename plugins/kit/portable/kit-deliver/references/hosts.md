# Host integration

All hosts receive the same task-first protocol. Check the current host's available tools
and permissions at runtime; never assume the presence of another host's commands.

| Coding host | Workspace skill | Useful discovery | Verification |
|---|---|---|---|
| Claude Code | Plugin `kit:deliver` or `.claude/skills/kit-deliver` | Plugin interface and `claude plugin list` | Native hooks where enabled; or the shared manual verifier |
| Codex | `.agents/skills/kit-deliver` | Available skill list and repository `.agents/skills` | Invoke the shared manual verifier and repo CI; automatic hook parity is not assumed |
| Grok Build | `.grok/skills/kit-deliver` | `grok inspect` reports discovered configuration, skills, plugins and hooks | Invoke the shared manual verifier and repo CI; confirm host hook compatibility before relying on it |

Grok Build also documents Claude plugin compatibility and an `.agents/skills` discovery
path, but native Grok and Codex installations here use their documented workspace roots.
Portable installations include shared reviewer briefs in `references/reviewers/`, including
quantitative causality and query reviews. Host-native tools and isolation still vary; use a
fresh reviewer when available and authorized, and otherwise apply the briefs with an honest
self-review limitation.

A model API alone does not load these instructions or execute scripts; it needs a host with
filesystem and tool access. If a capability is absent, use available sequential tools, and
report checks that cannot be run.

Primary references, accessed 2026-10-29:
- https://learn.chatgpt.com/docs/build-skills
- https://docs.x.ai/build/features/skills-plugins-marketplaces
- https://docs.x.ai/build/cli/reference
- https://code.claude.com/docs/en/skills

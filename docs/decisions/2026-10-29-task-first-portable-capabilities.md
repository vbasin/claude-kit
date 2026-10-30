# Complete the task before optional kit improvement, with portable skills

- Task: deliver requests using the most effective available capabilities, retain useful
  improvements, and support Claude Code, Codex, and Grok Build.
- Done-check: offline tests exercise task scoring, deferred ideas, safe installation,
  repository gates, and reuse of an evaluated portable skill across all three layouts.
- Binding constraints: a capability needed for the current request cannot be postponed;
  optional improvement cannot delay delivery; hosts differ in hooks and tools.
- Supersedes: the timing of optional kit improvements in the earlier `improve` workflow.

## Criteria

1. Complete and verify the user's outcome within the request, authority and budget.
2. Reuse suitable existing capabilities, but reopen choices when relevant evidence changes.
3. Obtain, adapt, or create a missing prerequisite during the task; defer nonessential
   experiments until delivery and retain a non-sensitive record.
4. Share portable instructions and executable helpers while preserving each host's native
   permissions, discovery and lifecycle semantics.
5. Score only comparable evidence against explicit criteria; expose unknowns and avoid
   treating a weighted score as proof of global optimality.

## Candidates

### A — Shared portable skill, reusable helpers and host-specific installation · chosen

Keep one task protocol in Agent Skills format. Claude's delivery skill reads it; an
installer copies the same protocol, verification and learning scripts to the native
workspace skill locations for Codex, Grok Build, and Claude Code. Host-neutral skills
promoted to the plugin with a `.kit-portable` marker can be installed on each host.
A local backlog retains optional improvement ideas; a separate scoring tool evaluates
numeric measures with explicit evidence, ranges, weights, and hard thresholds.

### B — Duplicate complete host-specific plugins · rejected

Three implementations of decision rules and learning would drift and cost more to keep
consistent. Native capabilities still differ, so one skill cannot make every host identical.

### C — Build a new universal agent runtime · rejected for now

A standalone runtime could control every phase, but would duplicate hosts' tools, sessions,
permissions, and workflow orchestration before a measured need justifies that complexity.

### D — Rely only on Claude compatibility mode in Grok · rejected

Grok Build documents Claude compatibility, but that does not address Codex, nor does it
prove that every Claude lifecycle hook or permission mode behaves identically. A shared
skill and independently callable scripts provide a smaller common baseline.

## What the critique changed

A first draft only copied the common delivery skill. That would leave promoted domain
skills stranded in Claude's plugin. The installer now discovers explicitly marked
host-neutral skills dynamically; an offline test promotes a fixture SEO skill, installs it
for the three hosts and checks reuse. Missing measurements remain incomplete rather than
receiving a fabricated score. Installation refuses to overwrite local edits.

## Limits and reversal conditions

- These changes implement portable instructions and scripts, not identical automatic hook
  enforcement, review agents, or model behavior across hosts. Live Claude, Codex and Grok
  behavioral evaluations are still required.
- Discovery is host-controlled and may need explicit invocation or workspace trust.
  Stale installed skills are not automatically deleted if removed upstream.
- Replace copies with a verified shared distribution protocol if host support matures and
  real cross-repository runs demonstrate lower maintenance or better outcomes.
- Reconsider a custom runner if necessary task features remain unavailable in supported
  hosts or measured integration failures outweigh the duplicated runtime cost.

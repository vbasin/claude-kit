---
name: improve
description: Develop and evaluate a reusable skill when work exposes a recurring capability gap. Use for capability discovery, targeted research, local candidates, and evidence-based promotion.
argument-hint: "<observed gap or failure>"
---

Improve the kit for: $ARGUMENTS

1. Record the observed task and concrete failure or missing capability. Search the repo's
   existing skills, tools, decision records and validated local candidates before building.
   If current facts matter, research primary documentation and retain source URLs and dates.
2. State what improvement is expected, when it applies, when it does not, and what could
   make it worse. Prefer a small existing capability over a duplicate. Remove secrets and
   unnecessary project data from reusable material.
3. If a reusable skill is justified, create a local candidate directory containing
   `candidate.json` with string fields `name`, `purpose`, `applies_when`, `not_for`, and
   `evidence`, plus `skill/SKILL.md` and any needed supporting files. Keep it out of the
   shared plugin until evaluated. Do not install or execute untrusted downloaded code.
4. Prepare or select a trusted independent suite outside the candidate. Each case supplies
   a small fixture and an argument-array check. The check receives `KIT_CANDIDATE_DIR`: it
   is empty for baseline and points to the skill for the candidate arm. Design a case that
   detects the desired improvement and at least one regression case that should remain
   successful. Include unseen tasks from more than one repository when practical.
5. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/learning.py" evaluate CANDIDATE --suite SUITE`.
   It runs each arm in a fresh copy, rejects regressions and requires at least one observed
   improvement. A shell suite executes with your permissions; only use a suite you trust.
   A passing synthetic suite is initial evidence, not proof that a skill improves LLM work.
6. For a generic candidate, run `promote` with `--destination` pointing to an authorized
   working checkout's `plugins/kit/skills`. Promotion reruns the suite and refuses to
   overwrite existing skills. Add meaningful integration or behavior evals, review the
   changes, and prepare a draft PR when the task and available permissions authorize it.
   Repo-specific knowledge stays in the relevant repo. Do not alter a suite just to pass.
7. Report the candidate, evidence, test commands, limitations, and proposed release/rollback.
   Use a bounded budget; stop and report a blocked outcome when checks cannot be run.

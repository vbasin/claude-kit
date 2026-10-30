# Reuse and improvement after delivery

Use this when the user task revealed an optional capability improvement. If a capability is
necessary to complete the task, obtain or build the minimum needed first, complete the user
request, and then evaluate whether the capability should be reusable.

## Record the opportunity

From the installed skill directory, save only non-sensitive summaries:

```bash
python scripts/backlog.py add --task "SEO audit" --idea "Improve rendered-page audit" --evidence "Existing audit met current requirements"
python scripts/backlog.py list
```

An entry is a reminder, not an instruction to postpone the user's task or a claim that a
new idea is better. After evaluation, use `resolve --id <id> --status evaluated|rejected|promoted
--evidence <summary>`. The default file is under the user's `~/.vtech-kit/` directory.

## Create and test a reusable candidate

A candidate directory has `candidate.json` with nonempty `name`, `purpose`, `applies_when`,
`not_for`, and `evidence` strings, plus `skill/SKILL.md`. Add `skill/.kit-portable` before
evaluation only if the skill is generic and works without host-specific commands. Its
frontmatter `name` must match the candidate name. Include only the supporting files needed.

Prepare a separate trusted suite with a `cases` array. Each case has a unique meaningful
`name`, a `fixture` directory relative to the suite, and an `argv` list. For each case the
runner copies the fixture twice and invokes the command from each copy. The baseline gets an
empty `KIT_CANDIDATE_DIR`; the candidate arm gets the skill directory. The checks must use
actual outputs: one should fail without the candidate and pass with it, and another should
pass in both arms. A regression or unresolved candidate failure blocks promotion.

```bash
python scripts/learning.py evaluate /path/to/candidate --suite /path/to/suite/suite.json
python scripts/learning.py promote /path/to/candidate --suite /path/to/suite/suite.json --destination /path/to/kit/plugins/kit/skills
```

The suite runs commands with the user's privileges. Use only a trusted suite, freeze its
criteria before evaluating, and avoid a check that passes merely because the candidate
exists. Local synthetic checks are initial evidence; test actual user outcomes with the
relevant hosts and independent cases before calling a capability proven. Shared promotion
requires authorization and must not replace an existing skill. Claude's plugin copy of the
runner is under `plugins/kit/scripts/learning.py`; portable installations include it here.

Marked promoted skills are discovered on the next portable installer run. Existing
project-specific skills stay local. A removed upstream skill is not automatically deleted
from projects; review old copies before reuse.

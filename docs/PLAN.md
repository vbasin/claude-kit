# Claude Code setup for large-scale coding: research and plan (Oct 22, 2026)

_Research done on 2026-10-22 that this kit implements. Prices and feature status are as of that date._

## Bottom line

For large-scale coding, the things that raise code quality also cut cost. The research points to four of them:

1. **A check Claude can run itself**, such as tests, a build or a linter.
2. **A small, stable context.** Stable context also keeps prompt-cache hits high.
3. **The strongest model at the lowest effort that still passes your checks.**
4. **The right parallel tool for each job.**

Everything below is how to set these up with what Anthropic offers as of October 2026.

## 1. What matters most, ranked

1. **Verification loops come first.** Anthropic's best-practices guide says a check Claude can run is "the difference between a session you watch and one you walk away from." There are four ways to enforce it, from loosest to strictest:
   - Ask for it in the prompt.
   - Set a `/goal` condition. A separate evaluator re-checks it after every turn.
   - Add a **Stop hook**. Claude can't end its turn until the script passes.
   - Get a review in a fresh context: a reviewer subagent, `/code-review`, or a workflow where independent agents check each finding.
2. **Context is the scarce resource.** Quality drops as the context window fills.
   - Keep CLAUDE.md under about 200 lines.
   - Move knowledge that's only sometimes needed into skills, which load on demand.
   - Push exploration into subagents so file reads stay out of the main session.
   - Use a code-intelligence (language server) plugin instead of grep-and-read.
   - Run `/clear` between unrelated tasks.
3. **Prompt caching is the biggest cost lever.** On Opus 5.5, cached input costs $0.20 per million tokens instead of $4, about 5% of the full price. Caches are per model. Changing the model, effort level or tools mid-session breaks the cache, and so does a timestamp in a prompt.
4. **Try the strongest model at lower effort before mixing models.** Claude Opus 5.5 (released September 22, 2026) is Claude Code's default model:
   - It costs $4 / $20 per million input/output tokens. Anthropic says it costs about 40% less than Opus 5 on typical work and runs over 30% faster.
   - Its default effort is `medium`, and its thinking can't be turned off, so effort is your only dial.
   - Anthropic's cost guidance says the top model at lower effort often beats a chain of cheaper models. A lead model handing work to cheaper workers only pays off when there's a lot of independent work to split up.

## 2. Which model and effort for each role

| Role | Model | Effort |
|---|---|---|
| Main development session | Opus 5.5 | `medium` for routine work, `high` for bug fixes, `xhigh` for long or hard tasks |
| Exploration and other read-heavy subagents | Haiku 5.5 ($0.10 / $0.50) or Sonnet 5.5 ($2 / $10) | low to medium |
| Parallel reviewers, test writers, agent teammates | Sonnet 5.5 (the cost docs recommend Sonnet for teammates) | medium to high |
| The hardest design and debugging problems | Fable 5.1 ($10 / $50), or Fable/Opus as an **advisor** to a cheaper main model (experimental, Anthropic API only) | high or above |
| Interactive work where speed matters | Opus 5.5 fast mode ($8 / $40, up to 2.5× faster; Anthropic API only) | — |

Change the model or effort between sessions, not partway through one, so you don't lose the cache.

## 3. Which parallel tool for which job

| Job | Tool | Scale and status |
|---|---|---|
| A side task that would flood the main context (searches, logs) | Subagent | 20 running at once by default, nesting up to 3 deep |
| Several independent tasks you check on later | Agent view (`claude agents`) | Each session gets its own git worktree before it edits; research preview |
| One mechanical change across many files | `/batch` | 5–30 subagents, each in its own worktree |
| A codebase-wide audit, a 500-file migration, cross-checked research | **Dynamic workflows** (put `ultracode:` in the prompt, or turn on `/effort ultracode`) | 16 agents at once by default (configurable up to 256), 1,000 agents per run, resumable, can be saved as a command; generally available |
| Work spanning days that should keep running with your machine off | Projects / cloud sessions | Public beta on Pro and Max |
| Workers that need to message each other | Agent teams | Experimental; about 7× the tokens in plan mode, usually not worth it |
| Scripted fan-out in CI | A `claude -p` loop | Use `--allowedTools`, `--permission-mode dontAsk`, `--output-format json` and `--max-budget-usd` |

**Dynamic workflows are the main new capability for scale.**
- Claude writes a JavaScript orchestration script using `agent()`, `pipeline()` and `parallel()`.
- Intermediate results stay in script variables, not in Claude's context.
- Sibling agents share a prompt cache.
- Jarred Sumner used them to port Bun from Zig to Rust: about 750K lines of Rust, 99.8% of the existing tests passing, 11 days from first commit to merge (not yet in production when announced).

## 4. Implementation plan

### Phase 0: Your access type decides what's available
- **Subscription (Pro, Max, Team, Enterprise):**
  - Cloud scheduled tasks (Pro and above).
  - Managed PR Code Review (Team and Enterprise only).
  - Ultrareview.
  - Workflows that pause at a usage limit and resume after it resets.
- **API / Console:** per-token billing, workspace spend limits, the advisor tool, fast mode, the Batch API and Managed Agents.
- **Bedrock, Vertex or Foundry:**
  - Workflows work.
  - The advisor tool doesn't.
  - Code Review still needs a Claude Team or Enterprise organization.

### Phase 1: Repo setup, committed to git (about 1–2 days)
1. Update to the latest Claude Code. Many of the features below need recent v2.1.x builds.
2. Run `/init`, then cut CLAUDE.md down to what Claude can't work out from the code:
   - commands it can't guess
   - conventions that differ from the defaults
   - gotchas
   - In a monorepo, add a CLAUDE.md per package.
   - Use `.claude/rules/` with `paths:` globs for rules that apply to scattered files.
   - Use `claudeMdExcludes` for packages you never work in.
3. In `.claude/settings.json`:
   - Pre-approve build, test, lint and git commands.
   - Deny reads of build output, vendored code and generated code, e.g. `Read(./**/dist/**/*)`.
   - Set `worktree.sparsePaths` and `symlinkDirectories: ["node_modules"]` so worktrees stay small.
   - Keep the sandbox on and auto mode as the permission mode (auto is the default in v2.1.283+).
4. Install a code-intelligence plugin, e.g. `/plugin install typescript-lsp@claude-plugins-official`.
5. Hooks:
   - Run the formatter or linter after every edit.
   - **Add a Stop hook that runs the typecheck and targeted tests.**
   - Add a filter that cuts test output down to the failures.
6. Skills in `.claude/skills/`: testing patterns, migration steps, and a `fix-issue` skill set to `disable-model-invocation: true` so it only runs when you call it.
7. Subagents in `.claude/agents/`:
   - `explorer`: Haiku, read-only tools.
   - `test-runner`: Sonnet.
   - `reviewer` and `security-reviewer`: fresh context, report only gaps that affect correctness.
   - Any agent that writes code: `isolation: worktree`.
8. Once you have more than one repo, package steps 5–7 as an internal plugin.

### Phase 2: The daily loop
- The basic cycle: explore → plan in plan mode (`Ctrl+G` opens the plan for editing) → implement → verify → `/code-review` → PR.
- For big features, have Claude interview you and write `SPEC.md`, then implement it in a fresh session.
- After two failed corrections, `/clear` and start again with a better prompt.
- Use `/goal` for runs nobody is watching.

### Phase 3: Scale out
- Pilot each workflow on one directory first, watch per-agent token use in `/workflows`, then run the full scope.
- Save runs that worked (press `s`) to `.claude/workflows/` and commit them, so audits and migrations become repeatable commands.
- Tune these settings:
  - `workflowSizeGuideline`
  - `subagentPromptCacheTtl: "1h"` for long fan-outs (1-hour cache writes cost more)
  - `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` to fit your rate limits
- In headless runs, add a `Workflow` (or `Workflow(<name>)`) allow rule so workflows can start.

### Phase 4: Continuous automation
- **PR review:**
  - Managed Code Review on Team or Enterprise: guidance in `REVIEW.md`, Quick, Standard or Deep level per repo.
  - Otherwise GitHub Actions or GitLab CI with an API key.
- **Scheduled tasks (`/schedule`, research preview):**
  - Nightly flaky-test hunts, docs-drift checks and backlog triage.
  - Runs triggered by GitHub events.
  - An API trigger called from your alerting that opens a draft fix PR.
- **Pipelines that run outside the IDE:**
  - **Managed Agents** (beta):
    - Keep agent configs as versioned files synced with `ant apply`.
    - Give the lead agent a roster: copies of itself plus Haiku or Sonnet workers.
    - Turn on dynamic workflows for big jobs.
    - Use outcomes with a rubric for "keep going until it passes".
    - Set hard dollar budgets per session.
    - Keep secrets in vaults.
    - Run on a schedule with deployments.
  - Or use the **Agent SDK** to run the Claude Code harness on your own infrastructure.
  - Use the **Batch API** for offline bulk jobs: 50% off, on top of cache savings.

### Phase 5: Measure and govern
- `/usage` shows:
  - cache hit percentage, and misses with their likely cause
  - token share per skill, subagent and MCP server
  - recommendations; press `f` to apply the ones it can
- `/insights` reports friction points in how you work.
- Track spend with OpenTelemetry or the Claude Code Analytics API, cap it with workspace spend limits, and set `modelPricing` to your contracted rates.
- Org controls in managed settings: `availableModels`, `maxEffortLevel`, `workflowSizeGuideline`, `disableWorkflows`.
- Keep a 20–30-task eval built from real tickets:
  - Compare setups on **cost per completed task**.
  - After each model release, re-test effort levels and trim CLAUDE.md.
- For reference, Anthropic reports enterprise users average about $13 per developer per active day, or $150–250 per month.

## 5. Mistakes to avoid
- Switching model or effort mid-session, which resets the cache.
- Leaving ultracode on for routine work. Every task then becomes a multi-agent workflow.
- Using a lead-plus-workers setup for one dependent chain of work. A single model does it cheaper and better.
- Running parallel writers on the same files without worktrees. Agent teammates share one checkout by default.
- Acting on every reviewer nitpick, which leads to over-engineering.
- Adding a large MCP server when a CLI such as `gh` or `aws` would do.


Sources:
- [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices)
- [Manage costs effectively](https://code.claude.com/docs/en/costs)
- [Dynamic workflows docs](https://code.claude.com/docs/en/workflows)
- [Introducing dynamic workflows](https://claude.com/blog/introducing-dynamic-workflows-in-claude-code)
- [Run agents in parallel](https://code.claude.com/docs/en/agents)
- [Monorepos and large codebases](https://code.claude.com/docs/en/large-codebases)
- [Subagents](https://code.claude.com/docs/en/sub-agents)
- [Model configuration](https://code.claude.com/docs/en/model-config)
- [Advisor tool](https://code.claude.com/docs/en/advisor)
- [Scheduled tasks](https://code.claude.com/docs/en/routines)
- [Code Review](https://code.claude.com/docs/en/code-review)
- [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)
- [Introducing Claude Opus 5.5](https://www.anthropic.com/claude-opus-5-5)
- [InfoQ on dynamic workflows](https://www.infoq.com/news/2026/06/dynamic-workflows-claude-code/)
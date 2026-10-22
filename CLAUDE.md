# claude-kit

This repo is a Claude Code plugin marketplace (`vtech-kit`) consumed by other repos. See README.md for the layout.

- Hook scripts in `plugins/kit/scripts/` must stay **stdlib-only Python 3.8+**: they run on machines whose project venv may not exist yet. They must never crash or print to stdout unless they mean to (SessionStart stdout goes into Claude's context). Wrap `main()` so unexpected errors exit 0.
- Every change to a hook needs a case in `tests/test_hooks.py`. Run `python -m pytest tests` and `claude plugin validate .` before committing.
- Plugins carry no `version`, so every commit to `main` ships to every repo on its next `/plugin marketplace update`. Treat `main` as released.
- Keep model-invocable skill descriptions short, because each one costs context in every session of every repo. Use `disable-model-invocation: true` for skills only a user should start.
- Plugin agents can't use `hooks`, `mcpServers` or `permissionMode` frontmatter (ignored for plugins). Use `tools`/`disallowedTools`.

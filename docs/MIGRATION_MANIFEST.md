# Preservation record

No paths were moved or deleted in the PR #13 follow-up. Before in-place edits,
the original files from commit `c5a90c2cb30c8f6296c39e5bee94bd6af685e6c5` were copied
to `/home/ubuntu/kit-validation-backups/pr13-review/`, preserving relative paths:

- `README.md`
- `plugins/kit/scripts/gates.py`
- `plugins/kit/scripts/install_native.py`
- `plugins/kit/scripts/install_portable.py`
- `plugins/kit/scripts/kit_common.py`
- `plugins/kit/scripts/learning.py`
- `tests/test_hooks.py`
- `tests/test_learning.py`
- `tests/test_native.py`

Edits correct the four outstanding integration-review findings and document actual
host observations. The backup is local external state, not part of the distributable
kit. No `/opt/vtech` files or its data stores were changed.

## PR #14 cancellation correction

Before addressing Copilot's Ctrl-C cleanup finding, the versions at
`d7c3c0bc003dc5ba877dfdcb29dabdd3d11d6d63` of the following files were copied to
`/home/ubuntu/kit-validation-backups/pr14-interrupt/`, preserving relative paths:

- `plugins/kit/scripts/kit_common.py`
- `tests/test_hooks.py`
- `docs/HOST_VALIDATION.md`
- `docs/MIGRATION_MANIFEST.md`

The in-place correction extends process-tree cleanup to cancellation and adds
real SIGINT regression coverage. No paths were moved or deleted.

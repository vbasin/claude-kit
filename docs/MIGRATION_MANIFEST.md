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

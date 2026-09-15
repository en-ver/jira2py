# Contributing to jira2py

Thank you for improving Jira2Py. Keep changes focused, preserve the public API, and
add or update tests and documentation for observable behavior changes.

## Local checks

Use the locked project environment:

```bash
uv sync --all-groups
make check-ci
# Generate the ignored API schema exactly as the documentation workflow does.
uv run --group docs griffe dump jira2py --search src -o docs/api-reference.json 2>/dev/null
uv run --group docs python -c "
import json, re, pathlib
data = pathlib.Path('docs/api-reference.json').read_text()
# Normalize absolute paths to relative.
data = re.sub(r'\"filepath\": \"[^\"]*?/src/', '\"filepath\": \"src/', data)
data = re.sub(r'\"repository\": \"[^\"]*\"', '\"repository\": \".\"', data)
pathlib.Path('docs/api-reference.json').write_text(data)
"
uv run --group docs mkdocs build --strict
make build
```

Run focused tests while developing. Do not commit generated `site/` output unless a
change explicitly requires it.

## ADF Bridge dependency and integration checklist

Apply this checklist when changing `pyproject.toml` or `uv.lock`; updating ADF Bridge
or its public exports, signatures, profile, diagnostics, or schema; changing
ADF-aware helper/presentation code or tests; or changing ADF-related documentation.

1. Inspect the exact first-party `adf-bridge` release selected by the lock.
2. Review `docs/adf-bridge/index.md`, `docs/adf-bridge/api.md`, and Jira2Py's linked
   helper/low-level ADF boundaries. Update reviewed-version wording and versioned
   upstream links when needed.
3. Keep standalone examples as a direct `adf-bridge` dependency and `adf_bridge`
   import. Do not rely on transitive installation or add a Jira2Py re-export without
   a separately approved public runtime API change.
4. Preserve the distinction between direct bridge diagnostics/strict behavior and
   Jira2Py's private adapters and managed-media integration.
5. Update `docs/changelog.md` under `Unreleased` for user-visible documentation or
   tooling changes.
6. Run `uv run --frozen python -m pytest tests/test_adf_bridge_docs_contract.py -v`,
   then the local checks above.

For changes that alter Jira behavior, follow the repository's applicable local
validation and release process before opening or updating a release change.

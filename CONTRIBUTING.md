# Contributing to chunkcite

Thanks for helping make RAG citations verifiable.

## Quick start

```bash
pip install -e ".[dev]"
python -m pytest -q
```

## Rules

- No LLM calls in the library path. Everything must be reproducible offline.
- Every new chunking rule needs a test with a real document snippet.
- No copied code: if you adapt an algorithm, credit the source in the
  docstring and check its license first.
- Use only synthetic or public example data. Never commit secrets,
  employer code, or private documents.

## Good first issues

See the open issues labelled `good first issue` on GitHub.
If one is already assigned, please pick another — and if you want to
work on one, comment first so it can be assigned to you. PRs are
reviewed promptly, CI must pass, and no contribution is auto-merged.

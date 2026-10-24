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

See `.github/ISSUES_DRAFT/` — these are prepared to be opened as
"good first issue" issues after the first release.

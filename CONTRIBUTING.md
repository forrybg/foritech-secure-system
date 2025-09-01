# Contributing

Thanks for your interest in ForiTech Secure System!

## How we work
- Branches: feature/*, fix/*, docs/*
- Open a PR to `main`, keep it small and focused.
- CI must be green. Add/adjust tests when changing behavior.

## Dev quickstart
1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -U pip`
3. `pip install -r requirements.txt || true`
4. `pytest -q` (core tests should pass even without OQS)

## Code style
- Python: `ruff`/`black` (configured in `pyproject.toml`)
- Shell: `shellcheck` (advice)
- Commits: conventional-ish (feat:, fix:, docs:, chore:, refactor:)

## Security & secrets
- Never commit private keys, tokens, real certs, or production configs.
- Use `.gitignore` and `detect-secrets` (pre-commit).

## Reporting issues
Open a GitHub issue with steps to reproduce and logs.

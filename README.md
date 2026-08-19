# Personal AI Assistant

Daily 5-questions AI assistant backend.

Project goal: build an adaptive daily Q/A service that:
- selects 5 questions based on user state,
- avoids repetitive questions with cooldown rules,
- stores check-ins and answers in Postgres,
- returns structured day artifacts,
- is ready for streaming, tool calling, and RAG.

## Tech Stack

- Python 3.12+
- `uv` for dependency management
- Ruff + Mypy for code quality
- Pre-commit hooks
- GitHub Actions CI (lint job)

## Project Status

Current repository is in early scaffold stage:
- base Python project initialized;
- quality tooling configured (`ruff`, `mypy`, `pre-commit`);
- CI workflow added for lint/type checks.

Business endpoints and data models are planned next.

## Local Setup

### 1) Install dependencies

```bash
uv sync --group dev --no-install-project
```

`--no-install-project` is used because this repo currently focuses on tooling/scaffold and may not yet have a finalized package layout.

### 2) Run quality checks

```bash
uv run ruff check .
uv run mypy .
```

Or use the helper script:

```bash
bash ./scripts/lint.sh
```

### 3) Enable pre-commit hooks

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

Configured hooks:
- Ruff check
- Mypy check

## CI

Workflow path: `.github/workflows/ci.yml`

On push/PR to `main`, CI runs:
1) setup `uv` and Python
2) install dependencies (`uv sync --frozen --all-groups --no-install-project`)
3) run lint script (`bash ./scripts/lint.sh`)

## Planned Architecture (next steps)

Target direction (based on project spec):
- FastAPI routers for daily check-in flow
- service layer for question selection logic (state + cooldown + diversification)
- repository layer for Postgres persistence
- structured response schemas via Pydantic
- optional extensions: streaming, tools, RAG

## Useful Commands

```bash
# Lint + type-check
bash ./scripts/lint.sh

# Run pre-commit hooks manually
uv run pre-commit run --all-files
```

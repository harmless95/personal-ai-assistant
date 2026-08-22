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
- FastAPI + Pydantic Settings
- SQLAlchemy 2.x (async) + asyncpg
- PostgreSQL
- `uv` for dependency management
- Ruff + Mypy for code quality
- Pytest + pytest-asyncio + pytest-cov
- Pre-commit hooks
- GitHub Actions CI (lint + test)

## Project Status

Implemented in this repository right now:
- base FastAPI app with health-check endpoint;
- auth (`register` / `login` / JWT / `me` / refresh / `logout`);
- daily check-in `ask` / `answer` / `history` / `artifact` endpoints (auth required);
- LLM day summary via Taskiq worker (poll `GET .../artifact/` until ready);
- centralized settings via `pydantic-settings`;
- async DB session layer for Postgres;
- lint + type-check setup (`ruff`, `mypy`);
- test tooling (`pytest`, `pytest-asyncio`, `pytest-cov`);
- pre-commit hooks;
- CI workflow for lint and tests;
- Docker image and Compose (`db` / `redis` / `migrate` / `backend` / `worker` / `bot`);
- Telegram bot MVP (`/login`, `/checkin`, `/history`) as an HTTP client of the API.

## Local Setup

### 1. Prepare environment

Make sure Python 3.12+ is installed.

```bash
# Install dependencies
uv sync --group dev --no-install-project

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Example environment variables:

```env
ENVIRONMENT=development
API_PREFIX_V1=/api/v1

HOST__HOST=127.0.0.1
HOST__PORT=8000

DB__POSTGRES_USER=postgres
DB__POSTGRES_PASSWORD=secret
DB__POSTGRES_HOST=localhost
DB__POSTGRES_PORT=5432
DB__POSTGRES_DB=personal_ai_assistant
```

Variables are loaded via `pydantic-settings` with nested delimiter `__` (see `app/config.py`).  
`DB__POSTGRES_*` values must match the PostgreSQL container credentials.

### 2. Start stack with Docker

From the repository root (uses `.env`):

```bash
docker compose -f Docker-compose.yml up -d --build
```

This starts Postgres, Redis, migrations, API, the Taskiq worker, and (if `TELEGRAM__BOT_TOKEN` is set) the Telegram bot.

Worker (day summary LLM):

```bash
taskiq worker app.tasks.broker_taskiq:broker
```

Telegram bot (local, API must be running):

```bash
# 1) Set TELEGRAM__BOT_TOKEN in .env (from @BotFather)
# 2) Register a user via Swagger: POST /api/v1/auth/register
python -m app.bot
```

In Telegram:
- `/login email password` (or `/login` then follow prompts)
- `/checkin` — state buttons → 5 questions → day summary
- `/history` — recent check-ins
- `/cancel` — reset dialog

Postgres only:

```bash
docker compose -f Docker-compose.yml up -d db
```

### 3. Run database migrations (local app)

If you run the API on the host against Docker Postgres:

```bash
alembic -c app/alembic.ini upgrade head
```

### 4. Run the application (local)

From the repository root:

```bash
python -m app.main
```

After startup, the API is available at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

Swagger docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Health-check endpoint: `GET /api/v1/utils/health-check`

Auth:
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login` (OAuth2 password form)
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/token/refresh`
- `POST /api/v1/auth/logout`

Daily check-in (Bearer access token required):
- `POST /api/v1/daily/checkin/ask/`
- `POST /api/v1/daily/checkin/answer/`
- `GET /api/v1/daily/checkin/history/`
- `GET /api/v1/daily/checkin/{checkin_id}/artifact/`

---

## Testing

Tests are run with **pytest**.

```bash
# Run all tests
uv run pytest

# Verbose output
uv run pytest -v
```

Or use the helper script:

```bash
bash ./scripts/test.sh
```

---

## Code Quality Checks

```bash
# Lint + type-check
bash ./scripts/lint.sh

# Run separately
uv run ruff check .
uv run mypy .
```

### Pre-commit hooks

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

Configured hooks:
- Ruff check
- Mypy check

---

## CI

Workflow path: `.github/workflows/ci.yml`

On push/PR to `main`, CI runs:
1) setup `uv` and Python
2) install dependencies (`uv sync --frozen --all-groups --no-install-project`)
3) lint job: `bash ./scripts/lint.sh`
4) test job: `bash ./scripts/test.sh`

## Roadmap

Planned work is tracked in `docs/roadmap.md`.

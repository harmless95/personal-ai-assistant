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
- `uv` for dependency management
- Ruff + Mypy for code quality
- Pytest + pytest-asyncio + pytest-cov
- Pre-commit hooks
- GitHub Actions CI (lint + test)

## Project Status

Implemented in this repository right now:
- base FastAPI app with health-check endpoint;
- centralized settings via `pydantic-settings`;
- lint + type-check setup (`ruff`, `mypy`);
- test tooling (`pytest`, `pytest-asyncio`, `pytest-cov`);
- pre-commit hooks;
- CI workflow for lint and tests.

## Local Setup

### 1. Подготовка окружения

Убедитесь, что у вас установлен Python 3.12+.

```bash
# Установка зависимостей
uv sync --group dev --no-install-project

# Для Windows:
.venv\Scripts\activate
# Для macOS/Linux:
source .venv/bin/activate
```

Создайте файл `.env` в корневом каталоге проекта (можно скопировать из `.env.example`):

```bash
cp .env.example .env
```

Пример переменных окружения:

```env
ENVIRONMENT=development
API_PREFIX_V1=/api/v1

HOST__HOST=127.0.0.1
HOST__PORT=8000
```

Переменные читаются через `pydantic-settings` с вложенным delimiter `__` (см. `app/config.py`).

### 2. Запуск приложения

Из корня репозитория:

```bash
python -m app.main
```

После запуска API будет доступно по адресу: [http://127.0.0.1:8000](http://127.0.0.1:8000)

Документация Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Health-check endpoint: `GET /api/v1/utils/health-check`

---

## Тестирование

Для запуска тестов используется **pytest**.

```bash
# Запуск всех тестов
uv run pytest

# Запуск с подробным выводом (verbose)
uv run pytest -v
```

Или через helper script:

```bash
bash ./scripts/test.sh
```

---

## Проверки качества кода

```bash
# Lint + type-check
bash ./scripts/lint.sh

# Отдельно
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

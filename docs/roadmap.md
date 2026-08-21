# Roadmap

This document tracks planned work that is not implemented yet.

## Done

- FastAPI routers for daily check-in flow (`ask`, `answer`, `history`, `artifact`).
- Service layer for question selection (state + cooldown).
- Repository layer and Postgres persistence for check-ins, answers, and artifacts.
- Structured response schemas for day summary / artifact output.
- Auth (`register` / `login` / JWT access+refresh / `me` / `logout`) wired into daily check-in.
- Docker image + Compose services for `db` / `migrate` / `backend`.
- LLM day summary on `/answer` (OpenAI JSON) with template fallback.

## Next Steps

- Replace question selection with LLM or hybrid pool+LLM (optional).
- Add streaming responses (SSE or WebSocket).
- Add tool calling (`search_docs`) with retries/fallback.
- Add RAG pipeline (ingest + retrieval) for knowledge-assisted prompts.
- Optionally add FK from `daily_checkins.user_id` to `users.id`.

## Environment Expansion (Planned)

Future `.env.example` sections will be added when corresponding features are implemented:
- Redis/Task queue settings
- RAG/index settings

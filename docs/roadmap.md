# Roadmap

This document tracks planned work that is not implemented yet.

## Done

- FastAPI routers for daily check-in flow (`ask`, `answer`, `history`, `artifact`).
- Service layer for question selection (state + cooldown).
- Repository layer and Postgres persistence for check-ins, answers, and artifacts.
- Structured response schemas for day summary / artifact output.
- Auth (`register` / `login` / JWT access+refresh / `me` / `logout`) wired into daily check-in.

## Next Steps

- Replace template day summary with LLM-generated structured output.
- Add streaming responses (SSE or WebSocket).
- Add tool calling (`search_docs`) with retries/fallback.
- Add RAG pipeline (ingest + retrieval) for knowledge-assisted prompts.
- Fix Docker `migrate` service (add Dockerfile or drop compose migrate step).
- Optionally add FK from `daily_checkins.user_id` to `users.id`.

## Environment Expansion (Planned)

Future `.env.example` sections will be added when corresponding features are implemented:
- Redis/Task queue settings
- LLM provider settings
- RAG/index settings

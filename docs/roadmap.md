# Roadmap

This document tracks planned work that is not implemented yet.

## Next Steps

- Add FastAPI routers for daily check-in flow (`ask`, `answer`, `history`, `artifact`).
- Add service layer for question selection (state + cooldown + diversification).
- Add repository layer and Postgres persistence for check-ins, answers, and artifacts.
- Add structured response schemas for day summary output.
- Add streaming responses (SSE or WebSocket).
- Add tool calling (`search_docs`) with retries/fallback.
- Add RAG pipeline (ingest + retrieval) for knowledge-assisted prompts.

## Environment Expansion (Planned)

Future `.env.example` sections will be added when corresponding features are implemented:
- Postgres settings
- Redis/Task queue settings
- LLM provider settings
- RAG/index settings

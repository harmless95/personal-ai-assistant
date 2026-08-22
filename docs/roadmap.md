# Roadmap

This document tracks planned work that is not implemented yet.

## Done

- FastAPI routers for daily check-in flow (`ask`, `answer`, `history`, `artifact`).
- Service layer for question selection (state + cooldown).
- Repository layer and Postgres persistence for check-ins, answers, and artifacts.
- Structured response schemas for day summary / artifact output.
- Auth (`register` / `login` / JWT access+refresh / `me` / `logout`) wired into daily check-in.
- LLM day summary on `/answer` enqueued via Taskiq; worker writes artifact (template fallback).
- Artifact lifecycle status (`pending` / `ready` / `failed`) on check-in artifact GET.
- Provider-pluggable day summary clients (`openai` / `template`) with shared OpenAI-compatible layer.
- Docker image + Compose services for `db` / `redis` / `migrate` / `backend` / `worker`.
- Structlog + CI (lint/tests on push and PR).
- FK from `daily_checkins.user_id` to `users.id` (`ON DELETE RESTRICT`).
- LLM usage metrics (tokens, estimated cost, latency) logged from day-summary worker calls.
- Telegram bot MVP (`/login`, `/checkin`, `/history`) calling the HTTP API via httpx.

## Next

- Optional SSE notify when artifact becomes ready (useful for web clients).
- LLM Gateway service over gRPC (optional training/architecture step).

## Later

- Replace question selection with LLM or hybrid pool+LLM (optional).
- Streaming responses for interactive coaching (SSE preferred; WebSocket if full chat).
- Tool calling (`search_docs`) with retries/fallback.
- Knowledge/RAG service in the same monorepo (`services/knowledge`): retrieve context for day-summary prompts.
  - Prefer curated or user docs over random public datasets.
  - Split into a separate deployable service only if indexing/search needs its own scale/release cycle.
- Tooling/eval harness for day-summary JSON quality (fallback rate, golden cases).

## Environment Expansion (Planned)

Future `.env.example` sections will be added when corresponding features are implemented:

- RAG/index settings
- Knowledge service URL (when split from the API process)
- LLM gateway gRPC address (when split)

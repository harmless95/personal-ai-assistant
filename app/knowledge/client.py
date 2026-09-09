from __future__ import annotations

import grpc

from app.knowledge.models import KnowledgeChunkHit
from knowledge_services.grpc_gen.knowledge.v1 import knowledge_pb2, knowledge_pb2_grpc


class KnowledgeSearchError(Exception):
    """Raised when the knowledge gRPC Search call fails."""


class KnowledgeGrpcClient:
    """Thin async client for KnowledgeService.Search."""

    def __init__(
        self,
        *,
        target: str,
        top_k: int = 3,
        timeout_seconds: float = 5.0,
        enabled: bool = True,
    ) -> None:
        self._target = target
        self._top_k = top_k
        self._timeout_seconds = timeout_seconds
        self._enabled = enabled

    async def search(self, query: str, *, top_k: int | None = None) -> list[KnowledgeChunkHit]:
        if not self._enabled:
            return []

        cleaned = query.strip()
        if not cleaned:
            return []

        resolved_top_k = top_k if top_k is not None else self._top_k
        try:
            async with grpc.aio.insecure_channel(self._target) as channel:
                stub = knowledge_pb2_grpc.KnowledgeServiceStub(channel)  # type: ignore[no-untyped-call]
                response = await stub.Search(
                    knowledge_pb2.SearchRequest(query=cleaned, top_k=resolved_top_k),
                    timeout=self._timeout_seconds,
                )
        except grpc.aio.AioRpcError as exc:
            raise KnowledgeSearchError(f"knowledge Search failed: {exc.code()}: {exc.details()}") from exc
        except grpc.RpcError as exc:
            raise KnowledgeSearchError(f"knowledge Search failed: {exc}") from exc

        return [
            KnowledgeChunkHit(
                chunk_id=chunk.chunk_id,
                source=chunk.source,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                tags=tuple(chunk.tags),
            )
            for chunk in response.chunks
        ]

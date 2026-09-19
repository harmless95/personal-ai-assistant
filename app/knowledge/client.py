from __future__ import annotations

import grpc

from app.knowledge.models import KnowledgeChunkHit, KnowledgeIngestFileResult
from knowledge_services.grpc_gen.knowledge.v1 import knowledge_pb2, knowledge_pb2_grpc


class KnowledgeSearchError(Exception):
    """Raised when the knowledge gRPC Search call fails."""


class KnowledgeIngestError(Exception):
    """Raised when the knowledge gRPC IngestFile call fails."""


class KnowledgeGrpcClient:
    """Thin async client for KnowledgeService Search / IngestFile."""

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

    async def ingest_file(
        self,
        content: bytes,
        *,
        source: str,
        content_type: str = "text/plain",
        tags: list[str] | None = None,
    ) -> KnowledgeIngestFileResult:
        if not self._enabled:
            raise KnowledgeIngestError("knowledge client is disabled")
        if not content:
            raise KnowledgeIngestError("content must be non-empty")
        cleaned_source = source.strip()
        if not cleaned_source:
            raise KnowledgeIngestError("source must be non-empty")

        try:
            async with grpc.aio.insecure_channel(self._target) as channel:
                stub = knowledge_pb2_grpc.KnowledgeServiceStub(channel)  # type: ignore[no-untyped-call]
                response = await stub.IngestFile(
                    knowledge_pb2.IngestFileRequest(
                        content=content,
                        source=cleaned_source,
                        content_type=content_type,
                        tags=tags or [],
                    ),
                    timeout=max(self._timeout_seconds, 60.0),
                )
        except grpc.aio.AioRpcError as exc:
            raise KnowledgeIngestError(f"knowledge IngestFile failed: {exc.code()}: {exc.details()}") from exc
        except grpc.RpcError as exc:
            raise KnowledgeIngestError(f"knowledge IngestFile failed: {exc}") from exc

        return KnowledgeIngestFileResult(
            chunks_saved=response.chunks_saved,
            s3_key=response.s3_key,
        )

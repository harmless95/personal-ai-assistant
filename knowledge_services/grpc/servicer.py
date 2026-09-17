import grpc
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from knowledge_services.core.data.repository import KnowledgeChunkRepository
from knowledge_services.core.embeddings.protocol import Embedder
from knowledge_services.core.ingest.document_service import DocumentIngestService
from knowledge_services.core.ingest.service import IngestService
from knowledge_services.core.retrievers.service import RetrieverService
from knowledge_services.core.storage.s3 import S3ObjectStorage
from knowledge_services.core.storage.session import s3_client_scope
from knowledge_services.db.models import KnowledgeChunk
from knowledge_services.db.session import session_scope
from knowledge_services.grpc_gen.knowledge.v1 import knowledge_pb2, knowledge_pb2_grpc


class KnowledgeServicer(knowledge_pb2_grpc.KnowledgeServiceServicer):
    def __init__(
        self,
        *,
        embedder: Embedder,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._embedder = embedder
        self._session_factory = session_factory

    async def Health(
        self,
        request: knowledge_pb2.HealthRequest,
        context: grpc.aio.ServicerContext,
    ) -> knowledge_pb2.HealthResponse:
        _ = request, context
        return knowledge_pb2.HealthResponse(ok=True)

    async def Search(
        self,
        request: knowledge_pb2.SearchRequest,
        context: grpc.aio.ServicerContext,
    ) -> knowledge_pb2.SearchResponse:
        top_k = request.top_k if request.top_k > 0 else 3
        try:
            async with session_scope(self._session_factory) as session:
                retriever = RetrieverService(
                    embedder=self._embedder,
                    repository=KnowledgeChunkRepository(session),
                )
                chunks = await retriever.search(request.query, top_k=top_k)
                return knowledge_pb2.SearchResponse(
                    chunks=[_to_proto_chunk(chunk) for chunk in chunks],
                )
        except Exception as exc:
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))
            raise

    async def IngestText(
        self,
        request: knowledge_pb2.IngestTextRequest,
        context: grpc.aio.ServicerContext,
    ) -> knowledge_pb2.IngestTextResponse:
        if not request.text.strip() or not request.source.strip():
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "text and source are required",
            )
            raise

        try:
            async with session_scope(self._session_factory) as session:
                ingest = IngestService(
                    embedder=self._embedder,
                    repository=KnowledgeChunkRepository(session),
                )
                saved = await ingest.ingest_text(
                    request.text,
                    source=request.source,
                    tags=list(request.tags) or None,
                )
                return knowledge_pb2.IngestTextResponse(chunks_saved=len(saved))
        except Exception as exc:
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))
            raise

    async def IngestFile(
        self,
        request: knowledge_pb2.IngestFileRequest,
        context: grpc.aio.ServicerContext,
    ) -> knowledge_pb2.IngestFileResponse:
        if not request.content or not request.source.strip():
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "content and source are required",
            )
            raise

        content_type = request.content_type.strip() or "text/plain"
        try:
            async with s3_client_scope() as s3_client:
                async with session_scope(self._session_factory) as session:
                    documents = DocumentIngestService(
                        embedder=self._embedder,
                        repository=KnowledgeChunkRepository(session),
                        storage=S3ObjectStorage(s3_client),
                    )
                    saved, s3_key = await documents.ingest_file(
                        request.content,
                        source=request.source,
                        content_type=content_type,
                        tags=list(request.tags) or None,
                    )
                    return knowledge_pb2.IngestFileResponse(
                        chunks_saved=len(saved),
                        s3_key=s3_key,
                    )
        except UnicodeDecodeError as exc:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"content is not valid utf-8 text: {exc}",
            )
            raise
        except ValueError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
            raise
        except Exception as exc:
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))
            raise


def _to_proto_chunk(chunk: KnowledgeChunk) -> knowledge_pb2.Chunk:
    return knowledge_pb2.Chunk(
        chunk_id=str(chunk.id),
        source=chunk.source,
        chunk_index=chunk.chunk_index,
        text=chunk.text,
        tags=list(chunk.tags),
    )

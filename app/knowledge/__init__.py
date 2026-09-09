from app.config import settings
from app.knowledge.client import KnowledgeGrpcClient, KnowledgeSearchError
from app.knowledge.models import KnowledgeChunkHit

__all__ = (
    "KnowledgeChunkHit",
    "KnowledgeGrpcClient",
    "KnowledgeSearchError",
    "get_knowledge_client",
)


def get_knowledge_client() -> KnowledgeGrpcClient:
    return KnowledgeGrpcClient(
        target=settings.knowledge.grpc_target,
        top_k=settings.knowledge.top_k,
        timeout_seconds=settings.knowledge.timeout_seconds,
        enabled=settings.knowledge.enabled,
    )

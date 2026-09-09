from __future__ import annotations

import asyncio

import grpc

from knowledge_services.config import settings
from knowledge_services.core.embeddings.ollama import OllamaEmbedder
from knowledge_services.db.session import SessionFactory, dispose
from knowledge_services.grpc.servicer import KnowledgeServicer
from knowledge_services.grpc_gen.knowledge.v1 import knowledge_pb2_grpc


async def serve() -> None:
    embedder = OllamaEmbedder()
    server = grpc.aio.server()
    knowledge_pb2_grpc.add_KnowledgeServiceServicer_to_server(  # type: ignore[no-untyped-call]
        KnowledgeServicer(embedder=embedder, session_factory=SessionFactory),
        server,
    )
    listen_addr = f"[::]:{settings.run.grpc_port}"
    server.add_insecure_port(listen_addr)
    await server.start()
    try:
        await server.wait_for_termination()
    finally:
        await server.stop(grace=5)
        await embedder.aclose()
        await dispose()


def main() -> None:
    asyncio.run(serve())


if __name__ == "__main__":
    main()

import asyncio

from knowledge_services.core.data.repository import KnowledgeChunkRepository
from knowledge_services.core.embeddings.ollama import OllamaEmbedder
from knowledge_services.core.ingest.service import IngestService
from knowledge_services.core.retrievers.service import RetrieverService
from knowledge_services.db.session import SessionFactory


async def main() -> None:
    embedder = OllamaEmbedder()
    async with SessionFactory() as session:
        repo = KnowledgeChunkRepository(session)
        ingest = IngestService(embedder=embedder, repository=repo)
        retriever = RetrieverService(embedder=embedder, repository=repo)

        await ingest.ingest_text(
            "Asyncio create_task starts a coroutine in the event loop.",
            source="smoke.md",
        )
        await session.commit()

        hits = await retriever.search("How do I start a coroutine with asyncio?")
        for hit in hits:
            print(hit.source, hit.chunk_index, hit.text[:120])

    await embedder.aclose()


if __name__ == "__main__":
    asyncio.run(main())

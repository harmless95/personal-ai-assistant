from knowledge_services.config import settings


def split_text(
    text: str,
    *,
    chunk_size: int = settings.rag.chunk_size,
    chunk_overlap: int = settings.rag.chunk_overlap,
) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and < chunk_size")

    if len(cleaned) <= chunk_size:
        return [cleaned]

    step = chunk_size - chunk_overlap
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = start + chunk_size
        piece = cleaned[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(cleaned):
            break
        start += step
    return chunks

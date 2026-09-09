from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class KnowledgeChunkHit:
    chunk_id: str
    source: str
    chunk_index: int
    text: str
    tags: tuple[str, ...]

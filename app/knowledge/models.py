from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class KnowledgeChunkHit:
    chunk_id: str
    source: str
    chunk_index: int
    text: str
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class KnowledgeIngestFileResult:
    chunks_saved: int
    s3_key: str

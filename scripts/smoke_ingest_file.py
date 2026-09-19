"""Smoke: local file -> knowledge gRPC IngestFile.

Usage:
  PYTHONPATH=. uv run python scripts/smoke_ingest_file.py path/to/notes.md
"""

from __future__ import annotations

import asyncio
import mimetypes
import sys
from pathlib import Path

from app.config import settings
from app.knowledge import KnowledgeGrpcClient, KnowledgeIngestError


async def main(path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"file not found: {path}")

    content = path.read_bytes()
    content_type = mimetypes.guess_type(path.name)[0] or "text/plain"
    client = KnowledgeGrpcClient(
        target=settings.knowledge.grpc_target,
        timeout_seconds=settings.knowledge.timeout_seconds,
        enabled=settings.knowledge.enabled,
    )
    try:
        result = await client.ingest_file(
            content,
            source=path.name,
            content_type=content_type,
        )
    except KnowledgeIngestError as exc:
        raise SystemExit(f"ingest failed: {exc}") from exc

    print(f"chunks_saved={result.chunks_saved}")
    print(f"s3_key={result.s3_key}")
    print(f"source={path.name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/smoke_ingest_file.py <file>")
    asyncio.run(main(Path(sys.argv[1])))

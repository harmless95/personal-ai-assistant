import sys
from pathlib import Path

_grpc_gen = str(Path(__file__).resolve().parent / "grpc_gen")
if _grpc_gen not in sys.path:
    sys.path.insert(0, _grpc_gen)

from knowledge_services.db import KnowledgeChunk  # noqa: E402

__all__ = ("KnowledgeChunk",)

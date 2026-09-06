import pytest

from knowledge_services.core.ingest.chunking import split_text


def test_split_text_empty() -> None:
    assert split_text("") == []
    assert split_text("   ") == []


def test_split_text_short_returns_single_chunk() -> None:
    assert split_text("hello", chunk_size=800, chunk_overlap=100) == ["hello"]


def test_split_text_with_overlap() -> None:
    text = "a" * 1000
    chunks = split_text(text, chunk_size=800, chunk_overlap=100)
    assert len(chunks) == 2
    assert len(chunks[0]) == 800
    assert len(chunks[1]) == 300
    assert chunks[0][-100:] == chunks[1][:100]


def test_split_text_rejects_invalid_sizes() -> None:
    with pytest.raises(ValueError, match="chunk_size"):
        split_text("abc", chunk_size=0, chunk_overlap=0)
    with pytest.raises(ValueError, match="chunk_overlap"):
        split_text("abc", chunk_size=10, chunk_overlap=10)

import pytest

from knowledge_services.core.ingest.chunking import split_text


def test_split_text_empty() -> None:
    assert split_text("") == []
    assert split_text("   ") == []


def test_split_text_short_returns_single_chunk() -> None:
    assert split_text("hello", chunk_size=800, chunk_overlap=100) == ["hello"]


def test_split_text_long_uniform_text_respects_size_and_overlap() -> None:
    text = "a" * 1000
    chunks = split_text(text, chunk_size=800, chunk_overlap=100)
    assert len(chunks) >= 2
    assert all(len(chunk) <= 800 for chunk in chunks)
    assert chunks[0][-100:] == chunks[1][:100]


def test_split_text_prefers_paragraph_boundaries() -> None:
    paragraph_a = "Alpha sentence one. Alpha sentence two."
    paragraph_b = "Beta sentence one. Beta sentence two."
    text = f"{paragraph_a}\n\n{paragraph_b}"
    chunks = split_text(text, chunk_size=60, chunk_overlap=10)
    assert len(chunks) >= 2
    assert all(len(chunk) <= 60 for chunk in chunks)
    assert any("Alpha" in chunk for chunk in chunks)
    assert any("Beta" in chunk for chunk in chunks)


def test_split_text_rejects_invalid_sizes() -> None:
    with pytest.raises(ValueError, match="chunk_size"):
        split_text("abc", chunk_size=0, chunk_overlap=0)
    with pytest.raises(ValueError, match="chunk_overlap"):
        split_text("abc", chunk_size=10, chunk_overlap=10)

from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class HealthRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthResponse(_message.Message):
    __slots__ = ("ok",)
    OK_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    def __init__(self, ok: _Optional[bool] = ...) -> None: ...

class SearchRequest(_message.Message):
    __slots__ = ("query", "top_k")
    QUERY_FIELD_NUMBER: _ClassVar[int]
    TOP_K_FIELD_NUMBER: _ClassVar[int]
    query: str
    top_k: int
    def __init__(self, query: _Optional[str] = ..., top_k: _Optional[int] = ...) -> None: ...

class Chunk(_message.Message):
    __slots__ = ("chunk_id", "source", "chunk_index", "text", "tags")
    CHUNK_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    CHUNK_INDEX_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    chunk_id: str
    source: str
    chunk_index: int
    text: str
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, chunk_id: _Optional[str] = ..., source: _Optional[str] = ..., chunk_index: _Optional[int] = ..., text: _Optional[str] = ..., tags: _Optional[_Iterable[str]] = ...) -> None: ...

class SearchResponse(_message.Message):
    __slots__ = ("chunks",)
    CHUNKS_FIELD_NUMBER: _ClassVar[int]
    chunks: _containers.RepeatedCompositeFieldContainer[Chunk]
    def __init__(self, chunks: _Optional[_Iterable[_Union[Chunk, _Mapping]]] = ...) -> None: ...

class IngestTextRequest(_message.Message):
    __slots__ = ("text", "source", "tags")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    text: str
    source: str
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, text: _Optional[str] = ..., source: _Optional[str] = ..., tags: _Optional[_Iterable[str]] = ...) -> None: ...

class IngestTextResponse(_message.Message):
    __slots__ = ("chunks_saved",)
    CHUNKS_SAVED_FIELD_NUMBER: _ClassVar[int]
    chunks_saved: int
    def __init__(self, chunks_saved: _Optional[int] = ...) -> None: ...

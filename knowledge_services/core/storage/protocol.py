from typing import Protocol


class ObjectStorage(Protocol):
    async def ensure_bucket(self) -> None: ...

    async def put_bytes(
        self,
        key: str,
        body: bytes,
        *,
        content_type: str = "application/octet-stream",
    ) -> str: ...

    async def get_bytes(self, key: str) -> bytes: ...

    async def delete(self, key: str) -> None: ...

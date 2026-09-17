from typing import Any

from botocore.exceptions import ClientError

from knowledge_services.config import settings


class S3ObjectStorage:
    """Object storage operations; S3 client is injected like a DB session."""

    def __init__(
        self,
        client: Any,
        *,
        bucket: str = settings.s3.bucket,
        region: str = settings.s3.region,
    ) -> None:
        self._client = client
        self._bucket = bucket
        self._region = region

    async def ensure_bucket(self) -> None:
        try:
            await self._client.head_bucket(Bucket=self._bucket)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code not in {"404", "NoSuchBucket", "NotFound"}:
                raise
            create_kwargs: dict[str, Any] = {"Bucket": self._bucket}
            if self._region != "us-east-1":
                create_kwargs["CreateBucketConfiguration"] = {"LocationConstraint": self._region}
            await self._client.create_bucket(**create_kwargs)

    async def put_bytes(
        self,
        key: str,
        body: bytes,
        *,
        content_type: str = "application/octet-stream",
    ) -> str:
        await self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
        )
        return key

    async def get_bytes(self, key: str) -> bytes:
        response = await self._client.get_object(Bucket=self._bucket, Key=key)
        async with response["Body"] as stream:
            return bytes(await stream.read())

    async def delete(self, key: str) -> None:
        await self._client.delete_object(Bucket=self._bucket, Key=key)

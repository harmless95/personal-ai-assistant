from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import aioboto3
from botocore.client import Config

from knowledge_services.config import settings


def s3_client_kwargs(
    *,
    endpoint_url: str = settings.s3.endpoint_url,
    access_key: str | None = None,
    secret_key: str | None = None,
    region: str = settings.s3.region,
    force_path_style: bool = settings.s3.force_path_style,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "service_name": "s3",
        "endpoint_url": endpoint_url,
        "aws_access_key_id": access_key if access_key is not None else settings.s3.access_key.get_secret_value(),
        "aws_secret_access_key": secret_key if secret_key is not None else settings.s3.secret_key.get_secret_value(),
        "region_name": region,
    }
    if force_path_style:
        kwargs["config"] = Config(s3={"addressing_style": "path"})
    return kwargs


@asynccontextmanager
async def s3_client_scope(
    *,
    endpoint_url: str = settings.s3.endpoint_url,
    access_key: str | None = None,
    secret_key: str | None = None,
    region: str = settings.s3.region,
    force_path_style: bool = settings.s3.force_path_style,
) -> AsyncIterator[Any]:
    session = aioboto3.Session()
    async with session.client(
        **s3_client_kwargs(
            endpoint_url=endpoint_url,
            access_key=access_key,
            secret_key=secret_key,
            region=region,
            force_path_style=force_path_style,
        )
    ) as client:
        yield client

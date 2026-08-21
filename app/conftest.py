from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest

from app.tasks.broker_taskiq import broker


@pytest.fixture(autouse=True)
async def _mock_broker_lifecycle() -> AsyncGenerator[None, None]:
    original_startup = broker.startup
    original_shutdown = broker.shutdown
    broker.startup = AsyncMock()  # type: ignore[method-assign]
    broker.shutdown = AsyncMock()  # type: ignore[method-assign]
    try:
        yield
    finally:
        broker.startup = original_startup  # type: ignore[method-assign]
        broker.shutdown = original_shutdown  # type: ignore[method-assign]

from typing import Any

import taskiq_fastapi
from taskiq import SimpleRetryMiddleware
from taskiq_redis import RedisStreamBroker

from app.config import settings

_redis_url = str(settings.redis.connection_url.get_secret_value())  # type: ignore[attr-defined]
_redis_connection_kwargs: dict[str, Any] = {
    "socket_timeout": settings.redis.socket_timeout,
    "socket_connect_timeout": settings.redis.socket_connect_timeout,
    "retry_on_timeout": settings.redis.retry_on_timeout,
    "health_check_interval": settings.redis.health_check_interval,
}

broker = RedisStreamBroker(
    url=_redis_url,
    queue_name=settings.taskiq.queue_name,
    max_connection_pool_size=settings.taskiq.max_connection_pool_size,
    **_redis_connection_kwargs,
).with_middlewares(SimpleRetryMiddleware(default_retry_count=settings.taskiq.default_retry_count))

taskiq_fastapi.init(broker=broker, app_or_path="app.main:app")

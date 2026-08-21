from uuid import UUID

import structlog

from app.config import settings
from app.tasks.broker_taskiq import broker
from app.tasks.deps import DaySummaryProcessorDep

logger = structlog.get_logger(__name__)


@broker.task(
    retry_on_error=settings.taskiq.day_summary_retry_on_error,
    max_retries=settings.taskiq.day_summary_max_retries,
)
async def process_day_summary(
    checkin_id: str,
    processor: DaySummaryProcessorDep,
) -> None:
    logger.info("day_summary_task_started", checkin_id=checkin_id)
    try:
        await processor.process_checkin(checkin_id=UUID(checkin_id))
    except Exception:
        logger.exception("day_summary_task_failed", checkin_id=checkin_id)
        raise
    logger.info("day_summary_task_finished", checkin_id=checkin_id)

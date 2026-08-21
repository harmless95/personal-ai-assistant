import structlog

from app.tasks.day_summary_tasks import process_day_summary

logger = structlog.get_logger(__name__)


async def enqueue_day_summary(checkin_id: str) -> bool:
    try:
        await process_day_summary.kiq(checkin_id)  # type: ignore[call-overload]
        logger.info("day_summary_enqueued", checkin_id=checkin_id)
        return True
    except Exception:
        logger.exception("failed_to_enqueue_day_summary_task", checkin_id=checkin_id)
        return False

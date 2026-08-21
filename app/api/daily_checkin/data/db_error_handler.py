from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

import structlog
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from app.api.daily_checkin.data.errors import (
    DatabaseError,
    DatabaseUnavailableError,
    DuplicateEntryError,
    ForeignKeyViolationError,
    IntegrityViolationError,
    NotNullViolationError,
)

logger = structlog.get_logger(__name__)

T = TypeVar("T")

PG_UNIQUE_VIOLATION = "23505"
PG_FOREIGN_KEY_VIOLATION = "23503"
PG_NOT_NULL_VIOLATION = "23502"

UQ_DAILY_CHECKINS_USER_DATE = "uq_daily_checkins_user_id_checkin_date"


def _parse_integrity_error(error: IntegrityError) -> tuple[str | None, str | None]:
    orig = getattr(error, "orig", None)
    if orig is None:
        return None, None

    pgcode = getattr(orig, "pgcode", None) or getattr(orig, "sqlstate", None)
    constraint = getattr(orig, "constraint_name", None)
    if not constraint:
        cause = getattr(orig, "__cause__", None)
        if cause is not None:
            constraint = getattr(cause, "constraint_name", None)

    return (
        str(pgcode) if pgcode is not None else None,
        str(constraint) if constraint is not None else None,
    )


def _raise_for_integrity_error(error: IntegrityError, func_name: str) -> None:
    pgcode, constraint = _parse_integrity_error(error)

    # Avoid logging full exception text — Postgres DETAIL can include emails/keys.
    logger.warning(
        "integrity_error",
        func=func_name,
        pgcode=pgcode,
        constraint=constraint,
        error_type=type(error).__name__,
    )

    if constraint == UQ_DAILY_CHECKINS_USER_DATE or pgcode == PG_UNIQUE_VIOLATION:
        raise DuplicateEntryError(constraint=constraint) from error

    if pgcode == PG_FOREIGN_KEY_VIOLATION:
        raise ForeignKeyViolationError() from error

    if pgcode == PG_NOT_NULL_VIOLATION:
        raise NotNullViolationError() from error

    logger.error(
        "unhandled_integrity_error",
        func=func_name,
        pgcode=pgcode,
        constraint=constraint,
        error_type=type(error).__name__,
    )
    raise IntegrityViolationError() from error


def handle_db_errors(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
        except IntegrityError as e:
            _raise_for_integrity_error(e, func.__name__)
            raise
        except OperationalError as e:
            logger.critical(
                "database_unavailable",
                func=func.__name__,
                error_type=type(e).__name__,
            )
            raise DatabaseUnavailableError() from e
        except SQLAlchemyError as e:
            logger.error(
                "database_error",
                func=func.__name__,
                error_type=type(e).__name__,
            )
            raise DatabaseError() from e

    return wrapper

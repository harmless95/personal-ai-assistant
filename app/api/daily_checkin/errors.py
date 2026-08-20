from typing import NoReturn

from fastapi import HTTPException, status


class DailyCheckinErrors:
    CHECKIN_NOT_FOUND = ("checkin_not_found", "Daily check-in not found", status.HTTP_404_NOT_FOUND)
    CHECKIN_FORBIDDEN = (
        "checkin_forbidden",
        "Daily check-in does not belong to this user",
        status.HTTP_403_FORBIDDEN,
    )
    CHECKIN_ALREADY_ANSWERED = (
        "checkin_already_answered",
        "Daily check-in already answered",
        status.HTTP_409_CONFLICT,
    )
    CHECKIN_ALREADY_EXISTS = (
        "checkin_already_exists",
        "Daily check-in for this user and date already exists",
        status.HTTP_409_CONFLICT,
    )
    INVALID_ANSWERS = (
        "invalid_answers",
        "Answers must match the check-in questions exactly",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    QUESTION_POOL_EMPTY = (
        "question_pool_empty",
        "Active question pool is empty or incomplete",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    DATABASE_UNAVAILABLE = ("database_unavailable", "Database is unavailable", status.HTTP_503_SERVICE_UNAVAILABLE)
    DATABASE_ERROR = ("database_error", "Database error", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def __init__(self, code: str, message: str, status_code: int):
        self.code = code
        self.message = message
        self.status_code = status_code

    @classmethod
    def from_tuple(cls, value: tuple[str, str, int]) -> "DailyCheckinErrors":
        return cls(*value)

    def raise_http(self) -> NoReturn:
        raise HTTPException(
            status_code=self.status_code,
            detail={"code": self.code, "message": self.message},
        )


def raise_error(error: tuple[str, str, int]) -> NoReturn:
    DailyCheckinErrors.from_tuple(error).raise_http()
    raise AssertionError("unreachable")

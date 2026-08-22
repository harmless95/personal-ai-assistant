from collections.abc import Sequence
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.daily_checkin.data.db_error_handler import handle_db_errors
from app.db import DailyCheckin, DailyQuestion, QuestionPool


class DailyCheckinRepository:
    def __init__(self, session: AsyncSession):
        self.__session = session

    @handle_db_errors
    async def list_active_questions(self) -> Sequence[QuestionPool]:
        stmt = select(QuestionPool).where(QuestionPool.is_active.is_(True)).order_by(QuestionPool.id)
        result = await self.__session.execute(stmt)
        return result.scalars().all()

    @handle_db_errors
    async def list_recent_question_usage(
        self,
        user_id: UUID,
        *,
        max_cooldown_days: int,
    ) -> tuple[dict[UUID, date], date]:
        today_result = await self.__session.execute(select(func.current_date()))
        today = today_result.scalar_one()
        since = today - timedelta(days=max(max_cooldown_days, 0))

        stmt = (
            select(DailyQuestion.question_id, DailyCheckin.checkin_date)
            .join(DailyCheckin, DailyQuestion.checkin_id == DailyCheckin.id)
            .where(
                DailyCheckin.user_id == user_id,
                DailyCheckin.checkin_date >= since,
            )
        )
        result = await self.__session.execute(stmt)
        usage: dict[UUID, date] = {}
        for question_id, checkin_date in result.all():
            previous = usage.get(question_id)
            if previous is None or checkin_date > previous:
                usage[question_id] = checkin_date
        return usage, today

    @handle_db_errors
    async def create_checkin(self, checkin: DailyCheckin) -> DailyCheckin:
        self.__session.add(checkin)
        await self.__session.flush()
        await self.__session.refresh(checkin, attribute_names=["id", "checkin_date", "questions"])
        return checkin

    @handle_db_errors
    async def get_checkin_by_id(
        self,
        checkin_id: UUID,
        *,
        with_questions: bool = False,
        with_answers: bool = False,
        with_artifact: bool = False,
    ) -> DailyCheckin | None:
        stmt = select(DailyCheckin).where(DailyCheckin.id == checkin_id)

        if with_questions:
            stmt = stmt.options(selectinload(DailyCheckin.questions))
        if with_answers:
            stmt = stmt.options(selectinload(DailyCheckin.answers))
        if with_artifact:
            stmt = stmt.options(selectinload(DailyCheckin.artifact))

        result = await self.__session.execute(stmt)
        return result.scalar_one_or_none()

    @handle_db_errors
    async def get_today_checkin(
        self,
        user_id: UUID,
        *,
        with_questions: bool = False,
    ) -> DailyCheckin | None:
        stmt = select(DailyCheckin).where(
            DailyCheckin.user_id == user_id,
            DailyCheckin.checkin_date == func.current_date(),
        )
        if with_questions:
            stmt = stmt.options(selectinload(DailyCheckin.questions))

        result = await self.__session.execute(stmt)
        return result.scalar_one_or_none()

    @handle_db_errors
    async def get_checkin_by_user_and_date(
        self,
        user_id: UUID,
        checkin_date: date,
        *,
        with_questions: bool = False,
    ) -> DailyCheckin | None:
        stmt = select(DailyCheckin).where(
            DailyCheckin.user_id == user_id,
            DailyCheckin.checkin_date == checkin_date,
        )
        if with_questions:
            stmt = stmt.options(selectinload(DailyCheckin.questions))

        result = await self.__session.execute(stmt)
        return result.scalar_one_or_none()

    @handle_db_errors
    async def list_checkins_by_user(
        self,
        user_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> Sequence[DailyCheckin]:
        stmt = (
            select(DailyCheckin)
            .where(DailyCheckin.user_id == user_id)
            .order_by(DailyCheckin.checkin_date.desc(), DailyCheckin.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.__session.execute(stmt)
        return result.scalars().all()

    @handle_db_errors
    async def save_checkin(self, checkin: DailyCheckin) -> DailyCheckin:
        await self.__session.flush()
        await self.__session.refresh(
            checkin,
            attribute_names=["status", "artifact_status", "answers", "artifact"],
        )
        return checkin

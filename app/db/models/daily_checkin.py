from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.daily_artifact import DailyArtifact
    from app.db.models.daily_question import DailyQuestion
    from app.db.models.question_answer import QuestionAnswer


class DailyCheckin(Base):
    __tablename__ = "daily_checkins"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    checkin_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        default=date.today,
        server_default=text("CURRENT_DATE"),
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="asked")
    artifact_status: Mapped[str | None] = mapped_column(String(32), nullable=True)

    stress_level: Mapped[int] = mapped_column(Integer, nullable=False)
    energy_level: Mapped[int] = mapped_column(Integer, nullable=False)
    plan_done: Mapped[int] = mapped_column(Integer, nullable=False)
    blocker_present: Mapped[int] = mapped_column(Integer, nullable=False)
    learning_done: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    questions: Mapped[list[DailyQuestion]] = relationship(
        "DailyQuestion",
        back_populates="checkin",
        cascade="all, delete-orphan",
    )
    answers: Mapped[list[QuestionAnswer]] = relationship(
        "QuestionAnswer",
        back_populates="checkin",
        cascade="all, delete-orphan",
    )
    artifact: Mapped[DailyArtifact | None] = relationship(
        "DailyArtifact",
        back_populates="checkin",
        cascade="all, delete-orphan",
        uselist=False,
    )

    __table_args__ = (UniqueConstraint("user_id", "checkin_date", name="uq_daily_checkins_user_id_checkin_date"),)

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.daily_checkin import DailyCheckin


class QuestionAnswer(Base):
    __tablename__ = "question_answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    checkin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("daily_checkins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[str] = mapped_column(String(64), nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    checkin: Mapped[DailyCheckin] = relationship("DailyCheckin", back_populates="answers")

    __table_args__ = (UniqueConstraint("checkin_id", "question_id", name="uq_question_answers_checkin_id_question_id"),)

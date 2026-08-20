"""create_daily_checkin_tables

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-08-20 21:50:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "daily_checkins",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("checkin_date", sa.Date(), server_default=sa.text("CURRENT_DATE"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("stress_level", sa.Integer(), nullable=False),
        sa.Column("energy_level", sa.Integer(), nullable=False),
        sa.Column("plan_done", sa.Integer(), nullable=False),
        sa.Column("blocker_present", sa.Integer(), nullable=False),
        sa.Column("learning_done", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_daily_checkins")),
        sa.UniqueConstraint("user_id", "checkin_date", name="uq_daily_checkins_user_id_checkin_date"),
    )
    op.create_index(op.f("ix_daily_checkins_checkin_date"), "daily_checkins", ["checkin_date"], unique=False)
    op.create_index(op.f("ix_daily_checkins_user_id"), "daily_checkins", ["user_id"], unique=False)

    op.create_table(
        "daily_questions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("checkin_id", sa.UUID(), nullable=False),
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["checkin_id"],
            ["daily_checkins.id"],
            name=op.f("fk_daily_questions_checkin_id_daily_checkins"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_daily_questions")),
        sa.UniqueConstraint("checkin_id", "question_id", name="uq_daily_questions_checkin_id_question_id"),
        sa.UniqueConstraint("checkin_id", "sort_order", name="uq_daily_questions_checkin_id_sort_order"),
    )
    op.create_index(op.f("ix_daily_questions_checkin_id"), "daily_questions", ["checkin_id"], unique=False)

    op.create_table(
        "question_answers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("checkin_id", sa.UUID(), nullable=False),
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["checkin_id"],
            ["daily_checkins.id"],
            name=op.f("fk_question_answers_checkin_id_daily_checkins"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_question_answers")),
        sa.UniqueConstraint("checkin_id", "question_id", name="uq_question_answers_checkin_id_question_id"),
    )
    op.create_index(op.f("ix_question_answers_checkin_id"), "question_answers", ["checkin_id"], unique=False)

    op.create_table(
        "daily_artifacts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("checkin_id", sa.UUID(), nullable=False),
        sa.Column("structured_summary_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["checkin_id"],
            ["daily_checkins.id"],
            name=op.f("fk_daily_artifacts_checkin_id_daily_checkins"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_daily_artifacts")),
        sa.UniqueConstraint("checkin_id", name=op.f("uq_daily_artifacts_checkin_id")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("daily_artifacts")
    op.drop_index(op.f("ix_question_answers_checkin_id"), table_name="question_answers")
    op.drop_table("question_answers")
    op.drop_index(op.f("ix_daily_questions_checkin_id"), table_name="daily_questions")
    op.drop_table("daily_questions")
    op.drop_index(op.f("ix_daily_checkins_user_id"), table_name="daily_checkins")
    op.drop_index(op.f("ix_daily_checkins_checkin_date"), table_name="daily_checkins")
    op.drop_table("daily_checkins")

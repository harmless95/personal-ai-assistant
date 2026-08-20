"""create_question_pool_table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-21 05:15:00.000000

"""

from typing import Sequence, Union
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Stable UUIDs for seed/tests (deterministic, not random).
Q_RISK_01 = UUID("a1111111-1111-4111-8111-111111111101")
Q_RISK_02 = UUID("a1111111-1111-4111-8111-111111111102")
Q_FOCUS_01 = UUID("a1111111-1111-4111-8111-111111111201")
Q_FOCUS_02 = UUID("a1111111-1111-4111-8111-111111111202")
Q_ENERGY_01 = UUID("a1111111-1111-4111-8111-111111111301")
Q_ENERGY_02 = UUID("a1111111-1111-4111-8111-111111111302")
Q_LEARNING_01 = UUID("a1111111-1111-4111-8111-111111111401")
Q_LEARNING_02 = UUID("a1111111-1111-4111-8111-111111111402")
Q_ACTION_01 = UUID("a1111111-1111-4111-8111-111111111501")
Q_ACTION_02 = UUID("a1111111-1111-4111-8111-111111111502")

QUESTION_POOL_SEED: list[dict[str, object]] = [
    {
        "id": Q_RISK_01,
        "category": "RISK",
        "text": "What is putting the most pressure on you today?",
        "weight": 1.0,
        "trigger_tags": ["stress", "blocker"],
        "cooldown_days": 3,
        "is_active": True,
    },
    {
        "id": Q_RISK_02,
        "category": "RISK",
        "text": "What risk are you currently ignoring?",
        "weight": 0.8,
        "trigger_tags": ["stress"],
        "cooldown_days": 5,
        "is_active": True,
    },
    {
        "id": Q_FOCUS_01,
        "category": "FOCUS",
        "text": "Which one priority task was not completed?",
        "weight": 1.0,
        "trigger_tags": ["plan_miss"],
        "cooldown_days": 3,
        "is_active": True,
    },
    {
        "id": Q_FOCUS_02,
        "category": "FOCUS",
        "text": "What distracted you from your main priorities?",
        "weight": 0.9,
        "trigger_tags": ["plan_miss", "blocker"],
        "cooldown_days": 4,
        "is_active": True,
    },
    {
        "id": Q_ENERGY_01,
        "category": "ENERGY",
        "text": "What drained your energy the most in the last 2-3 hours?",
        "weight": 1.0,
        "trigger_tags": ["low_energy"],
        "cooldown_days": 3,
        "is_active": True,
    },
    {
        "id": Q_ENERGY_02,
        "category": "ENERGY",
        "text": "When did you last take a real break today?",
        "weight": 0.7,
        "trigger_tags": ["low_energy"],
        "cooldown_days": 7,
        "is_active": True,
    },
    {
        "id": Q_LEARNING_01,
        "category": "LEARNING",
        "text": "What new thing did you try today, even if imperfect?",
        "weight": 0.8,
        "trigger_tags": ["learning_mid"],
        "cooldown_days": 3,
        "is_active": True,
    },
    {
        "id": Q_LEARNING_02,
        "category": "LEARNING",
        "text": "Which skill did not work out today?",
        "weight": 1.0,
        "trigger_tags": ["learning_low"],
        "cooldown_days": 4,
        "is_active": True,
    },
    {
        "id": Q_ACTION_01,
        "category": "ACTION",
        "text": "What is one small step you can still take today?",
        "weight": 1.0,
        "trigger_tags": ["low_energy", "plan_miss"],
        "cooldown_days": 2,
        "is_active": True,
    },
    {
        "id": Q_ACTION_02,
        "category": "ACTION",
        "text": "What can you postpone without real damage?",
        "weight": 0.8,
        "trigger_tags": ["stress", "plan_miss"],
        "cooldown_days": 5,
        "is_active": True,
    },
]


def upgrade() -> None:
    question_pool = op.create_table(
        "question_pool",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("trigger_tags", sa.JSON(), nullable=False),
        sa.Column("cooldown_days", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_question_pool")),
    )
    op.create_index(op.f("ix_question_pool_category"), "question_pool", ["category"], unique=False)
    op.bulk_insert(question_pool, QUESTION_POOL_SEED)


def downgrade() -> None:
    op.drop_index(op.f("ix_question_pool_category"), table_name="question_pool")
    op.drop_table("question_pool")

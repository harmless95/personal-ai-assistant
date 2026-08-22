"""add_daily_checkins_user_fk

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-22 18:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM daily_checkins AS c
            WHERE NOT EXISTS (
                SELECT 1 FROM users AS u WHERE u.id = c.user_id
            )
            """
        )
    )
    op.create_foreign_key(
        op.f("fk_daily_checkins_user_id_users"),
        "daily_checkins",
        "users",
        ["user_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_daily_checkins_user_id_users"),
        "daily_checkins",
        type_="foreignkey",
    )

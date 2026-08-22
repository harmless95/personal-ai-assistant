"""add_artifact_status_and_source

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-22 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "daily_checkins",
        sa.Column("artifact_status", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "daily_artifacts",
        sa.Column("source", sa.String(length=32), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE daily_checkins AS c
            SET artifact_status = 'ready'
            WHERE EXISTS (
                SELECT 1 FROM daily_artifacts AS a WHERE a.checkin_id = c.id
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE daily_artifacts
            SET source = 'template'
            WHERE source IS NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_column("daily_artifacts", "source")
    op.drop_column("daily_checkins", "artifact_status")

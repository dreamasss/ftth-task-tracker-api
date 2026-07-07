"""add site planned date

Revision ID: b1c2d3e4f5a6
Revises: a9c8b7d6e5f4
Create Date: 2026-07-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: str | None = "a9c8b7d6e5f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("sites", sa.Column("planned_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("sites", "planned_date")

"""add site priority

Revision ID: a9c8b7d6e5f4
Revises: 7edaa5946fb1
Create Date: 2026-07-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a9c8b7d6e5f4"
down_revision: str | None = "7edaa5946fb1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sites",
        sa.Column(
            "priority",
            sa.String(length=20),
            nullable=False,
            server_default="medium",
        ),
    )
    op.create_check_constraint(
        "ck_sites_priority_valid",
        "sites",
        "priority IN ('low', 'medium', 'high')",
    )
    op.alter_column("sites", "priority", server_default=None)


def downgrade() -> None:
    op.drop_constraint("ck_sites_priority_valid", "sites", type_="check")
    op.drop_column("sites", "priority")

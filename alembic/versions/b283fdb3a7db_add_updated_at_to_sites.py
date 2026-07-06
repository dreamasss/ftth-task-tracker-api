"""add updated_at to sites

Revision ID: b283fdb3a7db
Revises: 2c3d4e5f6a7b
Create Date: 2026-07-06 11:38:48.882049

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b283fdb3a7db'
down_revision: Union[str, Sequence[str], None] = '2c3d4e5f6a7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sites",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("sites", "updated_at")

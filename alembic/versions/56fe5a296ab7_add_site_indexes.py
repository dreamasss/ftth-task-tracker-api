"""add site indexes

Revision ID: 56fe5a296ab7
Revises: b283fdb3a7db
Create Date: 2026-07-06 12:56:12.426858

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56fe5a296ab7'
down_revision: Union[str, Sequence[str], None] = 'b283fdb3a7db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_sites_status", "sites", ["status"])
    op.create_index("ix_sites_created_at", "sites", ["created_at"])
    op.create_index("ix_sites_updated_at", "sites", ["updated_at"])


def downgrade() -> None:
    op.drop_index("ix_sites_updated_at", table_name="sites")
    op.drop_index("ix_sites_created_at", table_name="sites")
    op.drop_index("ix_sites_status", table_name="sites")

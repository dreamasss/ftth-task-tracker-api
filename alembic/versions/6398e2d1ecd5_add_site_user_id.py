"""add site user id

Revision ID: 6398e2d1ecd5
Revises: f0b3d8b29376
Create Date: 2026-07-06 14:42:54.086589

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6398e2d1ecd5'
down_revision: Union[str, Sequence[str], None] = 'f0b3d8b29376'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

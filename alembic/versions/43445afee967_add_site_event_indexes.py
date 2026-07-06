"""add site event indexes

Revision ID: 43445afee967
Revises: 56fe5a296ab7
Create Date: 2026-07-06 13:14:11.269363

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43445afee967'
down_revision: Union[str, Sequence[str], None] = '56fe5a296ab7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_site_events_site_id_id", "site_events", ["site_id", "id"])
    op.create_index(
        "ix_site_events_site_id_event_type_id",
        "site_events",
        ["site_id", "event_type", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_site_events_site_id_event_type_id", table_name="site_events")
    op.drop_index("ix_site_events_site_id_id", table_name="site_events")

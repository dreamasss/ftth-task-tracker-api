"""add status check constraints

Revision ID: f0b3d8b29376
Revises: 43445afee967
Create Date: 2026-07-06 13:23:14.881061

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0b3d8b29376'
down_revision: Union[str, Sequence[str], None] = '43445afee967'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_sites_status_valid",
        "sites",
        "status IN ('new', 'in_progress', 'blocked', 'done', 'reported')",
    )
    op.create_check_constraint(
        "ck_site_events_event_type_valid",
        "site_events",
        "event_type IN ('note', 'issue', 'status_change')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_site_events_event_type_valid", "site_events", type_="check")
    op.drop_constraint("ck_sites_status_valid", "sites", type_="check")

"""add site user id column

Revision ID: 7edaa5946fb1
Revises: 6398e2d1ecd5
"""

from alembic import op
import sqlalchemy as sa


revision: str = "7edaa5946fb1"
down_revision: str | None = "6398e2d1ecd5"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("sites", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index("ix_sites_user_id", "sites", ["user_id"], unique=False)
    op.create_foreign_key(
        "fk_sites_user_id_users",
        "sites",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_sites_user_id_users", "sites", type_="foreignkey")
    op.drop_index("ix_sites_user_id", table_name="sites")
    op.drop_column("sites", "user_id")

"""expand transaction type length

Revision ID: a1b2c3d4e5f6
Revises: 288f9f9cfa36
Create Date: 2026-03-04

"""

from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "288f9f9cfa36"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "transactions",
        "type",
        existing_type=sa.String(16),
        type_=sa.String(64),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "transactions",
        "type",
        existing_type=sa.String(64),
        type_=sa.String(16),
        existing_nullable=False,
    )

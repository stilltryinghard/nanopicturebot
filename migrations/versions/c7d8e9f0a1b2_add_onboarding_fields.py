"""add onboarding fields (language, terms_accepted)

Revision ID: c7d8e9f0a1b2
Revises: a1b2c3d4e5f6
Create Date: 2026-03-06

"""

from alembic import op
import sqlalchemy as sa

revision = "c7d8e9f0a1b2"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("language", sa.String(8), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "terms_accepted", sa.Boolean(), nullable=False, server_default="false"
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "terms_accepted")
    op.drop_column("users", "language")

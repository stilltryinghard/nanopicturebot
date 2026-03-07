"""initial

Revision ID: 76ba33c9f986
Revises:
Create Date: 2026-02-28 16:19:00.841907

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "76ba33c9f986"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("full_name", sa.String(128), nullable=False),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("referred_by", sa.BigInteger(), nullable=True),
        sa.Column("referral_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )

    op.create_table(
        "generations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("model", sa.String(32), nullable=False),
        sa.Column("prompt", sa.String(2048), nullable=False),
        sa.Column("preference", sa.String(1024), nullable=True),
        sa.Column("quality", sa.String(4), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("tokens_spent", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
            unique=True,
        ),
        sa.Column("plan", sa.String(32), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.String(128), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )

    op.create_table(
        "referrals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("referrer_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("referred_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("bonus_paid", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("bonus_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )


def downgrade() -> None:
    op.drop_table("referrals")
    op.drop_table("transactions")
    op.drop_table("subscriptions")
    op.drop_table("generations")
    op.drop_table("users")

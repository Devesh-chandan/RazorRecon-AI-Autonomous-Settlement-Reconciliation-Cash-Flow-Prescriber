"""Add merchants table for JWT auth.

Revision ID: 0002_add_merchants
Revises: 0001_initial
Create Date: 2026-08-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_merchants"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "merchants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(150), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(150), server_default=""),
        sa.Column("role", sa.String(20), nullable=False, server_default="finance"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_merchants_email"), "merchants", ["email"], unique=True)
    op.create_index(op.f("ix_merchants_id"), "merchants", ["id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_merchants_id"), table_name="merchants")
    op.drop_index(op.f("ix_merchants_email"), table_name="merchants")
    op.drop_table("merchants")

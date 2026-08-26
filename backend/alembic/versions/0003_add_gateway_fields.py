"""Add gateway and import_source columns to settlements table.

Revision ID: 0003_add_gateway_fields
Revises: 0002_add_merchants
Create Date: 2026-08-26

Changes:
  - settlements.gateway (VARCHAR 50, nullable) — HDFC Bank (PG) | ICICI Direct | etc.
  - settlements.import_source (VARCHAR 20, default 'seeded') — seeded | csv_import | webhook
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0003_add_gateway_fields"
down_revision: Union[str, None] = "0002_add_merchants"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add gateway column (nullable — existing rows will have NULL, seeder re-populates)
    op.add_column(
        "settlements",
        sa.Column("gateway", sa.String(50), nullable=True),
    )
    # Add import_source to distinguish seeded vs CSV-imported records for scope filtering
    op.add_column(
        "settlements",
        sa.Column("import_source", sa.String(20), nullable=True, server_default="seeded"),
    )


def downgrade() -> None:
    op.drop_column("settlements", "import_source")
    op.drop_column("settlements", "gateway")

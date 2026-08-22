"""Initial migration — creates all tables."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.String(20), nullable=False),
        sa.Column("payment_id", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("customer_email", sa.String(100), nullable=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("refund_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("erp_invoice", sa.String(30), nullable=True),
        sa.Column("created_in_db", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
    )
    op.create_index(op.f("ix_orders_order_id"), "orders", ["order_id"], unique=True)
    op.create_index(op.f("ix_orders_payment_id"), "orders", ["payment_id"])

    op.create_table(
        "settlements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entity_id", sa.String(20), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("fee", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax", sa.Numeric(12, 2), nullable=False),
        sa.Column("credit", sa.Numeric(12, 2), nullable=False),
        sa.Column("debit", sa.Numeric(12, 2), nullable=True),
        sa.Column("settlement_id", sa.String(20), nullable=False),
        sa.Column("settlement_utr", sa.String(30), nullable=True),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("order_id", sa.String(20), nullable=False),
        sa.Column("created_in_db", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_settlements_entity_id"), "settlements", ["entity_id"])
    op.create_index(op.f("ix_settlements_order_id"), "settlements", ["order_id"])
    op.create_index(op.f("ix_settlements_settlement_id"), "settlements", ["settlement_id"])

    op.create_table(
        "erp_ledger",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ledger_id", sa.String(20), nullable=False),
        sa.Column("invoice_id", sa.String(30), nullable=False),
        sa.Column("order_id", sa.String(20), nullable=False),
        sa.Column("expected_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("recorded_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_method", sa.String(20), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_in_db", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ledger_id"),
    )
    op.create_index(op.f("ix_erp_ledger_ledger_id"), "erp_ledger", ["ledger_id"], unique=True)
    op.create_index(op.f("ix_erp_ledger_order_id"), "erp_ledger", ["order_id"])

    op.create_table(
        "recon_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("total_records", sa.Integer(), nullable=True),
        sa.Column("matched_count", sa.Integer(), nullable=True),
        sa.Column("break_count", sa.Integer(), nullable=True),
        sa.Column("match_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("net_payout", sa.Numeric(14, 2), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id"),
    )
    op.create_index(op.f("ix_recon_runs_run_id"), "recon_runs", ["run_id"], unique=True)

    op.create_table(
        "recon_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recon_runs.run_id"), nullable=False),
        sa.Column("order_id", sa.String(20), nullable=False),
        sa.Column("settlement_id", sa.String(20), nullable=True),
        sa.Column("ledger_id", sa.String(20), nullable=True),
        sa.Column("pass_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column("flags", postgresql.JSONB(), nullable=True),
        sa.Column("delta", postgresql.JSONB(), nullable=True),
        sa.Column("root_cause", sa.String(50), nullable=True),
        sa.Column("explanation_en", sa.Text(), nullable=True),
        sa.Column("explanation_hi", sa.Text(), nullable=True),
        sa.Column("suggested_action", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recon_results_order_id"), "recon_results", ["order_id"])
    op.create_index(op.f("ix_recon_results_run_id"), "recon_results", ["run_id"])


def downgrade() -> None:
    op.drop_table("recon_results")
    op.drop_table("recon_runs")
    op.drop_table("erp_ledger")
    op.drop_table("settlements")
    op.drop_table("orders")

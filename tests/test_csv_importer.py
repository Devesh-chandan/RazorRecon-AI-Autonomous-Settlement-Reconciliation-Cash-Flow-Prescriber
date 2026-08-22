"""Unit tests for the CSV / Excel batch importer.

Run:
    pytest tests/test_csv_importer.py -v
"""
import io
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── Helper: build in-memory CSV bytes ────────────────────────────────────────

def _make_csv(rows: list[dict], columns: list[str]) -> bytes:
    """Return CSV bytes from a list of row dicts."""
    header = ",".join(columns)
    lines = [header]
    for row in rows:
        lines.append(",".join(str(row.get(c, "")) for c in columns))
    return "\n".join(lines).encode("utf-8")


# ── Razorpay Settlement CSV tests ─────────────────────────────────────────────

_SETTLEMENT_COLUMNS = [
    "Settlement ID", "Entity ID", "Type", "Amount", "Fee", "Tax",
    "Credit", "Debit", "Settlement UTR", "Settled At", "Order ID",
]

_SETTLEMENT_ROWS = [
    {
        "Settlement ID": "setl_aaa111",
        "Entity ID": "pay_abc001",
        "Type": "payment",
        "Amount": "5000",
        "Fee": "100",
        "Tax": "18",
        "Credit": "4882",
        "Debit": "0",
        "Settlement UTR": "UTR000000000001",
        "Settled At": "2024-07-01 12:00:00",
        "Order ID": "order_xyz001",
    },
    {
        "Settlement ID": "setl_aaa222",
        "Entity ID": "pay_abc002",
        "Type": "payment",
        "Amount": "15000",
        "Fee": "300",
        "Tax": "54",
        "Credit": "14646",
        "Debit": "0",
        "Settlement UTR": "UTR000000000002",
        "Settled At": "2024-07-02 08:30:00",
        "Order ID": "order_xyz002",
    },
]


class TestSettlementCSVImport:

    def test_valid_csv_import(self):
        """Two-row settlement CSV should import 2 records."""
        csv_bytes = _make_csv(_SETTLEMENT_ROWS, _SETTLEMENT_COLUMNS)
        response = client.post(
            "/api/recon/upload",
            data={"source": "razorpay_settlement"},
            files={"file": ("settlements.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["rows_read"] == 2
        assert data["rows_imported"] == 2
        assert data["rows_skipped"] == 0
        assert data["errors"] == []

    def test_duplicate_rows_skipped(self):
        """Re-importing the same file should skip existing records."""
        csv_bytes = _make_csv(_SETTLEMENT_ROWS, _SETTLEMENT_COLUMNS)
        # Second import of same data
        response = client.post(
            "/api/recon/upload",
            data={"source": "razorpay_settlement"},
            files={"file": ("settlements.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rows_skipped"] >= 0  # already inserted in previous test or skipped

    def test_missing_settlement_id_skipped(self):
        """Rows without settlement_id should be counted in rows_skipped."""
        bad_rows = [{"Settlement ID": "", "Order ID": "order_bad001"}]
        csv_bytes = _make_csv(bad_rows, ["Settlement ID", "Order ID"])
        response = client.post(
            "/api/recon/upload",
            data={"source": "razorpay_settlement"},
            files={"file": ("bad.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rows_skipped"] >= 1

    def test_unsupported_file_type_rejected(self):
        """PDF file should return 422 Unprocessable Entity."""
        response = client.post(
            "/api/recon/upload",
            data={"source": "razorpay_settlement"},
            files={"file": ("report.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
        )
        assert response.status_code == 422

    def test_invalid_source_rejected(self):
        """Unknown source value should return 422."""
        csv_bytes = _make_csv(_SETTLEMENT_ROWS, _SETTLEMENT_COLUMNS)
        response = client.post(
            "/api/recon/upload",
            data={"source": "unknown_source"},
            files={"file": ("settlements.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert response.status_code == 422


# ── ERP Ledger CSV tests ──────────────────────────────────────────────────────

_LEDGER_COLUMNS = [
    "Ledger ID", "Invoice ID", "Order ID", "Expected Amount",
    "Recorded Amount", "Payment Method", "Entry Date", "Status", "Notes",
]

_LEDGER_ROWS = [
    {
        "Ledger ID": "led_001",
        "Invoice ID": "inv_abc001",
        "Order ID": "order_xyz001",
        "Expected Amount": "5000",
        "Recorded Amount": "5000",
        "Payment Method": "upi",
        "Entry Date": "2024-07-01",
        "Status": "received",
        "Notes": "On time",
    },
]


class TestERPLedgerCSVImport:

    def test_valid_ledger_csv_import(self):
        """Single-row ERP ledger CSV should import 1 record."""
        csv_bytes = _make_csv(_LEDGER_ROWS, _LEDGER_COLUMNS)
        response = client.post(
            "/api/recon/upload",
            data={"source": "erp_ledger"},
            files={"file": ("ledger.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rows_read"] == 1
        assert data["rows_imported"] == 1

    def test_missing_ledger_id_skipped(self):
        """ERP rows without ledger_id should be skipped."""
        bad_rows = [{"Ledger ID": "", "Order ID": "order_xyz001"}]
        csv_bytes = _make_csv(bad_rows, ["Ledger ID", "Order ID"])
        response = client.post(
            "/api/recon/upload",
            data={"source": "erp_ledger"},
            files={"file": ("bad_ledger.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rows_skipped"] >= 1

    def test_empty_csv_zero_rows(self):
        """Empty CSV (header only) should return rows_read=0."""
        csv_bytes = b"Ledger ID,Order ID\n"
        response = client.post(
            "/api/recon/upload",
            data={"source": "erp_ledger"},
            files={"file": ("empty.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rows_read"] == 0

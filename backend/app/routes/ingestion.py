"""Real-world data ingestion routes.

Provides two endpoints:
1. ``POST /api/webhooks/razorpay``  — Live Razorpay webhook listener with
   HMAC-SHA256 signature verification.
2. ``POST /api/recon/upload``       — Batch CSV / Excel importer for Razorpay
   Settlement Reports and Tally / Zoho Books ERP ledgers.
"""
import hashlib
import hmac
import io
import logging
from datetime import datetime, timezone
from typing import Literal

import pandas as pd
from fastapi import APIRouter, Body, Depends, File, Form, Header, HTTPException, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Order, Settlement, ErpLedger

router = APIRouter(tags=["ingestion"])
logger = logging.getLogger(__name__)
settings = get_settings()


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Razorpay Webhook Listener
# ─────────────────────────────────────────────────────────────────────────────

class WebhookAck(BaseModel):
    status: str
    event: str
    message: str

# Sample JSON for Swagger UI documentation & testing
EXAMPLE_WEBHOOK_PAYLOAD = {
    "event": "payment.captured",
    "payload": {
        "payment": {
            "entity": {
                "id": "pay_test999",
                "order_id": "order_test999",
                "amount": 50000,
                "currency": "INR",
                "method": "upi",
                "email": "customer@example.com",
                "created_at": 1720000000,
                "description": "Live Test Order"
            }
        }
    }
}


@router.post(
    "/api/webhooks/razorpay",
    response_model=WebhookAck,
    summary="Razorpay Webhook Listener",
    description=(
        "Receives live payment events from Razorpay. "
        "Validates `X-Razorpay-Signature` using HMAC-SHA256 and persists "
        "settlement / payment / refund records into PostgreSQL."
    ),
)
async def razorpay_webhook(
    request: Request,
    body: dict = Body(..., example=EXAMPLE_WEBHOOK_PAYLOAD),
    x_razorpay_signature: str = Header(..., alias="X-Razorpay-Signature"),
    db: Session = Depends(get_db),
) -> WebhookAck:
    """Handle incoming Razorpay webhook events.

    Supported events:
    - ``payment.captured``      → upserts Order record
    - ``settlement.processed``  → upserts Settlement record
    - ``refund.processed``      → marks Order as refunded
    """
    raw_body = await request.body()

    # ── Signature verification (constant-time compare) ────────────────────────
    if settings.RAZORPAY_WEBHOOK_SECRET:
        expected = hmac.new(
            key=settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            msg=raw_body,
            digestmod=hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, x_razorpay_signature):
            logger.warning("Razorpay webhook: invalid signature — request rejected")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid X-Razorpay-Signature",
            )
    else:
        logger.warning(
            "RAZORPAY_WEBHOOK_SECRET not configured — skipping signature check (dev mode)"
        )

    # ── Parse JSON payload ────────────────────────────────────────────────────
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook payload must be valid JSON",
        )

    event: str = payload.get("event", "unknown")
    entity: dict = payload.get("payload", {})
    logger.info(f"Razorpay webhook received: event={event}")

    # ── Route by event type ───────────────────────────────────────────────────
    try:
        if event == "payment.captured":
            _handle_payment_captured(entity, db)
        elif event == "settlement.processed":
            _handle_settlement_processed(entity, db)
        elif event == "refund.processed":
            _handle_refund_processed(entity, db)
        else:
            logger.info(f"Webhook event '{event}' is not handled — acknowledged & ignored")
    except Exception as exc:
        logger.error(f"Error processing webhook event '{event}': {exc}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process event '{event}': {exc}",
        )

    return WebhookAck(status="ok", event=event, message=f"Event '{event}' processed")


# ── Event handlers ────────────────────────────────────────────────────────────

def _handle_payment_captured(payload: dict, db: Session) -> None:
    """Upsert an Order record from a payment.captured event."""
    payment = payload.get("payment", {}).get("entity", {})
    order_id = payment.get("order_id", "")
    payment_id = payment.get("id", "")

    existing = db.query(Order).filter(Order.order_id == order_id).first()
    if existing:
        existing.status = "captured"
        existing.captured_at = datetime.now(timezone.utc)
        logger.debug(f"Updated Order {order_id} → captured")
    else:
        order = Order(
            order_id=order_id or f"rzp_{payment_id}",
            payment_id=payment_id,
            amount=float(payment.get("amount", 0)) / 100,   # paisa → rupees
            currency=payment.get("currency", "INR"),
            status="captured",
            method=payment.get("method", "unknown"),
            created_at=datetime.fromtimestamp(
                payment.get("created_at", datetime.now(timezone.utc).timestamp()),
                tz=timezone.utc,
            ),
            captured_at=datetime.now(timezone.utc),
            customer_email=payment.get("email", ""),
            description=payment.get("description", ""),
        )
        db.add(order)
        logger.debug(f"Inserted Order {order_id} from webhook")
    db.commit()


def _handle_settlement_processed(payload: dict, db: Session) -> None:
    """Upsert a Settlement record from a settlement.processed event."""
    settlement = payload.get("settlement", {}).get("entity", {})
    settlement_id = settlement.get("id", "")

    existing = (
        db.query(Settlement).filter(Settlement.settlement_id == settlement_id).first()
    )
    if existing:
        logger.debug(f"Settlement {settlement_id} already exists — skipping")
        return

    record = Settlement(
        entity_id=settlement.get("entity_id", ""),
        type=settlement.get("type", "payment"),
        amount=float(settlement.get("amount", 0)) / 100,
        fee=float(settlement.get("fee", 0)) / 100,
        tax=float(settlement.get("tax", 0)) / 100,
        credit=float(settlement.get("credit", 0)) / 100,
        debit=float(settlement.get("debit", 0)) / 100,
        settlement_id=settlement_id,
        settlement_utr=settlement.get("utr", ""),
        settled_at=datetime.fromtimestamp(
            settlement.get("settled_at", datetime.now(timezone.utc).timestamp()),
            tz=timezone.utc,
        ),
        order_id=settlement.get("order_id", ""),
    )
    db.add(record)
    db.commit()
    logger.info(f"Inserted Settlement {settlement_id} from webhook")


def _handle_refund_processed(payload: dict, db: Session) -> None:
    """Mark an Order as refunded from a refund.processed event."""
    refund = payload.get("refund", {}).get("entity", {})
    payment_id = refund.get("payment_id", "")
    refund_amount = float(refund.get("amount", 0)) / 100

    order = db.query(Order).filter(Order.payment_id == payment_id).first()
    if order:
        order.status = "refunded"
        order.refund_amount = refund_amount
        db.commit()
        logger.info(f"Marked Order payment_id={payment_id} as refunded (₹{refund_amount})")
    else:
        logger.warning(f"Refund webhook: no Order found for payment_id={payment_id}")


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Batch CSV / Excel Importer
# ─────────────────────────────────────────────────────────────────────────────

# Column name normalisation — Razorpay Settlement Report headers → ORM fields
_RAZORPAY_SETTLEMENT_COLUMNS: dict[str, str] = {
    "entity id": "entity_id",
    "type": "type",
    "debit": "debit",
    "credit": "credit",
    "amount": "amount",
    "fee": "fee",
    "tax": "tax",
    "mdr fee": "fee",
    "gst": "tax",
    "net credit": "credit",
    "settlement id": "settlement_id",
    "settlement utr": "settlement_utr",
    "utr": "settlement_utr",
    "settled at": "settled_at",
    "order id": "order_id",
    "payment id": "entity_id",
}

# Tally / Zoho Books ERP ledger column mappings
_ERP_LEDGER_COLUMNS: dict[str, str] = {
    "ledger id": "ledger_id",
    "invoice id": "invoice_id",
    "order id": "order_id",
    "expected amount": "expected_amount",
    "recorded amount": "recorded_amount",
    "payment method": "payment_method",
    "entry date": "entry_date",
    "status": "status",
    "notes": "notes",
}


class ImportSummary(BaseModel):
    source: str
    rows_read: int
    rows_imported: int
    rows_skipped: int
    errors: list[str]


@router.post(
    "/api/recon/upload",
    response_model=ImportSummary,
    summary="Batch CSV / Excel Importer",
    description=(
        "Upload a Razorpay Settlement Report (CSV/XLSX) or ERP Ledger export. "
        "Auto-maps column headers and bulk-inserts into PostgreSQL."
    ),
)
async def upload_file(
    file: UploadFile = File(..., description="CSV or XLSX file to import"),
    source: Literal["razorpay_settlement", "erp_ledger"] = Form(
        ...,
        description="Type of file: 'razorpay_settlement' or 'erp_ledger'",
    ),
    db: Session = Depends(get_db),
) -> ImportSummary:
    """Ingest a settlement or ERP ledger file.

    - Accepts ``.csv`` and ``.xlsx`` files (up to 50 MB).
    - Normalises column headers (case-insensitive, strips whitespace).
    - Skips duplicate rows (by primary key — ``settlement_id`` or ``ledger_id``).
    - Returns an import summary with row counts and any per-row errors.
    """
    # ── Validate file type ────────────────────────────────────────────────────
    filename = file.filename or ""
    if not (filename.endswith(".csv") or filename.endswith(".xlsx")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only .csv and .xlsx files are supported",
        )

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 50 MB limit",
        )

    # ── Read into DataFrame ───────────────────────────────────────────────────
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse file: {exc}",
        )

    # Normalise column headers (lowercase, strip whitespace)
    df.columns = [str(c).strip().lower() for c in df.columns]
    rows_read = len(df)
    logger.info(f"Importing {rows_read} rows from '{filename}' (source={source})")

    # ── Dispatch to the appropriate importer ──────────────────────────────────
    if source == "razorpay_settlement":
        rows_imported, rows_skipped, errors = _import_settlements(df, db)
    else:
        rows_imported, rows_skipped, errors = _import_erp_ledger(df, db)

    return ImportSummary(
        source=source,
        rows_read=rows_read,
        rows_imported=rows_imported,
        rows_skipped=rows_skipped,
        errors=errors[:50],  # cap error list for response size
    )


def _normalise_row(row: pd.Series, column_map: dict[str, str]) -> dict:
    """Map raw DataFrame row keys to ORM field names."""
    result = {}
    for raw_col, orm_field in column_map.items():
        if raw_col in row.index:
            val = row[raw_col]
            result[orm_field] = None if pd.isna(val) else val
    return result


def _import_settlements(df: pd.DataFrame, db: Session):
    """Bulk-import Razorpay Settlement rows into the ``settlements`` table."""
    imported = skipped = 0
    errors: list[str] = []

    for idx, row in df.iterrows():
        try:
            data = _normalise_row(row, _RAZORPAY_SETTLEMENT_COLUMNS)
            settlement_id = str(data.get("settlement_id", "")).strip()
            if not settlement_id:
                skipped += 1
                errors.append(f"Row {idx}: missing settlement_id — skipped")
                continue

            # Dedup check
            if db.query(Settlement).filter(Settlement.settlement_id == settlement_id).first():
                skipped += 1
                continue

            # Parse settled_at
            settled_at_raw = data.get("settled_at")
            try:
                settled_at = pd.to_datetime(settled_at_raw, utc=True).to_pydatetime()
            except Exception:
                settled_at = datetime.now(timezone.utc)

            record = Settlement(
                entity_id=str(data.get("entity_id", "") or ""),
                type=str(data.get("type", "payment") or "payment"),
                amount=float(data.get("amount") or 0),
                fee=float(data.get("fee") or 0),
                tax=float(data.get("tax") or 0),
                credit=float(data.get("credit") or 0),
                debit=float(data.get("debit") or 0),
                settlement_id=settlement_id,
                settlement_utr=str(data.get("settlement_utr", "") or ""),
                settled_at=settled_at,
                order_id=str(data.get("order_id", "") or ""),
            )
            db.add(record)
            imported += 1
        except Exception as exc:
            errors.append(f"Row {idx}: {exc}")
            skipped += 1

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(f"Settlement import commit failed: {exc}")
        errors.append(f"Database commit error: {exc}")

    return imported, skipped, errors


def _import_erp_ledger(df: pd.DataFrame, db: Session):
    """Bulk-import ERP Ledger rows into the ``erp_ledger`` table."""
    imported = skipped = 0
    errors: list[str] = []

    for idx, row in df.iterrows():
        try:
            data = _normalise_row(row, _ERP_LEDGER_COLUMNS)
            ledger_id = str(data.get("ledger_id", "")).strip()
            if not ledger_id:
                skipped += 1
                errors.append(f"Row {idx}: missing ledger_id — skipped")
                continue

            if db.query(ErpLedger).filter(ErpLedger.ledger_id == ledger_id).first():
                skipped += 1
                continue

            entry_date_raw = data.get("entry_date")
            try:
                entry_date = pd.to_datetime(entry_date_raw).date()
            except Exception:
                entry_date = datetime.now(timezone.utc).date()

            record = ErpLedger(
                ledger_id=ledger_id,
                invoice_id=str(data.get("invoice_id", "") or ""),
                order_id=str(data.get("order_id", "") or ""),
                expected_amount=float(data.get("expected_amount") or 0),
                recorded_amount=float(data.get("recorded_amount") or 0),
                payment_method=str(data.get("payment_method", "unknown") or "unknown"),
                entry_date=entry_date,
                status=str(data.get("status", "pending") or "pending"),
                notes=str(data.get("notes", "") or ""),
            )
            db.add(record)
            imported += 1
        except Exception as exc:
            errors.append(f"Row {idx}: {exc}")
            skipped += 1

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(f"ERP ledger import commit failed: {exc}")
        errors.append(f"Database commit error: {exc}")

    return imported, skipped, errors

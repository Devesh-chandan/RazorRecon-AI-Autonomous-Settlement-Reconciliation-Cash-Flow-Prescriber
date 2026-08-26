"""SQLAlchemy engine + session factory."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def auto_heal_schema(db_engine):
    """Ensure newly added ORM columns exist in existing database tables."""
    import logging
    from sqlalchemy import inspect, text
    logger = logging.getLogger(__name__)

    try:
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()
        with db_engine.begin() as conn:
            # 1. Settlements table columns: gateway, import_source
            if "settlements" in tables:
                settlement_cols = {col["name"] for col in inspector.get_columns("settlements")}
                if "gateway" not in settlement_cols:
                    logger.info("Auto-healing: Adding missing column 'gateway' to 'settlements' table")
                    conn.execute(text("ALTER TABLE settlements ADD COLUMN gateway VARCHAR(50);"))
                if "import_source" not in settlement_cols:
                    logger.info("Auto-healing: Adding missing column 'import_source' to 'settlements' table")
                    conn.execute(text("ALTER TABLE settlements ADD COLUMN import_source VARCHAR(20) DEFAULT 'seeded';"))

            # 2. Orders table columns: refund_amount, erp_invoice
            if "orders" in tables:
                order_cols = {col["name"] for col in inspector.get_columns("orders")}
                if "refund_amount" not in order_cols:
                    logger.info("Auto-healing: Adding missing column 'refund_amount' to 'orders' table")
                    conn.execute(text("ALTER TABLE orders ADD COLUMN refund_amount NUMERIC(12, 2) DEFAULT 0;"))
                if "erp_invoice" not in order_cols:
                    logger.info("Auto-healing: Adding missing column 'erp_invoice' to 'orders' table")
                    conn.execute(text("ALTER TABLE orders ADD COLUMN erp_invoice VARCHAR(30);"))
    except Exception as exc:
        logger.warning(f"Schema auto-heal check warning: {exc}")


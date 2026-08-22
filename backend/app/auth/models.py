"""SQLAlchemy ORM model for the Merchant (user) table."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.database import Base


class Merchant(Base):
    """Represents a merchant / finance user who can log in to RazorRecon AI.

    Roles:
        admin    — full access (seed data, manage users)
        finance  — run reconciliation, upload files
        auditor  — read-only access to results and audit logs
    """
    __tablename__ = "merchants"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), default="")
    role = Column(String(20), nullable=False, default="finance")  # admin | finance | auditor
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

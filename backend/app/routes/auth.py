"""Authentication routes — register, login, and profile."""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.jwt import hash_password, verify_password, create_access_token
from app.auth.models import Merchant
from app.auth.dependencies import get_current_merchant

router = APIRouter(prefix="/api/auth", tags=["authentication"])
logger = logging.getLogger(__name__)


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class MerchantRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""
    role: str = "finance"   # admin | finance | auditor


class MerchantOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    merchant: MerchantOut


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=MerchantOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new merchant account",
)
async def register(body: MerchantRegister, db: Session = Depends(get_db)):
    """Create a new merchant account with a hashed password.

    - Role must be one of: ``admin``, ``finance``, ``auditor``.
    - Duplicate email addresses are rejected with **409 Conflict**.
    """
    if body.role not in {"admin", "finance", "auditor"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Role must be one of: admin, finance, auditor",
        )

    existing = db.query(Merchant).filter(Merchant.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Account with email '{body.email}' already exists",
        )

    merchant = Merchant(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    logger.info(f"Registered new merchant: {merchant.email} (role={merchant.role})")
    return merchant


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Login — returns JWT access token",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """OAuth2-compatible login endpoint.

    Accepts ``application/x-www-form-urlencoded`` with ``username`` (email) and
    ``password`` fields. Returns a JWT bearer token valid for
    ``ACCESS_TOKEN_EXPIRE_MINUTES`` minutes.
    """
    merchant = db.query(Merchant).filter(Merchant.email == form_data.username).first()
    if not merchant or not verify_password(form_data.password, merchant.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not merchant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled — contact your administrator",
        )

    # Update last_login timestamp
    merchant.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(merchant)

    token = create_access_token(data={"sub": str(merchant.id), "role": merchant.role})
    logger.info(f"Login success: {merchant.email}")
    return TokenResponse(access_token=token, merchant=merchant)


@router.get(
    "/me",
    response_model=MerchantOut,
    summary="Get the currently authenticated merchant",
)
async def get_me(merchant: Merchant = Depends(get_current_merchant)):
    """Returns profile of the authenticated merchant (requires Bearer token)."""
    return merchant

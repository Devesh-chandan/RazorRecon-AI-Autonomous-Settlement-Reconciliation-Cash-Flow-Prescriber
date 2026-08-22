"""FastAPI dependency injection for JWT-based authentication.

Usage in a route::

    from app.auth.dependencies import get_current_merchant

    @router.get("/protected")
    async def my_route(merchant = Depends(get_current_merchant)):
        return {"email": merchant.email}
"""
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.jwt import decode_access_token
from app.auth.models import Merchant

logger = logging.getLogger(__name__)

# Reads the Bearer token from the Authorization header automatically.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_current_merchant(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Merchant:
    """Dependency that validates the JWT and returns the authenticated Merchant.

    Raises:
        HTTPException 401: If the token is missing, invalid, or expired.
        HTTPException 403: If the merchant account is inactive.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        merchant_id: str = payload.get("sub")
        if merchant_id is None:
            raise credentials_exc
    except JWTError as exc:
        logger.warning(f"JWT decode failed: {exc}")
        raise credentials_exc

    merchant = db.query(Merchant).filter(Merchant.id == int(merchant_id)).first()
    if merchant is None:
        raise credentials_exc
    if not merchant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant account is inactive",
        )
    return merchant


def require_role(*roles: str):
    """Factory that returns a dependency enforcing one of the allowed roles.

    Usage::

        @router.delete("/admin-only", dependencies=[Depends(require_role("admin"))])
        async def admin_endpoint(): ...
    """
    def _check(merchant: Merchant = Depends(get_current_merchant)) -> Merchant:
        if merchant.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{merchant.role}' is not authorized for this endpoint",
            )
        return merchant
    return _check

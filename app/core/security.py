"""
Security utilities: password hashing, JWT token management, and RBAC.

- Passwords are hashed with **bcrypt** via passlib.
- JWTs are signed with **HS256** via python-jose.
- ``RoleChecker`` is a reusable FastAPI dependency for RBAC enforcement.
"""

import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.core.enums import UserRole

settings = get_settings()

# ── Password Hashing ────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of *plain_password*."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return ``True`` if *plain_password* matches *hashed_password*."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Tokens ───────────────────────────────────────────────

def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a short-lived access JWT."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4()),
    })
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(data: dict) -> str:
    """Create a long-lived refresh JWT with a unique JTI."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    })
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict:
    """Decode and validate a JWT.  Raises ``JWTError`` on failure."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


# ── RBAC ─────────────────────────────────────────────────────

class RoleChecker:
    """
    FastAPI dependency that restricts access to users with one of the
    *allowed_roles*.

    Usage::

        @router.get("/admin-only", dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
        async def admin_endpoint(): ...
    """

    def __init__(self, allowed_roles: list[UserRole]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, current_user_role: str) -> bool:
        """Return ``True`` if the user's role is permitted; raise otherwise."""
        from app.exceptions import ForbiddenException

        if current_user_role not in [r.value for r in self.allowed_roles]:
            raise ForbiddenException(
                detail=f"Role '{current_user_role}' is not allowed. "
                f"Required: {[r.value for r in self.allowed_roles]}"
            )
        return True

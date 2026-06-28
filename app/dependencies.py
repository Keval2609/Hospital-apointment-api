"""
Dependency Injection wiring for FastAPI.

Provides injectable factories for the current user, repositories,
services, and role-based access checks.
"""

import uuid
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.core.security import decode_token
from app.database import get_db
from app.exceptions import ForbiddenException, UnauthorizedException
from app.models.user import User
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.token_blacklist_repository import TokenBlacklistRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.doctor_service import DoctorService
from app.services.patient_service import PatientService
from app.services.user_service import UserService


# ── Database Session ─────────────────────────────────────────

DbSession = Annotated[AsyncSession, Depends(get_db)]


# ── Repository Factories ────────────────────────────────────

def get_user_repository(db: DbSession) -> UserRepository:
    return UserRepository(db)


def get_doctor_repository(db: DbSession) -> DoctorRepository:
    return DoctorRepository(db)


def get_patient_repository(db: DbSession) -> PatientRepository:
    return PatientRepository(db)


def get_token_blacklist_repository(db: DbSession) -> TokenBlacklistRepository:
    return TokenBlacklistRepository(db)


# ── Service Factories ────────────────────────────────────────

def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    token_bl_repo: Annotated[
        TokenBlacklistRepository, Depends(get_token_blacklist_repository)
    ],
) -> AuthService:
    return AuthService(user_repo, token_bl_repo)


def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(user_repo)


def get_doctor_service(
    doctor_repo: Annotated[DoctorRepository, Depends(get_doctor_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> DoctorService:
    return DoctorService(doctor_repo, user_repo)


def get_patient_service(
    patient_repo: Annotated[PatientRepository, Depends(get_patient_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> PatientService:
    return PatientService(patient_repo, user_repo)


# ── Authentication ───────────────────────────────────────────

async def get_current_user(
    authorization: Annotated[str, Header()],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    """
    Extract and validate the Bearer token from the Authorization header,
    then load and return the corresponding ``User`` entity.
    """
    if not authorization.startswith("Bearer "):
        raise UnauthorizedException(detail="Invalid authorization header format.")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_token(token)
    except Exception:
        raise UnauthorizedException(detail="Invalid or expired token.")

    if payload.get("type") != "access":
        raise UnauthorizedException(detail="Token is not an access token.")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException(detail="Token payload missing subject.")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException(detail="Invalid user ID in token.")

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedException(detail="User not found.")
    if not user.is_active:
        raise UnauthorizedException(detail="User account is deactivated.")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_token_payload(
    authorization: Annotated[str, Header()],
) -> dict:
    """Extract the full JWT payload (used for logout)."""
    if not authorization.startswith("Bearer "):
        raise UnauthorizedException(detail="Invalid authorization header format.")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        return decode_token(token)
    except Exception:
        raise UnauthorizedException(detail="Invalid or expired token.")


# ── Role-Based Access ────────────────────────────────────────

def require_roles(*roles: UserRole):
    """
    Return a FastAPI dependency that restricts access to the listed roles.

    Usage::

        @router.get("/admin", dependencies=[Depends(require_roles(UserRole.ADMIN))])
        async def admin_only(): ...
    """

    async def _check(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise ForbiddenException(
                detail=(
                    f"Role '{current_user.role.value}' is not permitted. "
                    f"Required: {[r.value for r in roles]}"
                )
            )
        return current_user

    return _check

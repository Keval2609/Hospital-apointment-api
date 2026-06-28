"""
Authentication service.

Orchestrates registration, login, token refresh, and logout by
composing the UserRepository, TokenBlacklistRepository, and security
utilities.
"""

from datetime import datetime, timezone

from app.core.enums import UserRole
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.exceptions import (
    ConflictException,
    UnauthorizedException,
    ValidationException,
)
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User
from app.repositories.token_blacklist_repository import TokenBlacklistRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest, TokenResponse


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        token_blacklist_repo: TokenBlacklistRepository,
    ) -> None:
        self.user_repo = user_repo
        self.token_blacklist_repo = token_blacklist_repo

    async def register(self, data: RegisterRequest) -> User:
        """
        Create a new user account.

        - Checks for duplicate email.
        - Hashes password.
        - Creates a role-specific profile (Doctor or Patient) automatically.
        """
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictException(detail=f"Email '{data.email}' is already registered.")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            phone=data.phone,
            role=data.role,
            is_active=True,
        )
        user = await self.user_repo.create(user)

        # Auto-create role-specific profile
        if data.role == UserRole.DOCTOR:
            doctor = Doctor(
                user_id=user.id,
                specialty="General",
                license_number=f"TEMP-{user.id.hex[:8]}",
                experience_years=0,
                consultation_fee=0.00,
                is_available=True,
            )
            self.user_repo.session.add(doctor)
            await self.user_repo.session.flush()
        elif data.role == UserRole.PATIENT:
            patient = Patient(user_id=user.id)
            self.user_repo.session.add(patient)
            await self.user_repo.session.flush()

        return user

    async def login(self, email: str, password: str) -> TokenResponse:
        """
        Authenticate a user and return access + refresh tokens.
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UnauthorizedException(detail="Invalid email or password.")
        if not user.is_active:
            raise UnauthorizedException(detail="Account is deactivated.")
        if not verify_password(password, user.hashed_password):
            raise UnauthorizedException(detail="Invalid email or password.")

        token_data = {"sub": str(user.id), "role": user.role.value}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """
        Validate a refresh token and issue a new token pair.
        """
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise UnauthorizedException(detail="Invalid or expired refresh token.")

        if payload.get("type") != "refresh":
            raise ValidationException(detail="Token is not a refresh token.")

        jti = payload.get("jti", "")
        if await self.token_blacklist_repo.is_blacklisted(jti):
            raise UnauthorizedException(detail="Token has been revoked.")

        # Blacklist the old refresh token
        exp_timestamp = payload.get("exp", 0)
        expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        blacklist_entry = TokenBlacklist(
            jti=jti,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
        )
        await self.token_blacklist_repo.create(blacklist_entry)

        # Issue new tokens
        token_data = {"sub": payload["sub"], "role": payload["role"]}
        new_access = create_access_token(token_data)
        new_refresh = create_refresh_token(token_data)

        return TokenResponse(access_token=new_access, refresh_token=new_refresh)

    async def logout(self, token_payload: dict) -> None:
        """
        Blacklist the current token's JTI so it cannot be reused.
        """
        jti = token_payload.get("jti", "")
        if not jti:
            raise ValidationException(detail="Token has no JTI.")

        if await self.token_blacklist_repo.is_blacklisted(jti):
            return  # Already blacklisted — idempotent

        exp_timestamp = token_payload.get("exp", 0)
        expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        blacklist_entry = TokenBlacklist(
            jti=jti,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
        )
        await self.token_blacklist_repo.create(blacklist_entry)

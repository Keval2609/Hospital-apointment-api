"""
Tests for the service layer business logic.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.exceptions import ConflictException, NotFoundException, UnauthorizedException
from app.repositories.token_blacklist_repository import TokenBlacklistRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate
from tests.conftest import create_test_user


class TestAuthService:
    """AuthService business logic."""

    @pytest.mark.asyncio
    async def test_register_creates_user(self, db_session: AsyncSession):
        user_repo = UserRepository(db_session)
        token_bl_repo = TokenBlacklistRepository(db_session)
        service = AuthService(user_repo, token_bl_repo)

        data = RegisterRequest(
            email="authsvc@example.com",
            password="strongpass123",
            full_name="Auth Svc User",
            role=UserRole.PATIENT,
        )
        user = await service.register(data)
        await db_session.commit()

        assert user.email == "authsvc@example.com"
        assert user.role == UserRole.PATIENT

    @pytest.mark.asyncio
    async def test_register_duplicate_raises_conflict(
        self, db_session: AsyncSession
    ):
        user_repo = UserRepository(db_session)
        token_bl_repo = TokenBlacklistRepository(db_session)
        service = AuthService(user_repo, token_bl_repo)

        data = RegisterRequest(
            email="dupsvc@example.com",
            password="strongpass123",
            full_name="Dup Svc",
            role=UserRole.PATIENT,
        )
        await service.register(data)
        await db_session.commit()

        with pytest.raises(ConflictException):
            await service.register(data)

    @pytest.mark.asyncio
    async def test_login_success(self, db_session: AsyncSession):
        user_repo = UserRepository(db_session)
        token_bl_repo = TokenBlacklistRepository(db_session)
        service = AuthService(user_repo, token_bl_repo)

        # Register
        data = RegisterRequest(
            email="loginsvc@example.com",
            password="strongpass123",
            full_name="Login Svc",
            role=UserRole.PATIENT,
        )
        await service.register(data)
        await db_session.commit()

        # Login
        token_response = await service.login("loginsvc@example.com", "strongpass123")
        assert token_response.access_token
        assert token_response.refresh_token

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises(self, db_session: AsyncSession):
        user_repo = UserRepository(db_session)
        token_bl_repo = TokenBlacklistRepository(db_session)
        service = AuthService(user_repo, token_bl_repo)

        data = RegisterRequest(
            email="wrongpwsvc@example.com",
            password="strongpass123",
            full_name="Wrong PW Svc",
            role=UserRole.PATIENT,
        )
        await service.register(data)
        await db_session.commit()

        with pytest.raises(UnauthorizedException):
            await service.login("wrongpwsvc@example.com", "wrongpassword")

    @pytest.mark.asyncio
    async def test_login_nonexistent_user_raises(self, db_session: AsyncSession):
        user_repo = UserRepository(db_session)
        token_bl_repo = TokenBlacklistRepository(db_session)
        service = AuthService(user_repo, token_bl_repo)

        with pytest.raises(UnauthorizedException):
            await service.login("ghost@example.com", "anypassword")

    @pytest.mark.asyncio
    async def test_login_inactive_user_raises(self, db_session: AsyncSession):
        user_repo = UserRepository(db_session)
        token_bl_repo = TokenBlacklistRepository(db_session)
        service = AuthService(user_repo, token_bl_repo)

        await create_test_user(
            db_session,
            email="inactive@example.com",
            is_active=False,
        )
        await db_session.commit()

        with pytest.raises(UnauthorizedException):
            await service.login("inactive@example.com", "testpassword123")

    @pytest.mark.asyncio
    async def test_refresh_and_blacklist(self, db_session: AsyncSession):
        user_repo = UserRepository(db_session)
        token_bl_repo = TokenBlacklistRepository(db_session)
        service = AuthService(user_repo, token_bl_repo)

        # Register and login
        data = RegisterRequest(
            email="refreshsvc@example.com",
            password="strongpass123",
            full_name="Refresh Svc",
            role=UserRole.PATIENT,
        )
        await service.register(data)
        await db_session.commit()

        tokens = await service.login("refreshsvc@example.com", "strongpass123")
        new_tokens = await service.refresh(tokens.refresh_token)
        await db_session.commit()

        assert new_tokens.access_token != tokens.access_token

        # Old refresh token should now be blacklisted
        with pytest.raises(UnauthorizedException):
            await service.refresh(tokens.refresh_token)


class TestUserService:
    """UserService business logic."""

    @pytest.mark.asyncio
    async def test_list_users(self, db_session: AsyncSession):
        user_repo = UserRepository(db_session)
        service = UserService(user_repo)

        for i in range(3):
            await create_test_user(
                db_session, email=f"listsvc{i}@example.com"
            )
        await db_session.commit()

        result = await service.list_users(page=1, page_size=10)
        assert result.total == 3
        assert len(result.items) == 3

    @pytest.mark.asyncio
    async def test_get_user_success(self, db_session: AsyncSession):
        user_repo = UserRepository(db_session)
        service = UserService(user_repo)

        user = await create_test_user(
            db_session, email="getsvc@example.com"
        )
        await db_session.commit()

        result = await service.get_user(user.id)
        assert result.email == "getsvc@example.com"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, db_session: AsyncSession):
        user_repo = UserRepository(db_session)
        service = UserService(user_repo)

        with pytest.raises(NotFoundException):
            await service.get_user(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        user_repo = UserRepository(db_session)
        service = UserService(user_repo)

        data = UserCreate(
            email="createsvc@example.com",
            password="strongpass123",
            full_name="Create Svc",
            role=UserRole.PATIENT,
        )
        result = await service.create_user(data)
        assert result.email == "createsvc@example.com"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_raises(self, db_session: AsyncSession):
        user_repo = UserRepository(db_session)
        service = UserService(user_repo)

        data = UserCreate(
            email="dupcreate@example.com",
            password="strongpass123",
            full_name="Dup Create",
            role=UserRole.PATIENT,
        )
        await service.create_user(data)
        await db_session.commit()

        with pytest.raises(ConflictException):
            await service.create_user(data)

    @pytest.mark.asyncio
    async def test_update_user(self, db_session: AsyncSession):
        user_repo = UserRepository(db_session)
        service = UserService(user_repo)

        user = await create_test_user(
            db_session, email="updatesvc@example.com"
        )
        await db_session.commit()

        update_data = UserUpdate(full_name="Updated Svc Name")
        result = await service.update_user(user.id, update_data)
        assert result.full_name == "Updated Svc Name"

    @pytest.mark.asyncio
    async def test_delete_user(self, db_session: AsyncSession):
        user_repo = UserRepository(db_session)
        service = UserService(user_repo)

        user = await create_test_user(
            db_session, email="deletesvc@example.com"
        )
        await db_session.commit()

        await service.delete_user(user.id)
        await db_session.commit()

        with pytest.raises(NotFoundException):
            await service.get_user(user.id)

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, db_session: AsyncSession):
        user_repo = UserRepository(db_session)
        service = UserService(user_repo)

        with pytest.raises(NotFoundException):
            await service.delete_user(uuid.uuid4())

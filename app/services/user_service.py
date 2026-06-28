"""
User CRUD service.

Provides business-logic operations on top of the UserRepository,
including password hashing on create and duplicate-email checks.
"""

import math
import uuid

from app.core.security import hash_password
from app.exceptions import ConflictException, NotFoundException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def list_users(
        self, *, page: int = 1, page_size: int = 20
    ) -> PaginatedResponse[UserResponse]:
        """Return a paginated list of all users."""
        offset = (page - 1) * page_size
        users = await self.user_repo.get_all(offset=offset, limit=page_size)
        total = await self.user_repo.count()
        total_pages = math.ceil(total / page_size) if page_size else 0
        return PaginatedResponse(
            items=[UserResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_user(self, user_id: uuid.UUID) -> UserResponse:
        """Return a single user by ID or raise ``NotFoundException``."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail=f"User '{user_id}' not found.")
        return UserResponse.model_validate(user)

    async def create_user(self, data: UserCreate) -> UserResponse:
        """Create a user (admin action). Hashes the password."""
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictException(detail=f"Email '{data.email}' already in use.")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            phone=data.phone,
            role=data.role,
            is_active=data.is_active,
        )
        user = await self.user_repo.create(user)
        return UserResponse.model_validate(user)

    async def update_user(
        self, user_id: uuid.UUID, data: UserUpdate
    ) -> UserResponse:
        """Partially update a user."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail=f"User '{user_id}' not found.")

        update_dict = data.model_dump(exclude_unset=True)

        # Check email uniqueness if email is being changed
        if "email" in update_dict and update_dict["email"] != user.email:
            existing = await self.user_repo.get_by_email(update_dict["email"])
            if existing:
                raise ConflictException(
                    detail=f"Email '{update_dict['email']}' already in use."
                )

        user = await self.user_repo.update(user, update_dict)
        return UserResponse.model_validate(user)

    async def delete_user(self, user_id: uuid.UUID) -> None:
        """Delete a user by ID."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail=f"User '{user_id}' not found.")
        await self.user_repo.delete(user)

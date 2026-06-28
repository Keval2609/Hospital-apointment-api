"""
User management endpoints (admin-only).
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.enums import UserRole
from app.dependencies import CurrentUser, get_user_service, require_roles
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="List all users",
    description="Return a paginated list of users. Admin only.",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def list_users(
    user_service: Annotated[UserService, Depends(get_user_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse[UserResponse]:
    return await user_service.list_users(page=page, page_size=page_size)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Return a single user. Admin only.",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def get_user(
    user_id: uuid.UUID,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    return await user_service.get_user(user_id)


@router.post(
    "",
    response_model=UserResponse,
    status_code=201,
    summary="Create a user",
    description="Create a new user account. Admin only.",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def create_user(
    data: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    return await user_service.create_user(data)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user",
    description="Partially update a user. Admin only.",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    return await user_service.update_user(user_id, data)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Delete a user",
    description="Delete a user. Admin only.",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def delete_user(
    user_id: uuid.UUID,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> MessageResponse:
    await user_service.delete_user(user_id)
    return MessageResponse(message="User deleted successfully.")

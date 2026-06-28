"""
User Pydantic schemas for CRUD operations.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.core.enums import UserRole


class UserCreate(BaseModel):
    """Admin-only user creation (password is set by admin)."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    role: UserRole
    is_active: bool = True


class UserUpdate(BaseModel):
    """Partial update schema — all fields optional."""

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    """Public representation of a User (no password)."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    full_name: str
    phone: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

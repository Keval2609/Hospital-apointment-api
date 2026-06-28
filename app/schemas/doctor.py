"""
Doctor Pydantic schemas for CRUD operations.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class DoctorCreate(BaseModel):
    """Payload for creating a doctor profile (user must already exist with role=doctor)."""

    user_id: uuid.UUID
    specialty: str = Field(min_length=1, max_length=255)
    license_number: str = Field(min_length=1, max_length=100)
    qualifications: str | None = None
    experience_years: int = Field(default=0, ge=0)
    consultation_fee: float = Field(default=0.00, ge=0)
    is_available: bool = True


class DoctorUpdate(BaseModel):
    """Partial update schema for doctor profiles."""

    specialty: str | None = Field(default=None, min_length=1, max_length=255)
    license_number: str | None = Field(default=None, min_length=1, max_length=100)
    qualifications: str | None = None
    experience_years: int | None = Field(default=None, ge=0)
    consultation_fee: float | None = Field(default=None, ge=0)
    is_available: bool | None = None


class DoctorResponse(BaseModel):
    """Public representation of a Doctor profile."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    specialty: str
    license_number: str
    qualifications: str | None
    experience_years: int
    consultation_fee: float
    is_available: bool
    created_at: datetime
    updated_at: datetime
    user: UserResponse | None = None

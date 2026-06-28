"""
Patient Pydantic schemas for CRUD operations.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class PatientCreate(BaseModel):
    """Payload for creating a patient profile (user must already exist with role=patient)."""

    user_id: uuid.UUID
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=20)
    blood_group: str | None = Field(default=None, max_length=5)
    address: str | None = None
    emergency_contact_name: str | None = Field(default=None, max_length=255)
    emergency_contact_phone: str | None = Field(default=None, max_length=20)
    medical_history: str | None = None


class PatientUpdate(BaseModel):
    """Partial update schema for patient profiles."""

    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=20)
    blood_group: str | None = Field(default=None, max_length=5)
    address: str | None = None
    emergency_contact_name: str | None = Field(default=None, max_length=255)
    emergency_contact_phone: str | None = Field(default=None, max_length=20)
    medical_history: str | None = None


class PatientResponse(BaseModel):
    """Public representation of a Patient profile."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    date_of_birth: date | None
    gender: str | None
    blood_group: str | None
    address: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    medical_history: str | None
    created_at: datetime
    updated_at: datetime
    user: UserResponse | None = None

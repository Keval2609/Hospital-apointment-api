"""
Patient CRUD service.

Handles patient profile management with ownership checks.
"""

import math
import uuid

from app.core.enums import UserRole
from app.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.patient import Patient
from app.repositories.patient_repository import PatientRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate


class PatientService:
    def __init__(
        self,
        patient_repo: PatientRepository,
        user_repo: UserRepository,
    ) -> None:
        self.patient_repo = patient_repo
        self.user_repo = user_repo

    async def list_patients(
        self, *, page: int = 1, page_size: int = 20
    ) -> PaginatedResponse[PatientResponse]:
        """Return a paginated list of all patient profiles."""
        offset = (page - 1) * page_size
        patients = await self.patient_repo.get_all(offset=offset, limit=page_size)
        total = await self.patient_repo.count()
        total_pages = math.ceil(total / page_size) if page_size else 0
        return PaginatedResponse(
            items=[PatientResponse.model_validate(p) for p in patients],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_patient(self, patient_id: uuid.UUID) -> PatientResponse:
        """Return a single patient profile by its ID."""
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundException(detail=f"Patient '{patient_id}' not found.")
        return PatientResponse.model_validate(patient)

    async def get_patient_by_user_id(self, user_id: uuid.UUID) -> PatientResponse:
        """Return a patient profile by the owning user's ID."""
        patient = await self.patient_repo.get_by_user_id(user_id)
        if not patient:
            raise NotFoundException(
                detail=f"Patient profile for user '{user_id}' not found."
            )
        return PatientResponse.model_validate(patient)

    async def create_patient(self, data: PatientCreate) -> PatientResponse:
        """Create a new patient profile."""
        # Verify user exists and has patient role
        user = await self.user_repo.get_by_id(data.user_id)
        if not user:
            raise NotFoundException(detail=f"User '{data.user_id}' not found.")
        if user.role != UserRole.PATIENT:
            raise ValidationException(
                detail=f"User '{data.user_id}' does not have the 'patient' role."
            )

        # Check for existing profile
        existing = await self.patient_repo.get_by_user_id(data.user_id)
        if existing:
            raise ConflictException(
                detail=f"Patient profile for user '{data.user_id}' already exists."
            )

        patient = Patient(
            user_id=data.user_id,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            blood_group=data.blood_group,
            address=data.address,
            emergency_contact_name=data.emergency_contact_name,
            emergency_contact_phone=data.emergency_contact_phone,
            medical_history=data.medical_history,
        )
        patient = await self.patient_repo.create(patient)
        return PatientResponse.model_validate(patient)

    async def update_patient(
        self, patient_id: uuid.UUID, data: PatientUpdate
    ) -> PatientResponse:
        """Partially update a patient profile."""
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundException(detail=f"Patient '{patient_id}' not found.")

        update_dict = data.model_dump(exclude_unset=True)
        patient = await self.patient_repo.update(patient, update_dict)
        return PatientResponse.model_validate(patient)

    async def delete_patient(self, patient_id: uuid.UUID) -> None:
        """Delete a patient profile."""
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundException(detail=f"Patient '{patient_id}' not found.")
        await self.patient_repo.delete(patient)

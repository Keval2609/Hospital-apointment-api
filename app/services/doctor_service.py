"""
Doctor CRUD service.

Handles doctor profile management with specialty filtering and
license number uniqueness.
"""

import math
import uuid

from app.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.enums import UserRole
from app.models.doctor import Doctor
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.doctor import DoctorCreate, DoctorResponse, DoctorUpdate


class DoctorService:
    def __init__(
        self,
        doctor_repo: DoctorRepository,
        user_repo: UserRepository,
    ) -> None:
        self.doctor_repo = doctor_repo
        self.user_repo = user_repo

    async def list_doctors(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        specialty: str | None = None,
        available_only: bool = False,
    ) -> PaginatedResponse[DoctorResponse]:
        """Return a paginated, optionally filtered, list of doctors."""
        offset = (page - 1) * page_size

        if specialty:
            doctors = await self.doctor_repo.get_by_specialty(
                specialty, offset=offset, limit=page_size
            )
        elif available_only:
            doctors = await self.doctor_repo.get_available(
                offset=offset, limit=page_size
            )
        else:
            doctors = await self.doctor_repo.get_all(
                offset=offset, limit=page_size
            )

        total = await self.doctor_repo.count()
        total_pages = math.ceil(total / page_size) if page_size else 0

        return PaginatedResponse(
            items=[DoctorResponse.model_validate(d) for d in doctors],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_doctor(self, doctor_id: uuid.UUID) -> DoctorResponse:
        """Return a single doctor profile by its ID."""
        doctor = await self.doctor_repo.get_by_id(doctor_id)
        if not doctor:
            raise NotFoundException(detail=f"Doctor '{doctor_id}' not found.")
        return DoctorResponse.model_validate(doctor)

    async def get_doctor_by_user_id(self, user_id: uuid.UUID) -> DoctorResponse:
        """Return a doctor profile by the owning user's ID."""
        doctor = await self.doctor_repo.get_by_user_id(user_id)
        if not doctor:
            raise NotFoundException(
                detail=f"Doctor profile for user '{user_id}' not found."
            )
        return DoctorResponse.model_validate(doctor)

    async def create_doctor(self, data: DoctorCreate) -> DoctorResponse:
        """Create a new doctor profile."""
        # Verify user exists and has doctor role
        user = await self.user_repo.get_by_id(data.user_id)
        if not user:
            raise NotFoundException(detail=f"User '{data.user_id}' not found.")
        if user.role != UserRole.DOCTOR:
            raise ValidationException(
                detail=f"User '{data.user_id}' does not have the 'doctor' role."
            )

        # Check for existing profile
        existing_profile = await self.doctor_repo.get_by_user_id(data.user_id)
        if existing_profile:
            raise ConflictException(
                detail=f"Doctor profile for user '{data.user_id}' already exists."
            )

        # Check license uniqueness
        existing_license = await self.doctor_repo.get_by_license_number(
            data.license_number
        )
        if existing_license:
            raise ConflictException(
                detail=f"License number '{data.license_number}' is already registered."
            )

        doctor = Doctor(
            user_id=data.user_id,
            specialty=data.specialty,
            license_number=data.license_number,
            qualifications=data.qualifications,
            experience_years=data.experience_years,
            consultation_fee=data.consultation_fee,
            is_available=data.is_available,
        )
        doctor = await self.doctor_repo.create(doctor)
        return DoctorResponse.model_validate(doctor)

    async def update_doctor(
        self, doctor_id: uuid.UUID, data: DoctorUpdate
    ) -> DoctorResponse:
        """Partially update a doctor profile."""
        doctor = await self.doctor_repo.get_by_id(doctor_id)
        if not doctor:
            raise NotFoundException(detail=f"Doctor '{doctor_id}' not found.")

        update_dict = data.model_dump(exclude_unset=True)

        # Check license uniqueness if changing
        if "license_number" in update_dict:
            existing = await self.doctor_repo.get_by_license_number(
                update_dict["license_number"]
            )
            if existing and existing.id != doctor_id:
                raise ConflictException(
                    detail=f"License number '{update_dict['license_number']}' is already registered."
                )

        doctor = await self.doctor_repo.update(doctor, update_dict)
        return DoctorResponse.model_validate(doctor)

    async def delete_doctor(self, doctor_id: uuid.UUID) -> None:
        """Delete a doctor profile."""
        doctor = await self.doctor_repo.get_by_id(doctor_id)
        if not doctor:
            raise NotFoundException(detail=f"Doctor '{doctor_id}' not found.")
        await self.doctor_repo.delete(doctor)

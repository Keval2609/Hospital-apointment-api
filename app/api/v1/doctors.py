"""
Doctor management endpoints.

- List / Get: authenticated users
- Create / Delete: admin only
- Update: admin or the owning doctor
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.enums import UserRole
from app.dependencies import CurrentUser, get_doctor_service, require_roles
from app.exceptions import ForbiddenException
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.doctor import DoctorCreate, DoctorResponse, DoctorUpdate
from app.services.doctor_service import DoctorService

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get(
    "",
    response_model=PaginatedResponse[DoctorResponse],
    summary="List doctors",
    description="Return a paginated list of doctor profiles. Supports specialty and availability filters.",
)
async def list_doctors(
    current_user: CurrentUser,
    doctor_service: Annotated[DoctorService, Depends(get_doctor_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    specialty: str | None = Query(default=None),
    available_only: bool = Query(default=False),
) -> PaginatedResponse[DoctorResponse]:
    return await doctor_service.list_doctors(
        page=page,
        page_size=page_size,
        specialty=specialty,
        available_only=available_only,
    )


@router.get(
    "/{doctor_id}",
    response_model=DoctorResponse,
    summary="Get doctor by ID",
    description="Return a single doctor profile.",
)
async def get_doctor(
    doctor_id: uuid.UUID,
    current_user: CurrentUser,
    doctor_service: Annotated[DoctorService, Depends(get_doctor_service)],
) -> DoctorResponse:
    return await doctor_service.get_doctor(doctor_id)


@router.post(
    "",
    response_model=DoctorResponse,
    status_code=201,
    summary="Create a doctor profile",
    description="Create a doctor profile for an existing user with the 'doctor' role. Admin only.",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def create_doctor(
    data: DoctorCreate,
    doctor_service: Annotated[DoctorService, Depends(get_doctor_service)],
) -> DoctorResponse:
    return await doctor_service.create_doctor(data)


@router.put(
    "/{doctor_id}",
    response_model=DoctorResponse,
    summary="Update a doctor profile",
    description="Partially update a doctor profile. Admin or the owning doctor.",
)
async def update_doctor(
    doctor_id: uuid.UUID,
    data: DoctorUpdate,
    current_user: CurrentUser,
    doctor_service: Annotated[DoctorService, Depends(get_doctor_service)],
) -> DoctorResponse:
    # Allow admin or the doctor who owns the profile
    if current_user.role != UserRole.ADMIN:
        doctor = await doctor_service.get_doctor(doctor_id)
        if doctor.user_id != current_user.id:
            raise ForbiddenException(
                detail="You can only update your own doctor profile."
            )
    return await doctor_service.update_doctor(doctor_id, data)


@router.delete(
    "/{doctor_id}",
    response_model=MessageResponse,
    summary="Delete a doctor profile",
    description="Delete a doctor profile. Admin only.",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def delete_doctor(
    doctor_id: uuid.UUID,
    doctor_service: Annotated[DoctorService, Depends(get_doctor_service)],
) -> MessageResponse:
    await doctor_service.delete_doctor(doctor_id)
    return MessageResponse(message="Doctor profile deleted successfully.")

"""
Patient management endpoints.

- List: admin or doctor
- Get: admin, doctor, or the owning patient
- Create / Delete: admin only
- Update: admin or the owning patient
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.enums import UserRole
from app.dependencies import CurrentUser, get_patient_service, require_roles
from app.exceptions import ForbiddenException
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate
from app.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get(
    "",
    response_model=PaginatedResponse[PatientResponse],
    summary="List patients",
    description="Return a paginated list of patient profiles. Admin or Doctor only.",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.DOCTOR))],
)
async def list_patients(
    patient_service: Annotated[PatientService, Depends(get_patient_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse[PatientResponse]:
    return await patient_service.list_patients(page=page, page_size=page_size)


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Get patient by ID",
    description="Return a single patient profile. Admin, Doctor, or the owning patient.",
)
async def get_patient(
    patient_id: uuid.UUID,
    current_user: CurrentUser,
    patient_service: Annotated[PatientService, Depends(get_patient_service)],
) -> PatientResponse:
    patient = await patient_service.get_patient(patient_id)

    # Allow admin, doctor, or the patient who owns the profile
    if current_user.role not in (UserRole.ADMIN, UserRole.DOCTOR):
        if patient.user_id != current_user.id:
            raise ForbiddenException(
                detail="You can only view your own patient profile."
            )
    return patient


@router.post(
    "",
    response_model=PatientResponse,
    status_code=201,
    summary="Create a patient profile",
    description="Create a patient profile for an existing user with the 'patient' role. Admin only.",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def create_patient(
    data: PatientCreate,
    patient_service: Annotated[PatientService, Depends(get_patient_service)],
) -> PatientResponse:
    return await patient_service.create_patient(data)


@router.put(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Update a patient profile",
    description="Partially update a patient profile. Admin or the owning patient.",
)
async def update_patient(
    patient_id: uuid.UUID,
    data: PatientUpdate,
    current_user: CurrentUser,
    patient_service: Annotated[PatientService, Depends(get_patient_service)],
) -> PatientResponse:
    # Allow admin or the patient who owns the profile
    if current_user.role != UserRole.ADMIN:
        patient = await patient_service.get_patient(patient_id)
        if patient.user_id != current_user.id:
            raise ForbiddenException(
                detail="You can only update your own patient profile."
            )
    return await patient_service.update_patient(patient_id, data)


@router.delete(
    "/{patient_id}",
    response_model=MessageResponse,
    summary="Delete a patient profile",
    description="Delete a patient profile. Admin only.",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def delete_patient(
    patient_id: uuid.UUID,
    patient_service: Annotated[PatientService, Depends(get_patient_service)],
) -> MessageResponse:
    await patient_service.delete_patient(patient_id)
    return MessageResponse(message="Patient profile deleted successfully.")

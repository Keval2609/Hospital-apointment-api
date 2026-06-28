"""
Tests for the repository layer.

Uses the async SQLite test database to verify BaseRepository and
entity-specific repository operations.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.patient_repository import PatientRepository
from tests.conftest import (
    create_test_doctor,
    create_test_patient,
    create_test_user,
)


class TestUserRepository:
    """UserRepository operations."""

    @pytest.mark.asyncio
    async def test_create_and_get_by_id(self, db_session: AsyncSession):
        repo = UserRepository(db_session)
        user = await create_test_user(db_session, email="repo@example.com")
        await db_session.commit()

        found = await repo.get_by_id(user.id)
        assert found is not None
        assert found.email == "repo@example.com"

    @pytest.mark.asyncio
    async def test_get_by_email(self, db_session: AsyncSession):
        repo = UserRepository(db_session)
        await create_test_user(db_session, email="find@example.com")
        await db_session.commit()

        found = await repo.get_by_email("find@example.com")
        assert found is not None
        assert found.email == "find@example.com"

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, db_session: AsyncSession):
        repo = UserRepository(db_session)
        found = await repo.get_by_email("ghost@example.com")
        assert found is None

    @pytest.mark.asyncio
    async def test_get_all_paginated(self, db_session: AsyncSession):
        repo = UserRepository(db_session)
        for i in range(5):
            await create_test_user(
                db_session, email=f"user{i}@example.com"
            )
        await db_session.commit()

        page1 = await repo.get_all(offset=0, limit=3)
        assert len(page1) == 3

        page2 = await repo.get_all(offset=3, limit=3)
        assert len(page2) == 2

    @pytest.mark.asyncio
    async def test_count(self, db_session: AsyncSession):
        repo = UserRepository(db_session)
        for i in range(3):
            await create_test_user(
                db_session, email=f"count{i}@example.com"
            )
        await db_session.commit()

        total = await repo.count()
        assert total == 3

    @pytest.mark.asyncio
    async def test_update(self, db_session: AsyncSession):
        repo = UserRepository(db_session)
        user = await create_test_user(db_session, email="update@example.com")
        await db_session.commit()

        updated = await repo.update(user, {"full_name": "Updated Name"})
        assert updated.full_name == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete(self, db_session: AsyncSession):
        repo = UserRepository(db_session)
        user = await create_test_user(db_session, email="delete@example.com")
        await db_session.commit()

        await repo.delete(user)
        await db_session.commit()

        found = await repo.get_by_id(user.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_role(self, db_session: AsyncSession):
        repo = UserRepository(db_session)
        await create_test_user(
            db_session, email="admin1@example.com", role=UserRole.ADMIN
        )
        await create_test_user(
            db_session, email="doc1@example.com", role=UserRole.DOCTOR
        )
        await create_test_user(
            db_session, email="pat1@example.com", role=UserRole.PATIENT
        )
        await db_session.commit()

        admins = await repo.get_by_role(UserRole.ADMIN)
        assert len(admins) == 1
        assert admins[0].role == UserRole.ADMIN


class TestDoctorRepository:
    """DoctorRepository operations."""

    @pytest.mark.asyncio
    async def test_get_by_user_id(self, db_session: AsyncSession):
        repo = DoctorRepository(db_session)
        user = await create_test_user(
            db_session, email="doc@example.com", role=UserRole.DOCTOR
        )
        doctor = await create_test_doctor(db_session, user)
        await db_session.commit()

        found = await repo.get_by_user_id(user.id)
        assert found is not None
        assert found.id == doctor.id

    @pytest.mark.asyncio
    async def test_get_by_user_id_not_found(self, db_session: AsyncSession):
        repo = DoctorRepository(db_session)
        found = await repo.get_by_user_id(uuid.uuid4())
        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_license_number(self, db_session: AsyncSession):
        repo = DoctorRepository(db_session)
        user = await create_test_user(
            db_session, email="liccheck@example.com", role=UserRole.DOCTOR
        )
        await create_test_doctor(
            db_session, user, license_number="LIC-UNIQUE-001"
        )
        await db_session.commit()

        found = await repo.get_by_license_number("LIC-UNIQUE-001")
        assert found is not None
        assert found.license_number == "LIC-UNIQUE-001"


class TestPatientRepository:
    """PatientRepository operations."""

    @pytest.mark.asyncio
    async def test_get_by_user_id(self, db_session: AsyncSession):
        repo = PatientRepository(db_session)
        user = await create_test_user(
            db_session, email="pat@example.com", role=UserRole.PATIENT
        )
        patient = await create_test_patient(db_session, user)
        await db_session.commit()

        found = await repo.get_by_user_id(user.id)
        assert found is not None
        assert found.id == patient.id

    @pytest.mark.asyncio
    async def test_get_by_user_id_not_found(self, db_session: AsyncSession):
        repo = PatientRepository(db_session)
        found = await repo.get_by_user_id(uuid.uuid4())
        assert found is None

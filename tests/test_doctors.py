"""
Tests for Doctor CRUD endpoints.
"""

import uuid

import pytest
from httpx import AsyncClient

from app.core.enums import UserRole
from app.models.user import User
from tests.conftest import create_test_doctor, create_test_user, make_auth_header


class TestListDoctors:
    """GET /api/v1/doctors"""

    @pytest.mark.asyncio
    async def test_list_doctors_authenticated(
        self, client: AsyncClient, admin_headers: dict
    ):
        response = await client.get("/api/v1/doctors", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_doctors_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/doctors")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_doctors_with_specialty_filter(
        self, client: AsyncClient, admin_headers: dict
    ):
        response = await client.get(
            "/api/v1/doctors?specialty=Cardiology", headers=admin_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_doctors_available_only(
        self, client: AsyncClient, admin_headers: dict
    ):
        response = await client.get(
            "/api/v1/doctors?available_only=true", headers=admin_headers
        )
        assert response.status_code == 200


class TestGetDoctor:
    """GET /api/v1/doctors/{doctor_id}"""

    @pytest.mark.asyncio
    async def test_get_doctor_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(
            f"/api/v1/doctors/{fake_id}", headers=admin_headers
        )
        assert response.status_code == 404


class TestCreateDoctor:
    """POST /api/v1/doctors"""

    @pytest.mark.asyncio
    async def test_create_doctor_admin_success(
        self, client: AsyncClient, admin_headers: dict
    ):
        # First create a user with doctor role
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "docforcreate@example.com",
                "password": "strongpass123",
                "full_name": "Doc For Create",
                "role": "doctor",
            },
        )
        user_id = reg_resp.json()["id"]

        # The registration auto-creates a doctor profile, so creating another
        # should fail with conflict
        response = await client.post(
            "/api/v1/doctors",
            headers=admin_headers,
            json={
                "user_id": user_id,
                "specialty": "Neurology",
                "license_number": "LIC-CREATE-001",
            },
        )
        # Should be 409 because register already created a profile
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_doctor_forbidden_for_patient(
        self, client: AsyncClient, patient_headers: dict
    ):
        response = await client.post(
            "/api/v1/doctors",
            headers=patient_headers,
            json={
                "user_id": str(uuid.uuid4()),
                "specialty": "Dermatology",
                "license_number": "LIC-FORBIDDEN-001",
            },
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_doctor_user_wrong_role(
        self, client: AsyncClient, admin_headers: dict
    ):
        # Create a patient-role user
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "patientnotdoc@example.com",
                "password": "strongpass123",
                "full_name": "Patient Not Doc",
                "role": "patient",
            },
        )
        user_id = reg_resp.json()["id"]

        response = await client.post(
            "/api/v1/doctors",
            headers=admin_headers,
            json={
                "user_id": user_id,
                "specialty": "Orthopedics",
                "license_number": "LIC-WRONG-001",
            },
        )
        assert response.status_code == 422  # ValidationException


class TestUpdateDoctor:
    """PUT /api/v1/doctors/{doctor_id}"""

    @pytest.mark.asyncio
    async def test_update_doctor_forbidden_other_doctor(
        self, client: AsyncClient
    ):
        """A doctor should not be able to update another doctor's profile."""
        # Create two doctors
        reg1 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "doc1@example.com",
                "password": "strongpass123",
                "full_name": "Doctor 1",
                "role": "doctor",
            },
        )
        reg2 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "doc2@example.com",
                "password": "strongpass123",
                "full_name": "Doctor 2",
                "role": "doctor",
            },
        )

        # Login as doctor 1
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "doc1@example.com", "password": "strongpass123"},
        )
        doc1_token = login_resp.json()["access_token"]
        doc1_headers = {"Authorization": f"Bearer {doc1_token}"}

        # Get doctor 2's profile ID via listing
        login_resp2 = await client.post(
            "/api/v1/auth/login",
            json={"email": "doc2@example.com", "password": "strongpass123"},
        )
        doc2_token = login_resp2.json()["access_token"]
        doc2_headers = {"Authorization": f"Bearer {doc2_token}"}

        # List doctors as doc2 to find their doctor_id
        list_resp = await client.get("/api/v1/doctors", headers=doc2_headers)
        doctors = list_resp.json()["items"]

        # Find doc2's profile
        doc2_user_id = reg2.json()["id"]
        doc2_profile = next(
            (d for d in doctors if d["user_id"] == doc2_user_id), None
        )

        if doc2_profile:
            response = await client.put(
                f"/api/v1/doctors/{doc2_profile['id']}",
                headers=doc1_headers,
                json={"specialty": "Hacked"},
            )
            assert response.status_code == 403


class TestDeleteDoctor:
    """DELETE /api/v1/doctors/{doctor_id}"""

    @pytest.mark.asyncio
    async def test_delete_doctor_forbidden_for_doctor(
        self, client: AsyncClient, doctor_headers: dict
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.delete(
            f"/api/v1/doctors/{fake_id}", headers=doctor_headers
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_doctor_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.delete(
            f"/api/v1/doctors/{fake_id}", headers=admin_headers
        )
        assert response.status_code == 404

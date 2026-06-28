"""
Tests for Patient CRUD endpoints.
"""

import uuid

import pytest
from httpx import AsyncClient

from app.models.user import User


class TestListPatients:
    """GET /api/v1/patients"""

    @pytest.mark.asyncio
    async def test_list_patients_admin(
        self, client: AsyncClient, admin_headers: dict
    ):
        response = await client.get("/api/v1/patients", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_list_patients_doctor(
        self, client: AsyncClient, doctor_headers: dict
    ):
        response = await client.get("/api/v1/patients", headers=doctor_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_patients_forbidden_for_patient(
        self, client: AsyncClient, patient_headers: dict
    ):
        response = await client.get("/api/v1/patients", headers=patient_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_patients_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/patients")
        assert response.status_code == 422


class TestGetPatient:
    """GET /api/v1/patients/{patient_id}"""

    @pytest.mark.asyncio
    async def test_get_patient_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(
            f"/api/v1/patients/{fake_id}", headers=admin_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_own_patient_profile(self, client: AsyncClient):
        """A patient should be able to view their own profile."""
        # Register as patient
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "myprofile@example.com",
                "password": "strongpass123",
                "full_name": "My Profile",
                "role": "patient",
            },
        )
        user_id = reg_resp.json()["id"]

        # Login
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "myprofile@example.com", "password": "strongpass123"},
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Need admin to list patients and find the profile ID
        # Register an admin
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "tempadmin@example.com",
                "password": "strongpass123",
                "full_name": "Temp Admin",
                "role": "admin",
            },
        )
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "tempadmin@example.com", "password": "strongpass123"},
        )
        admin_headers = {
            "Authorization": f"Bearer {admin_login.json()['access_token']}"
        }

        list_resp = await client.get("/api/v1/patients", headers=admin_headers)
        patients = list_resp.json()["items"]
        my_profile = next(
            (p for p in patients if p["user_id"] == user_id), None
        )

        if my_profile:
            response = await client.get(
                f"/api/v1/patients/{my_profile['id']}", headers=headers
            )
            assert response.status_code == 200


class TestCreatePatient:
    """POST /api/v1/patients"""

    @pytest.mark.asyncio
    async def test_create_patient_forbidden_for_patient(
        self, client: AsyncClient, patient_headers: dict
    ):
        response = await client.post(
            "/api/v1/patients",
            headers=patient_headers,
            json={
                "user_id": str(uuid.uuid4()),
                "gender": "Male",
                "blood_group": "A+",
            },
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_patient_user_wrong_role(
        self, client: AsyncClient, admin_headers: dict
    ):
        # Create a doctor-role user
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "docnotpat@example.com",
                "password": "strongpass123",
                "full_name": "Doc Not Pat",
                "role": "doctor",
            },
        )
        user_id = reg_resp.json()["id"]

        response = await client.post(
            "/api/v1/patients",
            headers=admin_headers,
            json={
                "user_id": user_id,
                "gender": "Male",
                "blood_group": "B+",
            },
        )
        assert response.status_code == 422  # Wrong role


class TestUpdatePatient:
    """PUT /api/v1/patients/{patient_id}"""

    @pytest.mark.asyncio
    async def test_update_patient_forbidden_other_patient(
        self, client: AsyncClient
    ):
        """A patient should not be able to update another patient's profile."""
        # Create two patients
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "pat1@example.com",
                "password": "strongpass123",
                "full_name": "Patient 1",
                "role": "patient",
            },
        )
        reg2 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "pat2@example.com",
                "password": "strongpass123",
                "full_name": "Patient 2",
                "role": "patient",
            },
        )

        # Login as patient 1
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "pat1@example.com", "password": "strongpass123"},
        )
        pat1_headers = {
            "Authorization": f"Bearer {login_resp.json()['access_token']}"
        }

        # Create admin to find patient 2's profile
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "adminforpat@example.com",
                "password": "strongpass123",
                "full_name": "Admin For Pat",
                "role": "admin",
            },
        )
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "adminforpat@example.com",
                "password": "strongpass123",
            },
        )
        admin_headers = {
            "Authorization": f"Bearer {admin_login.json()['access_token']}"
        }

        list_resp = await client.get("/api/v1/patients", headers=admin_headers)
        patients = list_resp.json()["items"]
        pat2_user_id = reg2.json()["id"]
        pat2_profile = next(
            (p for p in patients if p["user_id"] == pat2_user_id), None
        )

        if pat2_profile:
            response = await client.put(
                f"/api/v1/patients/{pat2_profile['id']}",
                headers=pat1_headers,
                json={"blood_group": "AB+"},
            )
            assert response.status_code == 403


class TestDeletePatient:
    """DELETE /api/v1/patients/{patient_id}"""

    @pytest.mark.asyncio
    async def test_delete_patient_forbidden_for_patient(
        self, client: AsyncClient, patient_headers: dict
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.delete(
            f"/api/v1/patients/{fake_id}", headers=patient_headers
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_patient_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.delete(
            f"/api/v1/patients/{fake_id}", headers=admin_headers
        )
        assert response.status_code == 404

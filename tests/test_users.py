"""
Tests for User CRUD endpoints (admin-only).
"""

import pytest
from httpx import AsyncClient

from app.models.user import User


class TestListUsers:
    """GET /api/v1/users"""

    @pytest.mark.asyncio
    async def test_list_users_admin(
        self, client: AsyncClient, admin_headers: dict
    ):
        response = await client.get("/api/v1/users", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "total_pages" in data

    @pytest.mark.asyncio
    async def test_list_users_forbidden_for_doctor(
        self, client: AsyncClient, doctor_headers: dict
    ):
        response = await client.get("/api/v1/users", headers=doctor_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_users_forbidden_for_patient(
        self, client: AsyncClient, patient_headers: dict
    ):
        response = await client.get("/api/v1/users", headers=patient_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_users_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/users")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_users_pagination(
        self, client: AsyncClient, admin_headers: dict
    ):
        response = await client.get(
            "/api/v1/users?page=1&page_size=5", headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5


class TestGetUser:
    """GET /api/v1/users/{user_id}"""

    @pytest.mark.asyncio
    async def test_get_user_success(
        self, client: AsyncClient, admin_headers: dict, admin_user: User
    ):
        response = await client.get(
            f"/api/v1/users/{admin_user.id}", headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json()["email"] == admin_user.email

    @pytest.mark.asyncio
    async def test_get_user_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(
            f"/api/v1/users/{fake_id}", headers=admin_headers
        )
        assert response.status_code == 404


class TestCreateUser:
    """POST /api/v1/users"""

    @pytest.mark.asyncio
    async def test_create_user_admin(
        self, client: AsyncClient, admin_headers: dict
    ):
        response = await client.post(
            "/api/v1/users",
            headers=admin_headers,
            json={
                "email": "created@example.com",
                "password": "strongpass123",
                "full_name": "Created User",
                "role": "patient",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "created@example.com"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(
        self, client: AsyncClient, admin_headers: dict
    ):
        payload = {
            "email": "dupuser@example.com",
            "password": "strongpass123",
            "full_name": "Dup User",
            "role": "patient",
        }
        await client.post("/api/v1/users", headers=admin_headers, json=payload)
        response = await client.post(
            "/api/v1/users", headers=admin_headers, json=payload
        )
        assert response.status_code == 409


class TestUpdateUser:
    """PUT /api/v1/users/{user_id}"""

    @pytest.mark.asyncio
    async def test_update_user_success(
        self, client: AsyncClient, admin_headers: dict, admin_user: User
    ):
        response = await client.put(
            f"/api/v1/users/{admin_user.id}",
            headers=admin_headers,
            json={"full_name": "Updated Admin"},
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Admin"

    @pytest.mark.asyncio
    async def test_update_user_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.put(
            f"/api/v1/users/{fake_id}",
            headers=admin_headers,
            json={"full_name": "Ghost"},
        )
        assert response.status_code == 404


class TestDeleteUser:
    """DELETE /api/v1/users/{user_id}"""

    @pytest.mark.asyncio
    async def test_delete_user_success(
        self, client: AsyncClient, admin_headers: dict
    ):
        # Create a user first
        create_resp = await client.post(
            "/api/v1/users",
            headers=admin_headers,
            json={
                "email": "todelete@example.com",
                "password": "strongpass123",
                "full_name": "To Delete",
                "role": "patient",
            },
        )
        user_id = create_resp.json()["id"]

        response = await client.delete(
            f"/api/v1/users/{user_id}", headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json()["message"] == "User deleted successfully."

        # Verify user is gone
        get_resp = await client.get(
            f"/api/v1/users/{user_id}", headers=admin_headers
        )
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.delete(
            f"/api/v1/users/{fake_id}", headers=admin_headers
        )
        assert response.status_code == 404

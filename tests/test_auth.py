"""
Tests for authentication endpoints (register, login, refresh, logout, me).
"""

import pytest
from httpx import AsyncClient


# ── Registration ─────────────────────────────────────────────

class TestRegister:
    """POST /api/v1/auth/register"""

    @pytest.mark.asyncio
    async def test_register_patient_success(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newpatient@example.com",
                "password": "strongpass123",
                "full_name": "New Patient",
                "role": "patient",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newpatient@example.com"
        assert data["role"] == "patient"
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_register_doctor_success(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newdoctor@example.com",
                "password": "strongpass123",
                "full_name": "New Doctor",
                "role": "doctor",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "doctor"

    @pytest.mark.asyncio
    async def test_register_admin_success(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newadmin@example.com",
                "password": "strongpass123",
                "full_name": "New Admin",
                "role": "admin",
            },
        )
        assert response.status_code == 201
        assert response.json()["role"] == "admin"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {
            "email": "dup@example.com",
            "password": "strongpass123",
            "full_name": "First User",
            "role": "patient",
        }
        await client.post("/api/v1/auth/register", json=payload)
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "short@example.com",
                "password": "short",
                "full_name": "Short Pass",
                "role": "patient",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "strongpass123",
                "full_name": "Bad Email",
                "role": "patient",
            },
        )
        assert response.status_code == 422


# ── Login ────────────────────────────────────────────────────

class TestLogin:
    """POST /api/v1/auth/login"""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        # Register first
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "strongpass123",
                "full_name": "Login User",
                "role": "patient",
            },
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "strongpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpw@example.com",
                "password": "strongpass123",
                "full_name": "Wrong PW",
                "role": "patient",
            },
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpw@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "strongpass123"},
        )
        assert response.status_code == 401


# ── Token Refresh ────────────────────────────────────────────

class TestRefresh:
    """POST /api/v1/auth/refresh"""

    @pytest.mark.asyncio
    async def test_refresh_success(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@example.com",
                "password": "strongpass123",
                "full_name": "Refresh User",
                "role": "patient",
            },
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@example.com", "password": "strongpass123"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_reuse_blacklisted_token(self, client: AsyncClient):
        """A refresh token should only be usable once (rotation)."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "reuse@example.com",
                "password": "strongpass123",
                "full_name": "Reuse User",
                "role": "patient",
            },
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "reuse@example.com", "password": "strongpass123"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        # First refresh — should succeed
        await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        # Second refresh with the same token — should fail (blacklisted)
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 401


# ── Logout ───────────────────────────────────────────────────

class TestLogout:
    """POST /api/v1/auth/logout"""

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "logout@example.com",
                "password": "strongpass123",
                "full_name": "Logout User",
                "role": "patient",
            },
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "logout@example.com", "password": "strongpass123"},
        )
        access_token = login_resp.json()["access_token"]

        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out."

    @pytest.mark.asyncio
    async def test_logout_unauthenticated(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 422  # Missing Authorization header


# ── Get Current User ─────────────────────────────────────────

class TestGetMe:
    """GET /api/v1/auth/me"""

    @pytest.mark.asyncio
    async def test_get_me_success(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "me@example.com",
                "password": "strongpass123",
                "full_name": "Me User",
                "role": "patient",
            },
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "me@example.com", "password": "strongpass123"},
        )
        token = login_resp.json()["access_token"]

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["full_name"] == "Me User"

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

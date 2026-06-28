"""
Tests for security utilities (password hashing, JWT, RoleChecker).
"""

import uuid
from datetime import timedelta

import pytest
from jose import jwt

from app.config import get_settings
from app.core.enums import UserRole
from app.core.security import (
    RoleChecker,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.exceptions import ForbiddenException

settings = get_settings()


class TestPasswordHashing:
    """hash_password / verify_password"""

    def test_hash_returns_bcrypt_string(self):
        hashed = hash_password("mysecretpassword")
        assert hashed.startswith("$2b$")
        assert hashed != "mysecretpassword"

    def test_verify_correct_password(self):
        hashed = hash_password("correcthorse")
        assert verify_password("correcthorse", hashed) is True

    def test_verify_incorrect_password(self):
        hashed = hash_password("correcthorse")
        assert verify_password("wronghorse", hashed) is False

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2  # bcrypt salts differ


class TestJWT:
    """create_access_token / create_refresh_token / decode_token"""

    def test_create_and_decode_access_token(self):
        data = {"sub": str(uuid.uuid4()), "role": "admin"}
        token = create_access_token(data)
        payload = decode_token(token)
        assert payload["sub"] == data["sub"]
        assert payload["role"] == data["role"]
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "jti" in payload

    def test_create_and_decode_refresh_token(self):
        data = {"sub": str(uuid.uuid4()), "role": "doctor"}
        token = create_refresh_token(data)
        payload = decode_token(token)
        assert payload["type"] == "refresh"
        assert payload["sub"] == data["sub"]

    def test_access_token_custom_expiry(self):
        data = {"sub": "user123", "role": "patient"}
        token = create_access_token(data, expires_delta=timedelta(minutes=5))
        payload = decode_token(token)
        assert payload["sub"] == "user123"

    def test_expired_token_raises(self):
        data = {"sub": "user123", "role": "patient"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        with pytest.raises(Exception):
            decode_token(token)

    def test_invalid_token_raises(self):
        with pytest.raises(Exception):
            decode_token("not.a.valid.token")

    def test_token_has_unique_jti(self):
        data = {"sub": "user123", "role": "admin"}
        t1 = create_access_token(data)
        t2 = create_access_token(data)
        p1 = decode_token(t1)
        p2 = decode_token(t2)
        assert p1["jti"] != p2["jti"]

    def test_tampered_token_raises(self):
        data = {"sub": "user123", "role": "admin"}
        token = create_access_token(data)
        # Tamper with the payload (middle segment) to break the signature
        parts = token.split(".")
        # Modify the payload by replacing it with a different base64 string
        parts[1] = parts[1][:5] + "TAMPERED" + parts[1][5:]
        tampered = ".".join(parts)
        with pytest.raises(Exception):
            decode_token(tampered)


class TestRoleChecker:
    """RoleChecker dependency"""

    def test_allowed_role_passes(self):
        checker = RoleChecker([UserRole.ADMIN, UserRole.DOCTOR])
        assert checker("admin") is True

    def test_disallowed_role_raises(self):
        checker = RoleChecker([UserRole.ADMIN])
        with pytest.raises(ForbiddenException):
            checker("patient")

    def test_multiple_allowed_roles(self):
        checker = RoleChecker([UserRole.ADMIN, UserRole.DOCTOR, UserRole.PATIENT])
        assert checker("doctor") is True
        assert checker("patient") is True

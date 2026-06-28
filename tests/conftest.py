"""
Shared test fixtures.

Sets up an in-memory async SQLite database, an httpx AsyncClient wired
to the FastAPI app, and pre-authenticated token fixtures for each role.
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings, get_settings
from app.core.enums import UserRole
from app.core.security import create_access_token, hash_password
from app.database import get_db
from app.main import create_app
from app.models.base import Base
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.token_blacklist import TokenBlacklist  # noqa: F401
from app.models.user import User

# ── Test database (async SQLite) ─────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///file::memory:?cache=shared&uri=true"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Override app settings for tests ──────────────────────────

def get_test_settings() -> Settings:
    return Settings(
        DATABASE_URL=TEST_DATABASE_URL,
        JWT_SECRET_KEY="test-secret-key-not-for-production",
        DEBUG=True,
    )


# ── Fixtures ─────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for all async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean database session for a test."""
    async with TestSessionLocal() as session:
        yield session


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an httpx AsyncClient wired to the test app."""
    application = create_app()
    application.dependency_overrides[get_db] = _override_get_db
    application.dependency_overrides[get_settings] = get_test_settings

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Helper: create user directly in DB ───────────────────────

async def create_test_user(
    db: AsyncSession,
    *,
    email: str = "test@example.com",
    password: str = "testpassword123",
    full_name: str = "Test User",
    role: UserRole = UserRole.PATIENT,
    is_active: bool = True,
) -> User:
    """Insert a user directly into the test database."""
    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
        is_active=is_active,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def create_test_doctor(
    db: AsyncSession,
    user: User,
    *,
    specialty: str = "Cardiology",
    license_number: str | None = None,
) -> Doctor:
    """Insert a doctor profile for an existing user."""
    doctor = Doctor(
        id=uuid.uuid4(),
        user_id=user.id,
        specialty=specialty,
        license_number=license_number or f"LIC-{uuid.uuid4().hex[:8]}",
        experience_years=5,
        consultation_fee=100.00,
        is_available=True,
    )
    db.add(doctor)
    await db.flush()
    await db.refresh(doctor)
    return doctor


async def create_test_patient(
    db: AsyncSession,
    user: User,
) -> Patient:
    """Insert a patient profile for an existing user."""
    patient = Patient(
        id=uuid.uuid4(),
        user_id=user.id,
        gender="Other",
        blood_group="O+",
    )
    db.add(patient)
    await db.flush()
    await db.refresh(patient)
    return patient


def make_auth_header(user_id: uuid.UUID, role: UserRole) -> dict[str, str]:
    """Generate an Authorization header with a valid access token."""
    token = create_access_token({"sub": str(user_id), "role": role.value})
    return {"Authorization": f"Bearer {token}"}


# ── Pre-built role-specific fixtures ─────────────────────────

@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    user = await create_test_user(
        db_session,
        email="admin@hospital.com",
        full_name="Admin User",
        role=UserRole.ADMIN,
    )
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def doctor_user(db_session: AsyncSession) -> User:
    user = await create_test_user(
        db_session,
        email="doctor@hospital.com",
        full_name="Doctor User",
        role=UserRole.DOCTOR,
    )
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def patient_user(db_session: AsyncSession) -> User:
    user = await create_test_user(
        db_session,
        email="patient@hospital.com",
        full_name="Patient User",
        role=UserRole.PATIENT,
    )
    await db_session.commit()
    return user


@pytest_asyncio.fixture
def admin_headers(admin_user: User) -> dict[str, str]:
    return make_auth_header(admin_user.id, UserRole.ADMIN)


@pytest_asyncio.fixture
def doctor_headers(doctor_user: User) -> dict[str, str]:
    return make_auth_header(doctor_user.id, UserRole.DOCTOR)


@pytest_asyncio.fixture
def patient_headers(patient_user: User) -> dict[str, str]:
    return make_auth_header(patient_user.id, UserRole.PATIENT)

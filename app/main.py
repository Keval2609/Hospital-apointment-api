"""
FastAPI application factory.

Creates and configures the application instance with middleware,
exception handlers, routers, and OpenAPI documentation.
"""

from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.config import get_settings
from app.exception_handlers import register_exception_handlers
from app.logging_config import setup_logging
from app.middleware import register_middleware
from app.schemas.common import HealthCheckResponse

settings = get_settings()


def create_app() -> FastAPI:
    """Build and return the fully-configured FastAPI application."""
    setup_logging()

    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "A production-ready REST API for managing hospital appointments.\n\n"
            "## Features\n"
            "- JWT-based authentication (register, login, refresh, logout)\n"
            "- Role-Based Access Control (Admin, Doctor, Patient)\n"
            "- Full CRUD for Users, Doctors, and Patients\n"
            "- Pagination, filtering, and validation\n"
            "- Structured logging and correlation IDs\n"
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=[
            {
                "name": "Authentication",
                "description": "Register, login, token refresh, logout, and current-user endpoints.",
            },
            {
                "name": "Users",
                "description": "Admin-only user management (CRUD).",
            },
            {
                "name": "Doctors",
                "description": "Doctor profile management with specialty and availability filters.",
            },
            {
                "name": "Patients",
                "description": "Patient profile management with ownership-based access.",
            },
        ],
    )

    # ── Wire up middleware, handlers, and routers ─────────
    register_middleware(application)
    register_exception_handlers(application)
    application.include_router(v1_router)

    # ── Health check ─────────────────────────────────────
    @application.get(
        "/health",
        response_model=HealthCheckResponse,
        tags=["Health"],
        summary="Health check",
    )
    async def health_check() -> HealthCheckResponse:
        return HealthCheckResponse(
            status="ok", version=settings.APP_VERSION
        )

    return application


app = create_app()

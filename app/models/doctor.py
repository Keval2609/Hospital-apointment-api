"""
Doctor profile ORM model.

Stores clinical details linked 1-to-1 with a User whose role is ``doctor``.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Doctor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "doctors"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    specialty: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    license_number: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    qualifications: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    consultation_fee: Mapped[float] = mapped_column(
        Numeric(10, 2), default=0.00, nullable=False
    )
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Relationships ────────────────────────────────────
    user: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="doctor_profile", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Doctor {self.license_number} specialty={self.specialty}>"

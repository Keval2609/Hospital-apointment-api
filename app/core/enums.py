"""
Application-wide enumerations.
"""

import enum


class UserRole(str, enum.Enum):
    """Roles available within the Hospital Appointment system."""

    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"

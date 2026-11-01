#!/usr/bin/env python
# app/blueprints/jwt_api/schemas.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 11/1/2026

File Purpose: JWT authentication route schemas for the project.
"""

# Standard library imports.
from pydantic import BaseModel, Field, RootModel

class LoginRequest(BaseModel):
    """Request model for login credentials."""
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(
        min_length=1, max_length=128, json_schema_extra={"writeOnly": True}
    )

class MFARequest(BaseModel):
    """Request model for MFA token (TOTP/Recovery Code) verification."""
    token: str = Field(
        min_length=1, max_length=128, json_schema_extra={"writeOnly": True}
    )

class CSRFHeader(BaseModel):
    """Request model for CSRF token header."""
    csrf_token: str | None = Field(
        default=None,
        alias="X-CSRFToken",
        description="Required when CSRF protection is enabled. Obtain from GET /api/v1/jwt/csrf/ and retain the session cookie.",
    )

class CSRFResponse(BaseModel):
    """Response model for CSRF token retrieval."""
    csrf_token: str

class TokenResponse(BaseModel):
    """Response model for successful login, containing JWT access and refresh tokens."""
    user_id: int
    access_token: str
    refresh_token: str
    flashed_messages: dict[str, list[str]]

class MFAResponse(BaseModel):
    """Response model for MFA verification, indicating the next step."""
    redirect_to: str = Field(description="URL to POST the MFA token to, using the same session cookie.")

class LoginResponse(RootModel[TokenResponse | MFAResponse]):
    """Login returns tokens or the next MFA verification URL."""

class ErrorResponse(BaseModel):
    """Error response model for failed authentication attempts."""
    error: str
    flashed_messages: dict[str, list[str]]

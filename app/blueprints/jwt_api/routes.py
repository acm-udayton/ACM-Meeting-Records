#!/usr/bin/env python
# app/blueprints/jwt_api/routes.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 11/1/2026

File Purpose: JWT authentication routes for the project.
"""

# Third-party imports.
from flask import request, url_for
from flask_openapi3 import APIBlueprint, Tag
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Users
from app.services.jwt_service import (
    AuthLoginResult,
    AuthResultStatus,
    authenticate_user,
    refresh_access_token,
    complete_mfa_login,
)
from app.utils import is_admin

# Local application imports.
from .schemas import (
    ErrorResponse,
    LoginRequest,
    LoginResponse,
    MFARequest,
    TokenResponse,
    RefreshTokenResponse,
)

jwt_tag = Tag(name="JWT", description="Operations related to JWT authentication.")
jwt_bp = APIBlueprint(
    "jwt", __name__, url_prefix="/api/v1/jwt", abp_tags=[jwt_tag],
    validate_response=True,
)

def _authentication_error():
    """Use the same response for all authentication failures."""
    return {
        "error": "Login failed",
        "flashed_messages": {"danger": ["Login attempt failed."]},
    }, 401

def _token_response(result: AuthLoginResult, user: Users):
    flashes = {}
    if is_admin(user) and not user.mfa_active:
        flashes["danger"] = [
            "Please enable multi-factor authentication for this administrator account!"
        ]
    return {
        "user_id": result.user_id,
        "access_token": result.access_token,
        "refresh_token": result.refresh_token,
        "flashed_messages": flashes,
    }, 200

@jwt_bp.after_request
def prevent_auth_response_caching(response):
    """ Prevent caching of sensitive authentication responses."""
    response.headers["Cache-Control"] = "no-store"
    return response

@jwt_bp.post(
    "/login/",
    responses={200: LoginResponse, 401: ErrorResponse},
)
def login(body: LoginRequest):
    """Return login tokens or a five-minute mfa_token requiring further verification."""
    result = authenticate_user(body.username, body.password, request.remote_addr)
    status = result.statuses[0] if result.statuses else None
    if status in {
        AuthResultStatus.REQUIRE_TOTP_MFA,
        AuthResultStatus.REQUIRE_RECOVERY_MFA,
    }:
        endpoint = (
            "jwt.verify_totp"
            if status == AuthResultStatus.REQUIRE_TOTP_MFA
            else "jwt.verify_recovery_code"
        )
        return {"redirect_to": url_for(endpoint), "mfa_token": result.mfa_token}, 200

    if status == AuthResultStatus.SUCCESS:
        user = db.session.get(Users, result.user_id)
        return _token_response(result, user)

    return _authentication_error()

def _verify_mfa(body: MFARequest, recovery=False):
    """Translate the MFA service result into an HTTP response."""
    result = complete_mfa_login(body.mfa_token, body.token, recovery=recovery)
    if AuthResultStatus.SUCCESS not in result.statuses:
        return _authentication_error()
    user = db.session.get(Users, result.user_id)
    return _token_response(result, user)

@jwt_bp.post(
    "/mfa/verify-totp/",
    responses={200: TokenResponse, 401: ErrorResponse},
)
def verify_totp(body: MFARequest):
    """Finish JWT login with a TOTP token within five minutes of password login."""
    return _verify_mfa(body)

@jwt_bp.post(
    "/mfa/verify-recovery-code/",
    responses={200: TokenResponse, 401: ErrorResponse},
)
def verify_recovery_code(body: MFARequest):
    """Finish JWT login with a recovery code, consuming it on success."""
    return _verify_mfa(body, recovery=True)

@jwt_bp.post(
    "/refresh",
    security=[{"RefreshBearer": []}],
    responses={200: RefreshTokenResponse, 401: ErrorResponse},
)
@jwt_required(refresh=True)
def refresh():
    """Refresh the JWT access token using a valid refresh token."""
    # Extract identity from the valid refresh token
    user = db.session.get(Users, int(get_jwt_identity()))
    if not user or not user.activated:
        return _authentication_error()
    # Create a fresh access token
    result = refresh_access_token(user)
    return {"access_token": result.access_token}, 200

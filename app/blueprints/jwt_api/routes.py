#!/usr/bin/env python
# app/blueprints/jwt_api/routes.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 11/1/2026

File Purpose: JWT authentication routes for the project.
"""

# Standard library imports.
from time import time

# Third-party imports.
from flask import request, session, url_for
from flask_openapi3 import APIBlueprint, Tag
from flask_wtf.csrf import CSRFError, generate_csrf

from app.extensions import db
from app.models import Users
from app.services.jwt_service import (
    AuthLoginResult,
    AuthResultStatus,
    authenticate_user,
    issue_login_tokens,
)
from app.services.mfa_service import verify_mfa_recovery_code, verify_mfa_totp_code
from app.utils import is_admin

# Local application imports.
from .schemas import (
    CSRFHeader,
    CSRFResponse,
    ErrorResponse,
    LoginRequest,
    LoginResponse,
    MFARequest,
    TokenResponse,
)

jwt_tag = Tag(name="JWT", description="Operations related to JWT authentication.")
jwt_bp = APIBlueprint(
    "jwt", __name__, url_prefix="/api/v1/jwt", abp_tags=[jwt_tag],
    validate_response=True,
)

MFA_SESSION_KEY = "jwt_mfa_login"
MFA_TIMEOUT_SECONDS = 300

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

@jwt_bp.errorhandler(CSRFError)
def csrf_error(error):
    """Keep API CSRF failures in JSON format."""
    return {"error": error.description, "flashed_messages": {}}, 400

@jwt_bp.after_request
def prevent_auth_response_caching(response):
    """ Prevent caching of sensitive authentication responses."""
    response.headers["Cache-Control"] = "no-store"
    return response

@jwt_bp.get("/csrf/", responses={200: CSRFResponse})
def csrf_token():
    """Get a CSRF token; retain the session cookie and send X-CSRFToken on POSTs."""
    return {"csrf_token": generate_csrf()}, 200

@jwt_bp.post(
    "/login/",
    responses={200: LoginResponse, 400: ErrorResponse, 401: ErrorResponse},
)
def login(body: LoginRequest, header: CSRFHeader):
    """Validate credentials and return tokens or an MFA verification URL.

    Send JSON and X-CSRFToken from GET /api/v1/jwt/csrf/. Retain the
    session cookie for CSRF validation and subsequent MFA verification.
    """
    session.pop(MFA_SESSION_KEY, None)
    result = authenticate_user(body.username, body.password, request.remote_addr)
    status = result.statuses[0] if result.statuses else None
    if status in {
        AuthResultStatus.REQUIRE_TOTP_MFA,
        AuthResultStatus.REQUIRE_RECOVERY_MFA,
    }:
        session[MFA_SESSION_KEY] = {"user_id": result.user_id, "started_at": time()}
        endpoint = (
            "jwt.verify_totp"
            if status == AuthResultStatus.REQUIRE_TOTP_MFA
            else "jwt.verify_recovery_code"
        )
        return {"redirect_to": url_for(endpoint)}, 200

    if status == AuthResultStatus.SUCCESS:
        user = db.session.get(Users, result.user_id)
        return _token_response(result, user)

    return _authentication_error()

def _verify_mfa(token, recovery=False):
    """Read session and verify MFA token (TOTP or recovery code) and return JWT tokens on success."""
    pending = session.get(MFA_SESSION_KEY)
    if not pending:
        return _authentication_error()

    age = time() - pending["started_at"]
    user = db.session.get(Users, pending["user_id"])

    # Check for session expiration, user existence, activation, and MFA status.
    if (
        not 0 <= age < MFA_TIMEOUT_SECONDS
        or not user
        or not user.activated
        or not user.mfa_active
    ):
        session.pop(MFA_SESSION_KEY, None)
        return _authentication_error()

    verify = verify_mfa_recovery_code if recovery else verify_mfa_totp_code
    result = verify(user, token)
    if not result.is_success:
        return _authentication_error()

    # Invalidate the login attempt session after successful MFA verification to prevent reuse.
    session.pop(MFA_SESSION_KEY, None)
    return _token_response(issue_login_tokens(user), user)

@jwt_bp.post(
    "/mfa/verify-totp/",
    responses={200: TokenResponse, 400: ErrorResponse, 401: ErrorResponse},
)
def verify_totp(body: MFARequest, header: CSRFHeader):
    """Finish JWT login with a TOTP token within five minutes of password login."""
    return _verify_mfa(body.token)

@jwt_bp.post(
    "/mfa/verify-recovery-code/",
    responses={200: TokenResponse, 400: ErrorResponse, 401: ErrorResponse},
)
def verify_recovery_code(body: MFARequest, header: CSRFHeader):
    """Finish JWT login with a recovery code, consuming it on success."""
    return _verify_mfa(body.token, recovery=True)

#!/usr/bin/env python
# app/services/jwt_service.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 11/1/2026

File Purpose: JWT authentication service for the project.
"""

# Standard library imports.
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

# Third-party imports.
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError

# Local application imports.
from app.models import Users
from app.extensions import db
from app.services.mfa_service import verify_mfa_recovery_code, verify_mfa_totp_code


MFA_TOKEN_LIFETIME = timedelta(minutes=5)


class AuthResultStatus(str, Enum):
    """Granular outcomes for auth operations."""

    SUCCESS = "success"
    USER_NOT_FOUND = "user_not_found"
    ACCOUNT_NOT_ACTIVATED = "account_not_activated"
    INVALID_PASSWORD = "invalid_password"
    REQUIRE_TOTP_MFA = "require_totp_mfa"
    REQUIRE_RECOVERY_MFA = "require_recovery_mfa"
    DUPLICATE_USERNAME = "duplicate_username"
    INVALID_MFA_TOKEN = "invalid_mfa_token"
    INVALID_MFA_CODE = "invalid_mfa_code"


@dataclass(slots=True)
class AuthLoginResult:
    """Login outcome plus the matched user, if any."""

    statuses: tuple[AuthResultStatus, ...]
    user_id: int | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    mfa_token: str | None = None


def authenticate_user(username: str, password: str, remote_addr: str | None) -> AuthLoginResult:
    """Validate login credentials and return the matching outcome."""
    user = Users.query.filter(Users.username == username).first()
    if user is None:
        return AuthLoginResult(statuses=(AuthResultStatus.USER_NOT_FOUND,))

    statuses: list[AuthResultStatus] = []

    if user.activated is False:
        statuses.append(AuthResultStatus.ACCOUNT_NOT_ACTIVATED)

    if not user.check_password(password):
        current_app.logger.warning(
            "Login attempt as %s from IP %s - failed",
            username,
            remote_addr,
        )
        statuses.append(AuthResultStatus.INVALID_PASSWORD)

    if statuses:
        return AuthLoginResult(statuses=tuple(statuses), user_id=user.id)

    if user.mfa_active:
        status = (
            AuthResultStatus.REQUIRE_TOTP_MFA
            if user.totp_active
            else AuthResultStatus.REQUIRE_RECOVERY_MFA
        )
        return AuthLoginResult(
            statuses=(status,),
            user_id=user.id,
            mfa_token=create_access_token(
                identity=str(user.id),
                expires_delta=MFA_TOKEN_LIFETIME,
                additional_claims={"type": "mfa"},
            ),
        )

    current_app.logger.info(
        "Login attempt as %s from IP %s - success", username, remote_addr
    )
    return issue_login_tokens(user)


def issue_login_tokens(user: Users) -> AuthLoginResult:
    """Issue tokens after all required authentication steps succeed."""
    return AuthLoginResult(
        statuses=(AuthResultStatus.SUCCESS,),
        user_id=user.id,
        access_token=create_access_token(identity=str(user.id)),
        refresh_token=create_refresh_token(identity=str(user.id)),
    )

def refresh_access_token(user: Users) -> AuthLoginResult:
    """Issue a new access token for the user."""
    return AuthLoginResult(
        statuses=(AuthResultStatus.SUCCESS,),
        access_token=create_access_token(identity=str(user.id)),
    )

def complete_mfa_login(mfa_token: str, token: str, recovery: bool = False) -> AuthLoginResult:
    """Verify the signed MFA challenge and code before issuing login tokens."""
    try:
        claims = decode_token(mfa_token)
        # Ensure correct token type.
        if claims.get("type") != "mfa":
            return AuthLoginResult(statuses=(AuthResultStatus.INVALID_MFA_TOKEN,))
        # JWT_IDENTITY_CLAIM defaults to "sub" on jwt.init_app().
        identity = claims[current_app.config["JWT_IDENTITY_CLAIM"]]
        user_id = int(identity)
    except (PyJWTError, JWTExtendedException, ValueError, TypeError, KeyError):
        return AuthLoginResult(statuses=(AuthResultStatus.INVALID_MFA_TOKEN,))

    user = db.session.get(Users, user_id)
    if not user or not user.activated or not user.mfa_active:
        return AuthLoginResult(statuses=(AuthResultStatus.INVALID_MFA_TOKEN,))

    # Verify the provided MFA code using the appropriate method.
    verify = verify_mfa_recovery_code if recovery else verify_mfa_totp_code
    if not verify(user, token).is_success:
        return AuthLoginResult(statuses=(AuthResultStatus.INVALID_MFA_CODE,))

    return issue_login_tokens(user)

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
from enum import Enum

# Third-party imports.
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token

# Local application imports.
from app.models import Users


class AuthResultStatus(str, Enum):
    """Granular outcomes for auth operations."""

    SUCCESS = "success"
    USER_NOT_FOUND = "user_not_found"
    ACCOUNT_NOT_ACTIVATED = "account_not_activated"
    INVALID_PASSWORD = "invalid_password"
    REQUIRE_TOTP_MFA = "require_totp_mfa"
    REQUIRE_RECOVERY_MFA = "require_recovery_mfa"
    DUPLICATE_USERNAME = "duplicate_username"


@dataclass(slots=True)
class AuthLoginResult:
    """Login outcome plus the matched user, if any."""

    statuses: tuple[AuthResultStatus, ...]
    user_id: int | None = None
    access_token: str | None = None
    refresh_token: str | None = None


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

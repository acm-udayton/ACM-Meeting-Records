#!/usr/bin/env python
# app/services/auth_service.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 8/1/2026

File Purpose: Authentication service for the project.
"""

# Standard library imports.
from dataclasses import dataclass
from enum import Enum

# Third-party imports.
from flask import current_app

# Local application imports.
from app.extensions import db
from app.models import RecoveryCodes, Users


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
    user: Users | None = None


@dataclass(slots=True)
class AuthOperationResult:
    """Generic auth mutation outcome plus the affected user, if any."""

    statuses: tuple[AuthResultStatus, ...]
    user: Users | None = None


@dataclass(slots=True)
class AccountViewData:
    """Precomputed account view values."""

    num_codes: int
    start_semester: str | None
    grad_semester: str | None


def authenticate_user(username: str, password: str, remote_addr: str | None) -> AuthLoginResult:
    """Validate login credentials and return the matching outcome."""
    user = Users.query.filter_by(username=username).first()
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

    if user.mfa_active and not statuses:
        return AuthLoginResult(
            statuses=(
                AuthResultStatus.REQUIRE_TOTP_MFA
                if user.totp_active
                else AuthResultStatus.REQUIRE_RECOVERY_MFA
            ,),
            user=user,
        )

    if not statuses:
        current_app.logger.info(
            "Login attempt as %s from IP %s - success",
            username,
            remote_addr,
        )
        statuses.append(AuthResultStatus.SUCCESS)

    return AuthLoginResult(statuses=tuple(statuses), user=user)


def register_user(username: str, password: str, remote_addr: str | None) -> AuthOperationResult:
    """Create a user account if the username is available."""
    if Users.query.filter_by(username=username).first() is not None:
        return AuthOperationResult(statuses=(AuthResultStatus.DUPLICATE_USERNAME,))

    current_app.logger.warning("New user %s from IP %s", username, remote_addr)
    new_user = Users()
    new_user.username = username
    new_user.role = "user"
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return AuthOperationResult(statuses=(AuthResultStatus.SUCCESS,), user=new_user)


def get_account_view_data(user_id: int) -> AccountViewData:
    """Return the account values needed to render the profile page."""
    user = db.session.get(Users, user_id)
    num_codes = RecoveryCodes.query.filter_by(user_id=user_id).count()
    return AccountViewData(
        num_codes=num_codes,
        start_semester=user.joined if user is not None else None,
        grad_semester=user.graduated if user is not None else None,
    )


def update_account(
    user_id: int,
    start_semester: str | None,
    grad_semester: str | None,
    password: str | None,
    username: str,
    remote_addr: str | None,
) -> AuthOperationResult:
    """Update the stored account data for a user."""
    update_user = db.session.get(Users, user_id)
    if update_user is None:
        current_app.logger.error(
            "Account update attempt - failure: %s from IP %s - user not found",
            username,
            remote_addr,
        )
        return AuthOperationResult(statuses=(AuthResultStatus.USER_NOT_FOUND,))

    current_app.logger.info(
        (
            "Account update attempt - success: %s from IP %s - "
            "start semester %s, end semester %s"
        ),
        username,
        remote_addr,
        start_semester,
        grad_semester,
    )

    if password:
        update_user.set_password(password)

    update_user.joined = start_semester
    update_user.graduated = grad_semester
    db.session.commit()
    return AuthOperationResult(statuses=(AuthResultStatus.SUCCESS,), user=update_user)
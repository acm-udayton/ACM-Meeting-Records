#!/usr/bin/env python
# app/services/mfa_service.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 7/27/2026

File Purpose: MFA service for the project.
"""

import base64
from dataclasses import dataclass
from enum import Enum
from io import BytesIO

import pyotp
import qrcode

# Local application imports.
from app.extensions import db
from app.models import RecoveryCodes, Users


class MfaResultStatus(str, Enum):
    """Granular outcomes for MFA operations."""

    SUCCESS = "success"
    USER_NOT_FOUND = "user_not_found"
    INVALID_TOTP = "invalid_totp"
    INVALID_RECOVERY_CODE = "invalid_recovery_code"
    MFA_NOT_ENABLED = "mfa_not_enabled"
    TOTP_ALREADY_ENABLED = "totp_already_enabled"


@dataclass(slots=True)
class MfaLoginResult:
    """MFA login outcome plus the matched user, if any."""

    statuses: tuple[MfaResultStatus, ...]
    user: Users | None = None

    @property
    def is_success(self) -> bool:
        return MfaResultStatus.SUCCESS in self.statuses


@dataclass(slots=True)
class MfaOperationResult:
    """Generic MFA mutation outcome plus the affected user, if any."""

    statuses: tuple[MfaResultStatus, ...]
    user: Users | None = None

    @property
    def is_success(self) -> bool:
        return MfaResultStatus.SUCCESS in self.statuses


# ==========================================
# Helper Utilities
# ==========================================

def generate_qr_code(data: str) -> str:
    """Generate a base64-encoded PNG QR code image string."""
    img = qrcode.make(data)
    stream = BytesIO()
    img.save(stream, format="PNG")
    return base64.b64encode(stream.getvalue()).decode("utf-8")


def user_has_recovery_codes(user: Users) -> bool:
    """Check if the user has active recovery codes remaining."""
    return RecoveryCodes.query.filter(RecoveryCodes.user_id == user.id).count() > 0


# ==========================================
# Authentication & Login Verification
# ==========================================

def verify_mfa_totp_code(user: Users | None, token: str) -> MfaLoginResult:
    """Verify a TOTP token during the login flow."""
    if not user:
        return MfaLoginResult(statuses=(MfaResultStatus.USER_NOT_FOUND,))

    if not user.totp_active or not user.totp_secret:
        return MfaLoginResult(
            statuses=(MfaResultStatus.MFA_NOT_ENABLED,), user=user
        )

    totp = pyotp.TOTP(user.totp_secret)
    if totp.verify(token, valid_window=1):  # Allow for slight time drift
        return MfaLoginResult(statuses=(MfaResultStatus.SUCCESS,), user=user)

    return MfaLoginResult(statuses=(MfaResultStatus.INVALID_TOTP,), user=user)


def verify_mfa_recovery_code(user: Users | None, code: str) -> MfaLoginResult:
    """Verify and consume a recovery code during the login flow."""
    if not user:
        return MfaLoginResult(statuses=(MfaResultStatus.USER_NOT_FOUND,))

    recovery_codes = RecoveryCodes.query.filter(
        RecoveryCodes.user_id == user.id
    ).all()

    for entry in recovery_codes:
        if entry.check_code(code):
            db.session.delete(entry)
            db.session.commit()
            return MfaLoginResult(
                statuses=(MfaResultStatus.SUCCESS,), user=user
            )

    return MfaLoginResult(
        statuses=(MfaResultStatus.INVALID_RECOVERY_CODE,), user=user
    )


# ==========================================
# Setup & Management Actions
# ==========================================

def prepare_totp_setup(user: Users) -> tuple[MfaOperationResult, str | None, str | None]:
    """Generate temporary TOTP secret & URI for setup. Returns (Result, URI, QR_Base64)."""
    if user.totp_active:
        return (
            MfaOperationResult(
                statuses=(MfaResultStatus.TOTP_ALREADY_ENABLED,), user=user
            ),
            None,
            None,
        )

    user.generate_totp_secret()
    db.session.commit()

    uri = user.get_totp_uri()
    qr_code_b64 = generate_qr_code(uri)

    return (
        MfaOperationResult(statuses=(MfaResultStatus.SUCCESS,), user=user),
        uri,
        qr_code_b64,
    )


def verify_and_enable_totp(user: Users, token: str) -> MfaOperationResult:
    """Verify TOTP token during setup and activate TOTP for the user."""
    if not user.totp_secret:
        return MfaOperationResult(
            statuses=(MfaResultStatus.MFA_NOT_ENABLED,), user=user
        )

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(token):
        return MfaOperationResult(
            statuses=(MfaResultStatus.INVALID_TOTP,), user=user
        )

    user.mfa_active = True
    user.totp_active = True
    db.session.commit()

    return MfaOperationResult(statuses=(MfaResultStatus.SUCCESS,), user=user)


def reset_recovery_codes_for_user(
    user: Users, count: int = 10
) -> tuple[MfaOperationResult, list[str]]:
    """Delete old recovery codes, enable MFA, and generate new recovery codes."""
    # Clear old codes
    RecoveryCodes.query.filter(RecoveryCodes.user_id == user.id).delete()

    # Ensure MFA is active
    user.mfa_active = True

    new_code_strings: list[str] = []
    for _ in range(count):
        new_code = RecoveryCodes(user_id=user.id)
        code_value = new_code.generate_code()
        db.session.add(new_code)
        new_code_strings.append(code_value)

    db.session.commit()

    return (
        MfaOperationResult(statuses=(MfaResultStatus.SUCCESS,), user=user),
        new_code_strings,
    )


def disable_totp_for_user(user: Users) -> MfaOperationResult:
    """Disable TOTP MFA specifically and regenerate secret."""
    user.totp_active = False
    user.generate_totp_secret()
    db.session.commit()

    return MfaOperationResult(statuses=(MfaResultStatus.SUCCESS,), user=user)


def disable_mfa_for_user(user: Users) -> MfaOperationResult:
    """Disable all MFA methods and delete all recovery codes."""
    user.mfa_active = False
    user.totp_active = False
    user.totp_secret = None
    RecoveryCodes.query.filter(RecoveryCodes.user_id == user.id).delete()
    db.session.commit()

    return MfaOperationResult(statuses=(MfaResultStatus.SUCCESS,), user=user)
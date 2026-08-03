#!/usr/bin/env python
# tests/blueprints/test_mfa.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 6/6/2026

File Purpose: Pytest for the blueprints/mfa endpoints.
"""

import io
import os
import re
from datetime import datetime, timedelta

from flask import current_app, get_flashed_messages
import pyotp

from app.models import Attachments, Attendees, Meetings, Minutes, RecoveryCodes, Users
from tests.conftest import app as flask_app, db  # Import the app fixture for context in tests.


def get_csrf_token(response):
    """Extract a Flask-WTF CSRF token from a rendered form."""
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert match is not None
    return match.group(1).decode()


def test_mfa_reset_recovery_codes(flask_app):
    """Test recovery-code replacement requires POST and a valid CSRF token."""
    with flask_app.app_context():
        user = Users(username="testuser", role="user", activated=True)
        user.set_password("password")
        old_code = RecoveryCodes(user_id=1)
        old_code.generate_code()
        db.session.add(user)
        db.session.commit()
        old_code.user_id = user.id
        db.session.add(old_code)
        db.session.commit()

        test_client = flask_app.test_client()
        unauthenticated_response = test_client.post("/mfa/reset-recovery-codes/")
        assert unauthenticated_response.status_code == 401

        login_response = test_client.post(
            "/login/",
            data={"username": "testuser", "password": "password"},
            follow_redirects=True
        )
        assert login_response.status_code == 200
        flask_app.config["WTF_CSRF_ENABLED"] = True

        account_response = test_client.get("/my-account/")
        csrf_token = get_csrf_token(account_response)
        assert b"method=\"POST\"" in account_response.data
        original_hashes = {
            code.code_hash
            for code in RecoveryCodes.query.filter_by(user_id=user.id).all()
        }

        get_response = test_client.get("/mfa/reset-recovery-codes/")
        assert get_response.status_code == 405

        missing_token_response = test_client.post("/mfa/reset-recovery-codes/")
        assert missing_token_response.status_code == 400
        invalid_token_response = test_client.post(
            "/mfa/reset-recovery-codes/",
            data={"csrf_token": "invalid"}
        )
        assert invalid_token_response.status_code == 400
        unchanged_hashes = {
            code.code_hash
            for code in RecoveryCodes.query.filter_by(user_id=user.id).all()
        }
        assert unchanged_hashes == original_hashes

        response = test_client.post(
            "/mfa/reset-recovery-codes/",
            data={"csrf_token": csrf_token}
        )
        assert response.status_code == 200
        assert b"Store these codes securely." in response.data

        codes = RecoveryCodes.query.filter_by(user_id=user.id).all()
        assert len(codes) == 10
        first_hashes = {code.code_hash for code in codes}
        assert first_hashes.isdisjoint(original_hashes)

        second_response = test_client.post(
            "/mfa/reset-recovery-codes/",
            data={"csrf_token": csrf_token}
        )
        assert second_response.status_code == 200
        codes_after = RecoveryCodes.query.filter_by(user_id=user.id).all()
        assert len(codes_after) == 10
        assert {code.code_hash for code in codes_after}.isdisjoint(first_hashes)

def test_verify_recovery_code_success(flask_app):
    """Test verifying a valid recovery code logs the user in and deletes the code."""
    with flask_app.app_context():
        user = Users(username="testuser", role="user", activated=True)
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

        code = RecoveryCodes(user_id=user.id)
        code_value = code.generate_code()
        db.session.add(code)
        db.session.commit()

        test_client = flask_app.test_client()

        # Simulate the MFA login flow by setting the user ID in the session.
        with test_client.session_transaction() as session:
            session['mfa_user_id'] = user.id

        # Test verifying a valid recovery code.
        verify_response = test_client.post("/mfa/verify-recovery-code/", data={"token": code_value}, follow_redirects=True)
        assert verify_response.status_code == 200
        assert verify_response.request.path == "/"  # Should redirect to home on successful login.

        # Test that the used code is deleted from the database.
        with flask_app.app_context():
            used_code = RecoveryCodes.query.filter_by(id=code.id).first()
            assert used_code is None  # Code should be deleted after use.

def test_verify_recovery_code_invalid(flask_app):
    """Test verifying an incorrect recovery code triggers the proper flash message."""
    with flask_app.app_context():
        user = Users(username="testuser_invalid", role="user", activated=True)
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

        test_client = flask_app.test_client()

        # Simulate the MFA login flow by setting the user ID in the session.
        with test_client.session_transaction() as session:
            session['mfa_user_id'] = user.id

        with test_client:
            invalid_verify_response = test_client.post("/mfa/verify-recovery-code/", data={"token": "invalidcode"}, follow_redirects=True)
            assert invalid_verify_response.status_code == 200
            assert get_flashed_messages() == ["Invalid recovery code."]

def test_verify_recovery_code_unauthenticated(flask_app):
    """Test trying to verify a recovery code without an active MFA session context."""
    with flask_app.app_context():
        user = Users(username="testuser_anon", role="user", activated=True)
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

        code = RecoveryCodes(user_id=user.id)
        code_value = code.generate_code()
        db.session.add(code)
        db.session.commit()

        # Completely clean client context: no cookies, no user sessions initialized.
        test_client = flask_app.test_client()

        with test_client:
            invalid_session_response = test_client.post("/mfa/verify-recovery-code/", data={"token": code_value}, follow_redirects=True)
            assert invalid_session_response.status_code == 200
            assert get_flashed_messages() == ['You must log in before using a recovery code.']

def test_verify_totp_success(flask_app):
    """Test valid TOTP token successfully logs user in."""
    with flask_app.app_context():
        # Setup user with active TOTP.
        user = Users(username="totpuser", role="user", activated=True, totp_active=True)
        user.set_password("password")
        # Generate a standard secret to create valid tokens.
        user.totp_secret = pyotp.random_base32()
        db.session.add(user)
        db.session.commit()

        test_client = flask_app.test_client()

        # Simulate the pre-auth stage.
        with test_client.session_transaction() as sess:
            sess['mfa_user_id'] = user.id

        # Generate a fresh valid token.
        totp = pyotp.TOTP(user.totp_secret)
        valid_token = totp.now()

        # Post valid token.
        response = test_client.post("/mfa/verify-totp/", data={"token": valid_token}, follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == "/"  # Successfully logs in and hits home.

def test_verify_totp_invalid(flask_app):
    """Test that an incorrect TOTP token flashes the correct danger message."""
    with flask_app.app_context():
        user = Users(username="totpuser2", role="user", activated=True, totp_active=True)
        user.set_password("password")
        user.totp_secret = pyotp.random_base32()
        db.session.add(user)
        db.session.commit()

        test_client = flask_app.test_client()

        with test_client.session_transaction() as sess:
            sess['mfa_user_id'] = user.id

        # Freeze context with follow_redirects=False to verify message assertions directly.
        with test_client:
            response = test_client.post("/mfa/verify-totp/", data={"token": "000000"}, follow_redirects=False)
            assert response.status_code == 200  # Form validation failure renders template (200), no redirect.
            assert get_flashed_messages() == ["Invalid TOTP MFA code."]

def test_verify_totp_not_active_or_user_missing(flask_app):
    """Test message flash when user hits endpoint but doesn't have TOTP active."""
    with flask_app.app_context():
        # Setup user with TOTP deactivated.
        user = Users(username="totpuser3", role="user", activated=True, totp_active=False)
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

        test_client = flask_app.test_client()

        with test_client.session_transaction() as sess:
            sess['mfa_user_id'] = user.id

        with test_client:
            response = test_client.post("/mfa/verify-totp/", data={"token": "123456"}, follow_redirects=False)
            assert response.status_code == 302  # Redirects to auth.login.
            assert get_flashed_messages() == ["TOTP MFA not required or user not found."]

def test_verify_totp_unauthenticated(flask_app):
    """Test that visiting the endpoint without a session variable triggers a warning flash."""
    with flask_app.app_context():
        # Clean client: completely empty session context.
        test_client = flask_app.test_client()

        with test_client:
            response = test_client.post("/mfa/verify-totp/", data={"token": "123456"}, follow_redirects=False)
            assert response.status_code == 302  # Redirects back to auth.login.
            assert get_flashed_messages() == ["You must log in before using TOTP MFA."]

def test_setup_totp_already_active(flask_app):
    """Test that a user with an already active TOTP is redirected and flashed an info message."""
    with flask_app.app_context():
        user = Users(username="activeuser", role="user", activated=True, totp_active=True)
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

        test_client = flask_app.test_client()

        # Log the user in via session transaction (or use Flask-Login's login_user).
        with test_client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)  # Standard Flask-Login key.

        with test_client:
            response = test_client.post("/mfa/setup-totp/", follow_redirects=False)
            assert response.status_code == 302
            assert get_flashed_messages() == ["MFA with TOTP is already enabled. Disable it first please!"]

def test_setup_totp_success(flask_app):
    """Test TOTP setup requires valid CSRF and keeps its secret pending."""
    with flask_app.app_context():
        user = Users(username="newuser", role="user", activated=True, totp_active=False)
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

        test_client = flask_app.test_client()

        with test_client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)

        flask_app.config["WTF_CSRF_ENABLED"] = True
        account_response = test_client.get("/my-account/")
        csrf_token = get_csrf_token(account_response)

        get_response = test_client.get("/mfa/setup-totp/")
        assert get_response.status_code == 405
        missing_token_response = test_client.post("/mfa/setup-totp/")
        assert missing_token_response.status_code == 400
        invalid_token_response = test_client.post(
            "/mfa/setup-totp/",
            data={"csrf_token": "invalid"}
        )
        assert invalid_token_response.status_code == 400

        db.session.refresh(user)
        assert user.totp_secret is None
        with test_client.session_transaction() as sess:
            assert sess.get('mfa_setup_secret') is None

        response = test_client.post(
            "/mfa/setup-totp/",
            data={"csrf_token": csrf_token},
            follow_redirects=False
        )
        assert response.status_code == 200
        assert b"TOTP Setup QR Code" in response.data

        db.session.refresh(user)
        assert user.totp_secret is None

        with test_client.session_transaction() as sess:
            assert sess.get('mfa_setup_secret') is not None

def test_setup_totp_unauthenticated(flask_app):
    """Test that an unauthenticated user cannot access the setup route."""
    with flask_app.app_context():
        # Completely fresh, empty client context.
        test_client = flask_app.test_client()

        get_response = test_client.get("/mfa/setup-totp/", follow_redirects=False)
        assert get_response.status_code == 405
        post_response = test_client.post("/mfa/setup-totp/", follow_redirects=False)
        assert post_response.status_code == 401

def test_verify_totp_setup_success_redirect_recovery(flask_app):
    """Test valid TOTP setup safely persists the secret and creates recovery codes."""
    with flask_app.app_context():
        user = Users(username="setupuser1", role="user", activated=True, totp_active=False)
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
        pending_secret = pyotp.random_base32()

        test_client = flask_app.test_client()

        with test_client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['mfa_setup_secret'] = pending_secret

        totp = pyotp.TOTP(pending_secret)
        valid_token = totp.now()

        response = test_client.post("/mfa/verify-totp-setup/", data={"token": valid_token}, follow_redirects=False)

        assert response.status_code == 200
        assert b"Store these codes securely." in response.data

        db.session.refresh(user)
        assert user.mfa_active is True
        assert user.totp_active is True
        assert user.totp_secret == pending_secret
        assert RecoveryCodes.query.filter_by(user_id=user.id).count() == 10

def test_verify_totp_setup_success_redirect_account(flask_app):
    """Test valid token redirects straight to account if recovery codes already exist."""
    with flask_app.app_context():
        user = Users(username="setupuser2", role="user", activated=True, totp_active=False)
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
        pending_secret = pyotp.random_base32()

        # Mock an existing recovery code
        dummy_code = RecoveryCodes(user_id=user.id, code_hash="dummy_hash")
        db.session.add(dummy_code)
        db.session.commit()

        test_client = flask_app.test_client()

        with test_client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['mfa_setup_secret'] = pending_secret

        totp = pyotp.TOTP(pending_secret)
        valid_token = totp.now()

        response = test_client.post("/mfa/verify-totp-setup/", data={"token": valid_token}, follow_redirects=False)

        # Should bypass recovery codes setup and head directly to account view.
        assert response.status_code == 302
        db.session.refresh(user)
        assert user.totp_secret == pending_secret

def test_verify_totp_setup_session_expired(flask_app):
    """Test verification fails gracefully if the setup secret session key is missing."""
    with flask_app.app_context():
        user = Users(username="setupuser3", role="user", activated=True, totp_active=False)
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

        test_client = flask_app.test_client()

        with test_client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            # Intentionally leaving out 'mfa_setup_secret'.

        with test_client:
            response = test_client.post("/mfa/verify-totp-setup/", data={"token": "123456"}, follow_redirects=False)
            assert response.status_code == 302
            assert get_flashed_messages() == ['TOTP MFA setup session expired. Start over.']

def test_verify_totp_setup_invalid_code(flask_app):
    """Test an incorrect token leaves the pending secret uncommitted."""
    with flask_app.app_context():
        user = Users(username="setupuser4", role="user", activated=True, totp_active=False)
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
        pending_secret = pyotp.random_base32()

        test_client = flask_app.test_client()

        with test_client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['mfa_setup_secret'] = pending_secret

        with test_client:
            response = test_client.post("/mfa/verify-totp-setup/", data={"token": "000000"}, follow_redirects=False)
            assert response.status_code == 200
            assert get_flashed_messages() == ['Invalid code. Please try scanning and verifying again.']

        db.session.refresh(user)
        assert user.totp_active is False
        assert user.totp_secret is None
        with test_client.session_transaction() as sess:
            assert sess['mfa_setup_secret'] == pending_secret

def test_verify_totp_setup_invalid_form(flask_app):
    """Test submission handling when form validation completely fails (empty token payload)."""
    with flask_app.app_context():
        user = Users(username="setupuser5", role="user", activated=True, totp_active=False)
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
        pending_secret = pyotp.random_base32()

        test_client = flask_app.test_client()

        with test_client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['mfa_setup_secret'] = pending_secret

        with test_client:
            # Submitting completely blank form fields.
            response = test_client.post("/mfa/verify-totp-setup/", data={}, follow_redirects=False)
            assert response.status_code == 200
            assert get_flashed_messages() == ['Invalid TOTP MFA setup form data.']

def test_disable_totp_success(flask_app):
    """Test disabling TOTP requires POST and a valid CSRF token."""
    with flask_app.app_context():
        user = Users(
            username="disableuser",
            role="user",
            activated=True,
            mfa_active=True,
            totp_active=True
        )
        user.set_password("password")
        user.totp_secret = pyotp.random_base32()
        db.session.add(user)
        db.session.commit()

        test_client = flask_app.test_client()

        with test_client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)

        flask_app.config["WTF_CSRF_ENABLED"] = True
        account_response = test_client.get("/my-account/")
        csrf_token = get_csrf_token(account_response)
        assert b"Are you sure you want to disable TOTP authentication?" in account_response.data
        original_secret = user.totp_secret

        get_response = test_client.get("/mfa/disable-totp/")
        assert get_response.status_code == 405
        missing_token_response = test_client.post("/mfa/disable-totp/")
        assert missing_token_response.status_code == 400
        invalid_token_response = test_client.post(
            "/mfa/disable-totp/",
            data={"csrf_token": "invalid"}
        )
        assert invalid_token_response.status_code == 400
        db.session.refresh(user)
        assert user.totp_active is True
        assert user.totp_secret == original_secret

        with test_client:
            response = test_client.post(
                "/mfa/disable-totp/",
                data={"csrf_token": csrf_token},
                follow_redirects=True
            )
            assert response.status_code == 200
            assert "Two-Factor TOTP Authentication has been disabled." in get_flashed_messages()

        db.session.refresh(user)
        assert not user.totp_active
        assert user.totp_secret is None

def test_disable_totp_unauthenticated(flask_app):
    """Test that an unauthenticated user cannot access the disable route."""
    with flask_app.app_context():
        # Completely fresh, empty client context.
        test_client = flask_app.test_client()

        get_response = test_client.get("/mfa/disable-totp/", follow_redirects=False)
        assert get_response.status_code == 405
        post_response = test_client.post("/mfa/disable-totp/", follow_redirects=False)
        assert post_response.status_code == 401

def test_disable_mfa_success(flask_app):
    """Test disabling all MFA requires POST and a valid CSRF token."""
    with flask_app.app_context():
        user = Users(username="disablemfauser", role="user", activated=True, mfa_active=True, totp_active=True)
        user.set_password("password")
        user.totp_secret = pyotp.random_base32()
        db.session.add(user)
        db.session.commit()

        # Add some recovery codes for the user.
        for _ in range(5):
            code = RecoveryCodes(user_id=user.id)
            code.generate_code()
            db.session.add(code)
        db.session.commit()

        test_client = flask_app.test_client()

        with test_client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)

        flask_app.config["WTF_CSRF_ENABLED"] = True
        account_response = test_client.get("/my-account/")
        csrf_token = get_csrf_token(account_response)
        assert b"Are you sure you want to disable all multi-factor authentication?" in account_response.data
        original_secret = user.totp_secret
        original_code_hashes = {
            code.code_hash
            for code in RecoveryCodes.query.filter_by(user_id=user.id).all()
        }

        get_response = test_client.get("/mfa/disable-mfa/")
        assert get_response.status_code == 405
        missing_token_response = test_client.post("/mfa/disable-mfa/")
        assert missing_token_response.status_code == 400
        invalid_token_response = test_client.post(
            "/mfa/disable-mfa/",
            data={"csrf_token": "invalid"}
        )
        assert invalid_token_response.status_code == 400
        db.session.refresh(user)
        assert user.mfa_active is True
        assert user.totp_active is True
        assert user.totp_secret == original_secret
        assert {
            code.code_hash
            for code in RecoveryCodes.query.filter_by(user_id=user.id).all()
        } == original_code_hashes

        with test_client:
            response = test_client.post(
                "/mfa/disable-mfa/",
                data={"csrf_token": csrf_token},
                follow_redirects=True
            )
            assert response.status_code == 200
            assert "Multi-Factor Authentication has been disabled." in get_flashed_messages()

        db.session.refresh(user)
        assert not user.mfa_active
        assert not user.totp_active
        assert user.totp_secret is None
        assert RecoveryCodes.query.filter_by(user_id=user.id).count() == 0

def test_disable_mfa_unauthenticated(flask_app):
    """Test that an unauthenticated user cannot access the disable MFA route."""
    with flask_app.app_context():
        # Completely fresh, empty client context.
        test_client = flask_app.test_client()

        get_response = test_client.get("/mfa/disable-mfa/", follow_redirects=False)
        assert get_response.status_code == 405
        post_response = test_client.post("/mfa/disable-mfa/", follow_redirects=False)
        assert post_response.status_code == 401

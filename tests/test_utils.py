#!/usr/bin/env python
# tests/test_utils.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 6/5/2026

File Purpose: Pytest for utility functions.
"""

import pytest

from flask_login import login_user, logout_user
from tests.conftest import app as flask_app  # Import the app fixture for context in tests.

from app.extensions import db

from app.utils import filter_by_role, sha_hash, generate_meeting_code, is_admin, is_not_admin
from app.models import Meetings, Users

def test_sha_hash(flask_app):
    """ Test the sha_hash function. """
    with flask_app.app_context():
        input_string = "test123"
        # Hashing should be consistent.
        assert sha_hash(input_string) == sha_hash(input_string)
        # Different inputs should produce different hashes.
        assert sha_hash(input_string) != sha_hash("different")
        # SHA-512 produces a 128-character hex string.
        assert len(sha_hash(input_string)) == 128

def test_generate_meeting_code(flask_app):
    """ Test the generate_meeting_code function. """
    with flask_app.app_context():
        code1 = generate_meeting_code()
        code2 = generate_meeting_code()
        # Length should be 8 by default.
        assert len(code1) == 8
        assert len(code2) == 8
        # Should produce different codes on each call (statistically unlikely to repeat).
        assert code1 != code2
from flask_login import AnonymousUserMixin, login_user, logout_user


def test_is_admin(flask_app):
    """ Test the is_admin function against all user states. """
    with flask_app.test_request_context():
        admin_user = Users(username="admin", role="admin")
        non_admin_user = Users(username="user", role="member")
        anon_user = AnonymousUserMixin()

        # Logged-in Admin
        login_user(admin_user)
        assert is_admin(admin_user) is True

        # Logged-in Non-Admin
        login_user(non_admin_user)
        assert is_admin(non_admin_user) is False

        # Logged-out
        logout_user()
        assert is_admin(anon_user) is False

        # None
        assert is_admin(None) is False


def test_is_not_admin(flask_app):
    """ Test the is_not_admin function against all user states. """
    with flask_app.test_request_context():
        admin_user = Users(username="admin", role="admin")
        non_admin_user = Users(username="user", role="member")
        anon_user = AnonymousUserMixin()

        # Logged-in Admin
        login_user(admin_user)
        assert is_not_admin(admin_user) is False

        # Logged-in Non-Admin
        login_user(non_admin_user)
        assert is_not_admin(non_admin_user) is True

        # Logged-out
        logout_user()
        assert is_not_admin(anon_user) is True

        # None
        assert is_not_admin(None) is True
        
def test_filter_by_role(flask_app):
    """ Test the filter_by_role function. """
    with flask_app.app_context():
        admin_user = Users(username="admin", role="admin")
        non_admin_user = Users(username="user", role="member")

        meetings = [
            Meetings(title="General Meeting", admin_only=False, state="active", host="admin", description="A general meeting."),
            Meetings(title="Another Admin Meeting", admin_only=True, state="active", host="admin", description="An admin-only meeting."),
        ]
        db.session.add_all(meetings)
        db.session.commit()

    with flask_app.test_request_context():
        # Test with an admin user.
        login_user(admin_user)
        filtered_meetings = filter_by_role(Meetings.query, admin_user).all()
        assert len(filtered_meetings) == 2  # Admin sees all meetings.
        logout_user()

        # Test with a non-admin user.
        filtered_meetings = filter_by_role(Meetings.query, non_admin_user).all()
        assert len(filtered_meetings) == 1  # Non-admin sees only non-admin meetings.

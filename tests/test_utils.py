#!/usr/bin/env python
# tests/test_utils.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 6/5/2026

File Purpose: Pytest for utility functions.
"""

import pytest

from app import create_app
from app.utils import sha_hash, generate_meeting_code, get_env_bool
from tests.conftest import app as flask_app  # Import the app fixture for context in tests.

def test_get_env_bool(monkeypatch):
    """ Test the get_env_bool function. """
    monkeypatch.setenv("TEST_BOOLEAN", "True")
    assert get_env_bool("TEST_BOOLEAN") is True

    monkeypatch.setenv("TEST_BOOLEAN", "False")
    assert get_env_bool("TEST_BOOLEAN") is False

def test_get_env_bool_returns_false_when_missing(monkeypatch):
    """ Missing environment variables should default to false. """
    monkeypatch.delenv("TEST_BOOLEAN", raising=False)
    assert get_env_bool("TEST_BOOLEAN") is False

def test_get_env_bool_rejects_invalid_value(monkeypatch):
    """ Test an invalid boolean environment variable. """
    monkeypatch.setenv("TEST_BOOLEAN", "Flase")
    with pytest.raises(ValueError):
        get_env_bool("TEST_BOOLEAN")

def test_create_app_parses_username_environment_flags(monkeypatch):
    """ The application factory should convert environment flags at startup. """
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    monkeypatch.setenv("ENFORCE_USERNAMES", "False")
    monkeypatch.setenv("REQUIRE_USERNAME_AS_EMAIL", "True")
    monkeypatch.setenv("USERNAME_EMAIL_DOMAIN", "example.com")

    flask_app = create_app()

    assert flask_app.config["ENFORCE_USERNAMES"] is False
    assert flask_app.config["REQUIRE_USERNAME_AS_EMAIL"] is True

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

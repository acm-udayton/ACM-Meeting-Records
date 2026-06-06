#!/usr/bin/env python
# tests/test_utils.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 6/5/2026

File Purpose: Pytest for utility functions.
"""

import pytest

from app.utils import sha_hash, generate_meeting_code
from tests.conftest import app as flask_app  # Import the app fixture for context in tests.

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

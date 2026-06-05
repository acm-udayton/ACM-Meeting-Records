#!/usr/bin/env python
# tests/test_forms.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 6/4/2026

File Purpose: Pytest for form validation with Flask-WTF.
"""

import pytest
from werkzeug.datastructures import MultiDict

from app.forms import CreateMeetingForm, SignUpFormEmail, AccountUpdateForm
from tests.conftest import app as flask_app  # Import the app fixture for context in tests

def test_meeting_form_valid(flask_app):
    """Test valid data for CreateMeetingForm."""
    with flask_app.app_context():
        form_data = MultiDict([
            ('title', 'General Meeting'),
            ('description', 'Monthly meeting')
        ])
        
        # Pass the MultiDict to 'formdata' (not 'data')
        form = CreateMeetingForm(formdata=form_data)
        
        # Now validate
        assert form.validate() is True

def test_meeting_form_invalid_length(flask_app):
    """Test title length constraints."""
    with flask_app.app_context():
        form_data = MultiDict([
            ('title', ''),
            ('description', 'Too short title')
        ])
        form = CreateMeetingForm(formdata=form_data)
        assert form.validate() is False
        assert 'This field is required.' in form.title.errors

def test_signup_email_validator(flask_app):
    """
    Test the custom email domain validator.
    We need the 'app' fixture to provide the context for current_app.
    """
    with flask_app.app_context():
        # Mocking the context config your validator looks for
        flask_app.context = {
            "usernames": {
                "enforce_usernames": "True",
                "username_email_domain": "udayton.edu"
            }
        }

        form_data = MultiDict([
            ('username', 'user@gmail.com'),
            ('password', 'password123'),
            ('confirm_password', 'password123')
        ])

        # Test wrong domain
        form = SignUpFormEmail(formdata=form_data)
        form.username.validate(form)
        assert 'Email must be from the domain udayton.edu' in form.username.errors

        # Test correct domain
        form_data_correct = MultiDict([
            ('username', 'user@udayton.edu'),
            ('password', 'password123'),
            ('confirm_password', 'password123')
        ])
        form = SignUpFormEmail(formdata=form_data_correct)
        form.username.validate(form)
        assert len(form.username.errors) == 0

@pytest.mark.parametrize("semester, is_valid", [
    ("FA 2026", True),
    ("SP 2025", True),
    ("", True),
    ("SU 2026", False),
    ("Fall 2026", False),
])
def test_semester_validator(flask_app, semester, is_valid):
    """Test the semester regex validator with various inputs."""
    with flask_app.app_context():
        form_data = MultiDict([
            ('start_semester', semester)
        ])
        form = AccountUpdateForm(formdata=form_data)
        form.start_semester.validate(form)

        if is_valid:
            assert len(form.start_semester.errors) == 0
        else:
            assert len(form.start_semester.errors) > 0

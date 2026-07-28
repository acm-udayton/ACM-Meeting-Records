#!/usr/bin/env python
# tests/test_forms.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 6/4/2026

File Purpose: Pytest for form validation with Flask-WTF.
"""

from datetime import datetime, timedelta

import pytest
from werkzeug.datastructures import MultiDict

from app.forms import (
    AccountUpdateForm,
    CreateMeetingForm,
    MeetingTimesForm,
    SignUpFormEmail,
    SignUpFormUsername
)
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

def test_meeting_times_form(flask_app):
    """Test meeting time validation and support for clearing both fields."""
    with flask_app.app_context():
        invalid_form_data = MultiDict([
            ('event_start', '2026-07-26T18:00'),
            ('event_end', '2026-07-26T17:59')
        ])
        invalid_form = MeetingTimesForm(formdata=invalid_form_data)

        empty_form_data = MultiDict([
            ('event_start', ''),
            ('event_end', '')
        ])
        empty_form = MeetingTimesForm(formdata=empty_form_data)

        future_form_data = MultiDict([
            ('event_start', (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')),
            ('event_end', '')
        ])
        future_form = MeetingTimesForm(formdata=future_form_data)

        future_end_form_data = MultiDict([
            ('event_start', (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')),
            ('event_end', (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'))
        ])
        future_end_form = MeetingTimesForm(formdata=future_end_form_data)

        assert invalid_form.validate() is False
        assert 'End time cannot be earlier than the start time.' in invalid_form.event_end.errors
        assert empty_form.validate() is True
        assert future_form.validate() is False
        assert 'Start time cannot be in the future.' in future_form.event_start.errors
        assert future_end_form.validate() is False
        assert 'End time cannot be in the future.' in future_end_form.event_end.errors

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

def test_signup_username_passwords_must_match(flask_app):
    """Test the shared password confirmation validator on the username form."""
    with flask_app.app_context():
        form_data = MultiDict([
            ('username', 'testuser'),
            ('password', 'password123'),
            ('confirm_password', 'different')
        ])

        form = SignUpFormUsername(formdata=form_data)
        assert form.validate() is False
        assert 'Passwords must match.' in form.confirm_password.errors

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

#!/usr/bin/env python
# tests/test_models.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 6/5/2026

File Purpose: Pytest for model functions.
"""

import time

import pyotp
import pytest

from app.models import Users, RecoveryCodes, Meetings, Attendees, Minutes, Attachments, Poll, PollQuestion, PollFreeResponse, PollOption, PollVoter
from tests.conftest import app as flask_app  # Import the app fixture for context in tests.

def test_user_set_password_not_store_password_in_plaintext(flask_app):
    """ Test the Users model. """
    with flask_app.app_context():
        user = Users(id=1, username="testuser", role="member")
        user.set_password("password")
        # The password should not be stored in plaintext.
        assert user.password != "password"

def test_user_check_password(flask_app):
    """ Test the Users model. """
    with flask_app.app_context():
        user = Users(id=1, username="testuser", role="member")
        user.set_password("password")
        # check_password should return True for the correct password.
        assert user.check_password("password")
        # check_password should return False for an incorrect password.
        assert user.check_password("wrongpassword") is False

def test_user_totp_secret_generation(flask_app):
    """ Test the Users model. """
    with flask_app.app_context():
        user = Users(id=1, username="testuser", role="member")
        user.generate_totp_secret()
        # The TOTP secret should be a 32-character base32 string.
        assert len(user.totp_secret) == 32
        # The TOTP secret should only contain valid base32 characters.
        valid_base32_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
        assert all(c in valid_base32_chars for c in user.totp_secret)

def test_user_get_totp_uri(flask_app):
    """ Test the Users model. """
    with flask_app.app_context():
        user = Users(id=1, username="testuser", role="member")
        user.generate_totp_secret()
        totp_uri = user.get_totp_uri()
        # The TOTP URI should contain the username and issuer name.
        assert "testuser" in totp_uri
        issuer_name = flask_app.config.get("TOTP_ISSUER_NAME").replace(" ", "%20")
        assert issuer_name in totp_uri
        # The TOTP URI should start with "otpauth://totp/"
        assert totp_uri.startswith("otpauth://totp/")

def test_user_verify_totp(flask_app):
    """ Test the Users model. """
    with flask_app.app_context():
        user = Users(id=1, username="testuser", role="member")
        user.generate_totp_secret()
        totp = pyotp.TOTP(user.totp_secret)
        current_otp = totp.now()
        # The current OTP should verify successfully.
        assert user.verify_totp(current_otp)
        # The last OTP should verify successfully (valid_window=1 allows for 30s drift).
        last_otp = totp.at(int((time.time()) - 30))
        assert user.verify_totp(last_otp)
        # An incorrect OTP should not verify.
        assert user.verify_totp("000000") is False

def test_user_to_dict(flask_app):
    """ Test the Users model's to_dict method. """
    with flask_app.app_context():
        user = Users(id = 1, username="testuser", role="member")
        user.set_password("password")
        user.generate_totp_secret()
        user_dict = user.to_dict()
        # The returned dictionary should contain the correct keys.
        assert "username" in user_dict
        assert "role" in user_dict
        assert "password" not in user_dict
        assert "totp_secret" not in user_dict
        assert "totp_active" in user_dict

        # The values in the dictionary should match the user's attributes.
        assert user_dict["username"] == "testuser" and user_dict["username"] == user.username
        assert user_dict["role"] == "member" and user_dict["role"] == user.role
        assert user_dict["id"] == 1 and user_dict["id"] == user.id

def test_recovery_code_generation_and_checking(flask_app):
    """ Test the RecoveryCodes model. """
    with flask_app.app_context():
        recovery_code = RecoveryCodes(user_id=1)
        code = recovery_code.generate_code()
        # The generated code should be a non-empty string.
        assert isinstance(code, str)
        assert len(code) > 0
        # The check_code method should return True for the correct code.
        assert recovery_code.check_code(code)
        # The check_code method should return False for an incorrect code.
        assert recovery_code.check_code("wrongcode") is False

def test_recovery_code_to_dict(flask_app):
    """ Test the RecoveryCodes model's to_dict method. """
    with flask_app.app_context():
        recovery_code = RecoveryCodes(user_id=1)
        recovery_code.generate_code()
        code_dict = recovery_code.to_dict()
        # The returned dictionary should contain the correct keys.
        assert "user_id" in code_dict
        assert "code_hash" in code_dict
        # The values in the dictionary should match the recovery code's attributes.
        assert code_dict["user_id"] == 1 and code_dict["user_id"] == recovery_code.user_id
        assert code_dict["code_hash"] == recovery_code.code_hash

def test_meetings_to_dict(flask_app):
    """ Test the Meetings model's to_dict method. """
    with flask_app.app_context():
        meeting = Meetings(title="Test Meeting", state="Scheduled", description="A test meeting.", host="testuser")
        meeting_dict = meeting.to_dict()
        # The returned dictionary should contain the correct keys.
        assert "title" in meeting_dict
        assert "state" in meeting_dict
        assert "description" in meeting_dict
        assert "host" in meeting_dict
        # The values in the dictionary should match the meeting's attributes.
        assert meeting_dict["title"] == "Test Meeting" and meeting_dict["title"] == meeting.title
        assert meeting_dict["state"] == "Scheduled" and meeting_dict["state"] == meeting.state
        assert meeting_dict["description"] == "A test meeting." and meeting_dict["description"] == meeting.description
        assert meeting_dict["host"] == "testuser" and meeting_dict["host"] == meeting.host

def test_attendees_to_dict(flask_app):
    """ Test the Attendees model's to_dict method. """
    with flask_app.app_context():
        attendee = Attendees(id=1, username="testuser", meeting = 1)
        attendee_dict = attendee.to_dict()
        # The returned dictionary should contain the correct keys.
        assert "id" in attendee_dict
        assert "username" in attendee_dict
        assert "meeting" in attendee_dict
        # The values in the dictionary should match the attendee's attributes.
        assert attendee_dict["id"] == 1 and attendee_dict["id"] == attendee.id
        assert attendee_dict["username"] == "testuser" and attendee_dict["username"] == attendee.username
        assert attendee_dict["meeting"] == 1 and attendee_dict["meeting"] == attendee.meeting

def test_minutes_to_dict(flask_app):
    """ Test the Minutes model's to_dict method. """
    with flask_app.app_context():
        minute = Minutes(id=1, notes="These are test minutes.", username_by="testuser", meeting=1)
        minute_dict = minute.to_dict()
        # The returned dictionary should contain the correct keys.
        assert "id" in minute_dict
        assert "notes" in minute_dict
        assert "username_by" in minute_dict
        assert "meeting" in minute_dict
        # The values in the dictionary should match the minute's attributes.
        assert minute_dict["id"] == 1 and minute_dict["id"] == minute.id
        assert minute_dict["notes"] == "These are test minutes." and minute_dict["notes"] == minute.notes
        assert minute_dict["username_by"] == "testuser" and minute_dict["username_by"] == minute.username_by
        assert minute_dict["meeting"] == 1 and minute_dict["meeting"] == minute.meeting

def test_attachments_to_dict(flask_app):
    """ Test the Attachments model's to_dict method. """
    with flask_app.app_context():
        attachment = Attachments(id=1)
        attachment_dict = attachment.to_dict()
        # The returned dictionary should contain the correct keys.
        assert "id" in attachment_dict
        # The values in the dictionary should match the attachment's attributes.
        assert attachment_dict["id"] == 1 and attachment_dict["id"] == attachment.id

def test_poll_relationships(flask_app):
    """ Test the Poll model's relationships. """
    with flask_app.app_context():
        poll = Poll(id=1, title="Test Poll", poll_expires=False)
        question = PollQuestion(id=1, question_text="Test Question", poll_id=1)
        free_response = PollFreeResponse(id=1, response_text="Test Response", question_id=1)
        option = PollOption(id=1, option_text="Test Option", question_id=1, votes=0)
        voter = PollVoter(id=1, user_id=1, option_id=1)

        # Create the relationships.
        poll.questions.append(question)
        question.free_responses.append(free_response)
        question.options.append(option)
        question.voters.append(voter)
        option.votes += 1

        # The relationships should be set up correctly.
        assert poll.questions == [question]
        assert question.free_responses == [free_response]
        assert question.options == [option]
        assert option.votes == 1
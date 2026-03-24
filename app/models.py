#!/usr/bin/env python
# app/models.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz), Thomas Crossman (github.com/crossmant1)
Last Modified: 2/14/2026

File Purpose: Create the database models for the project.
"""
# Standard library imports.
import secrets

# Third-party imports.
from flask import current_app
from flask_login import UserMixin
import pyotp

from werkzeug.security import generate_password_hash, check_password_hash

# Local application imports.
from .extensions import db # pylint: disable=relative-beyond-top-level

# Define the app database.
class Users(UserMixin, db.Model):
    """ Store all Users in the database. """
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(250), unique = True, nullable = False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(64), nullable = False)
    joined = db.Column(db.String(7), nullable = True) # Store FA|SP YYYY
    graduated = db.Column(db.String(7), nullable = True) # Store FA|SP YYYY

    mfa_active = db.Column(db.Boolean, nullable = True, default = False, server_default = '0')
    totp_secret = db.Column(db.String(32), nullable = True)
    totp_active = db.Column(db.Boolean, nullable = True, default = False, server_default = '0')

    # Store activation status - disable accounts until approved or after valid access period.
    activated = db.Column(db.Boolean, nullable = False, default = False, server_default = '0')

    def set_password(self, password):
        """Werkzeug automatically generates a cryptographically secure salt
        and incorporates it into the returned hash string."""
        self.password = generate_password_hash(password, method='scrypt', salt_length=16)

    def check_password(self, password):
        """Werkzeug extracts the salt and hash from the stored string
        and hashes the input password for comparison."""
        return check_password_hash(self.password, password)

    def generate_totp_secret(self):
        """ Generate a new OTP secret for the user. """
        self.totp_secret = pyotp.random_base32()

    def get_totp_uri(self):
        """ Get the OTP URI for the user. """
        issuer_name = current_app.config.get("TOTP_ISSUER_NAME")
        totp = pyotp.TOTP(self.totp_secret)
        return totp.provisioning_uri(name=self.username, issuer_name=issuer_name)

    def verify_totp(self, token):
        """ Check against the current token AND tokens immediately before/after (drift) """
        return pyotp.totp.TOTP(self.totp_secret).verify(token, valid_window=1)

    def to_dict(self):
        """ Get user data values as a dictionary. """
        return {"id": self.id,
                "username": self.username,
                "password": self.password,
                "role": self.role,
                "joined": self.joined,
                "graduated": self.graduated,
                "otp_secret": self.otp_secret,
                "otp_active": self.otp_active}

class RecoveryCodes(db.Model):
    """ Store recovery codes for users. """
    id = db.Column(db.Integer, primary_key = True, nullable = False)
    user_id = db.Column(db.Integer, nullable = False)
    code_hash = db.Column(db.String(255), nullable = True)

    def generate_code(self):
        """ Initialize a recovery code for a user. """
        code = secrets.token_urlsafe(8)
        self.code_hash = generate_password_hash(code, method='scrypt', salt_length=16)
        return code

    def check_code(self, code):
        """ Verify a recovery code for a user. """
        return check_password_hash(self.code_hash, code)

    def to_dict(self):
        """ Get recovery code data values as a dictionary. """
        return {"id": self.id,
                "user_id": self.user_id,
                "code_hash": self.code_hash}

class Meetings(db.Model):
    """ Store a list of meetings. """
    id = db.Column(db.Integer, primary_key = True, nullable = False)
    state = db.Column(db.String(250), nullable = False)
    title = db.Column(db.String(250), nullable = False)
    description = db.Column(db.String(250), nullable = False)
    host = db.Column(db.String(250), nullable = False)
    event_start = db.Column(db.DateTime, nullable = True)
    event_end = db.Column(db.DateTime, nullable = True)
    code_hash = db.Column(db.String(250), nullable = True)
    admin_only = db.Column(db.Boolean, nullable = True, default = False, server_default = '0')

    def to_dict(self):
        """ Get meeting data values as a dictionary. """
        return {"id": self.id,
                "state": self.state,
                "title": self.title,
                "description": self.description,
                "host": self.host,
                "event_start": self.event_start,
                "event_end": self.event_end,
                "code_hash": self.code_hash,
                "admin_only": self.admin_only}

class Attendees(db.Model):
    """ Store a list of meeting attendees. """
    id = db.Column(db.Integer, primary_key = True, nullable = False)
    username = db.Column(db.String(250), nullable = False)
    meeting = db.Column(db.Integer, nullable = False)

    def to_dict(self):
        """ Get attendee data values as a dictionary. """
        return {"id": self.id,
                "username": self.username,
                "meeting": self.meeting}

class Minutes(db.Model):
    """ Store a list of meeting minutes. """
    id = db.Column(db.Integer, primary_key = True, nullable = False)
    notes = db.Column(db.Text, nullable = False)
    username_by = db.Column(db.String(250), nullable = False)
    meeting = db.Column(db.Integer, nullable = False)

    def to_dict(self):
        """ Get meeting minute data values as a dictionary. """
        return {"id": self.id,
                "notes": self.notes,
                "username_by": self.username_by,
                "meeting": self.meeting}

class Attachments(db.Model):
    """ Store a list of meeting attachments. """
    id = db.Column(db.Integer, primary_key = True, nullable = False)
    filename = db.Column(db.String(250), nullable = False)
    filepath = db.Column(db.String(250), nullable = False)
    meeting = db.Column(db.Integer, nullable = False)

    def to_dict(self):
        """ Get attachment data values as a dictionary. """
        return {"id": self.id,
                "filename": self.filename,
                "filepath": self.filepath,
                "meeting": self.meeting}

class Poll(db.Model):
    """Store polls"""
    __tablename__="polls"
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(250), nullable=False)
    poll_expires=db.Column(db.DateTime, nullable=True)

    questions=db.relationship("PollQuestion", backref="poll", cascade="all, delete-orphan")


class PollQuestion(db.Model):
    """Store questions for polls."""
    __tablename__ = "poll_questions"

    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    is_free_response = db.Column(db.Boolean, nullable=False, default=False)
    allow_multiple_responses = db.Column(db.Boolean, nullable=False, default=False)

    poll_id = db.Column(db.Integer, db.ForeignKey("polls.id", ondelete="CASCADE"), nullable=False)

    options = db.relationship("PollOption", backref="question", cascade="all, delete-orphan")
    voters = db.relationship("PollVoter", backref="question", cascade="all, delete-orphan")
    free_responses = db.relationship("PollFreeResponse",
                                     backref="question",
                                     cascade="all, delete-orphan")


class PollFreeResponse(db.Model):
    """Store free response answers."""
    __tablename__ = "poll_free_responses"

    id = db.Column(db.Integer, primary_key=True)
    response_text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)

    question_id = db.Column(db.Integer,
                           db.ForeignKey("poll_questions.id", ondelete="CASCADE"),
                           nullable=False)

    created_at = db.Column(db.DateTime, default=db.func.now())

    __table_args__ = (
        db.UniqueConstraint('user_id', 'question_id', name='unique_user_question_response'),
    )

class PollOption(db.Model):
    """Store options for poll questions."""
    __tablename__="poll_options"

    id=db.Column(db.Integer, primary_key=True)
    option_text=db.Column(db.String(250), nullable=False)
    votes=db.Column(db.Integer, nullable=False, default=0)

    question_id=db.Column(db.Integer,
                           db.ForeignKey("poll_questions.id", ondelete="CASCADE"),
                           nullable=False)


class PollVoter(db.Model):
    """Store users who have voted on specific questions."""
    __tablename__ = "poll_voters"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)

    question_id = db.Column(db.Integer,
                            db.ForeignKey("poll_questions.id",
                                                       ondelete="CASCADE"),
                                                         nullable=False)

    option_id = db.Column(db.Integer,
                         db.ForeignKey("poll_options.id", ondelete="CASCADE"),
                         nullable=False)

    poll_id = db.Column(db.Integer, db.ForeignKey("polls.id", ondelete="CASCADE"), nullable=True)

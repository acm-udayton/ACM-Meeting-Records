#!/usr/bin/env python
# app/models.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 10/7/2025

File Purpose: Create the database models for the project.
"""

# Third-party imports.
from flask_login import UserMixin
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

    def set_password(self, password):
        """Werkzeug automatically generates a cryptographically secure salt
        and incorporates it into the returned hash string."""
        self.password = generate_password_hash(password, method='scrypt', salt_length=16)

    def check_password(self, password):
        """Werkzeug extracts the salt and hash from the stored string
        and hashes the input password for comparison."""
        return check_password_hash(self.password, password)


    def to_dict(self):
        """ Get user data values as a dictionary. """
        return {"id": self.id,
                "username": self.username,
                "password": self.password,
                "role": self.role,
                "joined": self.joined,
                "graduated": self.graduated}

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
    admin_only = db.Column(db.Boolean, nullable = True, default = False)

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

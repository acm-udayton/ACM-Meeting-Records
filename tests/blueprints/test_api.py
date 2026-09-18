#!/usr/bin/env python
# tests/blueprints/test_api.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitzj)
Last Modified: 8/19/2026

File Purpose: Pytest for the blueprints/api endpoints.
"""

from app.models import Attachments, Attendees, Meetings, Minutes, Users
from flask_login import login_user
from tests.conftest import app as flask_app, db  # Import the app fixture for context in tests.

def test_api_event_attendees(flask_app):
    """ Test the /event/attendees/<int:meeting_id>/ endpoint. """
    with flask_app.test_request_context():
        client = flask_app.test_client()

        # Test access denied for non-existent meeting ID.
        response = client.get("/api/event/attendees/9999/")
        assert response.status_code == 404
        assert response.json == {"error": "No attendees found"}

        # Write test data for meetings and attendees.
        admin_user = Users(username="admin", password="test_password", role="admin")
        meeting = Meetings(id=1, state="active", title="Test Meeting", admin_only=False, description="Test Description", host="testuser")
        admin_only_meeting = Meetings(id=2, state="active", title="Admin Meeting", admin_only=True, description="Admin Description", host="adminuser")
        
        attendee = Attendees(id=1, meeting=1, username="testuser")
        admin_attendee = Attendees(id=2, meeting=2, username="adminuser")
        
        db.session.add_all([admin_user, meeting, admin_only_meeting, attendee, admin_attendee])
        db.session.commit()

        # Test with a valid, accessible meeting ID.
        response = client.get("/api/event/attendees/1/")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 1
        assert response.json[0]['id'] == 1
        assert response.json[0]['meeting'] == 1
        assert response.json[0]['username'] == "testuser"

        # Test with an admin-only meeting ID (should return 403 for non-admin users).
        response = client.get("/api/event/attendees/2/")
        assert response.status_code == 403

        # Test logged-in admin user can access admin-only meeting.
        login_user(admin_user)
        response = client.get("/api/event/attendees/2/")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 1
        assert response.json[0]['id'] == 2
        assert response.json[0]['meeting'] == 2
        assert response.json[0]['username'] == "adminuser"


def test_api_event_minutes(flask_app):
    """ Test the /event/notes/<int:meeting_id>/ endpoint. """
    with flask_app.test_request_context():
        client = flask_app.test_client()

        # Test access denied for non-existent meeting ID.
        response = client.get("/api/event/notes/9999/")
        assert response.status_code == 404
        assert response.json == {"error": "No minutes found"}

        # Write test data for meetings and minutes.
        admin_user = Users(username="admin", password="test_password", role="admin")
        meeting = Meetings(id=1, state="active", title="Test Meeting", admin_only=False, description="Test Description", host="testuser")
        admin_only_meeting = Meetings(id=2, state="active", title="Admin Meeting", admin_only=True, description="Admin Description", host="adminuser")
        
        minute = Minutes(id=1, meeting=1, notes="Test Minutes", username_by="testuser")
        admin_minute = Minutes(id=2, meeting=2, notes="Admin Minutes", username_by="adminuser")

        db.session.add_all([admin_user, meeting, admin_only_meeting, minute, admin_minute])
        db.session.commit()

        # Test with a valid, accessible meeting ID.
        response = client.get("/api/event/notes/1/")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 1
        assert response.json[0]['id'] == 1
        assert response.json[0]['meeting'] == 1
        assert response.json[0]['notes'] == "Test Minutes"
        assert response.json[0]['username_by'] == "testuser"

        # Test with an admin-only meeting ID (should return 403 for non-admin users).
        response = client.get("/api/event/notes/2/")
        assert response.status_code == 403

        # Test logged-in admin user can access admin-only meeting.
        login_user(admin_user)
        response = client.get("/api/event/notes/2/")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 1
        assert response.json[0]['id'] == 2
        assert response.json[0]['meeting'] == 2
        assert response.json[0]['notes'] == "Admin Minutes"
        assert response.json[0]['username_by'] == "adminuser"


def test_api_event_state(flask_app):
    """ Test the /event/state/<int:meeting_id>/ endpoint. """
    with flask_app.test_request_context():
        client = flask_app.test_client()

        # Test access denied for non-existent meeting ID.
        response = client.get("/api/event/state/9999/")
        assert response.status_code == 404

        # Write test data for meetings.
        admin_user = Users(username="admin", password="test_password", role="admin")
        meeting = Meetings(id=1, state="active", title="Test Meeting", admin_only=False, description="Test Description", host="testuser")
        admin_only_meeting = Meetings(id=2, state="inactive", title="Admin Meeting", admin_only=True, description="Admin Description", host="adminuser")
        db.session.add_all([admin_user, meeting, admin_only_meeting])
        db.session.commit()

        # Test with a valid, accessible meeting ID.
        response = client.get("/api/event/state/1/")
        assert response.status_code == 200
        assert response.json == "Active"

        # Test with an admin-only meeting ID (should return 403 for non-admin users).
        response = client.get("/api/event/state/2/")
        assert response.status_code == 403

        # Test logged-in admin user can access admin-only meeting.
        login_user(admin_user)
        response = client.get("/api/event/state/2/")
        assert response.status_code == 200


def test_api_event_attachments(flask_app):
    """ Test the /event/attachments/<int:meeting_id>/ endpoint. """
    with flask_app.test_request_context():
        client = flask_app.test_client()

        # Test access denied for non-existent meeting ID.
        response = client.get("/api/event/attachments/9999/")
        assert response.status_code == 404
        assert response.json == {"error": "No attachments found"}

        # Write test data for meetings and attachments.
        admin_user = Users(username="admin", password="test_password", role="admin")
        meeting = Meetings(id=1, state="active", title="Test Meeting", admin_only=False, description="Test Description", host="testuser")
        admin_only_meeting = Meetings(id=2, state="active", title="Admin Meeting", admin_only=True, description="Admin Description", host="adminuser")

        attachment = Attachments(id=1, meeting=1, filename="testfile.txt", filepath="/path/to/testfile.txt")
        admin_attachment = Attachments(id=2, meeting=2, filename="adminfile.txt", filepath="/path/to/adminfile.txt")

        db.session.add_all([admin_user, meeting, admin_only_meeting, attachment, admin_attachment])
        db.session.commit()

        # Test with a valid, accessible meeting ID.
        response = client.get("/api/event/attachments/1/")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 1
        assert response.json[0]['id'] == 1
        assert response.json[0]['meeting'] == 1
        assert response.json[0]['filename'] == "testfile.txt"
        assert response.json[0]['filepath'] == "/path/to/testfile.txt"

        # Test with an admin-only meeting ID (should return 403 for non-admin users).
        response = client.get("/api/event/attachments/2/")
        assert response.status_code == 403

        # Test logged-in admin user can access admin-only meeting.
        login_user(admin_user)
        response = client.get("/api/event/attachments/2/")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 1
        assert response.json[0]['id'] == 2
        assert response.json[0]['meeting'] == 2
        assert response.json[0]['filename'] == "adminfile.txt"
        assert response.json[0]['filepath'] == "/path/to/adminfile.txt"
#!/usr/bin/env python
# tests/blueprints/test_api.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 6/6/2026

File Purpose: Pytest for the blueprints/api endpoints.
"""

from app.models import Attachments, Attendees, Meetings, Minutes
from tests.conftest import app as flask_app, db  # Import the app fixture for context in tests.

def test_api_event_attendees(flask_app):
    """ Test the /event/attendees/<int:meeting_id>/ endpoint. """
    with flask_app.app_context():
        # Test no data returned without valid meeting ID.
        response = flask_app.test_client().get("/api/event/attendees/9999/")
        assert response.status_code == 200
        assert response.json == []

        # Write test data for attendees and meeting.
        db.session.add(Attendees(id=1, meeting=1, username="testuser"))

        # Test with a valid meeting ID.
        response = flask_app.test_client().get("/api/event/attendees/1/")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 1
        assert response.json[0]['id'] == 1
        assert response.json[0]['meeting'] == 1
        assert response.json[0]['username'] == "testuser"

def test_api_event_minutes(flask_app):
    """ Test the /event/notes/<int:meeting_id>/ endpoint. """
    with flask_app.app_context():
        # Test no data returned without valid meeting ID.
        response = flask_app.test_client().get("/api/event/notes/9999/")
        assert response.status_code == 200
        assert response.json == []

        # Write test data for minutes and meeting.
        db.session.add(Minutes(id=1, meeting=1, notes="Test Minutes", username_by="testuser"))

        # Test with a valid meeting ID.
        response = flask_app.test_client().get("/api/event/notes/1/")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 1
        assert response.json[0]['id'] == 1
        assert response.json[0]['meeting'] == 1
        assert response.json[0]['notes'] == "Test Minutes"
        assert response.json[0]['username_by'] == "testuser"
        
def test_api_event_state(flask_app):
    """ Test the /event/state/<int:meeting_id>/ endpoint. """
    with flask_app.app_context():
        # Test 404 returned without valid meeting ID.
        response = flask_app.test_client().get("/api/event/state/9999/")
        assert response.status_code == 200
        assert response.json == None

        # Write test data for meeting.
        db.session.add(Meetings(id=1, state="active", title="Test Meeting", description="Test Description", host="testuser"))

        # Test with a valid meeting ID.
        response = flask_app.test_client().get("/api/event/state/1/")
        assert response.status_code == 200
        assert response.json == "Active"

def test_api_event_attachments(flask_app):
    """ Test the /event/attachments/<int:meeting_id>/ endpoint. """
    with flask_app.app_context():
        # Test no data returned without valid meeting ID.
        response = flask_app.test_client().get("/api/event/attachments/9999/")
        assert response.status_code == 200
        assert response.json == []

        # Write test data for attachments and meeting.
        db.session.add(Attachments(id=1, meeting=1, filename="testfile.txt", filepath="/path/to/testfile.txt"))

        # Test with a valid meeting ID.
        response = flask_app.test_client().get("/api/event/attachments/1/")
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 1
        assert response.json[0]['id'] == 1
        assert response.json[0]['meeting'] == 1
        assert response.json[0]['filename'] == "testfile.txt"
        assert response.json[0]['filepath'] == "/path/to/testfile.txt"
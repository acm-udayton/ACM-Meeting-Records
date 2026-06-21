#!/usr/bin/env python
# tests/blueprints/test_admin.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 6/6/2026

File Purpose: Pytest for the blueprints/admin endpoints.
"""

from datetime import datetime, timedelta

from flask import current_app

from app.models import Attachments, Attendees, Meetings, Minutes, Users
from tests.conftest import app as flask_app, db  # Import the app fixture for context in tests.

def test_get_last_attended_date(flask_app):
    """ Test the get_last_attended_date function. """
    from app.blueprints.admin import get_last_attended_date
    with flask_app.app_context():

        user1 = Users(username="testuser1", role="member")
        user2 = Users(username="testuser2", role="member")
        user3 = Users(username="testuser3", role="member")

        attendee1 = Attendees(username="testuser1", meeting=1)
        attendee2 = Attendees(username="testuser1", meeting=2)
        attendee3 = Attendees(username="testuser2", meeting=2)
        db.session.add_all([attendee1, attendee2, attendee3])
        db.session.commit()

        # Create test data for meetings and attendees.
        current_time = datetime.now()
        meeting1 = Meetings(title="Meeting 1", event_start = current_time, state="active", description="Test Meeting 1", host="testuser1")
        meeting2 = Meetings(title="Meeting 2", event_start = current_time - timedelta(days=1), state="active", description="Test Meeting 2", host="testuser2")
        db.session.add_all([meeting1, meeting2])
        db.session.commit()


        # Test the function with the test data.
        last_attended_date = get_last_attended_date(user1)
        assert last_attended_date is not None
        assert last_attended_date == current_time

        last_attended_date = get_last_attended_date(user2)
        assert last_attended_date is not None
        assert last_attended_date == current_time - timedelta(days=1)

        last_attended_date = get_last_attended_date(user3)
        assert last_attended_date is None

def test_admin_dashboard(flask_app):
    """ Test the /admin/dashboard/ endpoint. """
    with flask_app.app_context():
        # Create a test admin user.
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        test_client = flask_app.test_client()

        # Create a test  meeting to view the dashboard for.
        meeting = Meetings(title="Test Meeting", event_start=datetime.now(), state="active", description="Test Meeting Description", host="adminuser")
        db.session.add(meeting)
        db.session.commit()

        # Test access without login.
        response = test_client.get(f"/admin/dashboard/{meeting.id}/")
        assert response.status_code == 401  # Unauthorized.

        # Log in as the admin user.
        login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
        print(login_response.data)
        assert login_response.status_code == 200

        # Test access to the dashboard after login.
        dashboard_response = test_client.get(f"/admin/dashboard/{meeting.id}/")
        assert dashboard_response.status_code == 200

def test_event_create(flask_app):
    """ Test the /admin/create/ endpoint. """
    with flask_app.app_context():
        # Create a test admin user.
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        # Test access without login.
        test_client = flask_app.test_client()
        response = test_client.post("/admin/create/", data={"title": "New Meeting", "description": "Test Description", "host": "adminuser"}, follow_redirects=True)
        assert response.status_code == 401  # Unauthorized.

        # Log in as the admin user.
        login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
        assert login_response.status_code == 200

        # Test access to the create endpoint after login.
        create_response = test_client.post("/admin/create/", data={"title": "New Meeting", "description": "Test Description", "host": "adminuser"}, follow_redirects=True)
        assert create_response.status_code == 200

def test_event_start(flask_app):
    """ Test the /admin/start/ endpoint. """
    with flask_app.app_context():
        # Create a test admin user.
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        # Create a test meeting to start.
        meeting = Meetings(title="Test Meeting", state="not started", description="Test Meeting Description", host="adminuser")
        db.session.add(meeting)
        db.session.commit()

        # Test access without login.
        test_client = flask_app.test_client()
        response = test_client.post(f"/admin/start/{meeting.id}/")
        assert response.status_code == 401  # Unauthorized.

        # Log in as the admin user.
        login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
        assert login_response.status_code == 200


        # Test access to the start endpoint after login.
        start_response = test_client.post(f"/admin/start/{meeting.id}/")
        assert start_response.status_code == 200
#!/usr/bin/env python
# tests/blueprints/test_admin.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 6/6/2026

File Purpose: Pytest for the blueprints/admin endpoints.
"""

import io
import os
from datetime import datetime, timedelta

from flask import current_app, get_flashed_messages

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

        # Test starting an already active meeting.
        start_response_again = test_client.post(f"/admin/start/{meeting.id}/")
        assert start_response_again.status_code == 400

def test_reset_code(flask_app):
    """ Test the /admin/reset-code/ endpoint. """
    with flask_app.app_context():
        # Create a test admin user.
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        # Create a test meeting to reset the code for.
        meeting = Meetings(title="Test Meeting", state="active", description="Test Meeting Description", host="adminuser")
        db.session.add(meeting)
        db.session.commit()

        inactive_meeting = Meetings(title="Inactive Meeting", state="not started", description="Test Meeting Description", host="adminuser")
        db.session.add(inactive_meeting)
        db.session.commit()

        # Test access without login.
        test_client = flask_app.test_client()
        response = test_client.get(f"/admin/reset-code/{meeting.id}/", follow_redirects=True)
        assert response.status_code == 401  # Unauthorized.

        # Log in as the admin user.
        login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
        assert login_response.status_code == 200

        # Test access to the reset code endpoint after login.
        reset_code_response = test_client.get(f"/admin/reset-code/{meeting.id}/", follow_redirects=True)
        assert reset_code_response.status_code == 200

        # Test resetting the code for an inactive meeting.
        reset_code_response_inactive = test_client.get(f"/admin/reset-code/{inactive_meeting.id}/", follow_redirects=True)
        assert reset_code_response_inactive.status_code == 400

def test_show_code(flask_app):
    """ Test the /admin/show-code/ endpoint. """
    with flask_app.app_context():
        # Create a test admin user.
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        # Test access without login.
        test_client = flask_app.test_client()
        response = test_client.get(f"/admin/show-code/?code=testcode", follow_redirects=True)
        assert response.status_code == 401  # Unauthorized.

        # Log in as the admin user.
        login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
        assert login_response.status_code == 200

        # Test access to the show code endpoint after login.
        show_code_response = test_client.get(f"/admin/show-code/?code=testcode", follow_redirects=True)
        assert show_code_response.status_code == 200

        # Test with no code.
        show_code_response_blank = test_client.get(f"/admin/show-code/", follow_redirects=True)
        assert show_code_response_blank.status_code == 404

def test_event_end(flask_app):
    """ Test the /admin/end/ endpoint. """
    with flask_app.app_context():
        # Create a test admin user.
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        # Create a test meeting to end.
        meeting = Meetings(title="Test Meeting", state="active", description="Test Meeting Description", host="adminuser")
        db.session.add(meeting)
        db.session.commit()

        # Test access without login.
        test_client = flask_app.test_client()
        response = test_client.post(f"/admin/end/{meeting.id}/")
        assert response.status_code == 401  # Unauthorized.

        # Log in as the admin user.
        login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
        assert login_response.status_code == 200

        # Test access to the end endpoint after login.
        end_response = test_client.post(f"/admin/end/{meeting.id}/")
        assert end_response.status_code == 200

        # Test ending an already ended meeting.
        end_response_again = test_client.post(f"/admin/end/{meeting.id}/")
        assert end_response_again.status_code == 400

def test_event_attendees(flask_app):
    """ Test the /admin/attendees/ endpoint. """
    with flask_app.app_context():
        # Create a test admin user.
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        # Create a test user to be an attendee.
        attendee_user = Users(username="attendeeuser", role="member")
        attendee_user.set_password("testpassword")
        db.session.add(attendee_user)
        db.session.commit()

        # Create a test meeting to add attendees to.
        meeting = Meetings(title="Test Meeting", state="active", description="Test Meeting Description", host="adminuser")
        db.session.add(meeting)
        db.session.commit()

        # Test access without login.
        test_client = flask_app.test_client()
        response = test_client.post(f"/admin/attendees/{meeting.id}/", data={"username": "attendeeuser"}, follow_redirects=True)
        assert response.status_code == 401  # Unauthorized.

        # Log in as the admin user.
        login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
        assert login_response.status_code == 200

        # Test access to the attendees endpoint after login.
        attendees_response = test_client.post(f"/admin/attendees/{meeting.id}/", data={"username": "attendeeuser"}, follow_redirects=True)
        assert attendees_response.status_code == 201

        # Test access for second check-in of same user.
        attendees_response_duplicate = test_client.post(f"/admin/attendees/{meeting.id}/", data={"username": "attendeeuser"}, follow_redirects=True)
        assert attendees_response_duplicate.status_code == 400

        # Test access for non-existent user.
        attendees_response_nonexistent = test_client.post(f"/admin/attendees/{meeting.id}/", data={"username": "nonexistentuser"}, follow_redirects=True)
        assert attendees_response_nonexistent.status_code == 400

        # Test access for non-existent meeting.
        attendees_response_nonexistent_meeting = test_client.post(f"/admin/attendees/9999/", data={"username": "attendeeuser"}, follow_redirects=True)
        assert attendees_response_nonexistent_meeting.status_code == 400

def test_event_remove_attendee(flask_app):
    """ Test the /admin/remove-attendee/ endpoint. """
    with flask_app.app_context():
        # Create a test admin user.
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        # Create a test user to be an attendee.
        attendee_user = Users(username="attendeeuser", role="member")
        attendee_user.set_password("testpassword")
        db.session.add(attendee_user)
        db.session.commit()

        # Create a test meeting to add attendees to.
        meeting = Meetings(title="Test Meeting", state="active", description="Test Meeting Description", host="adminuser")
        db.session.add(meeting)
        db.session.commit()

        # Add the attendee to the meeting.
        attendee = Attendees(username="attendeeuser", meeting=meeting.id)
        db.session.add(attendee)
        db.session.commit()

        attendee_id = attendee.id

        # Test access without login.
        test_client = flask_app.test_client()
        response = test_client.post(f"/admin/remove-attendee/{meeting.id}/{attendee_id}", follow_redirects=True)
        assert response.status_code == 401  # Unauthorized.

        # Log in as the admin user.
        login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
        assert login_response.status_code == 200

        # Test access to the remove attendee endpoint after login.
        remove_attendee_response = test_client.post(f"/admin/remove-attendee/{meeting.id}/{attendee_id}", follow_redirects=True)
        assert remove_attendee_response.status_code == 200

        # Test removal of non-existent attendee.
        remove_attendee_response_nonexistent = test_client.post(f"/admin/remove-attendee/{meeting.id}/9999", follow_redirects=True)
        assert remove_attendee_response_nonexistent.status_code == 400

        # Test access for removing non-existent meeting.
        remove_attendee_response_nonexistent_meeting = test_client.post(f"/admin/remove-attendee/9999/{attendee_id}", follow_redirects=True)
        assert remove_attendee_response_nonexistent_meeting.status_code == 400

def test_event_minutes(flask_app):
    """ Test the /admin/minutes/ endpoint. """
    # 1. Setup DB records inside the app context
    with flask_app.app_context():
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        meeting = Meetings(title="Test Meeting", state="active", description="Test Meeting Description", host="adminuser")
        db.session.add(meeting)
        db.session.commit()
        
        meeting_id = meeting.id

    # 2. Run client requests outside the app context block so cookies persist
    test_client = flask_app.test_client()

    # Test access without login.
    # FIX: Changed "notes" to "meeting_minutes"
    response = test_client.post(f"/admin/minutes/{meeting_id}/", data={"meeting_minutes": "Test minutes"}, follow_redirects=True)
    assert response.status_code == 401  # Unauthorized.

    # Log in as the admin user.
    login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
    assert login_response.status_code == 200

    # Test access to the minutes endpoint after login.
    # FIX: Changed "notes" to "meeting_minutes"
    minutes_response = test_client.post(f"/admin/minutes/{meeting_id}/", data={"meeting_minutes": "Test minutes"}, follow_redirects=True)
    assert minutes_response.status_code == 201

    # Test updating the minutes with a different user.
    with flask_app.app_context():
        # Create a second admin user.
        admin_user2 = Users(username="adminuser2", role="admin", activated=True)
        admin_user2.set_password("testpassword")
        db.session.add(admin_user2)
        db.session.commit()

        # Log in as the second admin user.
        login_response2 = test_client.post("/login/", data={"username": "adminuser2", "password": "testpassword"}, follow_redirects=True)
        assert login_response2.status_code == 200

        # Get the minutes entry ID for the meeting.
        minutes_entry = Minutes.query.filter_by(meeting=meeting_id).first()
        minutes_id = minutes_entry.id if minutes_entry else None

        # Attempt to update the minutes with the second admin user.
        update_minutes_response = test_client.post(f"/admin/minutes/{meeting_id}/{minutes_id}/", data={"meeting_minutes": "Updated minutes"}, follow_redirects=True)
        assert update_minutes_response.status_code == 201

        # Test updating the minutes with an invalid minutes ID.
        update_minutes_response_invalid = test_client.post(f"/admin/minutes/{meeting_id}/9999/", data={"meeting_minutes": "Updated minutes"}, follow_redirects=True)
        assert update_minutes_response_invalid.status_code == 400

        # Test sending minutes to a non-existent meeting.
        update_minutes_response_nonexistent_meeting = test_client.post(f"/admin/minutes/9999/{minutes_id}/", data={"meeting_minutes": "Updated minutes"}, follow_redirects=True)
        assert update_minutes_response_nonexistent_meeting.status_code == 400

def test_add_attachment(flask_app):
    """ Test the /admin/add-attachment/ endpoint. """
    # Ensure the upload folder exists so file.save() doesn't crash.
    upload_folder = flask_app.config.get('UPLOAD_FOLDER', 'test_uploads')
    os.makedirs(upload_folder, exist_ok=True)

    # Setup DB records inside the app context.
    with flask_app.app_context():
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        meeting = Meetings(title="Test Meeting", state="active", description="Test Meeting Description", host="adminuser")
        db.session.add(meeting)
        db.session.commit()
        
        meeting_id = meeting.id

    # Initialize client.
    test_client = flask_app.test_client()

    # Test access without login.
    unauth_payload = {
        "file": (io.BytesIO(b"dummy file content"), "testfile.txt")
    }
    response = test_client.post(f"/admin/add-attachment/{meeting_id}/", data=unauth_payload, follow_redirects=True)
    assert response.status_code == 401 

    # Log in as the admin user.
    login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
    assert login_response.status_code == 200

    # Test access to the add attachment endpoint after login.
    auth_payload = {
        "file": (io.BytesIO(b"dummy file content"), "testfile.txt")
    }
    add_attachment_response = test_client.post(f"/admin/add-attachment/{meeting_id}/", data=auth_payload, follow_redirects=True)
    assert add_attachment_response.status_code == 201

    # Test with no file in the request.
    no_file_response = test_client.post(f"/admin/add-attachment/{meeting_id}/", data={}, follow_redirects=True)
    assert no_file_response.status_code == 400

    # Test with file but no filename.
    no_filename_payload = {
        "file": (io.BytesIO(b"dummy file content"), "")
    }
    no_filename_response = test_client.post(f"/admin/add-attachment/{meeting_id}/", data=no_filename_payload, follow_redirects=True)
    assert no_filename_response.status_code == 400

    # Test with invalid filetype.
    invalid_file_payload = {
        "file": (io.BytesIO(b"dummy file content"), "testfile.exe")
    }
    invalid_file_response = test_client.post(f"/admin/add-attachment/{meeting_id}/", data=invalid_file_payload, follow_redirects=True)
    assert invalid_file_response.status_code == 400

    # Test with non-existent meeting.
    auth_payload = {
        "file": (io.BytesIO(b"dummy file content"), "testfile.txt")
    }
    non_existent_meeting_response = test_client.post(f"/admin/add-attachment/9999/", data=auth_payload, follow_redirects=True)
    assert non_existent_meeting_response.status_code == 400

    # Clean up: delete the dummy file created by the test.
    uploaded_file_path = os.path.join(upload_folder, f"meeting-{meeting_id}-testfile.txt")
    if os.path.exists(uploaded_file_path):
        os.remove(uploaded_file_path)

def test_remove_attachement(flask_app):
    """ Test the /admin/remove-attachment/ endpoint. """
    with flask_app.app_context():
        # Create a test admin user.
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        # Create a test meeting to add attachments to.
        meeting = Meetings(title="Test Meeting", state="active", description="Test Meeting Description", host="adminuser")
        db.session.add(meeting)
        db.session.commit()

        # Create a test attachment to remove.
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        test_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], "testfile.txt")
        with open(test_file_path, "w") as f:
            f.write("Test file content")
        attachment = Attachments(filename="testfile.txt", filepath=test_file_path, meeting=meeting.id)
        db.session.add(attachment)
        db.session.commit()

        attachment_id = attachment.id

        # Test access without login.
        test_client = flask_app.test_client()
        response = test_client.post(f"/admin/remove-attachment/{meeting.id}/{attachment_id}/", follow_redirects=True)
        assert response.status_code == 401  # Unauthorized.

        # Log in as the admin user.
        login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
        assert login_response.status_code == 200

        # Test access to the remove attachment endpoint after login.
        remove_attachment_response = test_client.post(f"/admin/remove-attachment/{meeting.id}/{attachment_id}/", follow_redirects=True)
        assert remove_attachment_response.status_code == 200

        # Test removal of non-existent attachment.
        remove_attachment_response_nonexistent = test_client.post(f"/admin/remove-attachment/{meeting.id}/9999/", follow_redirects=True)
        assert remove_attachment_response_nonexistent.status_code == 400

        # Test access for removing non-existent meeting.
        remove_attachment_response_nonexistent_meeting = test_client.post(f"/admin/remove-attachment/9999/{attachment_id}/", follow_redirects=True)
        assert remove_attachment_response_nonexistent_meeting.status_code == 400

        # Clean up: delete the directory created for the test file if it still exists.
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        if os.path.exists(os.path.dirname(test_file_path)):
            os.rmdir(os.path.dirname(test_file_path))
        
def test_event_delete(flask_app):
    """ Test the /admin/delete/ endpoint. """
    with flask_app.app_context():
        # Create a test admin user.
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        # Create a test meeting to delete.
        meeting = Meetings(title="Test Meeting", state="active", description="Test Meeting Description", host="adminuser")
        db.session.add(meeting)
        db.session.commit()

        # Test access without login.
        test_client = flask_app.test_client()
        response = test_client.post(f"/admin/delete/{meeting.id}/", follow_redirects=True)
        assert response.status_code == 401  # Unauthorized.

        # Log in as the admin user.
        login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
        assert login_response.status_code == 200

        # Test access to the delete endpoint after login.
        delete_response = test_client.post(f"/admin/delete/{meeting.id}/", follow_redirects=True)
        assert delete_response.status_code == 200
        assert Attendees.query.filter_by(meeting=meeting.id).first() is None
        assert Minutes.query.filter_by(meeting=meeting.id).first() is None
        assert Attachments.query.filter_by(meeting=meeting.id).first() is None
        assert Meetings.query.filter_by(id=meeting.id).first() is None

def test_users(flask_app):
    """ Test the /admin/users/ endpoint. """
    with flask_app.app_context():
        # Create a test admin user.
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        # Test access without login.
        test_client = flask_app.test_client()
        response = test_client.get("/admin/users/", follow_redirects=True)
        assert response.status_code == 401  # Unauthorized.

        # Log in as the admin user.
        login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
        assert login_response.status_code == 200

        # Test access to the users endpoint after login.
        users_response = test_client.get("/admin/users/", follow_redirects=True)
        assert users_response.status_code == 200

        # Test access with the "since" parameter.
        since_response = test_client.get("/admin/users/?since=2023-01-01", follow_redirects=True)
        assert since_response.status_code == 200

        with test_client:
            # Test access with an invalid "since" parameter.
            test_client.get("/admin/users/?since=invalid-date", follow_redirects=True)
            assert get_flashed_messages(category_filter=["danger"]) == ["Invalid date format for 'since' filter. Use YYYY-MM-DD."]

def test_reset_user_password(flask_app):
    """ Test the /admin/reset-user-password/ endpoint. """
    with flask_app.app_context():
        # Create a test admin user.
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        # Create a test user to reset the password for.
        target_user = Users(username="targetuser", role="user")
        target_user.set_password("oldpassword")
        db.session.add(target_user)
        db.session.commit()

        # Test access without login.
        test_client = flask_app.test_client()
        response = test_client.post(f"/admin/users/reset-password/{target_user.id}/", data={"new_password": "newpassword"}, follow_redirects=True)
        assert response.status_code == 401  # Unauthorized.

        # Log in as the admin user.
        login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
        assert login_response.status_code == 200

        # Test access to the reset user password endpoint after login.
        reset_password_response = test_client.post(f"/admin/users/reset-password/{target_user.id}/", data={"new_password": "newpassword"}, follow_redirects=True)
        assert reset_password_response.status_code == 200

        # Verify that the target user's password was changed.
        target_user_from_db = Users.query.get(target_user.id)
        assert target_user_from_db is not None
        assert target_user_from_db.check_password("newpassword") == True

def test_promote_user(flask_app):
    """ Test the /admin/promote-user/ endpoint. """
    with flask_app.app_context():
        # Create a test admin user.
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        # Create a test user to promote.
        target_user = Users(username="targetuser", role="user")
        target_user.set_password("password")
        db.session.add(target_user)
        db.session.commit()

        # Test access without login.
        test_client = flask_app.test_client()
        response = test_client.post(f"/admin/users/promote/{target_user.id}/", follow_redirects=True)
        assert response.status_code == 401  # Unauthorized.

        # Log in as the admin user.
        login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
        assert login_response.status_code == 200

        # Test access to the promote user endpoint after login.
        promote_response = test_client.post(f"/admin/users/promote/{target_user.id}/", follow_redirects=True)
        assert promote_response.status_code == 200

        # Verify that the target user's role was changed.
        target_user_from_db = Users.query.get(target_user.id)
        assert target_user_from_db is not None
        assert target_user_from_db.role == "admin"

        # Test that you cannot promote an already promoted user.
        with test_client:
            test_client.post(f"/admin/users/promote/{target_user.id}/", follow_redirects=True)
            assert get_flashed_messages(category_filter=["danger"]) == [f"User {target_user.username} is already an admin."]
    
def test_demote_user(flask_app):
    """ Test the /admin/demote-user/ endpoint. """
    with flask_app.app_context():
        # Create a test admin user.
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        # Create a test user to demote.
        target_user = Users(username="targetuser", role="admin")
        target_user.set_password("password")
        db.session.add(target_user)
        db.session.commit()

        # Test access without login.
        test_client = flask_app.test_client()
        response = test_client.post(f"/admin/users/demote/{target_user.id}/", follow_redirects=True)
        assert response.status_code == 401  # Unauthorized.

        # Log in as the admin user.
        login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
        assert login_response.status_code == 200

        # Test access to the demote user endpoint after login.
        demote_response = test_client.post(f"/admin/users/demote/{target_user.id}/", follow_redirects=True)
        assert demote_response.status_code == 200

        # Verify that the target user's role was changed.
        target_user_from_db = Users.query.get(target_user.id)
        assert target_user_from_db is not None
        assert target_user_from_db.role == "user"

        # Test that you cannot self-demote (demote the only admin).
        with test_client:
            test_client.post(f"/admin/users/demote/{admin_user.id}/", follow_redirects=True)
            assert get_flashed_messages() == ["You cannot demote your own account."]
        
        # Test that you cannot demote an already demoted user.
        with test_client:
            test_client.post(f"/admin/users/demote/{target_user.id}/", follow_redirects=True)
            assert get_flashed_messages(category_filter=["danger"]) == [f"User {target_user.username} is already a user."]

def test_disable_user_mfa(flask_app):
    """ Test the /admin/users/disable-mfa/ endpoint. """
    with flask_app.app_context():
        # Create a test admin user.
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        # Create a test user to disable MFA for.
        target_user = Users(username="targetuser", role="user", mfa_active=True, totp_active=True, totp_secret="testsecret")
        target_user.set_password("password")
        db.session.add(target_user)
        db.session.commit()

        # Test access without login.
        test_client = flask_app.test_client()
        response = test_client.post(f"/admin/users/disable-mfa/{target_user.id}/", follow_redirects=True)
        assert response.status_code == 401  # Unauthorized.

        # Log in as the admin user.
        login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
        assert login_response.status_code == 200

        # Test access to the disable user MFA endpoint after login.
        disable_mfa_response = test_client.post(f"/admin/users/disable-mfa/{target_user.id}/", follow_redirects=True)
        assert disable_mfa_response.status_code == 200

        # Verify that the target user's MFA was disabled.
        target_user_from_db = Users.query.get(target_user.id)
        assert target_user_from_db is not None
        assert target_user_from_db.mfa_active == False
        assert target_user_from_db.totp_active == False
        assert target_user_from_db.totp_secret == None

        # Test that you cannot disable MFA for an already non-MFA user.
        with test_client:
            test_client.post(f"/admin/users/disable-mfa/{target_user.id}/", follow_redirects=True)
            assert get_flashed_messages() == [f"User {target_user.username} does not have two-factor authentication enabled."]

def test_disable_user_account(flask_app):
    """ Test the /admin/users/disable-account/ endpoint. """
    with flask_app.app_context():
        # Create a test admin user.
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        # Create a test user to disable.
        target_user = Users(username="targetuser", role="user", activated=True)
        target_user.set_password("password")
        db.session.add(target_user)
        db.session.commit()

        # Test access without login.
        test_client = flask_app.test_client()
        response = test_client.post(f"/admin/users/disable-account/{target_user.id}/", follow_redirects=True)
        assert response.status_code == 401  # Unauthorized.

        # Log in as the admin user.
        login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
        assert login_response.status_code == 200

        # Test access to the disable user account endpoint after login.
        disable_account_response = test_client.post(f"/admin/users/disable-account/{target_user.id}/", follow_redirects=True)
        assert disable_account_response.status_code == 200

        # Verify that the target user's account was disabled.
        target_user_from_db = Users.query.get(target_user.id)
        assert target_user_from_db is not None
        assert target_user_from_db.activated == False

        # Test that you cannot disable an already disabled account.
        with test_client:
            test_client.post(f"/admin/users/disable-account/{target_user.id}/", follow_redirects=True)
            assert get_flashed_messages() == [f"User {target_user.username}'s account is already disabled."]

def test_enable_user_account(flask_app):
    """ Test the /admin/users/enable-account/ endpoint. """
    with flask_app.app_context():
        # Create a test admin user.
        admin_user = Users(username="adminuser", role="admin", activated=True)
        admin_user.set_password("testpassword")
        db.session.add(admin_user)
        db.session.commit()

        # Create a test user to enable.
        target_user = Users(username="targetuser", role="user", activated=False)
        target_user.set_password("password")
        db.session.add(target_user)
        db.session.commit()

        # Test access without login.
        test_client = flask_app.test_client()
        response = test_client.post(f"/admin/users/enable-account/{target_user.id}/", follow_redirects=True)
        assert response.status_code == 401  # Unauthorized.

        # Log in as the admin user.
        login_response = test_client.post("/login/", data={"username": "adminuser", "password": "testpassword"}, follow_redirects=True)
        assert login_response.status_code == 200

        # Test access to the enable user account endpoint after login.
        enable_account_response = test_client.post(f"/admin/users/enable-account/{target_user.id}/", follow_redirects=True)
        assert enable_account_response.status_code == 200

        # Verify that the target user's account was enabled.
        target_user_from_db = Users.query.get(target_user.id)
        assert target_user_from_db is not None
        assert target_user_from_db.activated == True

        # Test that you cannot enable an already enabled account.
        with test_client:
            test_client.post(f"/admin/users/enable-account/{target_user.id}/", follow_redirects=True)
            assert get_flashed_messages() == [f"User {target_user.username}'s account is already enabled."]
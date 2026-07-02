#!/usr/bin/env python
# tests/blueprints/test_main.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 7/1/2026

File Purpose: Pytest for the blueprints/main endpoints.
"""

from datetime import datetime, timedelta

from flask import get_flashed_messages
from flask_login import login_user as flask_login_user

from app.blueprints import main as main_module
from app.extensions import db
from app.models import (
    Meetings,
    Attendees,
    Users,
    Poll,
    PollQuestion,
    PollOption,
    PollVoter,
    PollFreeResponse
)
from app.utils import sha_hash
from tests.conftest import app as flask_app

def create_user(username="testuser", password="password", role="user", activated=True, mfa_active=False, totp_active=False):
    """Create a test user and persist it to the database."""
    user = Users(
        username=username,
        role=role,
        activated=activated,
        mfa_active=mfa_active,
        totp_active=totp_active,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def login_user(test_client, username="testuser", password="password"):
    """Log a test user in through the auth route."""
    login_response = test_client.post(
        "/login/",
        data={"username": username, "password": password},
        follow_redirects=True,
    )
    assert login_response.status_code == 200
    return login_response

def create_meeting(title, state="active", description="Test meeting", host="testuser", admin_only=False, code=None):
    """Create and persist a meeting record."""
    meeting = Meetings(
        title=title,
        state=state,
        description=description,
        host=host,
        admin_only=admin_only,
    )
    if code is not None:
        meeting.code_hash = sha_hash(code)
    db.session.add(meeting)
    db.session.commit()
    return meeting

def create_poll(title, expires=None):
    """Create and persist a poll record."""
    poll = Poll(title=title, poll_expires=expires)
    db.session.add(poll)
    db.session.flush()
    return poll

def create_question(poll, question_text, *, is_free_response=False, allow_multiple=False, private_vote=False, immutable_question=False):
    """Create and persist a poll question."""
    question = PollQuestion(
        poll_id=poll.id,
        question_text=question_text,
        is_free_response=is_free_response,
        allow_multiple_responses=allow_multiple,
        private_vote=private_vote,
        immutable_question=immutable_question,
    )
    db.session.add(question)
    db.session.flush()
    return question

def create_option(question, option_text, votes=0):
    """Create and persist a poll option."""
    option = PollOption(question_id=question.id, option_text=option_text, votes=votes)
    db.session.add(option)
    db.session.flush()
    return option

def add_voter(user_id, question_id, option_id, poll_id=None):
    """Create and persist a poll vote record."""
    voter = PollVoter(
        user_id=user_id,
        question_id=question_id,
        option_id=option_id,
        poll_id=poll_id,
    )
    db.session.add(voter)
    db.session.flush()
    return voter

def add_free_response(user_id, question_id, response_text):
    """Create and persist a free-response answer."""
    response = PollFreeResponse(
        user_id=user_id,
        question_id=question_id,
        response_text=response_text,
    )
    db.session.add(response)
    db.session.flush()
    return response

def test_home_no_recent_meetings(flask_app):
    """The home page should render the empty-state message when no meetings exist."""
    with flask_app.app_context():
        response = flask_app.test_client().get("/")
        assert response.status_code == 200
        assert "No Meeting Records Found" in response.get_data(as_text=True)

def test_home_admin_sees_private_meetings_and_poll_state(flask_app):
    """Admins should see admin-only meetings and pre-existing poll state on the home page."""
    with flask_app.app_context():
        admin = create_user(username="adminuser", role="admin")
        test_client = flask_app.test_client()
        login_user(test_client, username="adminuser")

        # Temporary meeting rows are needed for the homepage admin branch.
        create_meeting(
            title="Public Meeting",
            state="active",
            description="Public meeting description",
            host="adminuser",
            admin_only=False,
            code="PUBLIC123",
        )
        create_meeting(
            title="Private Meeting",
            state="active",
            description="Private meeting description",
            host="adminuser",
            admin_only=True,
            code="PRIVATE123",
        )

        # Temporary poll rows are needed so voted questions and FRQ responses are populated.
        poll = create_poll("Admin Poll", expires=datetime.now() + timedelta(days=1))
        frq = create_question(poll, "Admin feedback", is_free_response=True)
        mcq = create_question(poll, "Choose one", allow_multiple=False)
        option = create_option(mcq, "Option A")
        add_free_response(admin.id, frq.id, "Stored admin response")
        add_voter(admin.id, mcq.id, option.id, poll.id)
        db.session.commit()

        response = test_client.get("/")
        page_text = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "Private Meeting" in page_text
        assert "Admin Poll" in page_text
        assert "Stored admin response" in page_text

def test_home_authenticated_user_with_no_polls(flask_app):
    """Authenticated users without polls should still render the empty poll state."""
    with flask_app.app_context():
        create_user()
        test_client = flask_app.test_client()
        login_user(test_client)

        response = test_client.get("/")
        assert response.status_code == 200
        assert "No polls created yet." in response.get_data(as_text=True)

def test_home_shows_recent_public_meeting_and_polls_for_authenticated_user(flask_app):
    """The home page should show public meetings and visible polls for a logged-in user."""
    with flask_app.app_context():
        create_user()
        test_client = flask_app.test_client()
        login_user(test_client)

        # Temporary meeting rows are needed for homepage featured meeting and recent list.
        public_meeting = create_meeting(
            title="Public Meeting",
            state="active",
            description="Public meeting description",
            host="testuser",
            admin_only=False,
            code="PUBLIC123",
        )
        create_meeting(
            title="Private Meeting",
            state="active",
            description="Private meeting description",
            host="testuser",
            admin_only=True,
            code="PRIVATE123",
        )

        # Temporary poll rows are needed so the authenticated home page can render the poll section.
        poll = create_poll("Weekly Poll", expires=datetime.now() + timedelta(days=1))
        question = create_question(poll, "Pick one", allow_multiple=False)
        create_option(question, "Option A")
        create_option(question, "Option B")
        db.session.commit()

        response = test_client.get("/")
        page_text = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "Public Meeting" in page_text
        assert "Private Meeting" not in page_text
        assert "Existing Polls" in page_text
        assert "Weekly Poll" in page_text
        assert "Pick one" in page_text
        assert "Option A" in page_text

def test_events_list_filters_admin_only_meetings_for_public_users(flask_app):
    """Anonymous users should only see non-admin meetings on the events list."""
    with flask_app.app_context():
        create_meeting("Public Event", state="not started", admin_only=False)
        create_meeting("Admin Event", state="not started", admin_only=True)

        response = flask_app.test_client().get("/events/")
        page_text = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "Public Event" in page_text
        assert "Admin Event" not in page_text

def test_events_list_shows_admin_only_meetings_to_admins(flask_app):
    """Admins should see admin-only meetings on the events list."""
    with flask_app.app_context():
        create_user(username="adminuser", role="admin")
        test_client = flask_app.test_client()
        login_user(test_client, username="adminuser")

        create_meeting("Public Event", state="not started", admin_only=False)
        create_meeting("Admin Event", state="not started", admin_only=True)

        response = test_client.get("/events/")
        page_text = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "Public Event" in page_text
        assert "Admin Event" in page_text

def test_user_event_success(flask_app):
    """The single-meeting page should render for an existing meeting."""
    with flask_app.app_context():
        meeting = create_meeting("Detail Meeting", state="active")

        response = flask_app.test_client().get(f"/event/{meeting.id}/")
        page_text = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "Detail Meeting" in page_text
        assert "Test meeting" in page_text

def test_user_event_not_found(flask_app):
    """The single-meeting page should return 404 for a missing meeting."""
    with flask_app.app_context():
        response = flask_app.test_client().get("/event/999999/")
        assert response.status_code == 404

def test_event_check_in_missing_meeting(flask_app):
    """Missing meetings should flash an error and redirect home during check-in."""
    with flask_app.app_context():
        create_user()
        test_client = flask_app.test_client()
        login_user(test_client)

        with test_client:
            response = test_client.post(
                "/event/check-in/999999/",
                data={"code": "NOPE"},
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert get_flashed_messages() == ["Check-in failed. Specified meeting does not exist."]

def test_event_check_in_success_and_duplicate(flask_app):
    """Reject second check-in attempts as duplicates."""
    with flask_app.app_context():
        user = create_user()
        meeting = create_meeting("Check-in Meeting", state="active", code="CHECKIN42")
        test_client = flask_app.test_client()
        login_user(test_client)

        with test_client:
            response = test_client.post(
                f"/event/check-in/{meeting.id}/",
                data={"code": "CHECKIN42"},
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert get_flashed_messages() == ["Check-in succeeded. Attendance updated successfully."]
            assert Attendees.query.filter_by(username=user.username, meeting=meeting.id).first() is not None

            second_response = test_client.post(
                f"/event/check-in/{meeting.id}/",
                data={"code": "CHECKIN42"},
                follow_redirects=True,
            )
            assert second_response.status_code == 200
            assert get_flashed_messages() == ["Check-in failed. You are already marked as an attendee."]

def test_event_check_in_invalid_code(flask_app):
    """A wrong meeting code should flash a failure message."""
    with flask_app.app_context():
        create_user()
        meeting = create_meeting("Code Meeting", state="active", code="RIGHTCODE")
        test_client = flask_app.test_client()
        login_user(test_client)

        with test_client:
            response = test_client.post(
                f"/event/check-in/{meeting.id}/",
                data={"code": "WRONGCODE"},
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert get_flashed_messages() == ["Check-in failed. Meeting code is invalid."]

def test_event_check_in_inactive_meeting(flask_app):
    """Inactive meetings should reject check-in attempts."""
    with flask_app.app_context():
        create_user()
        meeting = create_meeting("Inactive Meeting", state="not started", code="INACTIVE1")
        test_client = flask_app.test_client()
        login_user(test_client)

        with test_client:
            response = test_client.post(
                f"/event/check-in/{meeting.id}/",
                data={"code": "INACTIVE1"},
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert get_flashed_messages() == ["Check-in failed. Specified meeting is inactive."]

def test_event_check_in_form_validation_failure(flask_app):
    """A blank code should fail form validation before meeting logic runs."""
    with flask_app.app_context():
        create_user()
        meeting = create_meeting("Validation Meeting", state="active", code="VALID123")
        test_client = flask_app.test_client()
        login_user(test_client)

        with test_client:
            response = test_client.post(
                f"/event/check-in/{meeting.id}/",
                data={"code": ""},
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert get_flashed_messages() == ["Check-in failed. Please ensure all fields are filled out correctly."]

def test_event_check_in_admin_only_restricted(flask_app):
    """Non-admin users should be blocked from admin-only meetings even with the correct code."""
    with flask_app.app_context():
        create_user()
        meeting = create_meeting("Admin Only Meeting", state="active", admin_only=True, code="ADMINONLY")
        test_client = flask_app.test_client()
        login_user(test_client)

        with test_client:
            response = test_client.post(
                f"/event/check-in/{meeting.id}/",
                data={"code": "ADMINONLY"},
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert get_flashed_messages() == ["Check-in failed. This meeting is restricted to administrators only."]

def test_event_check_in_unactivated_user_is_logged_out(flask_app):
    """An unactivated user should be logged out after a valid code check-in attempt."""
    with flask_app.app_context():
        user = create_user(username="inactiveuser", activated=False)
        meeting = create_meeting("Activation Meeting", state="active", code="ACTIVATE1")
        test_client = flask_app.test_client()

        # This session-only login is needed because the route checks current_user before the account activation branch.
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)

        with test_client:
            response = test_client.post(
                f"/event/check-in/{meeting.id}/",
                data={"code": "ACTIVATE1"},
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert response.request.path == "/login/"
            assert get_flashed_messages() == ["Check-in failed. Your account is not activated. Please check in again."]
            assert Attendees.query.filter_by(username=user.username, meeting=meeting.id).first() is None

def test_submit_poll_immutable_free_response_failure(flask_app):
    """An immutable free-response question should fail when the user tries to change an existing response."""
    with flask_app.app_context():
        user = create_user()
        test_client = flask_app.test_client()
        login_user(test_client)

        poll = create_poll("Immutable FRQ Poll", expires=datetime.now() + timedelta(days=1))
        question = create_question(poll, "What changed?", is_free_response=True, immutable_question=True)
        add_free_response(user.id, question.id, "Original response")
        db.session.commit()

        with test_client:
            response = test_client.post(
                f"/submit-poll/{poll.id}",
                data={f"question_{question.id}_frq": "Updated response"},
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert get_flashed_messages() == ["Response for 'What changed?' cannot be changed once submitted.", "Some responses were not submitted successfully. Successes: 0, Failures: 1"]
            assert PollFreeResponse.query.filter_by(user_id=user.id, question_id=question.id).one().response_text == "Original response"

def test_submit_poll_helper_branches(flask_app):
    """Direct helper tests cover the remaining FRQ and MCQ branch logic without coupling to HTML forms."""
    with flask_app.app_context():
        user = create_user()

        # FRQ branches: blank, new response, identical response, update, immutable block.
        frq_poll = create_poll("FRQ Branch Poll", expires=datetime.now() + timedelta(days=1))
        frq_question = create_question(frq_poll, "Share a thought", is_free_response=True)
        immutable_frq_question = create_question(frq_poll, "Immutable thought", is_free_response=True, immutable_question=True)
        db.session.commit()

        with flask_app.test_request_context(
            f"/submit-poll/{frq_poll.id}",
            method="POST",
            data={f"question_{frq_question.id}_frq": ""},
        ):
            flask_login_user(user)
            assert main_module.handle_frq(frq_question) == (True, False)

        with flask_app.test_request_context(
            f"/submit-poll/{frq_poll.id}",
            method="POST",
            data={f"question_{frq_question.id}_frq": "Initial response"},
        ):
            flask_login_user(user)
            assert main_module.handle_frq(frq_question) == (True, True)
            db.session.commit()

        with flask_app.test_request_context(
            f"/submit-poll/{frq_poll.id}",
            method="POST",
            data={f"question_{frq_question.id}_frq": "Initial response"},
        ):
            flask_login_user(user)
            assert main_module.handle_frq(frq_question) == (True, False)

        with flask_app.test_request_context(
            f"/submit-poll/{frq_poll.id}",
            method="POST",
            data={f"question_{frq_question.id}_frq": "Updated response"},
        ):
            flask_login_user(user)
            assert main_module.handle_frq(frq_question) == (True, True)

        with flask_app.test_request_context(
            f"/submit-poll/{frq_poll.id}",
            method="POST",
            data={f"question_{immutable_frq_question.id}_frq": "Immutable response"},
        ):
            flask_login_user(user)
            assert main_module.handle_frq(immutable_frq_question) == (True, True)
            db.session.commit()

        with flask_app.test_request_context(
            f"/submit-poll/{frq_poll.id}",
            method="POST",
            data={f"question_{immutable_frq_question.id}_frq": "Changed immutable response"},
        ):
            flask_login_user(user)
            assert main_module.handle_frq(immutable_frq_question) == (False, True)

        # MCQ branches: new vote, no change, change, no selection, immutable block, invalid option.
        mcq_poll = create_poll("MCQ Branch Poll", expires=datetime.now() + timedelta(days=1))
        single_question = create_question(mcq_poll, "Single choice", allow_multiple=False)
        immutable_single_question = create_question(mcq_poll, "Immutable single", allow_multiple=False, immutable_question=True)
        multi_question = create_question(mcq_poll, "Multi choice", allow_multiple=True)
        empty_selection_question = create_question(mcq_poll, "No selection", allow_multiple=False)
        empty_multi_question = create_question(mcq_poll, "Empty multi", allow_multiple=True)
        immutable_multi_question = create_question(mcq_poll, "Immutable multi", allow_multiple=True, immutable_question=True)
        invalid_multi_question = create_question(mcq_poll, "Invalid multi", allow_multiple=True)
        invalid_question = create_question(mcq_poll, "Invalid choice", allow_multiple=False)

        single_a = create_option(single_question, "Single A")
        single_b = create_option(single_question, "Single B")
        immutable_a = create_option(immutable_single_question, "Immutable A")
        immutable_b = create_option(immutable_single_question, "Immutable B")
        multi_a = create_option(multi_question, "Multi A")
        multi_b = create_option(multi_question, "Multi B")
        immutable_multi_a = create_option(immutable_multi_question, "Immutable Multi A")
        immutable_multi_b = create_option(immutable_multi_question, "Immutable Multi B")
        create_option(invalid_question, "Valid option")
        db.session.commit()

        with flask_app.test_request_context(
            f"/submit-poll/{mcq_poll.id}",
            method="POST",
            data={f"question_{single_question.id}_mcq": str(single_a.id)},
        ):
            flask_login_user(user)
            assert main_module.handle_mcq(single_question) == (True, True)

        with flask_app.test_request_context(
            f"/submit-poll/{mcq_poll.id}",
            method="POST",
            data={f"question_{single_question.id}_mcq": str(single_a.id)},
        ):
            flask_login_user(user)
            assert main_module.handle_mcq(single_question) == (True, False)

        with flask_app.test_request_context(
            f"/submit-poll/{mcq_poll.id}",
            method="POST",
            data={f"question_{single_question.id}_mcq": str(single_b.id)},
        ):
            flask_login_user(user)
            assert main_module.handle_mcq(single_question) == (True, True)

        with flask_app.test_request_context(
            f"/submit-poll/{mcq_poll.id}",
            method="POST",
            data={},
        ):
            flask_login_user(user)
            assert main_module.handle_mcq(empty_selection_question) == (True, False)

        with flask_app.test_request_context(
            f"/submit-poll/{mcq_poll.id}",
            method="POST",
            data={f"question_{immutable_single_question.id}_mcq": str(immutable_a.id)},
        ):
            flask_login_user(user)
            assert main_module.handle_mcq(immutable_single_question) == (True, True)
            db.session.commit()

        with flask_app.test_request_context(
            f"/submit-poll/{mcq_poll.id}",
            method="POST",
            data={f"question_{immutable_single_question.id}_mcq": str(immutable_b.id)},
        ):
            flask_login_user(user)
            assert main_module.handle_mcq(immutable_single_question) == (False, True)

        with flask_app.test_request_context(
            f"/submit-poll/{mcq_poll.id}",
            method="POST",
            data={f"question_{multi_question.id}_mcq": [str(multi_a.id), str(multi_b.id)]},
        ):
            flask_login_user(user)
            assert main_module.handle_mcq(multi_question) == (True, True)
            db.session.commit()

        with flask_app.test_request_context(
            f"/submit-poll/{mcq_poll.id}",
            method="POST",
            data={f"question_{multi_question.id}_mcq": [str(multi_a.id), str(multi_b.id)]},
        ):
            flask_login_user(user)
            assert main_module.handle_mcq(multi_question) == (True, False)

        with flask_app.test_request_context(
            f"/submit-poll/{mcq_poll.id}",
            method="POST",
            data={f"question_{multi_question.id}_mcq": [str(multi_a.id)]},
        ):
            flask_login_user(user)
            assert main_module.handle_mcq(multi_question) == (True, True)

        with flask_app.test_request_context(
            f"/submit-poll/{mcq_poll.id}",
            method="POST",
            data={f"question_{empty_multi_question.id}_mcq": []},
        ):
            flask_login_user(user)
            assert main_module.handle_mcq(empty_multi_question) == (True, False)

        with flask_app.test_request_context(
            f"/submit-poll/{mcq_poll.id}",
            method="POST",
            data={f"question_{immutable_multi_question.id}_mcq": [str(immutable_multi_a.id)]},
        ):
            flask_login_user(user)
            assert main_module.handle_multiple_response_mcq([immutable_multi_a.id], immutable_multi_question) == (True, True)
            db.session.commit()

        with flask_app.test_request_context(
            f"/submit-poll/{mcq_poll.id}",
            method="POST",
            data={f"question_{immutable_multi_question.id}_mcq": []},
        ):
            flask_login_user(user)
            assert main_module.handle_multiple_response_mcq([], immutable_multi_question) == (True, False)

        with flask_app.test_request_context(
            f"/submit-poll/{mcq_poll.id}",
            method="POST",
            data={f"question_{immutable_multi_question.id}_mcq": [str(immutable_multi_b.id)]},
        ):
            flask_login_user(user)
            assert main_module.handle_multiple_response_mcq([immutable_multi_b.id], immutable_multi_question) == (False, True)

        with flask_app.test_request_context(
            f"/submit-poll/{mcq_poll.id}",
            method="POST",
            data={f"question_{invalid_multi_question.id}_mcq": ["999999"]},
        ):
            flask_login_user(user)
            assert main_module.handle_multiple_response_mcq([999999], invalid_multi_question) == (False, True)

        with flask_app.test_request_context(
            f"/submit-poll/{mcq_poll.id}",
            method="POST",
            data={f"question_{invalid_question.id}_mcq": "999999"},
        ):
            flask_login_user(user)
            assert main_module.handle_mcq(invalid_question) == (False, False)

def test_submit_poll_commit_exception(flask_app, monkeypatch):
    """A commit failure should trigger the generic submit_poll exception handler."""
    with flask_app.app_context():
        create_user()
        test_client = flask_app.test_client()
        login_user(test_client)

        poll = create_poll("Exception Poll", expires=datetime.now() + timedelta(days=1))
        question = create_question(poll, "Share something", is_free_response=True)
        db.session.commit()

        def raise_commit():
            raise Exception("boom")

        monkeypatch.setattr(db.session, "commit", raise_commit)

        with test_client:
            response = test_client.post(
                f"/submit-poll/{poll.id}",
                data={f"question_{question.id}_frq": "response"},
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert get_flashed_messages() == ["An error occurred while saving your responses. Please try again."]

def test_download_file(flask_app, tmp_path):
    """Uploaded files should be served from the configured upload folder."""
    with flask_app.app_context():
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        file_path = upload_dir / "notes.txt"
        file_path.write_text("meeting notes", encoding="utf-8")
        flask_app.config["UPLOAD_FOLDER"] = str(upload_dir)

        response = flask_app.test_client().get("/uploads/notes.txt")
        assert response.status_code == 200
        assert response.get_data(as_text=True) == "meeting notes"

def test_submit_poll_success_and_repeat_no_changes(flask_app):
    """A poll with FRQ, multi-select, and single-select questions should submit successfully and then report no changes on repeat submission."""
    with flask_app.app_context():
        user = create_user()
        test_client = flask_app.test_client()
        login_user(test_client)

        poll = create_poll("Composite Poll", expires=datetime.now() + timedelta(days=1))
        frq = create_question(poll, "Share feedback", is_free_response=True)
        multi = create_question(poll, "Pick two", allow_multiple=True)
        single = create_question(poll, "Pick one", allow_multiple=False)

        create_option(multi, "Multi A")
        create_option(multi, "Multi B")
        single_a = create_option(single, "Single A")
        create_option(single, "Single B")
        db.session.commit()

        with test_client:
            response = test_client.post(
                f"/submit-poll/{poll.id}",
                data={
                    f"question_{frq.id}_frq": "Good work",
                    f"question_{multi.id}_mcq": [str(multi.options[0].id), str(multi.options[1].id)],
                    f"question_{single.id}_mcq": str(single_a.id),
                },
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert get_flashed_messages() == ["All responses submitted successfully!"]
            assert PollFreeResponse.query.filter_by(user_id=user.id, question_id=frq.id).one().response_text == "Good work"
            assert PollVoter.query.filter_by(user_id=user.id, question_id=multi.id).count() == 2
            assert PollVoter.query.filter_by(user_id=user.id, question_id=single.id).count() == 1

            repeat_response = test_client.post(
                f"/submit-poll/{poll.id}",
                data={
                    f"question_{frq.id}_frq": "Good work",
                    f"question_{multi.id}_mcq": [str(multi.options[0].id), str(multi.options[1].id)],
                    f"question_{single.id}_mcq": str(single_a.id),
                },
                follow_redirects=True,
            )
            assert repeat_response.status_code == 200
            assert get_flashed_messages() == ["No changes were made to any responses."]

def test_submit_poll_rejects_expired_poll(flask_app):
    """Expired polls should be rejected before any submission work happens."""
    with flask_app.app_context():
        create_user()
        test_client = flask_app.test_client()
        login_user(test_client)

        poll = create_poll("Expired Poll", expires=datetime.now() - timedelta(days=1))
        create_question(poll, "Expired question", is_free_response=True)
        db.session.commit()

        with test_client:
            response = test_client.post(f"/submit-poll/{poll.id}", data={}, follow_redirects=True)
            assert response.status_code == 200
            assert get_flashed_messages() == ["Poll has expired. You cannot submit responses."]

def test_submit_poll_reports_invalid_option(flask_app):
    """A tampered poll submission should surface the option lookup failure."""
    with flask_app.app_context():
        create_user()
        test_client = flask_app.test_client()
        login_user(test_client)

        poll = create_poll("Tampered Poll", expires=datetime.now() + timedelta(days=1))
        question = create_question(poll, "Choose one")
        create_option(question, "Real option")
        db.session.commit()

        with test_client:
            response = test_client.post(
                f"/submit-poll/{poll.id}",
                data={f"question_{question.id}_mcq": "999999"},
                follow_redirects=True,
            )
            assert response.status_code == 200
            assert get_flashed_messages() == ["Selected option does not exist.", "Some responses were not submitted successfully. Successes: 0, Failures: 1"]

#!/usr/bin/env python
# tests/blueprints/test_polls.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 7/1/2026

File Purpose: Pytest for the blueprints/polls endpoints.
"""

from datetime import datetime, timedelta

from flask import get_flashed_messages

from app.models import Poll, PollOption, PollQuestion, PollVoter, Users
from tests.conftest import app as flask_app, db  # Import the app fixture for context in tests.


def create_admin_user(username="testadmin", password="password"):
    """Create an activated admin user for route tests."""
    user = Users(username=username, role="admin", activated=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def login_admin(test_client, username="testadmin", password="password"):
    """Log an admin user into the test client."""
    login_response = test_client.post(
        "/login/",
        data={"username": username, "password": password},
        follow_redirects=True,
    )
    assert login_response.status_code == 200


def build_create_poll_data(title, question_text, option_texts=None, *, expires=None, is_free_response=False, allow_multiple=False):
    """Build a form payload for the nested poll creation form."""
    payload = {
        "title": title,
        "poll_expires": expires.strftime("%Y-%m-%dT%H:%M") if expires else "",
        "questions-0-question_text": question_text,
        "questions-0-is_free_response": "y" if is_free_response else "",
        "questions-0-allow_multiple_responses": "y" if allow_multiple else "",
        "questions-0-private_vote": "",
        "questions-0-immutable_question": "",
    }

    for index, option_text in enumerate(option_texts or []):
        payload[f"questions-0-options-{index}-option_text"] = option_text

    return payload


def test_polls_list(flask_app):
    """Test the polls list route."""
    with flask_app.app_context():
        # Temporary poll rows are needed so the list view can exercise its query and render logic.
        user = create_admin_user()
        poll = Poll(title="Test Poll", poll_expires=datetime.now() + timedelta(days=1))
        db.session.add(poll)
        db.session.flush()

        question = PollQuestion(
            poll_id=poll.id,
            question_text="Favorite color?",
            is_free_response=False,
            allow_multiple_responses=True,
        )
        db.session.add(question)
        db.session.flush()

        option = PollOption(question_id=question.id, option_text="Blue")
        db.session.add(option)
        db.session.flush()

        db.session.add(PollVoter(user_id=user.id, question_id=question.id, option_id=option.id, poll_id=poll.id))
        db.session.commit()

        test_client = flask_app.test_client()
        login_admin(test_client)

        response = test_client.get("/admin/polls/")
        assert response.status_code == 200
    page_text = response.get_data(as_text=True)
    assert "Poll Management" in page_text
    assert "Test Poll" in page_text
    assert "Favorite color?" in page_text
    assert "Blue" in page_text


def test_create_poll_success(flask_app):
    """Test the create poll route with a valid multiple-choice poll."""
    with flask_app.app_context():
        create_admin_user()

        test_client = flask_app.test_client()
        login_admin(test_client)

        future_expires = datetime.now() + timedelta(days=1)
        with test_client:
            response = test_client.post(
                "/admin/create-poll/",
                data=build_create_poll_data(
                    title="Test Poll",
                    question_text="Pick one",
                    option_texts=["Option A", "Option B"],
                    expires=future_expires,
                    allow_multiple=True,
                ),
                follow_redirects=False,
            )

            assert response.status_code == 302
            assert get_flashed_messages() == ["Poll created successfully!"]

        poll = db.session.query(Poll).filter_by(title="Test Poll").one()
        assert poll.poll_expires is not None
        assert len(poll.questions) == 1
        assert poll.questions[0].question_text == "Pick one"
        assert [option.option_text for option in poll.questions[0].options] == ["Option A", "Option B"]


def test_create_poll_validation_failure(flask_app):
    """Test the create poll route when required question fields are missing."""
    with flask_app.app_context():
        create_admin_user()

        test_client = flask_app.test_client()
        login_admin(test_client)

        with test_client:
            response = test_client.post(
                "/admin/create-poll/",
                data={
                    "title": "Invalid Poll",
                    "questions-0-question_text": "",
                },
                follow_redirects=False,
            )

            assert response.status_code == 302
            assert get_flashed_messages() == ["Error in Question Text: This field is required."]
        assert db.session.query(Poll).count() == 0


def test_create_poll_expiration_must_be_future(flask_app):
    """Test that past expiration dates are rejected."""
    with flask_app.app_context():
        create_admin_user()

        test_client = flask_app.test_client()
        login_admin(test_client)

        past_expires = datetime.now() - timedelta(days=1)
        with test_client:
            response = test_client.post(
                "/admin/create-poll/",
                data=build_create_poll_data(
                    title="Expired Poll",
                    question_text="Should fail",
                    option_texts=["Yes"],
                    expires=past_expires,
                ),
                follow_redirects=False,
            )

            assert response.status_code == 302
            assert get_flashed_messages() == ["Poll expiration datetime must be in the future."]
        assert db.session.query(Poll).count() == 0


def test_create_poll_free_response_question(flask_app):
    """Test the free-response branch of poll creation."""
    with flask_app.app_context():
        create_admin_user()

        test_client = flask_app.test_client()
        login_admin(test_client)

        with test_client:
            response = test_client.post(
                "/admin/create-poll/",
                data=build_create_poll_data(
                    title="Free Response Poll",
                    question_text="Share feedback",
                    is_free_response=True,
                ),
                follow_redirects=False,
            )

            assert response.status_code == 302
            assert get_flashed_messages() == ["Poll created successfully!"]

        poll = db.session.query(Poll).filter_by(title="Free Response Poll").one()
        question = poll.questions[0]
        assert question.is_free_response is True
        assert question.allow_multiple_responses is False
        assert question.options == []


def test_delete_poll(flask_app):
    """Test deleting an existing poll."""
    with flask_app.app_context():
        create_admin_user()

        # Temporary poll rows are needed so the delete route can remove a real record.
        poll = Poll(title="Delete Me", poll_expires=datetime.now() + timedelta(days=1))
        db.session.add(poll)
        db.session.commit()

        test_client = flask_app.test_client()
        login_admin(test_client)

        with test_client:
            response = test_client.post(f"/admin/delete-poll/{poll.id}/", follow_redirects=False)

            assert response.status_code == 302
            assert get_flashed_messages() == ["Poll deleted successfully!"]
        assert db.session.get(Poll, poll.id) is None

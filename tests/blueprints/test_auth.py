#!/usr/bin/env python
# tests/blueprints/test_auth.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 6/6/2026

File Purpose: Pytest for the blueprints/auth endpoints.
"""

from flask import current_app

from app.models import Attachments, Attendees, Meetings, Minutes, Users
from tests.conftest import app as flask_app, db  # Import the app fixture for context in tests.

def test_auth_login(flask_app):
    """ Test the /auth/login endpoint. """
    with flask_app.app_context():
        # Test GET request to login page.
        response = flask_app.test_client().get("/login/", follow_redirects=True)
        assert response.status_code == 200
        assert b"Login" in response.data

        # Test POST request with credentials for a user that does not exist.
        response = flask_app.test_client().post("/login/", data={
            "username": "dne",
            "password": "dne"
        }, follow_redirects=True)
        assert response.status_code == 200
        print(response.data)
        assert b"Login attempt failed." in response.data

        # Write test user data.
        from app.models import Users
        user = Users(id=1, username="testuser", role="admin")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

        # Test POST request with invalid credentials.
        response = flask_app.test_client().post("/login/", data={
            "username": "testuser",
            "password": "invalid"
        }, follow_redirects=True)
        assert response.status_code == 200
        print(response.data)
        assert b"Login attempt failed." in response.data

        # Test POST request with valid credentials.
        response = flask_app.test_client().post("/login/", data={
            "username": "testuser",
            "password": "password"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Please enable multi-factor authentication" in response.data

def test_auth_sign_up_get(flask_app):
    """ Test the /auth/sign-up endpoint. """
    with flask_app.app_context():
        # Test GET request to sign-up page.
        response = flask_app.test_client().get("/sign-up/", follow_redirects=True)
        assert response.status_code == 200
        assert b"New Account" in response.data

def test_auth_sign_up_fail_if_duplicate_username(flask_app):
    """ Test the /auth/sign-up endpoint for duplicate username. """
    with flask_app.app_context():
        # Write test user data for duplicate checks.
        user = Users(id=1, username="testuser@example.com", role="user")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
    
        # Test POST request with duplicate username.
        response = flask_app.test_client().post("/sign-up/", data={
            "username": "testuser@example.com",
            "password": "password",
            "confirm_password": "password"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Username already registered." in response.data

def test_auth_sign_up_fail_with_mismatch_passwords(flask_app):
    """ Test the /auth/sign-up endpoint for mismatched passwords. """
    with flask_app.app_context():
        # Test POST request with non-matching passwords.
        response = flask_app.test_client().post("/sign-up/", data={
            "username": "testuser2@example.com",
            "password": "password",
            "confirm_password": "different"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert (b"Passwords must match." in response.data or 
                b"Passwords do not match." in response.data)

def test_auth_sign_up_fail_with_invalid_email_domain(flask_app):
    """ Test the /auth/sign-up endpoint for invalid email domain. """
    with flask_app.app_context():
        # Test POST request with incorrect email domain.
        response = flask_app.test_client().post("/sign-up/", data={
            "username": "testuser2@invalid.com",
            "password": "password",
            "confirm_password": "password"
        }, follow_redirects=True)
        print(flask_app.context["usernames"])

        if b"User creation succeeded." in response.data:
            print("Success")
        print(response.data)
        assert response.status_code == 200
        assert (b"Username must end with example.com." in response.data or
                b"Email must be from the domain example.com" in response.data)
          # Reset for other tests.

def test_auth_sign_up_success(flask_app):
    """ Test the /auth/sign-up endpoint for successful account creation. """
    with flask_app.app_context():
        # Test POST request with valid data.
        response = flask_app.test_client().post("/sign-up/", data={
            "username": "testuser2@example.com",
            "email": "testuser2@example.com",
            "password": "password",
            "confirm_password": "password"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"User creation succeeded." in response.data

def test_auth_logout(flask_app):
    """ Test the /auth/logout endpoint. """
    with flask_app.app_context():
        # Write test user data.
        from app.models import Users
        user = Users(id=1, username="testuser", role="admin", activated=True)
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

        # Log in the test user.
        response = flask_app.test_client().post("/login/", data={
            "username": "testuser",
            "password": "password"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Please enable multi-factor authentication" in response.data

        # Test logout.
        response = flask_app.test_client().get("/logout/", follow_redirects=True)
        assert response.status_code == 200

def test_auth_update_account(flask_app):
    """ Test the /auth/update-account endpoint. """
    with flask_app.app_context():
        # Write test user data.
        user = Users(id=1, username="testuser", role="admin", activated=True)
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

        # Log in the test user.
        response = flask_app.test_client().post("/login/", data={
            "username": "testuser",
            "password": "password"
        }, follow_redirects=True)
        assert response.status_code == 200

        # Test POST request to update account details.
        response = flask_app.test_client().post("/update-account/", data={
            "start_semester": "FA 2023",
            "grad_semester": "SP 2027",
            "password": "newpassword",
        }, follow_redirects=True)
        assert response.status_code == 200
        print(response.data)
        assert b"Account updated successfully." in response.data

        # Verify that the user's account details were updated in the database.
        updated_user = db.session.get(Users, 1)
        assert updated_user.joined == "FA 2023"
        assert updated_user.graduated == "SP 2027"
        assert updated_user.check_password("newpassword")

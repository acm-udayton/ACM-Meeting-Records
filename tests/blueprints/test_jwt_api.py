#!/usr/bin/env python
# tests/blueprints/test_jwt.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 11/1/2026

File Purpose: Pytest for the blueprints/jwt_api endpoints.
"""

from unittest.mock import patch

import pyotp
import pytest
from flask_jwt_extended import decode_token

from app.extensions import db
from app.models import RecoveryCodes, Users
from app.services.jwt_service import authenticate_user

BASE = "/api/v1/jwt"


def make_user(**kwargs):
    user = Users(username="testuser", role="user", activated=True)
    for key, value in kwargs.items():
        setattr(user, key, value)
    user.set_password("password")
    db.session.add(user)
    db.session.commit()
    return user


def login(client, **kwargs):
    return client.post(
        f"{BASE}/login/",
        json={"username": "testuser", "password": "password", **kwargs},
    )


def assert_tokens(response, user):
    assert response.status_code == 200, response.get_data(as_text=True)
    data = response.get_json()
    assert data["user_id"] == user.id
    for key, token_type in (("access_token", "access"), ("refresh_token", "refresh")):
        decoded = decode_token(data[key])
        assert decoded["sub"] == str(user.id)
        assert decoded["type"] == token_type
        assert decoded["username"] == user.username
        assert decoded["role"] == user.role


def test_login_tokens(app):
    user = make_user(role="admin")
    response = login(app.test_client())
    assert_tokens(response, user)
    assert "enable multi-factor" in response.json["flashed_messages"]["danger"][0]


@pytest.mark.parametrize("body", [{}, {"username": "testuser"}, {"username": "x", "password": ""}])
def test_login_invalid_input(app, body):
    response = app.test_client().post(f"{BASE}/login/", json=body)
    assert response.status_code == 422


@pytest.mark.parametrize("failure", ["unknown_user", "wrong_password", "inactive"])
def test_login_failures_do_not_issue_tokens(app, failure):
    make_user(activated=failure != "inactive")
    credentials = {}
    if failure == "unknown_user":
        credentials["username"] = "unknown"
    elif failure == "wrong_password":
        credentials["password"] = "wrong"
    with patch("app.services.jwt_service.create_access_token") as access, patch(
        "app.services.jwt_service.create_refresh_token"
    ) as refresh:
        response = login(app.test_client(), **credentials)
    assert response.status_code == 401
    assert response.json == {
        "error": "Login failed",
        "flashed_messages": {"danger": ["Login attempt failed."]},
    }
    access.assert_not_called()
    refresh.assert_not_called()


def test_totp_login(app):
    user = make_user(mfa_active=True, totp_active=True, totp_secret=pyotp.random_base32())
    client = app.test_client()
    result = authenticate_user("testuser", "password", None)
    assert result.user_id == user.id
    assert result.access_token is result.refresh_token is None
    response = login(client)
    assert response.status_code == 200
    assert response.json == {"redirect_to": f"{BASE}/mfa/verify-totp/"}
    endpoint = response.json["redirect_to"]
    assert client.post(endpoint, json={"token": "bad"}).status_code == 401
    assert_tokens(client.post(endpoint, json={"token": pyotp.TOTP(user.totp_secret).now()}), user)
    with client.session_transaction() as state:
        assert "jwt_mfa_login" not in state
        assert "mfa_user_id" not in state
    assert client.post(endpoint, json={"token": pyotp.TOTP(user.totp_secret).now()}).status_code == 401


def test_recovery_login_consumes_code(app):
    user = make_user(mfa_active=True)
    recovery = RecoveryCodes(user_id=user.id)
    raw_code = recovery.generate_code()
    db.session.add(recovery)
    db.session.commit()
    client = app.test_client()
    endpoint = login(client).json["redirect_to"]
    assert endpoint == f"{BASE}/mfa/verify-recovery-code/"
    assert client.post(endpoint, json={"token": "bad"}).status_code == 401
    assert_tokens(client.post(endpoint, json={"token": raw_code}), user)
    assert db.session.get(RecoveryCodes, recovery.id) is None
    login(client)
    assert client.post(endpoint, json={"token": raw_code}).status_code == 401


@pytest.mark.parametrize("state", ["missing", "expired", "inactive", "disabled", "deleted"])
def test_mfa_rejects_invalid_pending_login(app, state):
    user = make_user(mfa_active=True, totp_active=True, totp_secret=pyotp.random_base32())
    token = pyotp.TOTP(user.totp_secret).now()
    client = app.test_client()
    if state != "missing":
        login(client)
    if state == "expired":
        with client.session_transaction() as pending:
            pending["jwt_mfa_login"] = {"user_id": user.id, "started_at": 0}
    elif state == "inactive":
        user.activated = False
    elif state == "disabled":
        user.mfa_active = False
    elif state == "deleted":
        db.session.delete(user)
    db.session.commit()
    response = client.post(f"{BASE}/mfa/verify-totp/", json={"token": token})
    assert response.status_code == 401
    assert "access_token" not in response.json


def test_failed_new_login_clears_mfa_challenge(app):
    make_user(mfa_active=True)
    client = app.test_client()
    login(client)
    login(client, password="bad")
    with client.session_transaction() as pending:
        assert "jwt_mfa_login" not in pending


def test_csrf_protected_json_login_and_mfa(app):
    app.config["WTF_CSRF_ENABLED"] = True
    user = make_user(mfa_active=True, totp_active=True, totp_secret=pyotp.random_base32())
    client = app.test_client()
    response = login(client)
    assert response.status_code == 400
    assert response.is_json
    csrf = client.get(f"{BASE}/csrf/")
    assert csrf.headers["Cache-Control"] == "no-store"
    headers = {"X-CSRFToken": csrf.json["csrf_token"]}
    response = client.post(
        f"{BASE}/login/", json={"username": "testuser", "password": "password"}, headers=headers
    )
    endpoint = response.json["redirect_to"]
    token = {"token": pyotp.TOTP(user.totp_secret).now()}
    assert client.post(endpoint, json=token).status_code == 400
    assert_tokens(client.post(endpoint, json=token, headers=headers), user)


def test_openapi_contract(app):
    spec = app.test_client().get("/openapi/openapi.json").json
    operation = spec["paths"][f"{BASE}/login/"]["post"]
    assert "application/json" in operation["requestBody"]["content"]
    assert {"200", "400", "401", "422"} <= operation["responses"].keys()
    assert any(param["name"] == "X-CSRFToken" for param in operation["parameters"])
    schemas = spec["components"]["schemas"]
    assert len(schemas["LoginResponse"]["anyOf"]) == 2
    assert schemas["LoginRequest"]["properties"]["password"]["writeOnly"] is True
    for suffix in ("verify-totp/", "verify-recovery-code/"):
        assert f"{BASE}/mfa/{suffix}" in spec["paths"]

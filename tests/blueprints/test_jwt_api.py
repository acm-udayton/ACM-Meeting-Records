#!/usr/bin/env python
# tests/blueprints/test_jwt.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 11/1/2026

File Purpose: Pytest for the blueprints/jwt_api endpoints.
"""

from datetime import timedelta
from unittest.mock import patch

import pyotp
import pytest
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token, jwt_required

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
    result = authenticate_user("testuser", "password", None)
    assert result.user_id == user.id
    assert result.access_token is result.refresh_token is None
    claims = decode_token(result.mfa_token)
    assert claims["type"] == "mfa"
    assert claims["exp"] - claims["iat"] == 300

    response = login(app.test_client())
    assert response.status_code == 200
    assert response.json["redirect_to"] == f"{BASE}/mfa/verify-totp/"
    assert set(response.json) == {"redirect_to", "mfa_token"}
    assert "Set-Cookie" not in response.headers
    endpoint = response.json["redirect_to"]
    # A different client can complete MFA without a login session or CSRF cookie.
    client = app.test_client()
    body = {"mfa_token": response.json["mfa_token"], "token": "bad"}
    assert client.post(endpoint, json=body).status_code == 401
    body["token"] = pyotp.TOTP(user.totp_secret).now()
    assert_tokens(client.post(endpoint, json=body), user)


def test_recovery_login_consumes_code(app):
    user = make_user(mfa_active=True)
    recovery = RecoveryCodes(user_id=user.id)
    raw_code = recovery.generate_code()
    db.session.add(recovery)
    db.session.commit()
    response = login(app.test_client())
    endpoint = response.json["redirect_to"]
    assert endpoint == f"{BASE}/mfa/verify-recovery-code/"
    client = app.test_client()
    body = {"mfa_token": response.json["mfa_token"], "token": "bad"}
    assert client.post(endpoint, json=body).status_code == 401
    body["token"] = raw_code
    assert_tokens(client.post(endpoint, json=body), user)
    assert db.session.get(RecoveryCodes, recovery.id) is None
    assert client.post(endpoint, json=body).status_code == 401


@pytest.mark.parametrize("kind", ["expired", "tampered", "malformed", "access", "refresh"])
def test_invalid_mfa_tokens(app, kind):
    user = make_user(mfa_active=True, totp_active=True, totp_secret=pyotp.random_base32())
    challenge = login(app.test_client()).json["mfa_token"]
    if kind == "expired":
        challenge = create_access_token(
            identity=str(user.id), expires_delta=timedelta(seconds=-1),
            additional_claims={"type": "mfa"},
        )
    elif kind == "tampered":
        header, payload, signature = challenge.split(".")
        signature = ("a" if signature[0] != "a" else "b") + signature[1:]
        challenge = ".".join((header, payload, signature))
    elif kind == "malformed":
        challenge = "invalid"
    elif kind == "access":
        challenge = create_access_token(identity=str(user.id))
    else:
        challenge = create_refresh_token(identity=str(user.id))
    with patch("app.services.jwt_service.issue_login_tokens") as issue:
        response = app.test_client().post(
            f"{BASE}/mfa/verify-totp/",
            json={"mfa_token": challenge, "token": pyotp.TOTP(user.totp_secret).now()},
        )
    assert response.status_code == 401
    issue.assert_not_called()


@pytest.mark.parametrize("state", ["inactive", "disabled", "deleted"])
def test_mfa_rechecks_user(app, state):
    user = make_user(mfa_active=True, totp_active=True, totp_secret=pyotp.random_base32())
    body = {
        "mfa_token": login(app.test_client()).json["mfa_token"],
        "token": pyotp.TOTP(user.totp_secret).now(),
    }
    if state == "inactive":
        user.activated = False
    elif state == "disabled":
        user.mfa_active = False
    else:
        db.session.delete(user)
    db.session.commit()
    response = app.test_client().post(f"{BASE}/mfa/verify-totp/", json=body)
    assert response.status_code == 401
    assert "access_token" not in response.json


@pytest.mark.parametrize("endpoint", ["verify-totp", "verify-recovery-code"])
def test_mfa_requires_challenge(app, endpoint):
    response = app.test_client().post(f"{BASE}/mfa/{endpoint}/", json={"token": "123456"})
    assert response.status_code == 422


def test_mfa_token_cannot_authenticate_protected_routes(app):
    app.add_url_rule("/protected", view_func=jwt_required()(lambda: {"ok": True}), endpoint="protected")
    app.add_url_rule(
        "/refresh-protected", view_func=jwt_required(refresh=True)(lambda: {"ok": True}),
        endpoint="refresh_protected",
    )
    user = make_user(mfa_active=True)
    challenge = login(app.test_client()).json["mfa_token"]
    client = app.test_client()
    for endpoint in ("/protected", "/refresh-protected"):
        response = client.get(endpoint, headers={"Authorization": f"Bearer {challenge}"})
        assert response.status_code in {400, 401, 422}
    # Normal login tokens remain usable by the corresponding decorators.
    for endpoint, encoded in (
        ("/protected", create_access_token(identity=str(user.id))),
        ("/refresh-protected", create_refresh_token(identity=str(user.id))),
    ):
        assert client.get(endpoint, headers={"Authorization": f"Bearer {encoded}"}).status_code == 200


def test_stateless_login_and_mfa_with_global_csrf_enabled(app):
    app.config["WTF_CSRF_ENABLED"] = True
    user = make_user(mfa_active=True, totp_active=True, totp_secret=pyotp.random_base32())
    response = login(app.test_client())
    assert response.status_code == 200
    result = app.test_client().post(
        response.json["redirect_to"],
        json={"mfa_token": response.json["mfa_token"], "token": pyotp.TOTP(user.totp_secret).now()},
    )
    assert_tokens(result, user)
    assert "Set-Cookie" not in result.headers
    # Browser form routes still require CSRF.
    assert app.test_client().post("/login/", data={"username": "testuser", "password": "password"}).status_code == 400


def test_openapi_contract(app):
    spec = app.test_client().get("/openapi/openapi.json").json
    operation = spec["paths"][f"{BASE}/login/"]["post"]
    assert "application/json" in operation["requestBody"]["content"]
    assert {"200", "401", "422"} <= operation["responses"].keys()
    assert not operation.get("parameters")
    schemas = spec["components"]["schemas"]
    assert len(schemas["LoginResponse"]["anyOf"]) == 2
    assert schemas["LoginRequest"]["properties"]["password"]["writeOnly"] is True
    assert "mfa_token" in schemas["MFARequest"]["required"]
    assert "mfa_token" in schemas["MFAResponse"]["required"]
    assert f"{BASE}/csrf/" not in spec["paths"]
    for suffix in ("verify-totp/", "verify-recovery-code/"):
        assert f"{BASE}/mfa/{suffix}" in spec["paths"]


def test_refresh_returns_access_token(app):
    user = make_user()
    client = app.test_client()
    tokens = login(client).json
    response = client.post(
        f"{BASE}/refresh",
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )
    assert response.status_code == 200
    assert set(response.json) == {"access_token"}
    assert response.json["access_token"] != tokens["access_token"]
    claims = decode_token(response.json["access_token"])
    assert claims["sub"] == str(user.id)
    assert claims["type"] == "access"


@pytest.mark.parametrize("state", ["inactive", "deleted"])
def test_refresh_rechecks_user(app, state):
    user = make_user()
    client = app.test_client()
    refresh_token = login(client).json["refresh_token"]
    if state == "inactive":
        user.activated = False
    else:
        db.session.delete(user)
    db.session.commit()
    with patch("app.services.jwt_service.create_access_token") as issue:
        response = client.post(
            f"{BASE}/refresh", headers={"Authorization": f"Bearer {refresh_token}"}
        )
    assert response.status_code == 401
    assert response.json["error"] == "Login failed"
    issue.assert_not_called()


def test_admin_protected_route(app):
    make_user(role="admin")
    client = app.test_client()
    token = login(client).json["access_token"]
    response = client.get(f"{BASE}/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json == {"message": "Access granted to protected route."}


def test_admin_protected_route_forbids_non_admin(app):
    make_user(role="user")
    client = app.test_client()
    token = login(client).json["access_token"]
    response = client.get(f"{BASE}/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json["error"] == "Admin access required"


def test_admin_protected_route_requires_header(app):
    response = app.test_client().get(f"{BASE}/protected")
    assert response.status_code == 401
    assert response.json["msg"] == "Missing Authorization Header"


def test_admin_protected_route_rejects_expired_token(app):
    user = make_user(role="admin")
    token = create_access_token(identity=str(user.id), expires_delta=timedelta(seconds=-1))
    response = app.test_client().get(
        f"{BASE}/protected", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.json["msg"] == "Token has expired"


@pytest.mark.parametrize("recovery", [False, True])
def test_mfa_bearer_authorization(app, recovery):
    user = make_user(mfa_active=True, totp_active=True, totp_secret=pyotp.random_base32())
    if recovery:
        entry = RecoveryCodes(user_id=user.id)
        code = entry.generate_code()
        db.session.add(entry)
        db.session.commit()
        endpoint = f"{BASE}/mfa/verify-recovery-code/"
    else:
        code = pyotp.TOTP(user.totp_secret).now()
        endpoint = f"{BASE}/mfa/verify-totp/"
    mfa_token = login(app.test_client()).json["mfa_token"]
    response = app.test_client().post(
        endpoint, json={"token": code},
        headers={"Authorization": f"Bearer {mfa_token}"},
    )
    assert_tokens(response, user)


@pytest.mark.parametrize("kind", ["access", "refresh", "malformed"])
def test_mfa_rejects_wrong_authorization_even_with_valid_body(app, kind):
    user = make_user(mfa_active=True, totp_active=True, totp_secret=pyotp.random_base32())
    mfa_token = login(app.test_client()).json["mfa_token"]
    if kind == "malformed":
        authorization = "Basic invalid"
    else:
        create = create_access_token if kind == "access" else create_refresh_token
        authorization = f"Bearer {create(identity=str(user.id))}"
    response = app.test_client().post(
        f"{BASE}/mfa/verify-totp/",
        json={"token": pyotp.TOTP(user.totp_secret).now(), "mfa_token": mfa_token},
        headers={"Authorization": authorization},
    )
    assert response.status_code == 401

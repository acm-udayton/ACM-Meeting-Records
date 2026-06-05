#!/usr/bin/env python
# tests/conftest.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 6/3/2026

File Purpose: Pytest configuration file with fixtures for the application.
"""

import pytest
from app import create_app

@pytest.fixture
def app():
    """ Create and configure a new app instance for each test. """
    flask_app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', # Use in-memory database for tests.
            'WTF_CSRF_ENABLED': False,  # Disable CSRF for tests.
        })
    yield flask_app

@pytest.fixture
def client(flask_app):
    """ A test client for the app. """
    return flask_app.test_client()

@pytest.fixture
def runner(flask_app):
    """ A test runner for the app's Click commands, if needed. """
    return flask_app.test_cli_runner()

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
    app = create_app()
    app.config['TESTING'] = True

    yield app

@pytest.fixture
def client(app):
    """ A test client for the app. """
    return app.test_client()

@pytest.fixture
def runner(app):
    """ A test runner for the app's Click commands, if needed. """
    return app.test_cli_runner()

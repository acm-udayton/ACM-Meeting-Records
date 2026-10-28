#!/usr/bin/env python
# app/blueprints/jwt/routes.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 10/28/2026

File Purpose: JWT authentication routes for the project.
"""

# Third-party imports.
from flask import Blueprint

jwt_bp = Blueprint("jwt", __name__)
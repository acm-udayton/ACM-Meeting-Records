#!/usr/bin/env python
# app/extensions.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 10/7/2025

File Purpose: Load extensions for the project.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Initialize the app extensions.
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

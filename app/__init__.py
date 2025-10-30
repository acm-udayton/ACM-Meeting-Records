#!/usr/bin/env python
# app/__init__.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 10/7/2025

File Purpose: Application factory for the project.
"""

# Standard library imports.
from functools import wraps
import logging
import os

# Third-party imports.
from dotenv import load_dotenv
from flask import Flask, render_template, abort, redirect, url_for
from flask_login import current_user

# Local application imports.
from .extensions import db, login_manager, migrate

def admin_required(f):
    """ Route decorator to restrict page access to admin users. """
    @wraps(f)
    def decorated_admin_required(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("home"))
        if current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated_admin_required

def datetime_format(value):
    """Format a datetime object in a Jinja template to a custom string."""
    time_format = "%d/%m/%Y %I:%M %p"
    if value is None:
        return "" # Handle None values gracefully
    return value.strftime(time_format)


def configure_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
)

def register_error_handlers(app):
    """ Register Flask Error Handling. """
    @app.errorhandler(401)
    def authentication_required(e):
        """ Handle HTTP 401. """
        app.logger.error(e)
        return render_template(
            "error.html",
            page_title = "401 Error",
            error_message = "Requests to this page require authentication."
        )

    @app.errorhandler(403)
    def forbidden(e):
        """ Handle HTTP 403. """
        app.logger.error(e)
        return render_template(
            "error.html",
            page_title = "403 Error",
            error_message = "Request forbidden due to insufficient authorization."
        )

    @app.errorhandler(404)
    def page_not_found(e):
        """ Handle HTTP 404. """
        app.logger.error(e)
        return render_template(
            "error.html",
            page_title = "404 Error",
            error_message = "Request failed because page could not be found."
        )

    @app.errorhandler(405)
    def method_not_allowed(e):
        """ Handle HTTP 405. """
        app.logger.error(e)
        return render_template(
            "error.html",
            page_title = "405 Error",
            error_message = "Request method not allowed."
        )

def create_app():
    """ Create and configure the Flask app. """
    # Load .env variables.
    load_dotenv()

    # Start logging setup.
    configure_logging()

    # Create the Flask app.
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER")
    app.config["TOTP_ISSUER_NAME"] = f"Meeting Records - {os.getenv('ORGANIZATION_NAME')}"

    # Initialize the app extensions.
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Configure Flask-Login.
    from .models import Users  # pylint: disable=import-outside-toplevel
    @login_manager.user_loader
    def loader_user(user_id):
        """ Flask-Login login manager in combination with Flask-SQL-Alchemy. """
        return db.session.get(Users, user_id)

    # Define the app variables.
    app.context = {}
    app.logs = {}
    app.context["socials"] = {
                                "linkedin": os.getenv("LINKEDIN_URL"),
                                "instagram": os.getenv("INSTAGRAM_URL"),
                                "github": os.getenv("GITHUB_URL")
                            }
    app.context["details"] = {
                                "location": os.getenv("MEETING_LOCATION"),
                                "email": os.getenv("CONTACT_EMAIL"),
                                "organization": os.getenv("ORGANIZATION_NAME")
                            }
    app.context["usernames"] = {
                                "enforce_usernames": os.getenv("ENFORCE_USERNAMES"),
                                "username_email_domain": os.getenv("USERNAME_EMAIL_DOMAIN")
                            }
    app.context["source"] = os.getenv("GITHUB_SOURCE")
    app.logs["error"] = os.getenv("ERROR_LOG_PATH")
    app.logs["login"] = os.getenv("LOGIN_LOG_PATH")
    app.logs["full"] = os.getenv("FULL_LOG_PATH")
    app.base_url = os.getenv("BASE_URL")
    app.storage = os.getenv("STORE_PATH")

    # Define the app context processor.
    @app.context_processor
    def app_context():
        """ Set application-wide data values for jinja templates. """
        context = dict(
                        github_url = app.context["source"],
                        social_linkedin = app.context["socials"]["linkedin"],
                        social_instagram = app.context["socials"]["instagram"],
                        social_github = app.context["socials"]["github"],
                        contact_location = app.context["details"]["location"],
                        contact_email = app.context["details"]["email"],
                        organization_name = app.context["details"]["organization"],
                        current_user = current_user,
                        )
        return context

    # Initialize the database.
    with app.app_context():
        db.create_all()

    # Add custom Jinja filters.
    app.jinja_env.filters['datetime_format'] = datetime_format

    # Register the error handlers.
    register_error_handlers(app)

    # Register the blueprints.
    from .blueprints.admin import admin_bp
    from .blueprints.auth import auth_bp
    from .blueprints.main import main_bp
    from .blueprints.api import api_bp
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app

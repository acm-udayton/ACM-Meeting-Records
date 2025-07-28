#!/usr/bin/env python

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 7/26/2025

File Purpose: Implement the webserver for the project.
"""

# Standard library imports.
import datetime
from functools import wraps
import logging
import logging.config
import os
import re

# Third-party imports.
from dotenv import load_dotenv
from flask import abort, flash, Flask, jsonify, redirect, render_template, request, url_for
from flask_login import (
    current_user,
    LoginManager,
    login_required,
    login_user,
    logout_user,
    UserMixin
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc

# Local application imports.
from utils import sha_hash, generate_meeting_code, get_logger_config

def admin_required(f):
    """ Route decorator to restrict page access to admin users. """
    @wraps(f)
    def decorated_admin_required(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("home"))
        if current_user.role not in app.context["officers"].keys():
            abort(403)
        return f(*args, **kwargs)
    return decorated_admin_required

# Configure logging.
logging.config.dictConfig(get_logger_config())
user_logger = logging.getLogger("user_logger")
app_logger = logging.getLogger("werkzeug") # Flask's default logger

app = Flask(__name__)
load_dotenv() # Load the .env file's contents as environment variables.

# Configure flask-sqlalchemy.
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
db = SQLAlchemy()
db.init_app(app)

# Configure flask-login.
login_manager = LoginManager()
login_manager.init_app(app)


# Define the app database.
class Users(UserMixin, db.Model):
    """ Store all Users in the database. """
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(250), unique = True, nullable = False)
    password = db.Column(db.String(64), nullable = False)
    role = db.Column(db.String(64), nullable = False)
    joined = db.Column(db.String(7), nullable = True) # Store FA|SP YYYY
    graduated = db.Column(db.String(7), nullable = True) # Store FA|SP YYYY

    def to_dict(self):
        """ Get user data values as a dictionary. """
        return {"id": self.id,
                "username": self.username,
                "password": self.password,
                "role": self.role,
                "joined": self.joined,
                "graduated": self.graduated}

class Meetings(db.Model):
    """ Store a list of meetings. """
    id = db.Column(db.Integer, primary_key = True, nullable = False)
    state = db.Column(db.String(250), nullable = False)
    title = db.Column(db.String(250), nullable = False)
    description = db.Column(db.String(250), nullable = False)
    host = db.Column(db.String(250), nullable = False)
    event_start = db.Column(db.DateTime, nullable = True)
    event_end = db.Column(db.DateTime, nullable = True)
    code_hash = db.Column(db.String(250), nullable = True)

    def to_dict(self):
        """ Get meeting data values as a dictionary. """
        return {"id": self.id,
                "state": self.state,
                "title": self.title,
                "description": self.description,
                "host": self.host,
                "event_start": self.event_start,
                "event_end": self.event_end,
                "code_hash": self.code_hash}

class Attendees(db.Model):
    """ Store a list of meeting attendees. """
    id = db.Column(db.Integer, primary_key = True, nullable = False)
    username = db.Column(db.String(250), nullable = False)
    meeting = db.Column(db.Integer, nullable = False)

    def to_dict(self):
        """ Get attendee data values as a dictionary. """
        return {"id": self.id,
                "username": self.username,
                "meeting": self.meeting}

class Minutes(db.Model):
    """ Store a list of meeting minutes. """
    id = db.Column(db.Integer, primary_key = True, nullable = False)
    notes = db.Column(db.Text, nullable = False)
    username_by = db.Column(db.String(250), nullable = False)
    meeting = db.Column(db.Integer, nullable = False)

    def to_dict(self):
        """ Get meeting minute data values as a dictionary. """
        return {"id": self.id,
                "notes": self.notes,
                "username_by": self.username_by,
                "meeting": self.meeting}

with app.app_context():
    db.create_all()

# Define the app variables.
app.context = {}
app.logs = {}
app.context["socials"] = {
                            "linkedin": os.getenv("LINKEDIN_URL"),
                            "instagram": os.getenv("INSTAGRAM_URL"),
                            "github": os.getenv("GITHUB_URL")
                        }
app.context["details"] = {"location": os.getenv("MEETING_LOCATION"),
                            "email": os.getenv("CONTACT_EMAIL")
                        }
app.context["officers"] = {"admin": [os.getenv("ADMIN_USERNAME"), os.getenv("ADMIN_PASSWORD")],
                            "secretary": [
                                os.getenv("SECRETARY_USERNAME"),
                                os.getenv("SECRETARY_PASSWORD")
                            ]
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
                    current_user = current_user,
                    )
    return context

@login_manager.user_loader
def loader_user(user_id):
    """ Flask-Login login manager in combination with Flask-SQL-Alchemy. """
    return db.session.get(Users, user_id)

# Authentication routes.
@app.route("/login/", methods = ["GET", "POST"])
def login():
    """ Show a login page and process submissions. """
    if request.method =="POST":
        user = Users.query.filter_by(username = request.form["username"]).first()
        if user is not None:
            user_logger.info(
                "Login attempt as %s from IP %s - success",
                request.form["username"],
                request.remote_addr
            )
            if user.password == sha_hash(request.form["password"]):
                login_user(user)
            else:
                user_logger.warning(
                    "Login attempt as %s from IP %s - failed",
                    request.form["username"],
                    request.remote_addr
                )
                flash(
                    "Login attempt failed. Please try again or contact "
                    "the system administrator to reset your credentials."
                )
                return redirect(url_for("login"))
        elif (
            request.form["username"] == app.context["officers"]["admin"][0]
            and sha_hash(request.form["password"]) == app.context["officers"]["admin"][1]
        ):
            # User is a new admin.
            user = Users(
                username = app.context["officers"]["admin"][0],
                password = app.context["officers"]["admin"][1],
                role = "admin"
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
        elif (
            request.form["username"] == app.context["officers"]["secretary"][0]
            and sha_hash(request.form["password"]) == app.context["officers"]["secretary"][1]
        ):
            # User is a new secretary.
            user = Users(
                username = app.context["officers"]["secretary"][0],
                password = app.context["officers"]["secretary"][1],
                role = "secretary"
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
        else:
            flash("Login attempt failed. User does not exist.")
            return redirect(url_for("login"))
        return redirect(url_for("home"))
    else:
        return render_template("login.html", page_title = "User Log In")

@app.route("/sign-up/", methods = ["GET", "POST"])
def sign_up():
    """ Show a sign-up page and process submissions. """
    if request.method == "POST":
        # Log the user out if active.
        if not current_user.is_anonymous:
            logout_user()
        uname = request.form["username"]
        pword = request.form["password"]
        conf_pword = request.form["confirm_password"]
        # Handle new username and password issues or create the new user.
        if Users.query.filter_by(username = uname).first() is not None:
            flash(
                "User creation failed. Username already registered. "
                "Try logging in instead or contact an administrator.")
            return redirect(url_for("sign_up"))
        elif pword != conf_pword:
            flash("User creation failed. Passwords do not match.")
            return redirect(url_for("sign_up"))
        else:
            user_logger.warning(
                "New user %s from IP %s with password %s",
                uname,
                request.remote_addr,
                sha_hash(pword)
            )
            new_user = Users(username = uname,
                             password = sha_hash(pword),
                             role = "user")
            db.session.add(new_user)
            db.session.commit()
            flash("User creation succeeded. You can now log into your new account.")
            return redirect(url_for("login"))
    # Handle GET requests.
    else:
        return render_template("sign_up.html", page_title = "Create New Account")

@app.route("/logout/")
@login_required
def logout():
    """ Logout the user and redirect home. """
    logout_user()
    return redirect(url_for("home"))


# Account management routes.
@app.route("/my-account/")
@login_required
def my_account():
    """ Show account details page with update form. """
    return render_template("account.html", page_title = "My Account")

@app.route("/update-account/", methods = ["POST"])
def update_account():
    """ Update account details via the form /my-account/ page. """
    user_logger.info(
        "Account update attempt: %s from IP %s - success with password %s, start semester %s, end semester %s",
        request.form["username"],
        request.remote_addr,
        sha_hash(request.form["password"]),
        request.form["start_semester"],
        request.form["grad_semester"]
    )
    update_user = db.session.get(Users, current_user.get_id())
    form_password = request.form["password"].strip()
    if form_password != "":
        update_user.password = sha_hash(form_password)
    semester_regex = re.compile(r"^(FA|SP) \d{4}$|^$")
    # Validate start semester.
    form_start = request.form["start_semester"].strip().upper()
    if not semester_regex.fullmatch(form_start):
        flash(
            'Invalid format for Start Semester. Use "FA YYYY" or '
            '"SP YYYY" or leave it empty.', 'error'
        )
    else:
        update_user.joined = form_start

    # Validate graduation semester.
    form_grad = request.form["grad_semester"].strip().upper()
    if not semester_regex.fullmatch(form_grad):
        flash(
            'Invalid format for Graduation Semester. Use "FA YYYY" or '
            '"SP YYYY" or leave it empty.', 'error'
        )
    else:
        update_user.graduated = form_grad
    # Update database and redirect.
    db.session.commit()
    return redirect(url_for("my_account"))


# Public web routes.
@app.route("/")
def home():
    """ Show the home page. """
    recent_meetings = Meetings.query.order_by(desc(Meetings.id)).limit(4).all()
    if len(recent_meetings) != 0:
        featured_meeting = recent_meetings.pop(0)
    else:
        featured_meeting = None
    return render_template(
        "index.html",
        page_title = "Home",
        recent_meetings = recent_meetings,
        featured_meeting = featured_meeting
    )

@app.route("/events/")
def events_list():
    """ Show the event list page. """
    all_meetings = Meetings.query.all()
    print(all_meetings)
    return render_template("events.html", page_title = "Meetings", meetings = all_meetings)

@app.route("/event/<int:meeting_id>/")
def user_event(meeting_id):
    """ Show a page with the details of a single meeting. """
    meeting = Meetings.query.filter_by(id = meeting_id).first_or_404()
    attendees = Attendees.query.filter_by(meeting = meeting_id).all()
    minutes = Minutes.query.filter_by(meeting = meeting_id).all()
    return render_template(
        "event.html",
        page_title = f"Meeting - {meeting.title}",
        meeting = meeting,
        all_minutes = minutes,
        all_attendees = attendees
    )


# Admin web routes.
@app.route("/admin/dashboard/<int:meeting_id>/")
@login_required
@admin_required
def admin_dashboard(meeting_id):
    """ Show the administrator dashboard page for a single meeting. """
    meeting = Meetings.query.filter_by(id = meeting_id).first_or_404()
    attendees = Attendees.query.filter_by(meeting = meeting_id).all()
    minutes = Minutes.query.filter_by(meeting = meeting_id).all()
    return render_template(
        "admin/dashboard.html",
        page_title = f"Meeting - {meeting.title}",
        meeting = meeting,
        attendees = attendees,
        minutes = minutes
    )

@app.route("/admin/create/", methods = ["POST"])
@login_required
@admin_required
def event_create():
    """ Create a new meeting based from form inputs. """
    meeting_title = request.form["meeting_title"]
    meeting_description = request.form["meeting_description"]
    meeting = Meetings(state = "not started",
                        title = meeting_title,
                        description = meeting_description,
                        host = f"{current_user.username} - ACM at UDayton",
                        code_hash = None)
    db.session.add(meeting)
    db.session.commit()
    return redirect(url_for("admin_dashboard", meeting_id = meeting.id))

@app.route("/admin/start/<int:meeting_id>/", methods = ["POST"])
@login_required
@admin_required
def event_start(meeting_id):
    """ Start a single meeting from the administrator dashboard. """
    if current_user.role not in app.context["officers"].keys():
        # User is not an officer, so prevent access.
        abort(403)
    else:
        # Mark the meeting as "active".
        meeting = Meetings.query.filter_by(id = meeting_id).first_or_404()
        if meeting.state == "not started":
            meeting_code = generate_meeting_code()
            meeting.code_hash = sha_hash(meeting_code)
            meeting.state = "active"
            meeting.event_start = datetime.datetime.now()
            # Add the user (officer) as an attendee.
            attendance = Attendees(username = current_user.username, meeting = meeting_id)
            db.session.add(attendance)
            db.session.commit()
            return_data = {
                "success": True,
                "meeting_id": meeting_id,
                "message": "Meeting started successfully.",
                "meeting_code": meeting_code
            }
            return jsonify(return_data), 200
        else:
            # Meeting cannot be activated.
            return_data = {
                "success": False,
                "meeting_id": meeting_id,
                "message": f"Meeting could not be started because it is already {meeting.state}."
            }
            return jsonify(return_data), 400

@app.route("/admin/reset-code/<int:meeting_id>/")
@login_required
@admin_required
def reset_code(meeting_id):
    """ Reset the meeting join code for a single meeting. """
    if current_user.role not in app.context["officers"].keys():
        # User is not an officer, so prevent access.
        abort(403)
    else:
        # Mark the meeting as "active".
        meeting = Meetings.query.filter_by(id = meeting_id).first_or_404()
        if meeting.state == "active":
            meeting_code = generate_meeting_code()
            meeting.code_hash = sha_hash(meeting_code)
            # Add the user (officer) as an attendee.
            db.session.commit()
            return redirect(f"/admin/show-code?code = {meeting_code}")
        else:
            # Meeting cannot be activated.
            return render_template(
                "error.html",
                page_title = "400 Error",
                error_message = "This meeting is not active."
            )

@app.route("/admin/show-code/")
@login_required
@admin_required
def show_code():
    """ Show the meeting join code for a single meeting. """
    code = request.args.get("code")
    if code is not None:
        return render_template(
            "code.html",
            page_title = "Meeting Code",
            code = code
        )
    else:
        abort(404)

@app.route("/admin/end/<int:meeting_id>/", methods = ["POST"])
@login_required
@admin_required
def event_end(meeting_id):
    """ End a single meeting from the administrator dashboard. """
    if current_user.role not in app.context["officers"].keys():
        # User is not an officer, so prevent access.
        abort(403)
    else:
        # Mark the meeting as "ended".
        meeting = Meetings.query.filter_by(id = meeting_id).first_or_404()
        if meeting.state == "active":
            meeting.state = "ended"
            meeting.event_end = datetime.datetime.now()
            db.session.commit()
            return_data = {
                "success": True,
                "meeting_id": meeting_id,
                "message": "Meeting ended successfully."
            }
            return jsonify(return_data), 200
        else:
            # Meeting cannot be ended.
            return_data = {
                "success": False,
                "meeting_id": meeting_id,
                "message": f"Meeting could not be ended because it is currently {meeting.state}."
            }
            return return_data, 400

@app.route("/admin/attendees/<int:meeting_id>/", methods = ["POST"])
@login_required
@admin_required
def event_attendees(meeting_id):
    """ Add an attendee to a single meeting from the administrator dashboard. """
    if Meetings.query.filter_by(id = meeting_id).first() is not None:
        # Handle minutes submission.
        attendee_username = request.form["attendee_username"]
        if Users.query.filter_by(username = attendee_username).first() is not None:
            if Attendees.query.filter_by(
                meeting = meeting_id,
                username = attendee_username
            ).first() is None:
                attendee = Attendees(meeting = meeting_id, username = attendee_username)
                db.session.add(attendee)
                db.session.commit()
                return_data = {
                    "success": True,
                    "meeting_id": meeting_id,
                    "message": f"Attendee {attendee_username} checked in successfully."
                }
                return jsonify(return_data), 201
            else:
                return_data = {
                    "success": False,
                    "meeting_id": meeting_id,
                    "message": f"Attendee {attendee_username} is already checked in."
                }
                return jsonify(return_data), 400
        else:
            return_data = {
                "success": False,
                "meeting_id": meeting_id,
                "message": f"Attendee {attendee_username} does not exist."
            }
            return jsonify(return_data), 400
    else:
        # Meeting does not exist.
        return_data = {
            "success": False,
            "meeting_id": meeting_id,
            "message": "Specified meeting does not exist."
        }
        return jsonify(return_data), 400

@app.route("/admin/minutes/<int:meeting_id>/", methods = ["POST"])
@app.route("/admin/minutes/<int:meeting_id>/<int:minutes_id>/", methods = ["POST"])
@login_required
@admin_required
def event_minutes(meeting_id, minutes_id = None):
    """ Add minutes for a single meeting from the administrator dashboard. """
    if Meetings.query.filter_by(id = meeting_id).first() is not None:
        # Handle minutes submission.
        meeting_minutes = request.form["meeting_minutes"]
        if minutes_id is not None:
            minutes_entry = Minutes.query.filter_by(
                id = minutes_id,
                meeting = meeting_id
            ).first()
            if minutes_entry is not None:
                if current_user.username not in minutes_entry.username_by:
                    minutes_entry.username_by += f", {current_user.username}"
                minutes_entry.notes = meeting_minutes
                db.session.commit()
                return_data = {
                    "success": True,
                    "meeting_id": meeting_id,
                    "minutes_id":minutes_id,
                    "message": "Meeting minutes saved successfully."
                }
                return jsonify(return_data), 201

            else:
                return_data = {
                    "success": False,
                    "meeting_id": meeting_id,
                    "message": "Meeting minutes could not be updated due to minutes entry."
                }
                return jsonify(return_data), 400
        else:
            minutes = Minutes(
                meeting = meeting_id,
                username_by = current_user.username,
                notes = meeting_minutes
            )
            db.session.add(minutes)
            db.session.commit()
            return_data = {
                "success": True,
                "meeting_id": meeting_id,
                "minutes_id":minutes.id,
                "message": "Meeting minutes saved successfully."
            }
            return jsonify(return_data), 201
    else:
        # Meeting does not exist.
        return_data = {
            "success": False,
            "meeting_id": meeting_id,
            "message": "Specified meeting does not exist."
        }
        return jsonify(return_data), 400


# Public routing.
@app.route("/event/check-in/<int:meeting_id>/", methods = ["POST"])
@login_required
def event_check_in(meeting_id):
    """ Check into a single meeting from the homepage. """
    if Meetings.query.filter_by(id = meeting_id).first() is not None:
        code = request.form["meeting_code"]
        meeting = Meetings.query.filter_by(id = meeting_id).first_or_404()
        if Attendees.query.filter_by(meeting=meeting_id).first() is not None:
            if meeting.state == "active":
                if sha_hash(code) == meeting.code_hash:
                    # Meeting active, add the user as an attendee.
                    attendance = Attendees(username = current_user.username, meeting = meeting_id)
                    db.session.add(attendance)
                    db.session.commit()
                    flash("Check-in succeeded. Attendance updated successfully.")
                else:
                    # Invalid meeting code.
                    flash("Check-in failed. Meeting code is invalid.")
            else:
                # Already an attendee.
                flash("Check-in failed. You are already marked as an attendee.")
        else:
            # Meeting inactive, return an error message.
            flash("Check-in failed. Specified meeting is inactive.")
    else:
        # Meeting does not exist.
        flash("Check-in failed. Specified meeting does not exist.")
    return redirect(url_for("home"))

# API Routing.
@app.route("/api/event/attendees/<int:meeting_id>/")
def api_event_attendees(meeting_id):
    """ Get attendee list for a single meeting. """
    attendees = Attendees.query.filter_by(meeting = meeting_id).all()
    attendees_data = [attendee.to_dict() for attendee in attendees]
    return jsonify(attendees_data), 200

@app.route("/api/event/notes/<int:meeting_id>/")
def api_event_minutes(meeting_id):
    """ Get minutes for a single meeting. """
    minutes = Minutes.query.filter_by(meeting = meeting_id).all()
    minutes_data = [minute.to_dict() for minute in minutes]
    return jsonify(minutes_data), 200

@app.route("/api/event/state/<int:meeting_id>/")
def api_event_state(meeting_id):
    """ Get current state of a single meeting. """
    meeting = Meetings.query.filter_by(id = meeting_id).first_or_404()
    return jsonify(meeting.state.title()), 200


# Error Handling
@app.errorhandler(401)
def authentication_required(e):
    """ Handle HTTP 401. """
    app_logger.error(e)
    return render_template(
        "error.html",
        page_title = "401 Error",
        error_message = "Requests to this page require authentication."
    )

@app.errorhandler(403)
def forbidden(e):
    """ Handle HTTP 403. """
    app_logger.error(e)
    return render_template(
        "error.html",
        page_title = "403 Error",
        error_message = "Request forbidden due to insufficient authorization."
    )

@app.errorhandler(404)
def page_not_found(e):
    """ Handle HTTP 404. """
    app_logger.error(e)
    return render_template(
        "error.html",
        page_title = "404 Error",
        error_message = "Request failed because page could not be found."
    )

@app.errorhandler(405)
def method_not_allowed(e):
    """ Handle HTTP 405. """
    app_logger.error(e)
    return render_template(
        "error.html",
        page_title = "405 Error",
        error_message = "Request method not allowed."
    )

if __name__ == "__main__":
    # Run the application.
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for static files
    app.run(debug = True)

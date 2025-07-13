#!/usr/bin/env python

"""
Project Name: AttendanceTaker
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 6/7/2025

File Purpose: Implement the webserver for the project.
"""

import datetime 
import os

from dotenv import load_dotenv
from flask import Flask, abort, jsonify, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

from utils import sha_hash

def admin_required(f):
    @wraps(f)
    def decorated_admin_required(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("home"))
        if current_user.role not in app.context["officers"].keys():
            abort(403)
        return f(*args, **kwargs)
    return decorated_admin_required


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
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique = True, nullable = False)
    password = db.Column(db.String(64), nullable = False)
    role = db.Column(db.String(64), nullable = False)

class Meetings(db.Model):
    """ Store a list of meetings. """
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    state = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    host = db.Column(db.String(250), nullable=False)
    event_start = db.Column(db.DateTime, nullable=True)
    event_end = db.Column(db.DateTime, nullable=True)
    code_hash = db.Column(db.String(250), nullable=True)

class Attendees(db.Model):
    """ Store a list of meeting attendees. """
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String(250), nullable=False)
    meeting = db.Column(db.Integer, nullable=False)
    
class Minutes(db.Model):
    """ Store a list of meeting minutes. """
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    notes = db.Column(db.Text, nullable=False)
    username_by = db.Column(db.String(250), nullable=False)
    meeting = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()

# Define the app variables.
app.context = {}
app.logs = {}
app.context["socials"] = {"linkedin": os.getenv("LINKEDIN_URL"), 
                          "instagram": os.getenv("INSTAGRAM_URL"),
                          "github": os.getenv("GITHUB_URL"),}
app.context["details"] = {"location": os.getenv("MEETING_LOCATION"),
                          "email": os.getenv("CONTACT_EMAIL"),}
app.context["officers"] = {"admin": [os.getenv("ADMIN_USERNAME"), os.getenv("ADMIN_PASSWORD")],
                           "secretary": [os.getenv("SECRETARY_USERNAME"),os.getenv("SECRETARY_PASSWORD")]}
app.context["source"] = os.getenv("GITHUB_SOURCE")
app.logs["error"] = os.getenv("ERROR_LOG_PATH")
app.logs["login"] = os.getenv("LOGIN_LOG_PATH")
app.logs["full"] = os.getenv("FULL_LOG_PATH")
app.base_url = os.getenv("BASE_URL")
app.storage = os.getenv("STORE_PATH")

# Define the app context processor.
@app.context_processor
def app_context():
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

# User management routes.
@login_manager.user_loader
def loader_user(user_id):
    """ Flask-Login login manager in combination with Flask-SQL-Alchemy """
    return Users.query.get(user_id)

@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method=="POST":
        """ Authenticate. """
        user = Users.query.filter_by(username=request.form["username"]).first()
        if user != None:
            if user.password == sha_hash(request.form["password"]):
                login_user(user)
                print("MEMBER")
        elif request.form["username"] == app.context["officers"]["admin"][0] and sha_hash(request.form["password"]) == app.context["officers"]["admin"][1]:
            # User is a new admin.
            user = Users(username=app.context["officers"]["admin"][0], password = app.context["officers"]["admin"][1], role="admin")
            db.session.add(user)
            db.session.commit()
            login_user(user)
            print("ADMIN")
        elif request.form["username"] == app.context["officers"]["secretary"][0] and sha_hash(request.form["password"]) == app.context["officers"]["secretary"][1]:
            # User is a new secretary.
            user = Users(username=app.context["officers"]["secretary"][0], password = app.context["officers"]["secretary"][1], role="secretary")
            db.session.add(user)
            db.session.commit()
            login_user(user)
            print("SECRETARY")
        else:
            print("FAILED")
            print(request.form["password"])
        return redirect(url_for("home"))
    else:
        return render_template("login.html", page_title="User Log In")

@app.route("/create-account")
def create_account():
    if not current_user.is_anonymous:
        logout_user()

@app.route("/logout")
@login_required
def logout():
    """ De-authenticate. """
    logout_user()
    return redirect(url_for("home"))

@app.route("/")
def home():
    return render_template("base.html", page_title="Home")


@app.route("/events/")
def events_list():
    return render_template("events.html")

@app.route("/event/<int:meeting_id>")
@login_required
def user_event(meeting):
    return render_template("event.html")

@app.route("/event/admin/<int:meeting_id>")
@login_required
@admin_required
def admin_event(meeting_id):
    return render_template("event_admin.html")

@app.route("/dashboard")
@login_required
def user_dashboard():
    return render_template("dashboard.html")

@app.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    return render_template("admin/dashboard.html")


@app.route("/api/event/admin/create", methods=["POST"])
@login_required
@admin_required
def event_create():
    # Create a new meeting based on the form inputs.
    meeting_title = request.form["meeting_title"]
    meeting_description = request.form["meeting_description"]
    meeting = Meetings(state="not started", 
                        title=meeting_title, 
                        description=meeting_description, 
                        host=f"{current_user.username} - ACM at UDayton", 
                        code_hash=None)
    db.session.add(meeting)
    db.session.commit()
    redirect(url_for("admin_event"))

@app.route("/event/admin/start/<int:meeting_id>", methods=["POST"])
@login_required
@admin_required
def event_start(meeting_id):
    if current_user.role not in app.context["officers"].keys():
        # User is not an officer, so prevent access.
        abort(403)
    else:
        # Mark the meeting as "active".
        meeting = Meetings.query.filter_by(id = meeting_id).first_or_404()
        if meeting.status == "not started":
            meeting.status = "active"
            # Add the user (officer) as an attendee.
            attendance = Attendees(username=current_user.username, meeting=meeting_id, event_start=datetime.datetime.now())
            db.session.add(attendance)
            db.session.commit()
            return_data = {"success": True, "meeting_id": meeting_id, "message": "Meeting started successfully."}
            return jsonify(return_data), 200
        else:
            # Meeting cannot be activated.
            return_data = {"success": False, "meeting_id": meeting_id, "message": f"Meeting could not be started because it is already {meeting.status}."}
            return jsonify(return_data), 400

@app.route("/event/admin/end/<int:meeting_id>", methods=["POST"])
@login_required
@admin_required
def event_end(meeting_id):
    if current_user.role not in app.context["officers"].keys():
        # User is not an officer, so prevent access.
        abort(403)
    else:
        # Mark the meeting as "ended".
        meeting = Meetings.query.filter_by(id = meeting_id).first_or_404()
        if meeting.status == "active":
            meeting.status = "ended"
            meeting.event_end = datetime.datetime.now()
            db.session.commit()
            return_data = {"success": True, "meeting_id": meeting_id, "message": "Meeting ended successfully."}
            return jsonify(return_data), 200
        else:
            # Meeting cannot be ended.
            return_data = {"success": False, "meeting_id": meeting_id, "message": f"Meeting could not be ended because it is currently {meeting.status}."}
            return return_data, 400

@app.route("/event/admin/minutes:<int:meeting_id>", methods=["POST"])
@login_required
@admin_required
def event_minutes(meeting_id):
    if Meetings.query.filter_by(id = meeting_id).exists():
        # Handle minutes submission.
        meeting_minutes = request.form["meeting_minutes"]
        minutes = Minutes(meeting=meeting_id, username_by=current_user.username, notes=meeting_minutes)
        return_data = {"success": True, "meeting_id": meeting_id, "message": "Meeting minutes saved successfully."}
        return jsonify(return_data), 201
    else:
        # Meeting does not exist.
        return_data = {"success": False, "meeting_id": meeting_id, "message": "Specified meeting does not exist."}
        return jsonify(return_data), 400


# Public routing.
@app.route("/event/check-in/<int:meeting_id>", methods=["POST"])
@login_required
def event_check_in(meeting_id):
    if Meetings.query.filter_by(id = meeting_id).exists():
        code = request.form["meeting_code"]
        meeting = Meetings.query.filter_by(id = meeting_id).first_or_404()
        if meeting.state == "active":
            if sha_hash(code) == meeting.code_hash:
                # Meeting active, add the user as an attendee.
                attendance = Attendees(username=current_user.username, meeting=meeting_id)
                db.session.add(attendance)
                db.session.commit()
                return_data = {"success": True, "meeting_id": meeting_id, "message": "Attendance updated successfully."}
                return jsonify(return_data), 200
            else:
                # Invalid meeting code.
                return_data = {"success": False, "meeting_id": meeting_id, "message": "Meeting code is invalid."}
                return jsonify(return_data), 400
        else:
            # Meeting inactive, return an error message.
            return_data = {"success": False, "meeting_id": meeting_id, "message": "Specified meeting is inactive."}
            return jsonify(return_data), 400
    else: # Meeting does not exist.
        return_data = {"success": False, "meeting_id": meeting_id, "message": "Specified meeting does not exist."}
        return jsonify(return_data), 400

# API Routing.
@app.route("/api/event/attendees/<int:meeting_id>")
def api_event_attendees(meeting_id):
    attendees = Attendees.query.filter_by(meeting = meeting_id).all()
    return jsonify(attendees), 200

@app.route("/api/event/notes/<int:meeting_id>")
def api_event_minutes(meeting_id):
    minutes = Minutes.query.filter_by(meeting = meeting_id).all()
    return jsonify(minutes), 200

@app.route("/api/event/status/<int:meeting_id>")
def api_event_status(meeting_id):
    meeting = Meetings.query.filter_by(id = meeting_id).first_or_404()
    return jsonify(meeting.state), 200


if __name__ == "__main__":
    # Run the application.
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for static files
    app.run(debug=True)
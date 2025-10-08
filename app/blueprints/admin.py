#!/usr/bin/env python
# app/blueprints/admin.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 10/7/2025

File Purpose: Admin routes for the project.
"""

# Standard library imports.
import datetime

# Third-party imports.
from flask import Blueprint, render_template, request, jsonify, abort, redirect, url_for
from flask_login import login_required, current_user

# Local application imports.
from app.extensions import db
from app.models import Users, Meetings, Attendees, Minutes
from app.utils import generate_meeting_code, sha_hash
from app.__init__ import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates')

# Admin web routes.
@admin_bp.route("/dashboard/<int:meeting_id>/")
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

@admin_bp.route("/create/", methods = ["POST"])
@login_required
@admin_required
def event_create():
    """ Create a new meeting based from form inputs. """
    meeting_title = request.form["meeting_title"]
    meeting_description = request.form["meeting_description"]
    meeting_admin_only = request.form["meeting_admin_only"] == "on"
    meeting = Meetings(state = "not started",
                        title = meeting_title,
                        description = meeting_description,
                        host = f"{current_user.username} - ACM at UDayton",
                        code_hash = None,
                        admin_only = meeting_admin_only
                        )
    db.session.add(meeting)
    db.session.commit()
    return redirect(url_for("admin.admin_dashboard", meeting_id = meeting.id))

@admin_bp.route("/start/<int:meeting_id>/", methods = ["POST"])
@login_required
@admin_required
def event_start(meeting_id):
    """ Start a single meeting from the administrator dashboard. """
    if current_user.role != "admin":
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

@admin_bp.route("/reset-code/<int:meeting_id>/")
@login_required
@admin_required
def reset_code(meeting_id):
    """ Reset the meeting join code for a single meeting. """
    if current_user.role != "admin":
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
            return redirect(f"/admin/show-code?code={meeting_code}")
        else:
            # Meeting cannot be activated.
            return render_template(
                "error.html",
                page_title = "400 Error",
                error_message = "This meeting is not active."
            )

@admin_bp.route("/show-code/")
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

@admin_bp.route("/end/<int:meeting_id>/", methods = ["POST"])
@login_required
@admin_required
def event_end(meeting_id):
    """ End a single meeting from the administrator dashboard. """
    if current_user.role != "admin":
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

@admin_bp.route("/attendees/<int:meeting_id>/", methods = ["POST"])
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

@admin_bp.route("/minutes/<int:meeting_id>/", methods = ["POST"])
@admin_bp.route("/minutes/<int:meeting_id>/<int:minutes_id>/", methods = ["POST"])
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

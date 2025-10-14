#!/usr/bin/env python
# app/blueprints/main.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 10/7/2025

File Purpose: Primary routes for the project.
"""

# Third-party imports.
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    send_from_directory
)
from flask_login import current_user, login_required
from sqlalchemy import desc

# Local application imports.
from app.models import Meetings, Attendees, Minutes, Attachments
from app.extensions import db
from app.utils import sha_hash

main_bp = Blueprint('main', __name__, template_folder='templates')

# Public web routes.
@main_bp.route("/")
def home():
    """ Show the home page. """
    if not (current_user.is_authenticated and current_user.role == "admin"):
        recent_meetings = Meetings.query.filter(
            Meetings.admin_only != True,
        ).order_by(desc(Meetings.id)).limit(4).all()
    else:
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

@main_bp.route("/events/")
def events_list():
    """ Show the event list page. """
    all_meetings = Meetings.query.all()
    visible_meetings = []
    if current_user.is_authenticated and current_user.role == "admin":
        return render_template("events.html", page_title = "Meetings", meetings = all_meetings)
    else:
        for meeting in all_meetings:
            if meeting.admin_only is not True:
                visible_meetings.append(meeting)
        return render_template("events.html", page_title = "Meetings", meetings = visible_meetings)

@main_bp.route("/event/<int:meeting_id>/")
def user_event(meeting_id):
    """ Show a page with the details of a single meeting. """
    meeting = Meetings.query.filter_by(id = meeting_id).first_or_404()
    attendees = Attendees.query.filter_by(meeting = meeting_id).all()
    minutes = Minutes.query.filter_by(meeting = meeting_id).all()
    attachments = Attachments.query.filter_by(meeting = meeting_id).all()
    return render_template(
        "event.html",
        page_title = f"Meeting - {meeting.title}",
        meeting = meeting,
        all_minutes = minutes,
        all_attendees = attendees,
        all_attachments = attachments
    )

@main_bp.route("/event/check-in/<int:meeting_id>/", methods = ["POST"])
@login_required
def event_check_in(meeting_id):
    """ Check into a single meeting from the homepage. """
    if Meetings.query.filter_by(id = meeting_id).first() is not None:
        code = request.form["meeting_code"]
        meeting = Meetings.query.filter_by(id = meeting_id).first_or_404()
        if meeting.state == "active":
            if Attendees.query.filter_by(
            meeting = meeting_id,
            username = current_user.username
            ).first() is None:
                if sha_hash(code) == meeting.code_hash:
                    # Check for admin-only meeting status.
                    if meeting.admin_only and current_user.role != "admin":
                        flash("Check-in failed. This meeting is restricted to administrators only.")
                    else:
                        # Meeting active, add the user as an attendee.
                        attendance = Attendees(
                            username = current_user.username,
                            meeting = meeting_id)
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
    return redirect(url_for("main.home"))

@main_bp.route('/uploads/<name>')
def download_file(name):
    """ Serve an uploaded file. """
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], name)

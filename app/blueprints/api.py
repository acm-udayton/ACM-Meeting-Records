#!/usr/bin/env python
# app/blueprints/api.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 10/7/2025

File Purpose: API routes for the project.
"""

# Third-party imports.
from flask import Blueprint, jsonify

# Local application imports.
from app.models import Meetings, Attendees, Minutes, Attachments

api_bp = Blueprint('api', __name__, template_folder='templates')

# API Routing.
@api_bp.route("/event/attendees/<int:meeting_id>/")
def api_event_attendees(meeting_id):
    """ Get attendee list for a single meeting. """
    attendees = Attendees.query.filter_by(meeting = meeting_id).all()
    attendees_data = [attendee.to_dict() for attendee in attendees]
    return jsonify(attendees_data), 200

@api_bp.route("/event/notes/<int:meeting_id>/")
def api_event_minutes(meeting_id):
    """ Get minutes for a single meeting. """
    minutes = Minutes.query.filter_by(meeting = meeting_id).all()
    minutes_data = [minute.to_dict() for minute in minutes]
    return jsonify(minutes_data), 200

@api_bp.route("/event/state/<int:meeting_id>/")
def api_event_state(meeting_id):
    """ Get current state of a single meeting. """
    meeting = Meetings.query.filter_by(id = meeting_id).first_or_404()
    return jsonify(meeting.state.title()), 200

@api_bp.route("/event/attachments/<int:meeting_id>/")
def api_event_attachments(meeting_id):
    """ Get attachments for a single meeting. """
    attachments = Attachments.query.filter_by(meeting = meeting_id).all()
    attachments_data = [attachment.to_dict() for attachment in attachments]
    return jsonify(attachments_data), 200

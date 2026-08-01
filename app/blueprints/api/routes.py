#!/usr/bin/env python
# app/blueprints/api/routes.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 10/7/2025

File Purpose: API routes for the project.
"""

# Third-party imports.
from flask import Blueprint, abort, jsonify

# Local application imports.
from app.services.api_service import (
    get_attachment_dicts,
    get_attendee_dicts,
    get_meeting_state_title,
    get_minutes_dicts,
)

api_bp = Blueprint('api', __name__, template_folder='templates')

# API Routing.
@api_bp.route("/event/attendees/<int:meeting_id>/")
def api_event_attendees(meeting_id):
    """ Get attendee list for a single meeting. """
    return jsonify(get_attendee_dicts(meeting_id)), 200

@api_bp.route("/event/notes/<int:meeting_id>/")
def api_event_minutes(meeting_id):
    """ Get minutes for a single meeting. """
    return jsonify(get_minutes_dicts(meeting_id)), 200

@api_bp.route("/event/state/<int:meeting_id>/")
def api_event_state(meeting_id):
    """ Get current state of a single meeting. """
    state_title = get_meeting_state_title(meeting_id)
    if state_title is None:
        abort(404)
    return jsonify(state_title), 200

@api_bp.route("/event/attachments/<int:meeting_id>/")
def api_event_attachments(meeting_id):
    """ Get attachments for a single meeting. """
    return jsonify(get_attachment_dicts(meeting_id)), 200

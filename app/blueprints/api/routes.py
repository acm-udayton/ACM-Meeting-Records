#!/usr/bin/env python
# app/blueprints/api/routes.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 8/19/2026

File Purpose: API routes for the project.
"""

# Third-party imports.
from flask import Blueprint, abort, jsonify
from flask_login import current_user

# Local application imports.
from app.utils import filter_by_role, user_can_access_meeting_by_id
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
    if not user_can_access_meeting_by_id(current_user, meeting_id):
        return jsonify({"error": "Access denied"}), 403

    attendees = get_attendee_dicts(meeting_id)
    if len(attendees) < 1:
        return jsonify({"error": "No attendees found"}), 404
    return jsonify(attendees), 200

@api_bp.route("/event/notes/<int:meeting_id>/")
def api_event_minutes(meeting_id):
    """ Get minutes for a single meeting. """
    if not user_can_access_meeting_by_id(current_user, meeting_id):
        return jsonify({"error": "Access denied"}), 403

    minutes = get_minutes_dicts(meeting_id)
    if len(minutes) < 1:
        return jsonify({"error": "No minutes found"}), 404
    return jsonify(minutes), 200

@api_bp.route("/event/state/<int:meeting_id>/")
def api_event_state(meeting_id):
    """ Get current state of a single meeting. """
    if not user_can_access_meeting_by_id(current_user, meeting_id):
        return jsonify({"error": "Access denied"}), 403

    state_title = get_meeting_state_title(meeting_id)
    if state_title is None:
        abort(404)
    return jsonify(state_title), 200

@api_bp.route("/event/attachments/<int:meeting_id>/")
def api_event_attachments(meeting_id):
    """ Get attachments for a single meeting. """
    if not user_can_access_meeting_by_id(current_user, meeting_id):
        return jsonify({"error": "Access denied"}), 403

    attachments = get_attachment_dicts(meeting_id)
    if len(attachments) < 1:
        return jsonify({"error": "No attachments found"}), 404
    return jsonify(attachments), 200

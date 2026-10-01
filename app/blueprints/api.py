#!/usr/bin/env python
# app/blueprints/api.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 8/19/2026

File Purpose: API routes for the project.
"""

# Third-party imports.
from flask import Blueprint, jsonify
from flask_login import current_user

# Local application imports.
from app.models import Meetings, Attendees, Minutes, Attachments
from app.utils import filter_by_role, user_can_access_meeting_by_id

api_bp = Blueprint('api', __name__, template_folder='templates')

# API Routing.
@api_bp.route("/event/attendees/<int:meeting_id>/")
def api_event_attendees(meeting_id):
    """ Get attendee list for a single meeting. """
    if not user_can_access_meeting_by_id(current_user, meeting_id):
        return jsonify({"error": "Access denied"}), 403

    attendees = Attendees.query.filter(Attendees.meeting == meeting_id).all()
    if not attendees:
        return jsonify({"error": "No attendees found"}), 404
    attendees_data = [attendee.to_dict() for attendee in attendees]
    return jsonify(attendees_data), 200

@api_bp.route("/event/notes/<int:meeting_id>/")
def api_event_minutes(meeting_id):
    """ Get minutes for a single meeting. """
    if not user_can_access_meeting_by_id(current_user, meeting_id):
        return jsonify({"error": "Access denied"}), 403

    minutes = Minutes.query.filter(Minutes.meeting == meeting_id).all()
    if not minutes:
        return jsonify({"error": "No minutes found"}), 404
    minutes_data = [minute.to_dict() for minute in minutes]
    return jsonify(minutes_data), 200

@api_bp.route("/event/state/<int:meeting_id>/")
def api_event_state(meeting_id):
    """ Get current state of a single meeting. """
    if not user_can_access_meeting_by_id(current_user, meeting_id):
        return jsonify({"error": "Access denied"}), 403

    meeting = Meetings.query.filter(Meetings.id == meeting_id).first_or_404()
    return jsonify(meeting.state.title()), 200

@api_bp.route("/event/attachments/<int:meeting_id>/")
def api_event_attachments(meeting_id):
    """ Get attachments for a single meeting. """
    if not user_can_access_meeting_by_id(current_user, meeting_id):
        return jsonify({"error": "Access denied"}), 403
    
    attachments = Attachments.query.filter(Attachments.meeting == meeting_id).all()
    if not attachments:
        return jsonify({"error": "No attachments found"}), 404
    attachments_data = [attachment.to_dict() for attachment in attachments]
    return jsonify(attachments_data), 200

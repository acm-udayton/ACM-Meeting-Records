#!/usr/bin/env python
# app/services/api_service.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 7/27/2026

File Purpose: API service for the project.
"""

# Local application imports.
from app.extensions import db
from app.models import Attachments, Attendees, Meetings, Minutes


def get_attendee_dicts(meeting_id: int) -> list[dict]:
    """Return attendee data for a meeting as dictionaries."""
    attendees = Attendees.query.filter_by(meeting=meeting_id).all()
    return [attendee.to_dict() for attendee in attendees]


def get_minutes_dicts(meeting_id: int) -> list[dict]:
    """Return minutes data for a meeting as dictionaries."""
    minutes = Minutes.query.filter_by(meeting=meeting_id).all()
    return [minute.to_dict() for minute in minutes]


def get_meeting_state_title(meeting_id: int) -> str | None:
    """Return the display title for a meeting state, if the meeting exists."""
    meeting = db.session.get(Meetings, meeting_id)
    if meeting is None:
        return None
    return meeting.state.title()


def get_attachment_dicts(meeting_id: int) -> list[dict]:
    """Return attachment data for a meeting as dictionaries."""
    attachments = Attachments.query.filter_by(meeting=meeting_id).all()
    return [attachment.to_dict() for attachment in attachments]
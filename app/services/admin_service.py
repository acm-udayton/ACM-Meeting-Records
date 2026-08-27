#!/usr/bin/env python
# app/services/admin_service.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 8/1/2026

File Purpose: Admin service for the project.
"""

# Standard library imports.
import datetime
import os
from dataclasses import dataclass
from enum import Enum

# Third-party imports.
from flask import current_app
from werkzeug.utils import secure_filename

# Local application imports.
from app.extensions import db
from app.models import Attachments, Attendees, Meetings, Minutes, Users
from app.utils import generate_meeting_code, sha_hash


class AdminResultStatus(str, Enum):
    """Granular outcomes for admin operations."""

    SUCCESS = "success"
    INVALID_MEETING_DATA = "invalid_meeting_data"
    MEETING_NOT_FOUND = "meeting_not_found"
    MEETING_STATE_INVALID = "meeting_state_invalid"
    USER_NOT_FOUND = "user_not_found"
    ATTENDEE_EXISTS = "attendee_exists"
    ATTENDEE_NOT_FOUND = "attendee_not_found"
    MINUTES_ENTRY_NOT_FOUND = "minutes_entry_not_found"
    NO_FILE_SELECTED = "no_file_selected"
    INVALID_FILE_TYPE = "invalid_file_type"
    ATTACHMENT_NOT_FOUND = "attachment_not_found"
    ALREADY_ADMIN = "already_admin"
    ALREADY_USER = "already_user"
    CANNOT_DEMOTE_SELF = "cannot_demote_self"
    MFA_ALREADY_DISABLED = "mfa_already_disabled"
    ACCOUNT_ALREADY_DISABLED = "account_already_disabled"
    ACCOUNT_ALREADY_ENABLED = "account_already_enabled"


@dataclass(slots=True)
class AdminOperationResult:
    """Outcome for admin operations that mutate state."""

    statuses: tuple[AdminResultStatus, ...]
    meeting: Meetings | None = None
    attendee: Attendees | None = None
    minutes_entry: Minutes | None = None
    attachment: Attachments | None = None
    meeting_code: str | None = None
    user: Users | None = None


@dataclass(slots=True)
class AdminDashboardViewData:
    """Data required to render the admin dashboard."""

    meeting: Meetings
    attendees: list[Attendees]
    minutes: list[Minutes]
    attachments: list[Attachments]


@dataclass(slots=True)
class UsersListViewData:
    """Data required to render the users admin page."""

    users: list[Users]
    total_meetings: int
    most_recent_meeting_date: datetime.datetime | None
    active_user_count: int
    since: str | None


def get_last_attended_date(username: str) -> datetime.datetime | None:
    """Return the date of the user's most recent attended meeting."""
    last_meeting = (
        db.session.query(Meetings.event_start)
        .join(Attendees, Meetings.id == Attendees.meeting)
        .filter(Attendees.username == username)
        .filter(Meetings.event_start is not None)
        .order_by(Meetings.event_start.desc())
        .first()
    )
    return last_meeting[0] if last_meeting else None


def create_meeting(
    title: str,
    description: str,
    admin_only: bool,
    host_username: str,
) -> AdminOperationResult:
    """Create a meeting and persist it to the database."""
    if not title.strip() or not description.strip():
        return AdminOperationResult(statuses=(AdminResultStatus.INVALID_MEETING_DATA,))

    meeting = Meetings(
        state="not started",
        title=title,
        description=description,
        host=f"{host_username} - ACM at UDayton",
        code_hash=None,
        admin_only=admin_only,
    )
    db.session.add(meeting)
    db.session.commit()
    current_app.logger.info("Created meeting %s by %s", meeting.id, host_username)
    return AdminOperationResult(statuses=(AdminResultStatus.SUCCESS,), meeting=meeting)


def get_dashboard_data(meeting_id: int) -> AdminDashboardViewData | None:
    """Return the dashboard data for a meeting."""
    meeting = db.session.get(Meetings, meeting_id)
    if meeting is None:
        return None

    attendees = Attendees.query.filter_by(meeting=meeting_id).all()
    minutes = Minutes.query.filter_by(meeting=meeting_id).all()
    attachments = Attachments.query.filter_by(meeting=meeting_id).all()
    return AdminDashboardViewData(
        meeting=meeting,
        attendees=attendees,
        minutes=minutes,
        attachments=attachments,
    )


def start_meeting(meeting_id: int, username: str) -> AdminOperationResult:
    """Activate a meeting and generate a join code."""
    meeting = db.session.get(Meetings, meeting_id)
    if meeting is None:
        return AdminOperationResult(statuses=(AdminResultStatus.MEETING_NOT_FOUND,))

    if meeting.state != "not started":
        return AdminOperationResult(
            statuses=(AdminResultStatus.MEETING_STATE_INVALID,),
            meeting=meeting,
        )

    meeting_code = generate_meeting_code()
    meeting.code_hash = sha_hash(meeting_code)
    meeting.state = "active"
    meeting.event_start = datetime.datetime.now()

    attendance = Attendees(username=username, meeting=meeting_id)
    db.session.add(attendance)
    db.session.commit()
    current_app.logger.info("Started meeting %s by %s", meeting.id, username)
    return AdminOperationResult(
        statuses=(AdminResultStatus.SUCCESS,),
        meeting=meeting,
        meeting_code=meeting_code,
    )


def reset_meeting_code(meeting_id: int) -> AdminOperationResult:
    """Generate a new join code for an active meeting."""
    meeting = db.session.get(Meetings, meeting_id)
    if meeting is None:
        return AdminOperationResult(statuses=(AdminResultStatus.MEETING_NOT_FOUND,))

    if meeting.state != "active":
        return AdminOperationResult(
            statuses=(AdminResultStatus.MEETING_STATE_INVALID,),
            meeting=meeting,
        )

    meeting_code = generate_meeting_code()
    meeting.code_hash = sha_hash(meeting_code)
    db.session.commit()
    return AdminOperationResult(
        statuses=(AdminResultStatus.SUCCESS,),
        meeting=meeting,
        meeting_code=meeting_code,
    )


def end_meeting(meeting_id: int) -> AdminOperationResult:
    """End an active meeting."""
    meeting = db.session.get(Meetings, meeting_id)
    if meeting is None:
        return AdminOperationResult(statuses=(AdminResultStatus.MEETING_NOT_FOUND,))

    if meeting.state != "active":
        return AdminOperationResult(
            statuses=(AdminResultStatus.MEETING_STATE_INVALID,),
            meeting=meeting,
        )

    meeting.state = "ended"
    meeting.event_end = datetime.datetime.now()
    db.session.commit()
    current_app.logger.info("Ended meeting %s", meeting.id)
    return AdminOperationResult(statuses=(AdminResultStatus.SUCCESS,), meeting=meeting)


def add_attendee(meeting_id: int, attendee_username: str) -> AdminOperationResult:
    """Add an attendee to a meeting if the user exists and is not already present."""
    meeting = db.session.get(Meetings, meeting_id)
    if meeting is None:
        return AdminOperationResult(statuses=(AdminResultStatus.MEETING_NOT_FOUND,))

    if Users.query.filter_by(username=attendee_username).first() is None:
        return AdminOperationResult(statuses=(AdminResultStatus.USER_NOT_FOUND,))

    if Attendees.query.filter_by(meeting=meeting_id, username=attendee_username).first() is not None:
        return AdminOperationResult(statuses=(AdminResultStatus.ATTENDEE_EXISTS,))

    attendee = Attendees(meeting=meeting_id, username=attendee_username)
    db.session.add(attendee)
    db.session.commit()
    return AdminOperationResult(statuses=(AdminResultStatus.SUCCESS,), attendee=attendee)


def remove_attendee(meeting_id: int, attendee_id: int) -> AdminOperationResult:
    """Remove an attendee from a meeting."""
    meeting = db.session.get(Meetings, meeting_id)
    if meeting is None:
        return AdminOperationResult(statuses=(AdminResultStatus.MEETING_NOT_FOUND,))

    attendee = Attendees.query.filter_by(id=attendee_id, meeting=meeting_id).first()
    if attendee is None:
        return AdminOperationResult(statuses=(AdminResultStatus.ATTENDEE_NOT_FOUND,))

    db.session.delete(attendee)
    db.session.commit()
    return AdminOperationResult(statuses=(AdminResultStatus.SUCCESS,), attendee=attendee)


def save_minutes(
    meeting_id: int,
    meeting_minutes: str,
    username: str,
    minutes_id: int | None = None,
) -> AdminOperationResult:
    """Create or update meeting minutes."""
    meeting = db.session.get(Meetings, meeting_id)
    if meeting is None:
        return AdminOperationResult(statuses=(AdminResultStatus.MEETING_NOT_FOUND,))

    if minutes_id is not None:
        minutes_entry = Minutes.query.filter_by(id=minutes_id, meeting=meeting_id).first()
        if minutes_entry is None:
            return AdminOperationResult(statuses=(AdminResultStatus.MINUTES_ENTRY_NOT_FOUND,))

        if username not in minutes_entry.username_by:
            minutes_entry.username_by += f", {username}"
        minutes_entry.notes = meeting_minutes
        db.session.commit()
        return AdminOperationResult(statuses=(AdminResultStatus.SUCCESS,), minutes_entry=minutes_entry)

    minutes_entry = Minutes(meeting=meeting_id, username_by=username, notes=meeting_minutes)
    db.session.add(minutes_entry)
    db.session.commit()
    return AdminOperationResult(statuses=(AdminResultStatus.SUCCESS,), minutes_entry=minutes_entry)


def add_attachment(meeting_id: int, uploaded_file, upload_folder: str) -> AdminOperationResult:
    """Persist an uploaded attachment to disk and database."""
    meeting = db.session.get(Meetings, meeting_id)
    if meeting is None:
        return AdminOperationResult(statuses=(AdminResultStatus.MEETING_NOT_FOUND,))

    if uploaded_file is None or uploaded_file.filename == "":
        return AdminOperationResult(statuses=(AdminResultStatus.NO_FILE_SELECTED,))

    original_filename = uploaded_file.filename.replace(" ", "_")
    extension = original_filename.lower().split(".")[-1] if "." in original_filename else ""
    if extension not in {"pptx", "pdf", "docx", "txt", "png", "jpg", "jpeg", "gif"}:
        return AdminOperationResult(statuses=(AdminResultStatus.INVALID_FILE_TYPE,))

    filename = secure_filename(f"meeting-{meeting_id}-{original_filename}")
    attachment = Attachments(
        meeting=meeting_id,
        filename=original_filename,
        filepath=os.path.join(upload_folder, filename),
    )
    db.session.add(attachment)
    db.session.commit()

    uploaded_file.save(os.path.join(upload_folder, filename))
    return AdminOperationResult(statuses=(AdminResultStatus.SUCCESS,), attachment=attachment)


def remove_attachment(meeting_id: int, attachment_id: int) -> AdminOperationResult:
    """Delete an attachment from storage and the database."""
    meeting = db.session.get(Meetings, meeting_id)
    if meeting is None:
        return AdminOperationResult(statuses=(AdminResultStatus.MEETING_NOT_FOUND,))

    attachment = Attachments.query.filter_by(id=attachment_id, meeting=meeting_id).first()
    if attachment is None:
        return AdminOperationResult(statuses=(AdminResultStatus.ATTACHMENT_NOT_FOUND,))

    if attachment.filepath:
        if os.path.exists(attachment.filepath):
            os.remove(attachment.filepath)

    db.session.delete(attachment)
    db.session.commit()
    return AdminOperationResult(statuses=(AdminResultStatus.SUCCESS,), attachment=attachment)


def delete_meeting(meeting_id: int) -> AdminOperationResult:
    """Delete a meeting and all related records."""
    meeting = db.session.get(Meetings, meeting_id)
    if meeting is None:
        return AdminOperationResult(statuses=(AdminResultStatus.MEETING_NOT_FOUND,))

    Attendees.query.filter_by(meeting=meeting_id).delete()
    Minutes.query.filter_by(meeting=meeting_id).delete()
    for attachment in Attachments.query.filter_by(meeting=meeting_id).all():
        if attachment.filepath and os.path.exists(attachment.filepath):
            os.remove(attachment.filepath)
    Attachments.query.filter_by(meeting=meeting_id).delete()
    db.session.delete(meeting)
    db.session.commit()
    return AdminOperationResult(statuses=(AdminResultStatus.SUCCESS,), meeting=meeting)


def get_users_list_data(since_date: datetime.datetime | None) -> UsersListViewData:
    """Prepare the data needed by the admin users overview page."""
    all_users = Users.query.order_by(Users.id).all()
    for user in all_users:
        user.meetings_attended = Attendees.query.filter_by(username=user.username).count()
        user.last_checkin = get_last_attended_date(user.username)

    meetings_query = Meetings.query
    if since_date is not None:
        meetings_query = meetings_query.filter(Meetings.event_start >= since_date)

    most_recent_public_meeting = (
        Meetings.query.filter(Meetings.admin_only != True)
        .filter(Meetings.event_start is not None)
        .order_by(Meetings.event_start.desc())
        .first()
    )
    return UsersListViewData(
        users=all_users,
        total_meetings=meetings_query.count(),
        most_recent_meeting_date=(
            most_recent_public_meeting.event_start if most_recent_public_meeting else None
        ),
        active_user_count=Users.query.filter_by(activated=True).count(),
        since=None,
    )


def reset_password(user_id: int, new_password: str) -> AdminOperationResult:
    """Reset a user's password."""
    user = db.session.get(Users, user_id)
    if user is None:
        return AdminOperationResult(statuses=(AdminResultStatus.USER_NOT_FOUND,))

    user.set_password(new_password)
    db.session.commit()
    return AdminOperationResult(statuses=(AdminResultStatus.SUCCESS,), user=user)


def promote_user(user_id: int) -> AdminOperationResult:
    """Promote a user to admin."""
    user = db.session.get(Users, user_id)
    if user is None:
        return AdminOperationResult(statuses=(AdminResultStatus.USER_NOT_FOUND,))
    if user.role == "admin":
        return AdminOperationResult(statuses=(AdminResultStatus.ALREADY_ADMIN,), user=user)

    user.role = "admin"
    db.session.commit()
    return AdminOperationResult(statuses=(AdminResultStatus.SUCCESS,), user=user)


def demote_user(user_id: int, current_user_id: int) -> AdminOperationResult:
    """Demote a user to the regular role."""
    if user_id == current_user_id:
        return AdminOperationResult(statuses=(AdminResultStatus.CANNOT_DEMOTE_SELF,))

    user = db.session.get(Users, user_id)
    if user is None:
        return AdminOperationResult(statuses=(AdminResultStatus.USER_NOT_FOUND,))
    if user.role == "user":
        return AdminOperationResult(statuses=(AdminResultStatus.ALREADY_USER,), user=user)

    user.role = "user"
    db.session.commit()
    return AdminOperationResult(statuses=(AdminResultStatus.SUCCESS,), user=user)


def disable_user_mfa(user_id: int) -> AdminOperationResult:
    """Disable two-factor authentication for a user."""
    user = db.session.get(Users, user_id)
    if user is None:
        return AdminOperationResult(statuses=(AdminResultStatus.USER_NOT_FOUND,))
    if not user.mfa_active:
        return AdminOperationResult(statuses=(AdminResultStatus.MFA_ALREADY_DISABLED,), user=user)

    user.mfa_active = False
    user.totp_active = False
    user.totp_secret = None
    db.session.commit()
    return AdminOperationResult(statuses=(AdminResultStatus.SUCCESS,), user=user)


def disable_user_account(user_id: int) -> AdminOperationResult:
    """Disable a user account."""
    user = db.session.get(Users, user_id)
    if user is None:
        return AdminOperationResult(statuses=(AdminResultStatus.USER_NOT_FOUND,))
    if not user.activated:
        return AdminOperationResult(statuses=(AdminResultStatus.ACCOUNT_ALREADY_DISABLED,), user=user)

    user.activated = False
    db.session.commit()
    return AdminOperationResult(statuses=(AdminResultStatus.SUCCESS,), user=user)


def enable_user_account(user_id: int) -> AdminOperationResult:
    """Enable a user account."""
    user = db.session.get(Users, user_id)
    if user is None:
        return AdminOperationResult(statuses=(AdminResultStatus.USER_NOT_FOUND,))
    if user.activated:
        return AdminOperationResult(statuses=(AdminResultStatus.ACCOUNT_ALREADY_ENABLED,), user=user)

    user.activated = True
    db.session.commit()
    return AdminOperationResult(statuses=(AdminResultStatus.SUCCESS,), user=user)
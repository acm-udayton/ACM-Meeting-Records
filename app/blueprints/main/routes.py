#!/usr/bin/env python
# app/blueprints/main/routes.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz), Thomas Crossman (github.com/crossmant1)
Last Modified: 8/2/2026

File Purpose: Primary routes for the project.
"""

# Third-party imports.
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required, logout_user

# Local application imports.
from app.forms import CreateMeetingForm, MeetingCheckinForm, PollVoteForm
from app.services.main_service import (
    MainResultStatus,
    check_in_to_meeting,
    get_event_view_data,
    get_events_list_data,
    get_home_view_data,
    meeting_exists,
    submit_poll_responses,
)

main_bp = Blueprint('main', __name__, template_folder='templates')


def _get_poll_response_payload() -> tuple[dict[int, str], dict[int, list[str]]]:
    """Convert submitted poll fields into plain service arguments."""
    free_responses: dict[int, str] = {}
    selected_options: dict[int, list[str]] = {}

    for field_name in request.form:
        field_parts = field_name.split("_")
        if len(field_parts) != 3 or field_parts[0] != "question":
            continue

        try:
            question_id = int(field_parts[1])
        except ValueError:
            continue

        if field_parts[1] != str(question_id):
            continue

        if field_parts[2] == "frq":
            free_responses[question_id] = request.form.get(field_name, "")
        elif field_parts[2] == "mcq":
            selected_options[question_id] = request.form.getlist(field_name)

    return free_responses, selected_options


def _flash_poll_question_failures(question_results) -> None:
    """Map service-level poll failures to the existing user-visible messages."""
    for result in question_results:
        if MainResultStatus.IMMUTABLE_RESPONSE in result.statuses:
            flash(
                f"Response for '{result.question_text}' cannot be changed once submitted.",
                "danger",
            )
        elif MainResultStatus.IMMUTABLE_RESPONSES in result.statuses:
            flash(
                f"Responses for '{result.question_text}' cannot be changed once submitted.",
                "danger",
            )
        elif MainResultStatus.ONE_SELECTED_OPTION_NOT_FOUND in result.statuses:
            flash("One of the selected options does not exist.", "danger")
        elif MainResultStatus.SELECTED_OPTION_NOT_FOUND in result.statuses:
            flash("Selected option does not exist.", "danger")


# Public web routes.
@main_bp.route("/")
def home():
    """Show the home page."""
    form = MeetingCheckinForm()
    poll_form = PollVoteForm()
    is_authenticated = current_user.is_authenticated
    view_data = get_home_view_data(
        current_user.id if is_authenticated else None,
        is_authenticated and current_user.role == "admin",
    )

    return render_template(
        "index.html",
        page_title="Home",
        recent_meetings=view_data.recent_meetings,
        featured_meeting=view_data.featured_meeting,
        polls=view_data.polls,
        voted_questions=view_data.voted_questions,
        voted_options=view_data.voted_options,
        user_frq_responses=view_data.user_frq_responses,
        form=form,
        poll_form=poll_form,
    )


@main_bp.route("/events/")
def events_list():
    """Show the event list page."""
    form = CreateMeetingForm()
    is_admin = current_user.is_authenticated and current_user.role == "admin"
    view_data = get_events_list_data(is_admin)
    return render_template(
        "events.html",
        page_title="Meetings",
        meetings=view_data.meetings,
        form=form,
    )


@main_bp.route("/event/<int:meeting_id>/")
def user_event(meeting_id):
    """Show a page with the details of a single meeting."""
    view_data = get_event_view_data(meeting_id)
    if view_data is None:
        abort(404)

    form = MeetingCheckinForm()
    return render_template(
        "event.html",
        page_title=f"Meeting - {view_data.meeting.title}",
        meeting=view_data.meeting,
        all_minutes=view_data.minutes,
        all_attendees=view_data.attendees,
        all_attachments=view_data.attachments,
        form=form,
    )


@main_bp.route("/event/check-in/<int:meeting_id>/", methods=["POST"])
@login_required
def event_check_in(meeting_id):
    """Check into a single meeting from the homepage."""
    if not meeting_exists(meeting_id):
        flash("Check-in failed. Specified meeting does not exist.", "danger")
        return redirect(url_for("main.home"))

    form = MeetingCheckinForm()
    if not form.validate_on_submit():
        flash(
            "Check-in failed. Please ensure all fields are filled out correctly.",
            "danger",
        )
        return redirect(url_for("main.home"))

    result = check_in_to_meeting(
        meeting_id=meeting_id,
        username=current_user.username,
        user_role=current_user.role,
        user_activated=current_user.activated,
        code=form.code.data,
    )
    status = result.statuses[0]

    if status == MainResultStatus.MEETING_NOT_FOUND:
        flash("Check-in failed. Specified meeting does not exist.", "danger")
    elif status == MainResultStatus.MEETING_INACTIVE:
        flash("Check-in failed. Specified meeting is inactive.", "danger")
    elif status == MainResultStatus.ATTENDEE_EXISTS:
        flash("Check-in failed. You are already marked as an attendee.", "danger")
    elif status == MainResultStatus.INVALID_MEETING_CODE:
        flash("Check-in failed. Meeting code is invalid.", "danger")
    elif status == MainResultStatus.ADMIN_ONLY_RESTRICTED:
        flash(
            "Check-in failed. This meeting is restricted to administrators only.",
            "danger",
        )
    elif status == MainResultStatus.ACCOUNT_NOT_ACTIVATED:
        logout_user()
        flash("Check-in failed. Your account is not activated. Please check in again.")
        return redirect(url_for("auth.login"))
    elif status == MainResultStatus.SUCCESS:
        flash("Check-in succeeded. Attendance updated successfully.", "success")

    return redirect(url_for("main.home"))


@main_bp.route('/uploads/<name>')
def download_file(name):
    """Serve an uploaded file."""
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], name)


@main_bp.route('/submit-poll/<int:poll_id>', methods=['POST'])
@login_required
def submit_poll(poll_id):
    """Handle bulk submission of all questions in a poll."""
    free_responses, selected_options = _get_poll_response_payload()
    result = submit_poll_responses(
        poll_id=poll_id,
        user_id=current_user.id,
        free_responses=free_responses,
        selected_options=selected_options,
    )

    if MainResultStatus.POLL_NOT_FOUND in result.statuses:
        abort(404)

    if MainResultStatus.POLL_EXPIRED in result.statuses:
        flash("Poll has expired. You cannot submit responses.", "danger")
        return redirect(url_for('main.home'))

    _flash_poll_question_failures(result.question_results)

    if MainResultStatus.ERROR in result.statuses:
        flash("An error occurred while saving your responses. Please try again.", "danger")
    elif MainResultStatus.SUCCESS in result.statuses:
        flash("All responses submitted successfully!", "success")
    elif MainResultStatus.NO_CHANGES in result.statuses:
        flash("No changes were made to any responses.", "success")
    elif MainResultStatus.PARTIAL_FAILURE in result.statuses:
        flash(
            "Some responses were not submitted successfully. "
            f"Successes: {result.successes}, Failures: {result.failures}",
            "danger",
        )

    return redirect(url_for('main.home'))

#!/usr/bin/env python
# app/blueprints/main.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz), Thomas Crossman (github.com/crossmant1)
Last Modified: 3/22/2026

File Purpose: Primary routes for the project.
"""

# Standard library imports.
from datetime import datetime

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
from flask_login import current_user, login_required, logout_user
from sqlalchemy import desc

# Local application imports.
from app.forms import CreateMeetingForm, MeetingCheckinForm, PollVoteForm
from app.models import (Meetings,
    Attendees,
    Minutes,
    Attachments,
    Poll,
    PollOption,
    PollVoter,
    PollFreeResponse
)
from app.extensions import db
from app.utils import sha_hash

main_bp = Blueprint('main', __name__, template_folder='templates')

# Poll submission helper functions.
def handle_frq(question):
    """ Handle free response question submissions. """
    response_text = request.form.get(f'question_{question.id}_frq', '').strip()

    if response_text:  # Only save if they entered something
        existing_response = PollFreeResponse.query.filter_by(
            user_id=current_user.id,
            question_id=question.id
        ).first()

        if existing_response:
            # Error if immutable response already exists, otherwise update.
            if question.immutable_question:
                flash(f"Response for '{question.question_text}' cannot be changed once submitted.", "danger")
                return False, True

            existing_response.response_text = response_text
            existing_response.created_at = db.func.now()
            return True, True
        else:
            new_response = PollFreeResponse(
                user_id=current_user.id,
                question_id=question.id,
                response_text=response_text
            )
            db.session.add(new_response)
            return True, True
    else:
        # No response entered, but not a failure.
        return True, False

def handle_multiple_response_mcq(selected_option_ids, question):
    """ Handle multiple response MCQ submissions. """
    # Remove all existing votes, then add new ones.
    existing_votes = PollVoter.query.filter_by(
        user_id=current_user.id,
        question_id=question.id
    ).all()

    # Error if immutable response already exists, otherwise update.
    if question.immutable_question and existing_votes:
        flash(f"Responses for '{question.question_text}' cannot be changed once submitted.", "danger")
        return False, True

    # Decrement vote counts for removed options
    changes_made = False
    for vote in existing_votes:
        if vote.option_id not in selected_option_ids:
            option = PollOption.query.get(vote.option_id)
            if option and option.votes > 0:
                option.votes -= 1
            db.session.delete(vote)
            changes_made = True

    # Add votes for newly selected options
    existing_option_ids = {vote.option_id for vote in existing_votes}
    for option_id in selected_option_ids:
        if option_id not in existing_option_ids:
            option = PollOption.query.get(option_id)
            if option:
                option.votes += 1
                new_vote = PollVoter(
                    user_id=current_user.id,
                    question_id=question.id,
                    option_id=option_id
                )
                db.session.add(new_vote)
                changes_made = True
            else:
                flash("One of the selected options does not exist.", "danger")
                return False, True  # Option not found, treat as failure
    return True, changes_made  # Success, changes made

def handle_single_mcq(selected_option_ids, question):
    """ Handle single response MCQ submissions. """
    # Remove old vote if different, add new one.
    option_id = selected_option_ids[0]  # Only one selection for radio

    existing_vote = PollVoter.query.filter_by(
        user_id=current_user.id,
        question_id=question.id
    ).first()

    if existing_vote:
        # Error if immutable response already exists, otherwise update.
        if question.immutable_question:
            flash(f"Response for '{question.question_text}' cannot be changed once submitted.", "danger")
            return False, True

        vote_changed = existing_vote.option_id != option_id
        if vote_changed:
            # Changed vote
            old_option = PollOption.query.get(existing_vote.option_id)
            if old_option and old_option.votes > 0:
                old_option.votes -= 1

            new_option = PollOption.query.get(option_id)
            if new_option:
                new_option.votes += 1
                existing_vote.option_id = option_id
            return True, True
        else:
            # No change in vote
            return True, False
        
    else:
        # New vote
        option = PollOption.query.get(option_id)
        if option:
            option.votes += 1
            new_vote = PollVoter(
                user_id=current_user.id,
                question_id=question.id,
                option_id=option_id
            )
            db.session.add(new_vote)
            return True, True
        else:
            flash("Selected option does not exist.", "danger")
            return False, False  # Option not found, treat as failure

def handle_mcq(question):
    """  Handle both single and multiple response MCQs based on the question configuration. """
    selected_options = request.form.getlist(f'question_{question.id}_mcq')
    # Only process if they selected something
    if selected_options:
        selected_option_ids = [int(opt_id) for opt_id in selected_options]

        if question.allow_multiple_responses:
            # Multi-response.
            return handle_multiple_response_mcq(selected_option_ids, question)
        else:
            # Single-response.
            return handle_single_mcq(selected_option_ids, question)
    else:
        # No options selected, but not a failure.
        return True, False


# Public web routes.
@main_bp.route("/")
def home():
    """ Show the home page. """
    form = MeetingCheckinForm()
    poll_form = PollVoteForm()
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

    all_polls = Poll.query.filter(
        Poll.poll_expires.is_(None) |
        (Poll.poll_expires > datetime.now())
    ).all()

    voted_questions = set()
    voted_options = set()
    user_frq_responses = {}

    if current_user.is_authenticated:
        voter_records = PollVoter.query.filter_by(user_id=current_user.id).all()
        voted_questions = {voter.question_id for voter in voter_records}
        voted_options = {voter.option_id for voter in voter_records}

        frq_records = PollFreeResponse.query.filter_by(user_id=current_user.id).all()
        user_frq_responses = {frq.question_id: frq.response_text for frq in frq_records}
        voted_questions.update(user_frq_responses.keys())

    return render_template(
        "index.html",
        page_title = "Home",
        recent_meetings = recent_meetings,
        featured_meeting = featured_meeting,
        polls=all_polls,
        voted_questions=voted_questions,
        voted_options=voted_options,
        user_frq_responses=user_frq_responses,
        form = form,
        poll_form = poll_form
    )

@main_bp.route("/events/")
def events_list():
    """ Show the event list page. """
    all_meetings = Meetings.query.order_by(desc(Meetings.id)).all()
    visible_meetings = []
    form = CreateMeetingForm()
    if current_user.is_authenticated and current_user.role == "admin":
        return render_template("events.html",
                               page_title = "Meetings",
                               meetings = all_meetings,
                               form = form)
    else:
        for meeting in all_meetings:
            if meeting.admin_only is not True:
                visible_meetings.append(meeting)
        return render_template("events.html",
                               page_title = "Meetings",
                               meetings = visible_meetings,
                               form = form)

@main_bp.route("/event/<int:meeting_id>/")
def user_event(meeting_id):
    """ Show a page with the details of a single meeting. """
    form = MeetingCheckinForm()
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
        all_attachments = attachments,
        form = form
    )

@main_bp.route("/event/check-in/<int:meeting_id>/", methods = ["POST"])
@login_required
def event_check_in(meeting_id):
    """ Check into a single meeting from the homepage. """
    if Meetings.query.filter_by(id = meeting_id).first() is not None:
        form = MeetingCheckinForm()
        if form.validate_on_submit():
            code = form.code.data
            meeting = Meetings.query.filter_by(id = meeting_id).first_or_404()
            if meeting.state == "active":
                if Attendees.query.filter_by(
                meeting = meeting_id,
                username = current_user.username
                ).first() is None:
                    if sha_hash(code) == meeting.code_hash:
                        # Check for admin-only meeting status.
                        if meeting.admin_only and current_user.role != "admin":
                            flash("Check-in failed. "
                                  "This meeting is restricted to administrators only.",
                                "danger")
                        else:
                            if current_user.activated is False:
                                # User not activated, log them out and return an error.
                                logout_user()
                                flash(("Check-in failed. "
                                    "Your account is not activated. Please check in again."))
                                return redirect(url_for("auth.login"))
                            # Meeting active, add the user as an attendee.
                            attendance = Attendees(
                                username = current_user.username,
                                meeting = meeting_id)
                            db.session.add(attendance)
                            db.session.commit()
                            flash("Check-in succeeded. Attendance updated successfully.", "success")
                    else:
                        # Invalid meeting code.
                        flash("Check-in failed. Meeting code is invalid.", "danger")
                else:
                    # Already an attendee.
                    flash("Check-in failed. You are already marked as an attendee.", "danger")
            else:
                # Meeting inactive, return an error message.
                flash("Check-in failed. Specified meeting is inactive.", "danger")
        else:
            # Form validation failed.
            flash("Check-in failed. Please ensure all fields are filled out correctly.", "danger")
    else:
        # Meeting does not exist.
        flash("Check-in failed. Specified meeting does not exist.", "danger")
    return redirect(url_for("main.home"))

@main_bp.route('/uploads/<name>')
def download_file(name):
    """ Serve an uploaded file. """
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], name)

@main_bp.route('/submit-poll/<int:poll_id>', methods=['POST'])
@login_required
def submit_poll(poll_id):
    """Handle bulk submission of all questions in a poll."""
    submission_successful = True
    changes_made = False
    successes = 0
    failures = 0
    poll = Poll.query.get_or_404(poll_id)
    if poll.poll_expires and poll.poll_expires <= datetime.now():
        flash("Poll has expired. You cannot submit responses.", "danger")
        return redirect(url_for('main.home'))

    try:
        for question in poll.questions:
            if question.is_free_response:
                # Handle FRQ
                status, changes = handle_frq(question)
                changes_made = changes_made or changes
                submission_successful = submission_successful and status
                if status:
                    successes += 1
                else:
                    failures += 1
            else:
                # Handle MCQ (both single and multiple response)
                status, changes = handle_mcq(question)
                changes_made = changes_made or changes
                submission_successful = submission_successful and status
                if status:
                    successes += 1
                else:
                    failures += 1

        db.session.commit()
        if submission_successful and changes_made:
            flash("All responses submitted successfully!", "success")
        elif submission_successful and not changes_made:
            # No changes were made, but no failures either (e.g. all responses were the same as before).
            flash("No changes were made to any responses.", "success")
        else:
            flash(f"Some responses were not submitted successfully. Successes: {successes}, Failures: {failures}", "danger")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error submitting poll: {str(e)}")
        flash("An error occurred while saving your responses. Please try again.", "danger")

    return redirect(url_for('main.home'))

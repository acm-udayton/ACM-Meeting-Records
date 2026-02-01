#!/usr/bin/env python
# app/blueprints/main.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz), Thomas Crossman (github.com/crossmant1)
Last Modified: 1/24/2026

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
    PollQuestion,
    PollFreeResponse
)
from app.extensions import db
from app.utils import sha_hash

main_bp = Blueprint('main', __name__, template_folder='templates')

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

    all_polls = Poll.query.all()

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
        return render_template("events.html", page_title = "Meetings", meetings = all_meetings, form = form)
    else:
        for meeting in all_meetings:
            if meeting.admin_only is not True:
                visible_meetings.append(meeting)
        return render_template("events.html", page_title = "Meetings", meetings = visible_meetings, form = form)

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
                            flash("Check-in failed. This meeting is restricted to administrators only.",
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



@main_bp.route('/polls')
def show_polls():
    """Fetch all polls"""
    polls = Poll.query.all()

    voted_question_ids = set()

    if current_user.is_authenticated:
        user_votes = PollVoter.query.filter_by(user_id=current_user.id).all()  # Use .id
        voted_question_ids = {vote.question_id for vote in user_votes}

    return redirect(url_for('main.home'))


@main_bp.route('/vote/<int:option_id>', methods=['POST'])
@login_required
def vote_option(option_id):
    """Handle voting for a poll option."""
    option = PollOption.query.get_or_404(option_id)
    question_id = option.question_id

    existing_vote = PollVoter.query.filter_by(
        user_id=current_user.id,
        question_id=question_id
    ).first()

    if existing_vote:
        old_option = PollOption.query.get(existing_vote.option_id)

        if old_option.votes > 0:
            old_option.votes -= 1

        option.votes += 1

        existing_vote.option_id = option_id

        db.session.commit()
        flash("Vote changed successfully!", "success")
        return redirect(url_for('main.home'))

    # New vote
    option.votes += 1
    new_voter = PollVoter(
        user_id=current_user.id, 
        question_id=question_id,
        option_id=option_id
    )

    db.session.add(new_voter)
    db.session.commit()

    flash("Vote submitted!", "success")
    return redirect(url_for('main.home'))

@main_bp.route('/submit-frq/<int:question_id>', methods=['POST'])
@login_required
def submit_frq(question_id):
    """Handle free response question submission."""
    question = PollQuestion.query.get_or_404(question_id)

    # Verify it's actually an FRQ
    if not question.is_free_response:
        flash("Invalid request.", "danger")
        return redirect(url_for('main.home'))

    response_text = request.form.get('response_text', '').strip()

    if not response_text:
        flash("Please enter a response.", "danger")
        return redirect(url_for('main.home'))

    # Check if user already submitted a response
    existing_response = PollFreeResponse.query.filter_by(
        user_id=current_user.id,
        question_id=question_id
    ).first()

    if existing_response:
        # Update existing response
        existing_response.response_text = response_text
        db.session.commit()
        flash("Response updated successfully!", "success")
    else:
        # Create new response
        new_response = PollFreeResponse(
            user_id=current_user.id,
            question_id=question_id,
            response_text=response_text
        )
        db.session.add(new_response)
        db.session.commit()
        flash("Response submitted!", "success")

    return redirect(url_for('main.home'))

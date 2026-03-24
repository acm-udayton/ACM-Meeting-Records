#!/usr/bin/env python
# app/blueprints/admin.py

"""
Project Name: ACM-Meeting-Records 
Project Author(s): Thomas Crossman (github.com/crossmant1), Joseph Lefkovitz (github.com/lefkovitz)
Last Modfied: March 22, 2026. 

File Purpose: Polling routes for polling system
"""

# Standard library imports.
from datetime import datetime

# Third-party imports.
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
)
from flask_login import login_required, current_user

# Local application imports.
from app.extensions import db
from app.models import Poll, PollQuestion, PollOption, PollVoter
from app.forms import CreatePollForm, DeletePollForm
from app.__init__ import admin_required

polls_bp = Blueprint('polls', __name__, url_prefix='/admin', template_folder='templates')


@polls_bp.route("/polls/")
@login_required
@admin_required
def polls_list():
    """ Show the polls. """
    all_polls = Poll.query.all()
    form = CreatePollForm()
    delete_poll_form = DeletePollForm()
    # Get all question IDs the current user has voted on
    voted_questions = set()
    if current_user.is_authenticated:
        voter_records = PollVoter.query.filter_by(user_id=current_user.id).all()
        voted_questions = {voter.question_id for voter in voter_records}

    return render_template("admin/polls.html",
                          page_title="Polls",
                          polls=all_polls,
                          voted_questions=voted_questions,
                          form=form,
                          delete_poll_form=delete_poll_form,
                          datetime_now=datetime.now())

@polls_bp.route("/create-poll/", methods=["POST"])
@login_required
@admin_required
def create_poll():
    """Create a new poll from admin dashboard."""
    form = CreatePollForm()
    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", "danger")
        return redirect(url_for("polls.polls_list"))
    else:
        if form.poll_expires.data and form.poll_expires.data <= datetime.now():
            flash("Poll expiration datetime must be in the future.", "danger")
            return redirect(url_for("polls.polls_list"))
        poll = Poll(title=form.title.data, poll_expires=form.poll_expires.data)
        db.session.add(poll)
        db.session.flush()

        for question_form in form.questions.entries:
            is_frq = question_form.form.is_free_response.data
            allow_multiple = question_form.form.allow_multiple_responses.data
            private_votes = question_form.form.private_vote.data


            question = PollQuestion(
                poll_id=poll.id,
                question_text=question_form.form.question_text.data,
                is_free_response=is_frq,
                allow_multiple_responses=allow_multiple if not is_frq else False,  # Only for MCQs
                private_vote = private_votes
            )
            db.session.add(question)
            db.session.flush()

            # Only add options if it's NOT a free response question
            if not is_frq:
                for option_form in question_form.form.options.entries:
                    option = PollOption(
                        question_id=question.id,
                        option_text=option_form.form.option_text.data
                    )
                    db.session.add(option)

        db.session.commit()
        flash("Poll created successfully!", "success")
        return redirect(url_for("polls.polls_list"))

@polls_bp.route("/delete-poll/<int:poll_id>/", methods=["POST"])
@login_required
@admin_required
def delete_poll(poll_id):
    """Delete a poll."""
    poll = Poll.query.get_or_404(poll_id)
    db.session.delete(poll)
    db.session.commit()
    flash("Poll deleted successfully!", "success")

    return redirect(url_for("polls.polls_list"))

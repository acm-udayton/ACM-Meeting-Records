#!/usr/bin/env python
# app/blueprints/admin.py

"""
Project Name: ACM-Meeting-Records 
Project Author(s): Thomas Crossman (github.com/crossmant1)

File Purpose: Polling routes for polling system

Last Modfied: January 24, 2024. 
"""

# Standard library imports.

# Third-party imports.
from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    abort,
    redirect,
    url_for,
    flash,
    current_app
)
from flask_login import login_required, current_user

# Local application imports.
from app.extensions import db
from app.models import Poll, PollQuestion, PollOption, PollVoter
from app.__init__ import admin_required

polls_bp = Blueprint('polls', __name__, url_prefix='/admin', template_folder='templates')


@polls_bp.route("/polls/")
@login_required
@admin_required
def polls_list():
    """ Show the polls. """
    all_polls = Poll.query.all()
    # Get all question IDs the current user has voted on
    voted_questions = set()
    if current_user.is_authenticated:
        voter_records = PollVoter.query.filter_by(user_id=current_user.id).all()
        voted_questions = {voter.question_id for voter in voter_records}

    return render_template("admin/polls.html",
                          page_title="Polls",
                          polls=all_polls,
                          voted_questions=voted_questions)

@polls_bp.route("/create-poll/", methods= ["POST"])
@login_required
@admin_required
def create_poll():
    """Create a new poll from admin dashboard."""
    poll_title=request.form["title"]
    poll= Poll(title=poll_title)
    db.session.add(poll)
    db.session.flush()

    questions={}

    for key, value in request.form.items():
        if key.startswith("questions["):
            parts= key.replace("]","").split("[")

            q_index= int(parts[1])

            if q_index not in questions:
                questions[q_index]= {"text": None, "options": {}}

            if parts[2]== "text":
                questions[q_index]["text"]= value.strip()

            elif parts[2]== "options":
                # Store options with their index to maintain order
                option_index = int(parts[3])
                questions[q_index]["options"][option_index] = value.strip()

    # Convert options dict to sorted list
    for q_data in questions.values():
        q_data["options"] = [q_data["options"][i] for i in sorted(q_data["options"].keys())]

    for q in questions.values():
        if not q["text"] or len(q["options"]) < 2:
            continue

        question = PollQuestion(poll_id=poll.id, question_text=q["text"])
        db.session.add(question)
        db.session.flush()

        for opt_text in q["options"]:
            option = PollOption(
                question_id=question.id,
                option_text=opt_text
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
    poll=Poll.query.get_or_404(poll_id)
    db.session.delete(poll)
    db.session.commit()
    flash("Poll deleted successfully!", "success")

    return redirect(url_for("polls.polls_list"))

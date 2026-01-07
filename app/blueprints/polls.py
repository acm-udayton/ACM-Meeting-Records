#!/usr/bin/env python
# app/blueprints/admin.py

"""
Project Name: ACM-Meeting-Records 
Project Author(s): Thomas Crossman

File Purpose: Polling routes for polling system
"""

# Standard library imports.
import datetime
import os

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
from werkzeug.utils import secure_filename

# Local application imports.
from app.extensions import db
from app.models import Poll, PollQuestion, PollOption
from app.utils import generate_meeting_code, sha_hash
from app.__init__ import admin_required

polls_bp = Blueprint('polls', __name__, url_prefix='/admin', template_folder='templates')


@polls_bp.route("/polls/")
@login_required
@admin_required
def polls_list():
    """ Show the polls. """
    all_polls = Poll.query.all()
    return render_template("admin/polls.html", page_title = "Polls", polls = all_polls)


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
            
            q_intex= int(parts[1]) # changes format from q[0]o[0] to ['q', '0', 'o', '0']

            if q_intex not in questions:
                questions[q_intex]= {"text": None, "options": []}

            if parts[2]== "text":
                questions[q_intex]["text"]= value.strip()

            elif parts[2]== "options":
                questions[q_intex]["options"].append(value.strip())

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
    
    return redirect(url_for("admin.create_poll"))    

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
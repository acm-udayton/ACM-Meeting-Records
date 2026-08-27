#!/usr/bin/env python
# app/blueprints/polls/routes.py

"""
Project Name: ACM-Meeting-Records 
Project Author(s): Thomas Crossman (github.com/crossmant1), Joseph Lefkovitz (github.com/lefkovitz)
Last Modfied: August 1, 2026. 

File Purpose: Polling routes for polling system
"""

# Standard library imports.
from datetime import datetime

# Third-party imports.
from flask import (
    Blueprint,
    abort,
    render_template,
    redirect,
    url_for,
    flash,
)
from flask_login import login_required, current_user

# Local application imports.
from app.forms import CreatePollForm, DeletePollForm
from app.services.polls_service import (
    PollResultStatus,
    create_poll as create_poll_service,
    delete_poll as delete_poll_service,
    get_polls_list_data,
)
from app.__init__ import admin_required

polls_bp = Blueprint('polls', __name__, url_prefix='/admin', template_folder='templates')


def flash_form_errors(form):
    """Flash human-readable validation errors, including nested FieldList/FormField entries."""
    for field in form._fields.values():
        if not field.errors:
            continue

        if hasattr(field, "entries"):
            for entry in field.entries:
                if not entry.errors:
                    continue

                for nested_name, nested_errors in entry.errors.items():
                    nested_field = getattr(entry.form, nested_name, None)
                    nested_label = (
                        nested_field.label.text
                        if nested_field is not None and hasattr(nested_field, "label")
                        else nested_name.replace("_", " ").title()
                    )
                    for error in nested_errors:
                        flash(f"Error in {nested_label}: {error}", "danger")
            continue

        for error in field.errors:
            flash(f"Error in {field.label.text}: {error}", "danger")


@polls_bp.route("/polls/")
@login_required
@admin_required
def polls_list():
    """ Show the polls. """
    form = CreatePollForm()
    delete_poll_form = DeletePollForm()
    view_data = get_polls_list_data(current_user.id if current_user.is_authenticated else None)

    return render_template("admin/polls.html",
                          page_title="Polls",
                          polls=view_data.polls,
                          voted_questions=view_data.voted_questions,
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
        flash_form_errors(form)
        return redirect(url_for("polls.polls_list"))

    question_payloads = []
    for question_form in form.questions.entries:
        question_payloads.append(
            {
                "question_text": question_form.form.question_text.data,
                "is_free_response": question_form.form.is_free_response.data,
                "allow_multiple_responses": question_form.form.allow_multiple_responses.data,
                "private_vote": question_form.form.private_vote.data,
                "immutable_question": question_form.form.immutable_question.data,
                "options": [
                    option_form.form.option_text.data
                    for option_form in question_form.form.options.entries
                ],
            }
        )

    result = create_poll_service(
        title=form.title.data or "",
        poll_expires=form.poll_expires.data,
        questions=question_payloads,
    )
    if PollResultStatus.INVALID_POLL_EXPIRATION in result.statuses:
        flash("Poll expiration datetime must be in the future.", "danger")
        return redirect(url_for("polls.polls_list"))

    flash("Poll created successfully!", "success")
    return redirect(url_for("polls.polls_list"))

@polls_bp.route("/delete-poll/<int:poll_id>/", methods=["POST"])
@login_required
@admin_required
def delete_poll(poll_id):
    """Delete a poll."""
    result = delete_poll_service(poll_id)
    if PollResultStatus.POLL_NOT_FOUND in result.statuses:
        abort(404)

    flash("Poll deleted successfully!", "success")

    return redirect(url_for("polls.polls_list"))

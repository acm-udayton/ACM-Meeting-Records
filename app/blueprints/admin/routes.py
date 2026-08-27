#!/usr/bin/env python
# app/blueprints/admin/routes.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 8/1/2026

File Purpose: Administrator routes for the project.
"""
import datetime

from flask import Blueprint, render_template, request, jsonify, abort, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from app.__init__ import admin_required
from app.forms import AdminAttendeeAddForm, CreateMeetingForm
from app.services.admin_service import (
    AdminResultStatus,
    add_attachment as add_attachment_service,
    add_attendee as add_attendee_service,
    create_meeting as create_meeting_service,
    delete_meeting as delete_meeting_service,
    demote_user as demote_user_service,
    disable_user_account as disable_user_account_service,
    disable_user_mfa as disable_user_mfa_service,
    enable_user_account as enable_user_account_service,
    end_meeting as end_meeting_service,
    get_dashboard_data,
    get_users_list_data,
    promote_user as promote_user_service,
    remove_attachment as remove_attachment_service,
    remove_attendee as remove_attendee_service,
    reset_meeting_code as reset_meeting_code_service,
    reset_password as reset_password_service,
    save_minutes as save_minutes_service,
    start_meeting as start_meeting_service,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="templates")


@admin_bp.route("/dashboard/<int:meeting_id>/")
@login_required
@admin_required
def admin_dashboard(meeting_id):
    """Show the administrator dashboard page for a single meeting."""
    dashboard_data = get_dashboard_data(meeting_id)
    if dashboard_data is None:
        abort(404)

    add_attendee_form = AdminAttendeeAddForm()
    return render_template(
        "admin/dashboard.html",
        page_title=f"Meeting - {dashboard_data.meeting.title}",
        meeting=dashboard_data.meeting,
        attendees=dashboard_data.attendees,
        minutes=dashboard_data.minutes,
        attachments=dashboard_data.attachments,
        add_attendee_form=add_attendee_form,
    ), 200


@admin_bp.route("/create/", methods=["POST"])
@login_required
@admin_required
def event_create():
    """Create a new meeting based on form inputs."""
    form = CreateMeetingForm()
    if form.validate_on_submit():
        result = create_meeting_service(
            title=form.title.data,
            description=form.description.data,
            admin_only=form.admin_only.data,
            host_username=current_user.username,
        )
        if result.statuses == (AdminResultStatus.SUCCESS,):
            return redirect(url_for("admin.admin_dashboard", meeting_id=result.meeting.id))

    flash("Meeting creation failed. Please check the input fields and try again.")
    return redirect(url_for("main.events_list"))


@admin_bp.route("/start/<int:meeting_id>/", methods=["POST"])
@login_required
@admin_required
def event_start(meeting_id):
    """Start a single meeting from the administrator dashboard."""
    if current_user.role != "admin":
        abort(403)

    result = start_meeting_service(meeting_id, current_user.username)
    if result.statuses == (AdminResultStatus.SUCCESS,):
        return jsonify(
            {
                "success": True,
                "meeting_id": meeting_id,
                "message": "Meeting started successfully.",
                "meeting_code": result.meeting_code,
            }
        ), 200

    if result.statuses == (AdminResultStatus.MEETING_NOT_FOUND,):
        return jsonify(
            {
                "success": False,
                "meeting_id": meeting_id,
                "message": "Specified meeting does not exist.",
            }
        ), 400

    return jsonify(
        {
            "success": False,
            "meeting_id": meeting_id,
            "message": f"Meeting could not be started because it is already {result.meeting.state}.",
        }
    ), 400


@admin_bp.route("/reset-code/<int:meeting_id>/")
@login_required
@admin_required
def reset_code(meeting_id):
    """Reset the meeting join code for a single meeting."""
    if current_user.role != "admin":
        abort(403)

    result = reset_meeting_code_service(meeting_id)
    if result.statuses == (AdminResultStatus.SUCCESS,):
        return redirect(f"/admin/show-code?code={result.meeting_code}")

    return render_template(
        "error.html",
        page_title="400 Error",
        error_message="This meeting is not active.",
    ), 400


@admin_bp.route("/show-code/")
@login_required
@admin_required
def show_code():
    """Show the meeting join code for a single meeting."""
    code = request.args.get("code")
    if code is not None:
        return render_template("code.html", page_title="Meeting Code", code=code)
    abort(404)


@admin_bp.route("/end/<int:meeting_id>/", methods=["POST"])
@login_required
@admin_required
def event_end(meeting_id):
    """End a single meeting from the administrator dashboard."""
    if current_user.role != "admin":
        abort(403)

    result = end_meeting_service(meeting_id)
    if result.statuses == (AdminResultStatus.SUCCESS,):
        return jsonify(
            {
                "success": True,
                "meeting_id": meeting_id,
                "message": "Meeting ended successfully.",
            }
        ), 200

    return jsonify(
        {
            "success": False,
            "meeting_id": meeting_id,
            "message": f"Meeting could not be ended because it is currently {result.meeting.state}.",
        }
    ), 400


@admin_bp.route("/attendees/<int:meeting_id>/", methods=["POST"])
@login_required
@admin_required
def event_attendees(meeting_id):
    """Add an attendee to a single meeting from the administrator dashboard."""
    form = AdminAttendeeAddForm()
    if form.validate_on_submit():
        result = add_attendee_service(meeting_id, form.username.data)
        if result.statuses == (AdminResultStatus.SUCCESS,):
            return jsonify(
                {
                    "success": True,
                    "meeting_id": meeting_id,
                    "message": f"Attendee {result.attendee.username} checked in successfully.",
                }
            ), 201

        if result.statuses == (AdminResultStatus.USER_NOT_FOUND,):
            return jsonify(
                {
                    "success": False,
                    "meeting_id": meeting_id,
                    "message": f"Attendee {form.username.data} does not exist.",
                }
            ), 400
        if result.statuses == (AdminResultStatus.ATTENDEE_EXISTS,):
            return jsonify(
                {
                    "success": False,
                    "meeting_id": meeting_id,
                    "message": f"Attendee {form.username.data} is already checked in.",
                }
            ), 400

        return jsonify(
            {
                "success": False,
                "meeting_id": meeting_id,
                "message": "Specified meeting does not exist.",
            }
        ), 400

    return jsonify(
        {
            "success": False,
            "meeting_id": meeting_id,
            "message": "Invalid form submission.",
        }
    ), 400


@admin_bp.route("/remove-attendee/<int:meeting_id>/<int:attendee_id>/", methods=["POST"])
@login_required
@admin_required
def event_remove_attendee(meeting_id, attendee_id):
    """Remove an attendee from a single meeting from the administrator dashboard."""
    result = remove_attendee_service(meeting_id, attendee_id)
    if result.statuses == (AdminResultStatus.SUCCESS,):
        return jsonify(
            {
                "success": True,
                "meeting_id": meeting_id,
                "message": "Attendee removed successfully.",
            }
        ), 200

    return jsonify(
        {
            "success": False,
            "meeting_id": meeting_id,
            "message": "Attendee could not be found.",
        }
    ), 400


@admin_bp.route("/minutes/<int:meeting_id>/", methods=["POST"])
@admin_bp.route("/minutes/<int:meeting_id>/<int:minutes_id>/", methods=["POST"])
@login_required
@admin_required
def event_minutes(meeting_id, minutes_id=None):
    """Add minutes for a single meeting from the administrator dashboard."""
    meeting_minutes = request.form["meeting_minutes"]
    result = save_minutes_service(meeting_id, meeting_minutes, current_user.username, minutes_id)
    if result.statuses == (AdminResultStatus.SUCCESS,):
        return jsonify(
            {
                "success": True,
                "meeting_id": meeting_id,
                "minutes_id": result.minutes_entry.id,
                "message": "Meeting minutes saved successfully.",
            }
        ), 201

    return jsonify(
        {
            "success": False,
            "meeting_id": meeting_id,
            "message": "Meeting minutes could not be saved due to invalid minutes entry.",
        }
    ), 400


@admin_bp.route("/add-attachment/<int:meeting_id>/", methods=["POST"])
@login_required
@admin_required
def event_add_attachment(meeting_id):
    """Add an attachment to a single meeting from the administrator dashboard."""
    if "file" not in request.files:
        return jsonify(
            {
                "success": False,
                "meeting_id": meeting_id,
                "message": "No file part in the request.",
            }
        ), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify(
            {
                "success": False,
                "meeting_id": meeting_id,
                "message": "No selected file.",
            }
        ), 400

    result = add_attachment_service(meeting_id, uploaded_file, current_app.config["UPLOAD_FOLDER"])
    if result.statuses == (AdminResultStatus.SUCCESS,):
        return jsonify(
            {
                "success": True,
                "meeting_id": meeting_id,
                "message": "Attachment added successfully.",
            }
        ), 201

    if result.statuses == (AdminResultStatus.INVALID_FILE_TYPE,):
        return jsonify(
            {
                "success": False,
                "meeting_id": meeting_id,
                "message": "File type not allowed.",
            }
        ), 400

    return jsonify(
        {
            "success": False,
            "meeting_id": meeting_id,
            "message": "Specified meeting does not exist.",
        }
    ), 400


@admin_bp.route("/remove-attachment/<int:meeting_id>/<int:attachment_id>/", methods=["POST"])
@login_required
@admin_required
def event_remove_attachment(meeting_id, attachment_id):
    """Remove an attachment from a single meeting from the administrator dashboard."""
    result = remove_attachment_service(meeting_id, attachment_id)
    if result.statuses == (AdminResultStatus.SUCCESS,):
        return jsonify(
            {
                "success": True,
                "meeting_id": meeting_id,
                "message": "Attachment removed successfully.",
            }
        ), 200

    return jsonify(
        {
            "success": False,
            "meeting_id": meeting_id,
            "message": "Attachment could not be found.",
        }
    ), 400


@admin_bp.route("/delete/<int:meeting_id>/", methods=["POST"])
@login_required
@admin_required
def event_delete(meeting_id):
    """Delete a single meeting from the administrator dashboard."""
    result = delete_meeting_service(meeting_id)
    if result.statuses != (AdminResultStatus.SUCCESS,):
        abort(404)
    return redirect(url_for("main.events_list"))


@admin_bp.route("/users/")
@login_required
@admin_required
def users_list():
    """Show the users index page."""
    since_param = request.args.get("since")
    since_date = None
    if since_param:
        try:
            since_date = datetime.datetime.strptime(since_param, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date format for 'since' filter. Use YYYY-MM-DD.", "danger")
            since_param = None

    view_data = get_users_list_data(since_date)
    return render_template(
        "admin/users.html",
        page_title="Users",
        users=view_data.users,
        total_meetings=view_data.total_meetings,
        most_recent_meeting_date=view_data.most_recent_meeting_date,
        active_user_count=view_data.active_user_count,
        since=since_param,
    )


@admin_bp.route("/users/reset-password/<int:user_id>/", methods=["POST"])
@login_required
@admin_required
def reset_user_password(user_id):
    """Reset a user's password."""
    result = reset_password_service(user_id, request.form["new_password"])
    if result.statuses == (AdminResultStatus.SUCCESS,):
        flash(f"Password for user {result.user.username} reset successfully.", "success")
    else:
        flash("The requested user could not be found.", "danger")
    return redirect(url_for("admin.users_list"))


@admin_bp.route("/users/promote/<int:user_id>/", methods=["POST"])
@login_required
@admin_required
def promote_user(user_id):
    """Promote a user to an admin role."""
    result = promote_user_service(user_id)
    if result.statuses == (AdminResultStatus.SUCCESS,):
        flash(f"User {result.user.username} promoted to admin successfully.", "success")
    elif result.statuses == (AdminResultStatus.ALREADY_ADMIN,):
        flash(f"User {result.user.username} is already an admin.", "danger")
    else:
        flash("The requested user could not be found.", "danger")
    return redirect(url_for("admin.users_list"))


@admin_bp.route("/users/demote/<int:user_id>/", methods=["POST"])
@login_required
@admin_required
def demote_user(user_id):
    """Demote a user to a user role."""
    result = demote_user_service(user_id, current_user.id)
    if result.statuses == (AdminResultStatus.SUCCESS,):
        flash(f"User {result.user.username} demoted to user successfully.", "success")
    elif result.statuses == (AdminResultStatus.CANNOT_DEMOTE_SELF,):
        flash("You cannot demote your own account.", "danger")
    elif result.statuses == (AdminResultStatus.ALREADY_USER,):
        flash(f"User {result.user.username} is already a user.", "danger")
    else:
        flash("The requested user could not be found.", "danger")
    return redirect(url_for("admin.users_list"))


@admin_bp.route("/users/disable-mfa/<int:user_id>/", methods=["POST"])
@login_required
@admin_required
def disable_user_mfa(user_id):
    """Disable two-factor authentication for a user."""
    result = disable_user_mfa_service(user_id)
    if result.statuses == (AdminResultStatus.SUCCESS,):
        flash(f"Two-factor authentication for user {result.user.username} disabled successfully.", "success")
    elif result.statuses == (AdminResultStatus.MFA_ALREADY_DISABLED,):
        flash(f"User {result.user.username} does not have two-factor authentication enabled.", "danger")
    else:
        flash("The requested user could not be found.", "danger")
    return redirect(url_for("admin.users_list"))


@admin_bp.route("/users/disable-account/<int:user_id>/", methods=["POST"])
@login_required
@admin_required
def disable_user_account(user_id):
    """Disable a user's account."""
    result = disable_user_account_service(user_id)
    if result.statuses == (AdminResultStatus.SUCCESS,):
        flash(f"Account for user {result.user.username} disabled successfully.", "success")
    elif result.statuses == (AdminResultStatus.ACCOUNT_ALREADY_DISABLED,):
        flash(f"User {result.user.username}'s account is already disabled.", "danger")
    else:
        flash("The requested user could not be found.", "danger")
    return redirect(url_for("admin.users_list"))


@admin_bp.route("/users/enable-account/<int:user_id>/", methods=["POST"])
@login_required
@admin_required
def enable_user_account(user_id):
    """Enable a user's account."""
    result = enable_user_account_service(user_id)
    if result.statuses == (AdminResultStatus.SUCCESS,):
        flash(f"Account for user {result.user.username} enabled successfully.", "success")
    elif result.statuses == (AdminResultStatus.ACCOUNT_ALREADY_ENABLED,):
        flash(f"User {result.user.username}'s account is already enabled.", "danger")
    else:
        flash("The requested user could not be found.", "danger")
    return redirect(url_for("admin.users_list"))

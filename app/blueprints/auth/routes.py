#!/usr/bin/env python
# app/blueprints/auth/routes.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 8/1/2026

File Purpose: Authentication routes for the project.
"""

# Third-party imports.
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

# Local application imports.
from app.forms import AccountUpdateForm, LoginForm, SignUpFormEmail, SignUpFormUsername
from app.services.auth_service import (
    AccountViewData,
    AuthLoginResult,
    AuthOperationResult,
    AuthResultStatus,
    get_account_view_data,
    authenticate_user,
    register_user,
    update_account as update_account_service,
)

auth_bp = Blueprint("auth", __name__)


def _flash_login_statuses(result: AuthLoginResult) -> bool:
    """Flash login feedback and return whether relogin is required."""
    needs_relogin = False

    for status in result.statuses:
        if status == AuthResultStatus.USER_NOT_FOUND:
            flash("Login attempt failed. User does not exist.", "danger")
            needs_relogin = True
        elif status == AuthResultStatus.ACCOUNT_NOT_ACTIVATED:
            flash(
                "Login attempt failed. Account is not activated. "
                "Please contact the system administrator for approval.",
                "danger",
            )
            needs_relogin = True
        elif status == AuthResultStatus.INVALID_PASSWORD:
            flash(
                "Login attempt failed. Please try again or contact "
                "the system administrator to reset your credentials.",
                "danger",
            )
            needs_relogin = True

    return needs_relogin


# Authentication routes.
@auth_bp.route("/login/", methods=["GET", "POST"])
def login():
    """Show a login page and process submissions."""
    form = LoginForm()
    if form.validate_on_submit():
        result = authenticate_user(form.username.data, form.password.data, request.remote_addr)

        if _flash_login_statuses(result):
            return redirect(url_for("auth.login"))

        if result.statuses and result.statuses[0] in {
            AuthResultStatus.REQUIRE_TOTP_MFA,
            AuthResultStatus.REQUIRE_RECOVERY_MFA,
        }:
            session["mfa_user_id"] = result.user.id
            redirect_to = (
                "mfa.verify_totp"
                if result.statuses[0] == AuthResultStatus.REQUIRE_TOTP_MFA
                else "mfa.verify_recovery_code"
            )
            return redirect(url_for(redirect_to))

        if result.statuses and result.statuses[0] == AuthResultStatus.SUCCESS:
            login_user(result.user)

            if result.user.role == "admin":
                flash("Please enable multi-factor authentication for this administrator account!", "danger")

            return redirect(url_for("main.home"))

    # Process GET requests or failed validation.
    return render_template("login.html", page_title="User Log In", form=form)


@auth_bp.route("/sign-up/", methods=["GET", "POST"])
def sign_up():
    """Show a sign-up page and process submissions."""
    form = (
        SignUpFormEmail()
        if current_app.context["usernames"]["require_username_as_email"] == "True"
        else SignUpFormUsername()
    )

    if form.validate_on_submit():
        # Log the user out if active.
        if not current_user.is_anonymous:
            logout_user()

        result = register_user(form.username.data, form.password.data, request.remote_addr)

        if result.statuses and result.statuses[0] == AuthResultStatus.DUPLICATE_USERNAME:
            flash(
                "User creation failed. Username already registered. "
                "Try logging in instead or contact an administrator.",
                "danger",
            )
            return redirect(url_for("auth.sign_up"))

        flash("User creation succeeded. You can now log into your new account.", "success")
        return redirect(url_for("auth.login"))

    # Handle GET requests.
    if (
        current_app.context["usernames"]["enforce_usernames"] == "True"
        and current_app.context["usernames"]["require_username_as_email"] == "True"
    ):
        required_domain = current_app.context["usernames"]["username_email_domain"]
    else:
        required_domain = None

    return render_template(
        "sign_up.html",
        page_title="Create New Account",
        required_domain=required_domain,
        form=form,
    )


@auth_bp.route("/logout/")
@login_required
def logout():
    """Logout the user and redirect home."""
    logout_user()
    return redirect(url_for("main.home"))


# Account management routes.
@auth_bp.route("/my-account/")
@login_required
def my_account():
    """Show account details page with update form."""
    account_updated_form = AccountUpdateForm()
    account_view_data: AccountViewData = get_account_view_data(current_user.id)
    account_updated_form.start_semester.data = account_view_data.start_semester
    account_updated_form.grad_semester.data = account_view_data.grad_semester
    return render_template(
        "account.html",
        page_title="My Account",
        num_codes=account_view_data.num_codes,
        account_update_form=account_updated_form,
    )


@auth_bp.route("/update-account/", methods=["POST"])
@login_required
def update_account():
    """Update account details via the form /my-account/ page."""
    form = AccountUpdateForm()

    if form.validate_on_submit():
        result: AuthOperationResult = update_account_service(
            current_user.id,
            form.start_semester.data,
            form.grad_semester.data,
            form.password.data,
            current_user.username,
            request.remote_addr,
        )

        if result.statuses and result.statuses[0] != AuthResultStatus.SUCCESS:
            flash("Account update failed. Please try again.", "danger")
        else:
            flash("Account updated successfully.", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                if field == "csrf_token":
                    flash("Security Error: Invalid or missing form data. Please refresh and try again.", "danger")
                else:
                    flash(f"Error in the {getattr(form, field).label.text} field - {error}", "danger")
                current_app.logger.info(
                    (
                        "Account update attempt - failure: %s from IP %s - "
                        "Field: %s, Error: %s"
                    ),
                    current_user.username,
                    request.remote_addr,
                    field,
                    error,
                )
                # Only show the first error message to the user.
                break
            break

    # Return to account page for success or failure.
    return redirect(url_for("auth.my_account"))

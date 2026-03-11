#!/usr/bin/env python
# app/blueprints/auth.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 2/14/2026

File Purpose: Authentication routes for the project.
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
    session
)
from flask_login import login_user, logout_user, login_required, current_user

# Local application imports.
from app.extensions import db
from app.forms import LoginForm, SignUpFormEmail, SignUpFormUsername, AccountUpdateForm
from app.models import Users, RecoveryCodes

auth_bp = Blueprint('auth', __name__, template_folder='templates')


# Authentication routes.
@auth_bp.route("/login/", methods = ["GET", "POST"])
def login():
    """ Show a login page and process submissions. """
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username = form.username.data).first()

        needs_relogin = False

        # Existence check.
        if user is None:
            flash("Login attempt failed. User does not exist.", "danger")
            needs_relogin = True

        # Activation check.
        if user.activated is False:
            flash(
                "Login attempt failed. Account is not activated. "
                "Please contact the system administrator for approval.",
                "danger"
            )
            needs_relogin = True

        # Password check.
        if not user.check_password(form.password.data):
            current_app.logger.warning(
                "Login attempt as %s from IP %s - failed",
                form.username.data,
                request.remote_addr
            )
            flash(
                "Login attempt failed. Please try again or contact "
                "the system administrator to reset your credentials.",
                "danger"
            )
            needs_relogin = True

        # Redirect on login failure.
        if needs_relogin:
            return redirect(url_for("auth.login"))

        # MFA check.
        if user.mfa_active:
            # Store the user ID in the session temporarily - do not login yet.
            session['mfa_user_id'] = user.id
            if user.totp_active:
                redirect_to = 'mfa.verify_totp'
            else:
                redirect_to = 'mfa.verify_recovery_code'
            return redirect(url_for(redirect_to))

        # Admin without MFA warning.
        if user.role == "admin":
            flash("Please enable multi-factor authentication for this administrator account!")

        login_user(user)
        current_app.logger.info(
            "Login attempt as %s from IP %s - success",
            form.username.data,
            request.remote_addr
        )
        return redirect(url_for("main.home"))

    # Process GET requests or failed validation.
    return render_template("login.html", page_title = "User Log In", form=form)

@auth_bp.route("/sign-up/", methods = ["GET", "POST"])
def sign_up():
    """ Show a sign-up page and process submissions. """
    form = SignUpFormEmail() if current_app.context["usernames"]["require_username_as_email"] == "True" else SignUpFormUsername()

    if form.validate_on_submit():
        # Log the user out if active.
        if not current_user.is_anonymous:
            logout_user()
        uname = form.username.data
        pword = form.password.data
        conf_pword = form.confirm_password.data
        # Handle new username and password issues or create the new user.
        if Users.query.filter_by(username = uname).first() is not None:
            flash(
                "User creation failed. Username already registered. "
                "Try logging in instead or contact an administrator."
                , "danger"
                )
            return redirect(url_for("auth.sign_up"))
        elif (current_app.context["usernames"]["enforce_usernames"] == "True" and
              current_app.context["usernames"]["require_username_as_email"] == "True" and
              not uname.endswith(
                  current_app.context["usernames"]["username_email_domain"])):
            flash(
                ("User creation failed. Username must end with "
                f"{current_app.context['usernames']['username_email_domain']}."),
                "danger"
                )
            return redirect(url_for("auth.sign_up"))
        elif pword != conf_pword:
            flash("User creation failed. Passwords do not match.", "danger")
            return redirect(url_for("auth.sign_up"))
        else:
            current_app.logger.warning(
                "New user %s from IP %s",
                uname,
                request.remote_addr
            )
            new_user = Users(username = uname,
                             role = "user")
            new_user.set_password(pword)
            db.session.add(new_user)
            db.session.commit()
            flash("User creation succeeded. You can now log into your new account.", "success")
            return redirect(url_for("auth.login"))
    # Handle GET requests.
    else:
        if (current_app.context["usernames"]["enforce_usernames"] == "True" and
            current_app.context["usernames"]["require_username_as_email"] == "True"):
            required_domain = current_app.context["usernames"]["username_email_domain"]
        else:
            required_domain = None
        return render_template("sign_up.html",
                               page_title = "Create New Account",
                               required_domain=required_domain,
                               form = form)

@auth_bp.route("/logout/")
@login_required
def logout():
    """ Logout the user and redirect home. """
    logout_user()
    return redirect(url_for("main.home"))


# Account management routes.
@auth_bp.route("/my-account/")
@login_required
def my_account():
    """ Show account details page with update form. """
    account_updated_form = AccountUpdateForm()
    num_codes = RecoveryCodes.query.filter_by(user_id=current_user.id).count()
    account_updated_form.start_semester.data = current_user.joined
    account_updated_form.grad_semester.data = current_user.graduated
    return render_template("account.html",
                           page_title = "My Account",
                           num_codes=num_codes,
                           account_update_form=account_updated_form)

@auth_bp.route("/update-account/", methods = ["POST"])
def update_account():
    """ Update account details via the form /my-account/ page. """
    form = AccountUpdateForm()

    if form.validate_on_submit():

        current_app.logger.info(
            ("Account update attempt - success: %s from IP %s - "
            "start semester %s, end semester %s"),
            current_user.username,
            request.remote_addr,
            form.start_semester.data,
            form.grad_semester.data
        )
        update_user = db.session.get(Users, current_user.get_id())
        if form.password.data != "":
            update_user.set_password(form.password.data)

        # Update semesters (join and grad).
        update_user.joined = form.start_semester.data
        update_user.graduated = form.grad_semester.data

        # Update database and redirect.
        db.session.commit()
        flash("Account updated successfully.", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                if field == 'csrf_token':
                    flash("Security Error: Invalid or missing form data." \
                    " Please refresh and try again.", 'danger')
                else:
                    flash((f"Error in the {getattr(form, field).label.text} "
                        f" field - {error}"), "danger")
                current_app.logger.info(
                    ("Account update attempt - failure: %s from IP %s - "
                    "Field: %s, Error: %s"),
                    current_user.username,
                    request.remote_addr,
                    field,
                    error
                )
                # Only show the first error message to the user.
                break
            break

    # Return to account page for success or failure.
    return redirect(url_for("auth.my_account"))

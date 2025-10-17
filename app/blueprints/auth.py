#!/usr/bin/env python
# app/blueprints/auth.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 10/7/2025

File Purpose: Authentication routes for the project.
"""

# Standard library imports.
import re

# Third-party imports.
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user

# Local application imports.
from app.extensions import db
from app.models import Users

auth_bp = Blueprint('auth', __name__, template_folder='templates')


# Authentication routes.
@auth_bp.route("/login/", methods = ["GET", "POST"])
def login():
    """ Show a login page and process submissions. """
    if request.method =="POST":
        user = Users.query.filter_by(username = request.form["username"]).first()
        if user is not None:
            if user.check_password(request.form["password"]):
                login_user(user)
                current_app.logger.info(
                    "Login attempt as %s from IP %s - success",
                    request.form["username"],
                    request.remote_addr
                )
            else:
                current_app.logger.warning(
                    "Login attempt as %s from IP %s - failed",
                    request.form["username"],
                    request.remote_addr
                )
                flash(
                    "Login attempt failed. Please try again or contact "
                    "the system administrator to reset your credentials."
                )
                return redirect(url_for("auth.login"))
        else:
            flash("Login attempt failed. User does not exist.")
            return redirect(url_for("auth.login"))
        return redirect(url_for("main.home"))
    else:
        return render_template("login.html", page_title = "User Log In")

@auth_bp.route("/sign-up/", methods = ["GET", "POST"])
def sign_up():
    """ Show a sign-up page and process submissions. """
    if request.method == "POST":
        # Log the user out if active.
        if not current_user.is_anonymous:
            logout_user()
        uname = request.form["username"]
        pword = request.form["password"]
        conf_pword = request.form["confirm_password"]
        # Handle new username and password issues or create the new user.
        if Users.query.filter_by(username = uname).first() is not None:
            flash(
                "User creation failed. Username already registered. "
                "Try logging in instead or contact an administrator.")
            return redirect(url_for("auth.sign_up"))
        elif (current_app.context["usernames"]["enforce_usernames"] == "True" and
              not uname.endswith(
                  current_app.context["usernames"]["username_email_domain"])):
            flash(
                ("User creation failed. Username must end with "
                f"{current_app.context['usernames']['username_email_domain']}.")
                )
            return redirect(url_for("auth.sign_up"))
        elif pword != conf_pword:
            flash("User creation failed. Passwords do not match.")
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
            flash("User creation succeeded. You can now log into your new account.")
            return redirect(url_for("auth.login"))
    # Handle GET requests.
    else:
        return render_template("sign_up.html", page_title = "Create New Account")

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
    return render_template("account.html", page_title = "My Account")

@auth_bp.route("/update-account/", methods = ["POST"])
def update_account():
    """ Update account details via the form /my-account/ page. """

    form_password = request.form.get("password", "").strip()
    form_start = request.form.get("start_semester", "").strip().upper()
    form_grad = request.form.get("grad_semester", "").strip().upper()

    current_app.logger.info(
        ("Account update attempt: %s from IP %s - "
        "start semester %s, end semester %s"),
        current_user.username,
        request.remote_addr,
        form_start,
        form_grad
    )
    update_user = db.session.get(Users, current_user.get_id())
    if form_password != "":
        update_user.set_password(form_password)
    semester_regex = re.compile(r"^(FA|SP) \d{4}$|^$")
    # Validate start semester.
    if not semester_regex.fullmatch(form_start):
        flash(
            'Invalid format for Start Semester. Use "FA YYYY" or '
            '"SP YYYY" or leave it empty.', 'error'
        )
    else:
        update_user.joined = form_start

    # Validate graduation semester.
    if not semester_regex.fullmatch(form_grad):
        flash(
            'Invalid format for Graduation Semester. Use "FA YYYY" or '
            '"SP YYYY" or leave it empty.', 'error'
        )
    else:
        update_user.graduated = form_grad
    # Update database and redirect.
    db.session.commit()
    return redirect(url_for("auth.my_account"))

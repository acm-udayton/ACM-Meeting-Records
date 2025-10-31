#!/usr/bin/env python
# app/blueprints/auth.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 10/7/2025

File Purpose: Authentication routes for the project.
"""

# Standard library imports.
import base64
from io import BytesIO
import re

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
import pyotp
import qrcode

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
                # Check if 2FA is enabled for the user.
                if user.totp_active:
                    # Store the user ID in the session temporarily - do not login yet.
                    session['2fa_user_id'] = user.id
                    return redirect(url_for('auth.verify_2fa'))
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

@auth_bp.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    """ Handle the 2FA verification step during login. """
    # Ensure the user has passed the password stage
    user_id = session.get('2fa_user_id')
    print(f"User ID: {user_id}")
    if not user_id:
        flash('You must log in before using 2FA.', 'warning')
        return redirect(url_for('auth.login'))

    user = Users.query.get(user_id)
    if not user or not user.totp_active:
        flash('2FA not required or user not found.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        token = request.form.get('token')

        # Step 2: Verify TOTP Code
        if user.verify_totp(token):
            # Success - log the user in and clear the temporary session variable
            login_user(user)
            session.pop('2fa_user_id', None)
            current_app.logger.info(
                    "Login attempt as %s from IP %s - success with 2FA",
                    user.username,
                    request.remote_addr
            )
            return redirect(url_for('main.home'))

        flash('Invalid 2FA code.', 'danger')

    return '<h1>2FA Verification</h1><p>Enter the code from your Authenticator App:</p><form method="POST"><input name="token" placeholder="6-digit code"><br><button type="submit">Verify</button></form>'


@auth_bp.route('/setup-2fa')
@login_required
def setup_2fa():
    """ Setup Two-Factor Authentication for the current user. """
    # If 2FA is already enabled, just show the status and offer to disable/re-setup.
    if current_user.totp_active:
        return '<h1>2FA is Enabled</h1><p>You can regenerate your key if needed.</p><a href="/disable-2fa">Disable 2FA</a>'

    # 1. Get the provisioning URI
    current_user.generate_totp_secret()
    db.session.commit()
    uri = current_user.get_totp_uri()

    # 2. Generate the QR Code image data using 'qrcode'
    img = qrcode.make(uri)
    stream = BytesIO()
    # Save the image to the in-memory buffer as PNG
    img.save(stream, format='PNG')

    # 3. Encode image data for embedding in HTML
    qr_data = base64.b64encode(stream.getvalue()).decode('utf-8')

    # Store the URI or secret temporarily if needed for verification in a separate route
    session['2fa_setup_secret'] = current_user.totp_secret

    return f'''
    <h1>Setup Two-Factor Authentication</h1>
    <p>Scan this QR code with your authenticator app (e.g., Google Authenticator, Authy).</p>
    <img src="data:image/png;base64,{qr_data}" alt="QR Code">
    <p>Alternatively, enter the secret key manually: <strong>{current_user.totp_secret}</strong></p>
    <form action="{url_for('auth.verify_setup')}" method="POST">
        <input name="token" placeholder="Enter code from app to confirm setup">
        <button type="submit">Verify Setup</button>
    </form>
    '''
@auth_bp.route('/verify-setup', methods=['POST'])
@login_required
def verify_setup():
    """ Verify the TOTP code entered by the user during 2FA setup. """
    token = request.form.get('token')

    # Use the temporary secret stored in the session for verification
    secret = session.pop('2fa_setup_secret', None)

    if not secret:
        flash('2FA setup session expired. Start over.', 'danger')
        return redirect(url_for('auth.setup_2fa'))

    # Create a TOTP object with the secret from the session and verify the code
    if pyotp.TOTP(secret).verify(token):
        # Finalize setup: save the secret (already on the model) and enable 2FA
        current_user.totp_active = True
        db.session.commit()
        flash('Two-Factor Authentication successfully enabled!', 'success')
        return redirect(url_for('main.home'))
    else:
        # If verification fails, we don't save the secret or enable 2FA
        flash('Invalid code. Please try scanning and verifying again.', 'danger')
        return redirect(url_for('auth.setup_2fa'))


@auth_bp.route('/disable-2fa')
@login_required
def disable_2fa():
    """ Disable Two-Factor Authentication for the current user. """
    current_user.totp_active = False
    current_user.generate_totp_secret()
    db.session.commit()
    flash('Two-Factor Authentication has been disabled.', 'success')
    return redirect(url_for('main.home'))


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

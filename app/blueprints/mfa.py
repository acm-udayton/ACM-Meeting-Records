#!/usr/bin/env python
# app/blueprints/mfa.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 2/14/2026

File Purpose: Multi-factor authentication routes for the project.
"""

# Standard library imports.
import base64
from io import BytesIO

# Third-party imports.
import qrcode
import pyotp
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
from flask_login import login_user, login_required, current_user

# Local application imports.
from app.forms import TotpVerifyForm, TotpSetupForm, RecoveryCodeVerifyForm
from app.extensions import db
from app.models import Users, RecoveryCodes


mfa_bp = Blueprint('mfa', __name__, template_folder='templates')


@mfa_bp.route('/reset-recovery-codes/', methods=['GET'])
def reset_recovery_codes():
    """ Generate new recovery codes for the user. """
    # Clear old codes and generate new codes.
    for old_code in RecoveryCodes.query.filter_by(user_id=current_user.id).all():
        db.session.delete(old_code)

    # Ensure MFA is active for the user.
    user = Users.query.get(current_user.id)
    user.mfa_active = True

    # Store codes for display in template.
    codes = ""

    # Create 10 new codes.
    for _ in range(10):
        new_code = RecoveryCodes(user_id=current_user.id)
        code_value = new_code.generate_code()
        db.session.add(new_code)
        codes += f"{code_value}\t" if not codes.endswith("\t") else f"{code_value}\n"

    # Save to database.
    db.session.commit()
    return render_template("auth/reset-codes.html", page_title="MFA Recovery Codes", codes=codes)

@mfa_bp.route('/verify-recovery-code/', methods=['GET', 'POST'])
def verify_recovery_code():
    """ Authenticate with a recovery code during MFA login. """
    user_id = session.get('mfa_user_id')
    if not user_id:
        flash('You must log in before using a recovery code.', 'warning')
        return redirect(url_for('auth.login'))

    user = Users.query.get(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))

    form = RecoveryCodeVerifyForm()
    if form.validate_on_submit():
        code = form.token.data
        recovery_code_entry = RecoveryCodes.query.filter_by(user_id=user.id).all()
        for entry in recovery_code_entry:
            if entry.check_code(code):
                # Code used, so delete it.
                db.session.delete(entry)
                db.session.commit()
                login_user(user)
                session.pop('mfa_user_id', None)
                current_app.logger.info(
                    "Login attempt as %s from IP %s - success with recovery code",
                    user.username,
                    request.remote_addr
                )
                return redirect(url_for('main.home'))
        flash('Invalid recovery code.', 'danger')

    return render_template('auth/verify-code.html',
                           page_title='Verify MFA Recovery Code',
                           form=form)

@mfa_bp.route('/verify-totp/', methods=['GET', 'POST'])
def verify_totp():
    """ Handle the TOTP verification step during login. """
    # Ensure the user has passed the password stage.
    user_id = session.get('mfa_user_id')
    if not user_id:
        flash('You must log in before using TOTP MFA.', 'warning')
        return redirect(url_for('auth.login'))

    # Verify that the user exists and has TOTP active.
    user = Users.query.get(user_id)
    if not user or not user.totp_active:
        flash('TOTP MFA not required or user not found.', 'danger')
        return redirect(url_for('auth.login'))

    form = TotpVerifyForm()
    if form.validate_on_submit():
        token = form.token.data

        # Step 2: Verify TOTP Code
        if user.verify_totp(token):
            # Success - log the user in and clear the temporary session variable
            login_user(user)
            session.pop('mfa_user_id', None)
            current_app.logger.info(
                    "Login attempt as %s from IP %s - success with TOTP MFA",
                    user.username,
                    request.remote_addr
            )
            return redirect(url_for('main.home'))

        flash('Invalid TOTP MFA code.', 'danger')

    return render_template('auth/verify-totp.html', page_title='Verify MFA TOTP Code', form=form)

@mfa_bp.route('/setup-totp/')
@login_required
def setup_totp():
    """ Setup Two-Factor Authentication for the current user. """
    # If TOTP MFA is already enabled, just show the status and offer to disable/re-setup.
    if current_user.totp_active:

        flash("MFA with TOTP is already enabled. Disable it first please!", 'info')
        return redirect(url_for('auth.my_account'))

    form = TotpSetupForm()

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
    session['mfa_setup_secret'] = current_user.totp_secret

    return render_template('auth/setup-totp.html',
                           page_title='Setup TOTP MFA',
                           qr_data=qr_data,
                           totp_secret=current_user.totp_secret,
                           form=form)

@mfa_bp.route('/verify-totp-setup/', methods=['POST'])
@login_required
def verify_totp_setup():
    """ Verify the TOTP code entered by the user during setup. """
    form = TotpSetupForm()
    if form.validate_on_submit():
        token = form.token.data
        # Use the temporary secret stored in the session for verification
        secret = session.pop('mfa_setup_secret', None)
        if not secret:
            flash('TOTP MFA setup session expired. Start over.', 'danger')
            return redirect(url_for('mfa.setup_totp'))

        # Create a TOTP object with the secret from the session and verify the code
        if pyotp.TOTP(secret).verify(token):
            # Finalize setup: save the secret (already on the model) and enable MFA
            current_user.mfa_active = True
            current_user.totp_active = True
            db.session.commit()
            flash('TOTP MFA successfully enabled!', 'success')

            # Prompt user to set up recovery codes if not already present.
            if not RecoveryCodes.query.filter_by(user_id=current_user.id).first():
                return redirect(url_for('mfa.reset_recovery_codes'))
            return redirect(url_for('auth.my_account'))
        else:
            # If verification fails, we don't save the secret or enable MFA
            flash('Invalid code. Please try scanning and verifying again.', 'danger')
            return redirect(url_for('mfa.setup_totp'))

    else:
        flash('Invalid TOTP MFA setup form data.', 'danger')
        return redirect(url_for('mfa.setup_totp'))




@mfa_bp.route('/disable-totp/')
@login_required
def disable_totp():
    """ Disable Two-Factor Authentication for the current user. """
    current_user.totp_active = False
    current_user.generate_totp_secret()
    db.session.commit()
    flash('Two-Factor TOTP Authentication has been disabled.', 'success')
    return redirect(url_for('auth.my_account'))

@mfa_bp.route('/disable-mfa/')
@login_required
def disable_mfa():
    """ Disable Multi-Factor Authentication for the current user. """
    current_user.mfa_active = False
    current_user.totp_active = False
    current_user.totp_secret = None
    RecoveryCodes.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('Multi-Factor Authentication has been disabled.', 'success')
    return redirect(url_for('auth.my_account'))

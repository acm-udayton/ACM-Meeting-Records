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


def _generate_recovery_codes(user_id):
    """Replace a user's recovery codes and return their plaintext values once."""
    RecoveryCodes.query.filter_by(user_id=user_id).delete()
    code_values = []

    for _ in range(10):
        new_code = RecoveryCodes(user_id=user_id)
        code_values.append(new_code.generate_code())
        db.session.add(new_code)

    return "\n".join(
        "\t".join(code_values[index:index + 2])
        for index in range(0, len(code_values), 2)
    )


def _render_totp_setup(secret, form=None):
    """Render the TOTP setup page for a pending, uncommitted secret."""
    setup_form = form if form is not None else TotpSetupForm()
    uri = pyotp.TOTP(secret).provisioning_uri(
        name=current_user.username,
        issuer_name=current_app.config.get("TOTP_ISSUER_NAME")
    )

    img = qrcode.make(uri)
    stream = BytesIO()
    img.save(stream, format='PNG')
    qr_data = base64.b64encode(stream.getvalue()).decode('utf-8')

    return render_template(
        'auth/setup-totp.html',
        page_title='Setup TOTP MFA',
        qr_data=qr_data,
        totp_secret=secret,
        form=setup_form
    )


@mfa_bp.route('/reset-recovery-codes/', methods=['POST'])
@login_required
def reset_recovery_codes():
    """ Generate new recovery codes for the user. """
    # Ensure MFA is active for the user.
    user = db.session.get(Users, current_user.id)
    user.mfa_active = True
    codes = _generate_recovery_codes(current_user.id)

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

@mfa_bp.route('/setup-totp/', methods=['POST'])
@login_required
def setup_totp():
    """ Setup Two-Factor Authentication for the current user. """
    # If TOTP MFA is already enabled, just show the status and offer to disable/re-setup.
    if current_user.totp_active:

        flash("MFA with TOTP is already enabled. Disable it first please!", 'info')
        return redirect(url_for('auth.my_account'))

    pending_secret = pyotp.random_base32()
    session['mfa_setup_secret'] = pending_secret
    return _render_totp_setup(pending_secret)

@mfa_bp.route('/verify-totp-setup/', methods=['POST'])
@login_required
def verify_totp_setup():
    """ Verify the TOTP code entered by the user during setup. """
    form = TotpSetupForm()
    secret = session.get('mfa_setup_secret')

    if form.validate_on_submit():
        token = form.token.data
        if not secret:
            flash('TOTP MFA setup session expired. Start over.', 'danger')
            return redirect(url_for('auth.my_account'))

        # Create a TOTP object with the secret from the session and verify the code
        if pyotp.TOTP(secret).verify(token):
            # Finalize setup only after the pending secret has been verified.
            session.pop('mfa_setup_secret', None)
            current_user.totp_secret = secret
            current_user.mfa_active = True
            current_user.totp_active = True
            flash('TOTP MFA successfully enabled!', 'success')

            # Generate recovery codes within this protected POST when none exist.
            if not RecoveryCodes.query.filter_by(user_id=current_user.id).first():
                codes = _generate_recovery_codes(current_user.id)
                db.session.commit()
                return render_template(
                    "auth/reset-codes.html",
                    page_title="MFA Recovery Codes",
                    codes=codes
                )

            db.session.commit()
            return redirect(url_for('auth.my_account'))
        # Keep the pending secret available so the user can try again.
        flash('Invalid code. Please try scanning and verifying again.', 'danger')
        return _render_totp_setup(secret, form)

    flash('Invalid TOTP MFA setup form data.', 'danger')
    if secret:
        return _render_totp_setup(secret, form)
    return redirect(url_for('auth.my_account'))


@mfa_bp.route('/disable-totp/', methods=['POST'])
@login_required
def disable_totp():
    """ Disable Two-Factor Authentication for the current user. """
    current_user.totp_active = False
    current_user.totp_secret = None
    session.pop('mfa_setup_secret', None)
    db.session.commit()
    flash('Two-Factor TOTP Authentication has been disabled.', 'success')
    return redirect(url_for('auth.my_account'))

@mfa_bp.route('/disable-mfa/', methods=['POST'])
@login_required
def disable_mfa():
    """ Disable Multi-Factor Authentication for the current user. """
    current_user.mfa_active = False
    current_user.totp_active = False
    current_user.totp_secret = None
    session.pop('mfa_setup_secret', None)
    RecoveryCodes.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('Multi-Factor Authentication has been disabled.', 'success')
    return redirect(url_for('auth.my_account'))

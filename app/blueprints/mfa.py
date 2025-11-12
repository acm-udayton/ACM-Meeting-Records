#!/usr/bin/env python
# app/blueprints/mfa.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 10/7/2025

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
from app.extensions import db
from app.models import Users, RecoveryCodes


mfa_bp = Blueprint('mfa', __name__, template_folder='templates')


@mfa_bp.route('/reset-recovery-codes/', methods=['GET'])
def reset_recovery_codes():
    """ Generate new recovery codes for the user. """
    # Clear old codes and generate new codes.
    for old_code in RecoveryCodes.query.filter_by(user_id=current_user.id).all():
        db.session.delete(old_code)

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
    return render_template("auth/reset-codes.html", page_title="Recovery Codes", codes=codes)

@mfa_bp.route('/verify-recovery-code/', methods=['GET', 'POST'])
def verify_recovery_code():
    """ Authenticate with a recovery code during 2FA login. """
    user_id = session.get('2fa_user_id')
    if not user_id:
        flash('You must log in before using a recovery code.', 'warning')
        return redirect(url_for('auth.login'))

    user = Users.query.get(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        code = request.form.get('recovery_code')
        recovery_code_entry = RecoveryCodes.query.filter_by(user_id=user.id).all()
        for entry in recovery_code_entry:
            if entry.check_code(code):
                # Code used, so delete it.
                db.session.delete(entry)
                db.session.commit()
                login_user(user)
                session.pop('2fa_user_id', None)
                current_app.logger.info(
                    "Login attempt as %s from IP %s - success with recovery code",
                    user.username,
                    request.remote_addr
                )
                return redirect(url_for('main.home'))
        flash('Invalid recovery code.', 'danger')

    return render_template('auth/verify-code.html', page_title='Verify Recovery Code')


@mfa_bp.route('/verify-2fa/', methods=['GET', 'POST'])
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

    return render_template('auth/verify-2fa.html', page_title='Two-Factor Authentication')

@mfa_bp.route('/setup-2fa/')
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
    <form action="{url_for('mfa.verify_setup')}" method="POST">
        <input name="token" placeholder="Enter code from app to confirm setup">
        <button type="submit">Verify Setup</button>
    </form>
    '''

@mfa_bp.route('/verify-setup/', methods=['POST'])
@login_required
def verify_setup():
    """ Verify the TOTP code entered by the user during 2FA setup. """
    token = request.form.get('token')

    # Use the temporary secret stored in the session for verification
    secret = session.pop('2fa_setup_secret', None)

    if not secret:
        flash('2FA setup session expired. Start over.', 'danger')
        return redirect(url_for('mfa.setup_2fa'))

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
        return redirect(url_for('mfa.setup_2fa'))


@mfa_bp.route('/disable-2fa/')
@login_required
def disable_2fa():
    """ Disable Two-Factor Authentication for the current user. """
    current_user.totp_active = False
    current_user.generate_totp_secret()
    db.session.commit()
    flash('Two-Factor Authentication has been disabled.', 'success')
    return redirect(url_for('main.home'))

#!/usr/bin/env python
# app/blueprints/mfa/routes.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 7/27/2026

File Purpose: MFA routes for the project.
"""

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user

from app.forms import RecoveryCodeVerifyForm, TotpSetupForm, TotpVerifyForm
from app.models import Users
from app.services.mfa_service import (
    MfaResultStatus,
    disable_mfa_for_user,
    disable_totp_for_user,
    prepare_totp_setup,
    reset_recovery_codes_for_user,
    user_has_recovery_codes,
    verify_and_enable_totp,
    verify_mfa_recovery_code,
    verify_mfa_totp_code,
)

mfa_bp = Blueprint("mfa", __name__, template_folder="templates")


@mfa_bp.route("/reset-recovery-codes/", methods=["GET"])
@login_required
def reset_recovery_codes():
    """Generate new recovery codes for the user."""
    _, raw_codes = reset_recovery_codes_for_user(current_user)

    # Format codes for tab/newline display in template
    formatted_codes = ""
    for code in raw_codes:
        formatted_codes += f"{code}\t" if not formatted_codes.endswith("\t") else f"{code}\n"

    return render_template(
        "auth/reset-codes.html",
        page_title="MFA Recovery Codes",
        codes=formatted_codes,
    )


@mfa_bp.route("/verify-recovery-code/", methods=["GET", "POST"])
def verify_recovery_code():
    """Authenticate with a recovery code during MFA login."""
    user_id = session.get("mfa_user_id")
    if not user_id:
        flash("You must log in before using a recovery code.", "warning")
        return redirect(url_for("auth.login"))

    user = Users.query.get(user_id)
    form = RecoveryCodeVerifyForm()

    if form.validate_on_submit():
        result = verify_mfa_recovery_code(user, form.token.data)

        if result.is_success:
            login_user(result.user)
            session.pop("mfa_user_id", None)
            current_app.logger.info(
                "Login attempt as %s from IP %s - success with recovery code",
                result.user.username,
                request.remote_addr,
            )
            return redirect(url_for("main.home"))

        flash("Invalid recovery code.", "danger")

    return render_template(
        "auth/verify-code.html",
        page_title="Verify MFA Recovery Code",
        form=form,
    )


@mfa_bp.route("/verify-totp/", methods=["GET", "POST"])
def verify_totp():
    """Handle the TOTP verification step during login."""
    user_id = session.get("mfa_user_id")
    if not user_id:
        flash("You must log in before using TOTP MFA.", "warning")
        return redirect(url_for("auth.login"))

    user = Users.query.get(user_id)
    if not user or not user.totp_active:
        flash("TOTP MFA not required or user not found.", "danger")
        return redirect(url_for("auth.login"))
    
    form = TotpVerifyForm()

    if form.validate_on_submit():
        result = verify_mfa_totp_code(user, form.token.data)

        if result.is_success:
            login_user(result.user)
            session.pop("mfa_user_id", None)
            current_app.logger.info(
                "Login attempt as %s from IP %s - success with TOTP MFA",
                result.user.username,
                request.remote_addr,
            )
            return redirect(url_for("main.home"))

        flash("Invalid TOTP MFA code.", "danger")

    return render_template(
        "auth/verify-totp.html", page_title="Verify MFA TOTP Code", form=form
    )


@mfa_bp.route("/setup-totp/")
@login_required
def setup_totp():
    """Setup Two-Factor Authentication for the current user."""
    result, uri, qr_data = prepare_totp_setup(current_user)

    if MfaResultStatus.TOTP_ALREADY_ENABLED in result.statuses:
        flash("MFA with TOTP is already enabled. Disable it first please!", "info")
        return redirect(url_for("auth.my_account"))

    form = TotpSetupForm()
    return render_template(
        "auth/setup-totp.html",
        page_title="Setup TOTP MFA",
        qr_data=qr_data,
        totp_secret=current_user.totp_secret,
        form=form,
    )


@mfa_bp.route("/verify-totp-setup/", methods=["POST"])
@login_required
def verify_totp_setup():
    """Verify the TOTP code entered by the user during setup."""
    form = TotpSetupForm()
    if form.validate_on_submit():
        result = verify_and_enable_totp(current_user, form.token.data)

        if result.is_success:
            flash("TOTP MFA successfully enabled!", "success")
            if not user_has_recovery_codes(current_user):
                return redirect(url_for("mfa.reset_recovery_codes"))
            return redirect(url_for("auth.my_account"))

        flash("Invalid code. Please try scanning and verifying again.", "danger")
        return redirect(url_for("mfa.setup_totp"))

    flash("Invalid TOTP MFA setup form data.", "danger")
    return redirect(url_for("mfa.setup_totp"))


@mfa_bp.route("/disable-totp/")
@login_required
def disable_totp():
    """Disable Two-Factor Authentication for the current user."""
    disable_totp_for_user(current_user)
    flash("Two-Factor TOTP Authentication has been disabled.", "success")
    return redirect(url_for("auth.my_account"))


@mfa_bp.route("/disable-mfa/")
@login_required
def disable_mfa():
    """Disable Multi-Factor Authentication for the current user."""
    disable_mfa_for_user(current_user)
    flash("Multi-Factor Authentication has been disabled.", "success")
    return redirect(url_for("auth.my_account"))
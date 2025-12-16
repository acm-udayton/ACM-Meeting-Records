# app/forms.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 12/16/2025

File Purpose: Flask-WTF forms for the project.
"""

# Standard library imports.
import re

# Third-party imports.
from flask import current_app
from flask_wtf import FlaskForm, RecaptchaField, Recaptcha
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import (
    Optional,
    Length,
    Regexp,
    EqualTo,
    Email,
    ValidationError,
    InputRequired
)


# Define the custom regex validator for the semester format
SEMESTER_REGEX = r"^(FA|SP) \d{4}$|^$" # FA YYYY or SP YYYY or empty

def email_domain_validator(form, field):
    """ WTForms Validator to check for the required email domain (if applicable). """
    if field.data and current_app.context["usernames"]["enforce_usernames"] == "True":
        # Use regex to check the required email_domain.
        match = re.match(r"[^@]+@([^@]+)", field.data)
        if match:
            print(match.groups())
            required_domain = current_app.context["usernames"]["username_email_domain"]
            domain = match.group(1)
            if domain != required_domain:
                raise ValidationError(f'Email must be from the domain {required_domain}')
        else:
            raise ValidationError('Invalid email format.')

class LoginForm(FlaskForm):
    """ Form for user login. """
    username = StringField(
        'Email',
        validators=[
            InputRequired(),
            Length(min=1, max=64)
            ]
    )
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(),
            Length(min=1, max=128)
        ]
    )
    submit = SubmitField('Log In')

class SignUpForm(FlaskForm):
    """ Form for registration of new user. """
    username = StringField(
        'Email',
        validators=[
            InputRequired(),
            Email(message='A valid email address is required.'),
            email_domain_validator
        ]
    )
    password = PasswordField(
        'Password', 
        validators=[
            InputRequired(),
            Length(min=1, max=128)
        ]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators = [
            InputRequired(),
            Length(min=1, max=128),
            EqualTo('password', message='Passwords must match.')
        ]
    )
    recaptcha = RecaptchaField(
        validators = [
            Recaptcha(message="Please complete the CAPTCHA to continue.")
        ]
    )
    submit = SubmitField("Create Account")

class AccountUpdateForm(FlaskForm):
    """ Form for updating user account details. """
    # Password: Optional, but needs validation if provided
    password = PasswordField(
        'New Password', 
        validators=[
            Optional(),
            Length(min=1, message="Password must be at least 1 character long.")
        ]
    )
    # Start Semester - validate with regex
    start_semester = StringField(
        'Start Semester (FA YYYY / SP YYYY)', 
        validators=[
            Optional(), # Allows it to be empty
            Regexp(SEMESTER_REGEX,
                   message='Invalid format. Use "FA YYYY", "SP YYYY", or leave empty.')
        ]
    )
    # Grad Semester - validate with regex
    grad_semester = StringField(
        'Graduation Semester (FA YYYY / SP YYYY)', 
        validators=[
            Optional(),
            Regexp(SEMESTER_REGEX,
                   message='Invalid format. Use "FA YYYY", "SP YYYY", or leave empty.')
        ]
    )
    submit = SubmitField('Save Account Details')

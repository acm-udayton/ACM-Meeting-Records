# app/forms.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz), Thomas Crossman (github.com/crossmant1)
Last Modified: 2/14/2025

File Purpose: Flask-WTF forms for the project.
"""

# Standard library imports.
import re

# Third-party imports.
from flask import current_app
from flask_wtf import FlaskForm, RecaptchaField, Recaptcha
from wtforms import DateTimeField, DateTimeLocalField, StringField, PasswordField, SubmitField, BooleanField, FieldList, FormField
from wtforms.validators import (
    DataRequired,
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

def email_domain_validator(_form, field):
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

class AdminAttendeeAddForm(FlaskForm):
    """ Form for admin to add an attendee to a meeting. """
    username = StringField(
        'Attendee Username',
        validators=[
            InputRequired(),
        ]
    )
    submit = SubmitField('Add Attendee')

class CreateMeetingForm(FlaskForm):
    """ Form for new meeting creation. """
    title = StringField(
        'Meeting Title',
        validators=[
            InputRequired(),
            Length(min=1, max=128)
        ]
    )
    description = StringField(
        'Meeting Description',
        validators=[
            InputRequired(),
            Length(min=1, max=512)
        ]
    )
    admin_only = BooleanField(
        'Admin Only'
    )
    submit = SubmitField('Create Meeting')

class MeetingCheckinForm(FlaskForm):
    """ Form for check-in to a meeting. """
    code = StringField(
        'Meeting Code',
        validators=[
            InputRequired(),
            Length(min=1, max=64)
        ]
    )
    submit = SubmitField('Check In')

class RecoveryCodeVerifyForm(FlaskForm):
    """ Form for verifying recovery code. """
    token = StringField(
        'Recovery Code',
        validators=[
            InputRequired()
        ]
    )
    submit = SubmitField('Verify')

class TotpVerifyForm(FlaskForm):
    """ Form for verifying TOTP setup. """
    token = StringField(
        'Authentication Code',
        validators=[
            InputRequired(),
            Length(min=6, max=6, message='The authentication code must be 6 digits long.')
        ]
    )
    submit = SubmitField('Verify')

class TotpSetupForm(FlaskForm):
    """ Form for setting up TOTP. """
    token = StringField(
        'Authenticator App Code',
        validators=[
            InputRequired(),
            Length(min=6, max=6, message='The code must be 6 digits long.')
        ]
    )
    submit = SubmitField('Verify Setup')

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

class SignUpFormEmail(FlaskForm):
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

class SignUpFormUsername(FlaskForm):
    """ Form for registration of new user. """
    username = StringField(
        'Username',
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

class CreatePollOptionForm(FlaskForm):
    """ Form for options subsection of poll creation form. """
    option_text = StringField(
        "Option",
        validators=[
            InputRequired(),
        ]
    )

class CreatePollQuestionForm(FlaskForm):
    """ Form for questions subsection of poll creation form. """
    question_text = StringField(
        "Question Text",
        validators=[
            InputRequired(),
        ]
    )
    is_free_response = BooleanField(
        "Free Response Question",
        default=False
    )
    allow_multiple_responses = BooleanField(
        "Allow Multiple Responses",
        default=False
    )
    private_vote = BooleanField(
        "Private Vote",
        default=False
    )
    immutable_question = BooleanField(
        "Immutable Question",
        default=False
    )
    options = FieldList(FormField(CreatePollOptionForm), min_entries=0)

class CreatePollForm(FlaskForm):
    """ Form for creating a new poll. """
    title = StringField(
        'Poll Title',
        validators=[
            InputRequired(),
            Length(min=1, max=128)
        ]
    )
    poll_expires = DateTimeLocalField(
        'Poll Expiration Datetime',
        format='%Y-%m-%dT%H:%M',
        validators=[Optional()]
    )
    questions = FieldList(FormField(CreatePollQuestionForm), min_entries=1)
    submit = SubmitField('Create Poll')

class PollVoteForm(FlaskForm):
    """ Form for voting in a poll. """
    submit = SubmitField('Vote')

class DeletePollForm(FlaskForm):
    """ Form for deleting a poll. """
    submit = SubmitField('Delete Poll')

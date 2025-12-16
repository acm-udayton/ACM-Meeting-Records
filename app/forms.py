# app/forms.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 12/15/2025

File Purpose: Flask-WTF forms for the project.
"""

# Third-party imports.
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Optional, Length, Regexp, EqualTo

# Define the custom regex validator for the semester format
SEMESTER_REGEX = r"^(FA|SP) \d{4}$|^$" # FA YYYY or SP YYYY or empty

class LoginForm(FlaskForm):
    """ Form for user login. """
    username = StringField('Email', validators=[Length(min=1, max=64)])
    password = PasswordField('Password', validators=[Length(min=1, max=128)])
    submit = SubmitField('Log In')

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

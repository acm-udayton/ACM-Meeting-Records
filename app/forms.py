# app/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Length

class LoginForm(FlaskForm):
    username = StringField('Email', validators=[Length(min=1, max=64)])
    password = PasswordField('Password', validators=[Length(min=1, max=128)])
    submit = SubmitField('Log In')

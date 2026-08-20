#!/usr/bin/env python

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 7/26/2025

File Purpose: Provide utilities used by the webserver for the project.
"""

import hashlib
import secrets
import string
from typing import Any

from flask_login import AnonymousUserMixin

from app.models import Meetings, Users

def sha_hash(string_to_hash):
    """ Wrapper function for hashlib's SHA-512 hash. """
    m = hashlib.sha3_512()
    m.update(bytes(string_to_hash, "utf-8"))
    return m.hexdigest()

def generate_meeting_code(length=8):
    """ Generate a random meeting code. """
    # Define the character set for the password
    characters = string.ascii_letters + string.digits

    # Use secrets.choice for cryptographic randomness
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password

def is_admin(user: Users) -> bool:
    """ Helper function to determine if a user is an admin. """
    return bool(user and user.is_authenticated and user.role == "admin")

def is_not_admin(user: Users) -> bool:
    """ Helper function to determine if a user is not an admin. """
    return not is_admin(user)

def user_can_access_meeting_by_id(user: Users | AnonymousUserMixin, meeting_id: int) -> bool:
    """ Determine if a user can access a given meeting. """
    meeting = Meetings.query.filter(Meetings.id == meeting_id).first()
    if not meeting:
        return True  # Meeting does not exist, return a 404/empty response data.
    if is_admin(user):
        return True
    return not meeting.admin_only

def filter_by_role(query: Any, user: Users | AnonymousUserMixin) -> Any:
    """ Filter a query based on the user's role. """
    if is_admin(user):
        return query
    else:
        return query.filter(Meetings.admin_only == False)
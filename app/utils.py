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

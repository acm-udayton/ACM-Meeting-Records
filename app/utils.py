#!/usr/bin/env python

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 7/26/2025

File Purpose: Provide utilities used by the webserver for the project.
"""

import hashlib
import json
import os
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


def get_logger_config():
    """ Load the logger configuration from the logger_config.json file. """
    # Get (and if necessary create) directories.
    project_dir = os.path.abspath(os.path.dirname(__file__))
    log_dir = os.path.join(project_dir, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Open the logger json configuration.
    log_config_path = os.path.join(project_dir, "logger_config.json")
    with open(log_config_path, 'r', encoding="utf-8") as logger_config_file:
        logger_config = json.load(logger_config_file)

    # Ensure correct filepaths are used.
    for handler_config in logger_config['handlers'].values():
        if "filename" in handler_config:
            handler_config["filename"] = os.path.join(project_dir, handler_config["filename"])

    return logger_config

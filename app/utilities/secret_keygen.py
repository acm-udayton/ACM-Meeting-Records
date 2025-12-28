#! /usr/bin/env python3

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 12/15/2025

File Purpose: Generate a random secret key for Flask applications.
"""

# Standard library imports.
import secrets

def main():
    """ Generate a random secret key for Flask applications. """
    return f"SECRET_KEY = \"{secrets.token_hex()}\""

if __name__ == "__main__":
    print(main())

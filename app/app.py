#!/usr/bin/env python

"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 7/26/2025

File Purpose: Import and run the webserver for the project.
"""

from .web import app # pylint: disable=relative-beyond-top-level

if __name__ == "__main__":
    app.run()

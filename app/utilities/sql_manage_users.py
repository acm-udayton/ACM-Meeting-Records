"""
Project Name: ACM-Meeting-Records
Project Author(s): Joseph Lefkovitz (github.com/lefkovitz)
Last Modified: 9/9/2025

File Purpose: Utility to help create admins in DB.
"""

import hashlib
import sys

def sha_hash(string_to_hash):
    """ Wrapper function for hashlib's SHA-512 hash. """
    m = hashlib.sha3_512()
    m.update(bytes(string_to_hash, "utf-8"))
    return m.hexdigest()

def create():
    """Process an admin creation."""
    role = "admin"
    uname = input("Username: ")
    pword = sha_hash(input("Password: "))
    pconf = sha_hash(input("Password (Confirm): "))
    if pword != pconf:
        print("Invalid Password, passwords must match")
        sys.exit()
    output_message = ("INSERT into users (username, password, role) "
                      f"VALUES ('{uname}', '{pword}', '{role}');")
    return output_message

def demote():
    """Process a user demotion."""
    uname = input("Username: ")
    output_message = ("UPDATE users SET role = 'user' "
                       f"WHERE username = '{uname}';")
    return output_message

def promote():
    """Process a user promotion."""
    uname = input("Username: ")
    output_message = ("UPDATE users SET role = 'admin' "
                       f"WHERE username = '{uname}';")
    return output_message

def main():
    """Process a user's selected action."""
    options = ("(1) Create Admin\n"
               "(2) Demote Admin\n"
               "(3)Promote User\n\n"
               "Enter the number for your preferred action: ")
    match input(options):
        case "1":
            return create()
        case "2":
            return demote()
        case "3":
            return promote()
        case _:
            return "Error: Invalid action number. Please try again."

if __name__ == "__main__":
    print(main())

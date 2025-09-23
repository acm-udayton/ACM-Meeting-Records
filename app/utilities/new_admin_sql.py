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

def main():
    """ Process the main functionality of the file. """
    role = "admin"
    uname = input("Username: ")
    pword = sha_hash(input("Password: "))
    pconf = sha_hash(input("Password (Confirm): "))
    if pword != pconf:
        print("Invalid Password, passwords must match")
        sys.exit()
    output_message = ("INSERT into users (username, password, role) " +
                      f"VALUES ('{uname}', '{pword}', '{role}');")
    return output_message


if __name__ == "__main__":
    print(main())

import hashlib
import sys

def sha_hash(string_to_hash):
    """ Wrapper function for hashlib's SHA-512 hash. """
    m = hashlib.sha3_512()
    m.update(bytes(string_to_hash, "utf-8"))
    return m.hexdigest()

def main():
    """ Process the main functionality of the file. """
    role = input("Admin (enter 'a') or Secretary (enter 's'):").lower().strip()
    if role == "a":
        role = "ADMIN"
    elif role == "s":
        role = "SECRETARY"
    else:
        print("Invalid Role, must be Admin (a) or Secretary (s)")
        sys.exit()
    
    uname = input("Username: ")
    pword = sha_hash(input("Password: "))
    pconf = sha_hash(input("Password (Confirm): "))
    if pword != pconf:
        print("Invalid Password, passwords must match")
        sys.exit()
    output_message = f"{role}_USERNAME = \"{uname}\"\n{role}_PASSWORD = \"{pword}\""
    return output_message


if __name__ == "__main__":
    print(main())
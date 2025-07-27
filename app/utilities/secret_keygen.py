import secrets

def main():
    return f"SECRET_KEY = \"{secrets.token_hex()}\""

if __name__ == "__main__":
    print(main())
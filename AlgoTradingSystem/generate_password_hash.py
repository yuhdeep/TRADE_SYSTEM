"""
Run this locally to turn a password you choose into the hash that goes in
your app's Secrets. Your plaintext password never leaves your machine.

Usage:
    python generate_password_hash.py
"""

import getpass
import hashlib

if __name__ == "__main__":
    pw = getpass.getpass("Choose a password for the dashboard: ")
    confirm = getpass.getpass("Confirm password: ")
    if pw != confirm:
        print("Passwords didn't match. Try again.")
    else:
        digest = hashlib.sha256(pw.encode()).hexdigest()
        print("\nAdd these two lines to your app's Secrets:\n")
        print(f'AUTH_USERNAME = "your-chosen-username"')
        print(f'AUTH_PASSWORD_HASH = "{digest}"')

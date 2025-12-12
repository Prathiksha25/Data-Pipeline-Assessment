# generate_fernet.py
import os
import base64

def make_fernet_key():
    key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    return key

if __name__ == "__main__":
    print(make_fernet_key())


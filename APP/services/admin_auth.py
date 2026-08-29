import csv
import hashlib
import hmac
import os
import secrets

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ADMIN_USERS_CSV = os.path.join(BASE_DIR, "APP", "admin_users.csv")


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000
    ).hex()


def create_password_hash(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    return salt, _hash_password(password, salt)


def authenticate(username: str, password: str) -> bool:
    if not username or not password or not os.path.exists(ADMIN_USERS_CSV):
        return False
    with open(ADMIN_USERS_CSV, newline="", encoding="utf-8") as file:
        for user in csv.DictReader(file):
            if hmac.compare_digest(user.get("username", ""), username.strip()):
                if user.get("password"):
                    return hmac.compare_digest(user["password"], password)
                expected = _hash_password(password, user.get("salt", ""))
                return hmac.compare_digest(expected, user.get("password_hash", ""))
    return False

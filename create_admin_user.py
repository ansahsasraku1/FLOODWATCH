import csv
import getpass
import os
import sys

sys.path.insert(0, "APP")
from services.admin_auth import ADMIN_USERS_CSV, create_password_hash

username = input("Admin username: ").strip()
password = getpass.getpass("Admin password: ")
confirmation = getpass.getpass("Confirm password: ")

if not username or not password or password != confirmation:
    raise SystemExit("Username is required and passwords must match.")

salt, password_hash = create_password_hash(password)
os.makedirs(os.path.dirname(ADMIN_USERS_CSV), exist_ok=True)
file_exists = os.path.exists(ADMIN_USERS_CSV) and os.path.getsize(ADMIN_USERS_CSV) > 0
with open(ADMIN_USERS_CSV, "a", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["username", "salt", "password_hash"])
    if not file_exists:
        writer.writeheader()
    writer.writerow({"username": username, "salt": salt, "password_hash": password_hash})

print(f"Administrator account created in {ADMIN_USERS_CSV}")

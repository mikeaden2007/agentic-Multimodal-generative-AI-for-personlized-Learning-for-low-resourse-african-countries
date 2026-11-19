import getpass
import secrets
import sqlite3
from pathlib import Path

from app.auth import AuthStore

DB_PATH = Path("app/data/users.db")

if not DB_PATH.is_file():
    raise SystemExit("STOP: Authentication database not found.")

print("=== ASKTUTOR ADMINISTRATOR SETUP ===")
print("Create a NEW administrator account.")
print("Do not use an existing student email.")

email = input("Administrator email: ").strip().lower()
name = input("Administrator name: ").strip()
password = getpass.getpass("Administrator password: ")
confirm = getpass.getpass("Confirm password: ")

if not email or "@" not in email:
    raise SystemExit("STOP: Enter a valid email address.")

if not name:
    raise SystemExit("STOP: Administrator name is required.")

if len(password) < 12:
    raise SystemExit("STOP: Password must contain at least 12 characters.")

if password != confirm:
    raise SystemExit("STOP: Passwords do not match.")

store = AuthStore(str(DB_PATH))
conn = sqlite3.connect(str(DB_PATH))

try:
    existing = conn.execute(
        "SELECT id FROM users WHERE lower(email) = ?",
        (email,)
    ).fetchone()

    if existing:
        raise SystemExit(
            "STOP: This email already belongs to an account. "
            "No account was modified."
        )

    user_id = secrets.token_hex(8)
    salt = secrets.token_bytes(16)
    password_hash = store._hash_password(password, salt)

    conn.execute(
        """
        INSERT INTO users (
            id, name, email, password_hash, password_salt,
            country, class_level, stream, academic_goal, role
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            name,
            email,
            password_hash,
            salt.hex(),
            "Nigeria",
            "N/A",
            None,
            "AskTutor administration",
            "admin"
        )
    )

    conn.commit()

    role = conn.execute(
        "SELECT role FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()[0]

    if role != "admin":
        raise SystemExit("STOP: Administrator verification failed.")

    print("\nADMINISTRATOR ACCOUNT CREATED")
    print("Email:", email)
    print("Role:", role)
    print("Existing learner records: UNCHANGED")

finally:
    conn.close()

# ============================================================
# NEONSOCIAL AI — REAL USER AUTHENTICATION
# ============================================================

import os
import sqlite3
import hashlib
import hmac
import secrets
from functools import wraps

from flask import session, jsonify, redirect


# ============================================================
# DATABASE
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATABASE_FILE = os.path.join(
    BASE_DIR,
    "neonsocial_users.db"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_auth_database():

    connection = get_db()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            email TEXT NOT NULL UNIQUE,

            password_hash TEXT NOT NULL,

            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()

    connection.close()


# ============================================================
# NORMALIZE EMAIL
# ============================================================

def normalize_email(email):

    return str(
        email or ""
    ).strip().lower()


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password):

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600000
    )

    return (
        salt.hex()
        + ":"
        + password_hash.hex()
    )


# ============================================================
# PASSWORD VERIFY
# ============================================================

def verify_password(
    password,
    stored_hash
):

    try:

        salt_hex, hash_hex = (
            stored_hash.split(":")
        )

        salt = bytes.fromhex(
            salt_hex
        )

        expected_hash = bytes.fromhex(
            hash_hex
        )

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            600000
        )

        return hmac.compare_digest(
            actual_hash,
            expected_hash
        )

    except Exception:

        return False


# ============================================================
# CREATE USER
# ============================================================

def create_user(
    email,
    password
):

    email = normalize_email(
        email
    )

    if not email:

        return False, "Email is required."

    if len(email) > 255:

        return False, "Email is too long."

    if "@" not in email:

        return False, "Enter a valid email address."

    if not password:

        return False, "Password is required."

    if len(password) < 8:

        return False, (
            "Password must contain at least 8 characters."
        )

    password_hash = hash_password(
        password
    )

    from datetime import datetime, timezone

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    connection = get_db()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO users
            (
                email,
                password_hash,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                email,
                password_hash,
                created_at
            )
        )

        connection.commit()

        user_id = cursor.lastrowid

        return True, {
            "id": user_id,
            "email": email,
            "created_at": created_at
        }

    except sqlite3.IntegrityError:

        return False, (
            "An account with this email already exists."
        )

    finally:

        connection.close()


# ============================================================
# AUTHENTICATE USER
# ============================================================

def authenticate_user(
    email,
    password
):

    email = normalize_email(
        email
    )

    connection = get_db()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            email,
            password_hash,
            created_at
        FROM users
        WHERE email = ?
        """,
        (email,)
    )

    user = cursor.fetchone()

    connection.close()

    if not user:

        return None

    if not verify_password(
        password,
        user["password_hash"]
    ):

        return None

    return {

        "id":
            user["id"],

        "email":
            user["email"],

        "created_at":
            user["created_at"]
    }


# ============================================================
# CURRENT USER
# ============================================================

def get_current_user():

    user_id = session.get(
        "user_id"
    )

    if not user_id:

        return None

    connection = get_db()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            email,
            created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    connection.close()

    if not user:

        session.clear()

        return None

    return {

        "id":
            user["id"],

        "email":
            user["email"],

        "created_at":
            user["created_at"]
    }


# ============================================================
# LOGIN USER
# ============================================================

def login_user(user):

    session.clear()

    session["user_id"] = user["id"]

    session["user_email"] = user["email"]

    session.permanent = True

    session.modified = True


# ============================================================
# LOGOUT USER
# ============================================================

def logout_user():

    session.clear()


# ============================================================
# LOGIN REQUIRED — API
# ============================================================

def login_required_api(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        user = get_current_user()

        if not user:

            return jsonify({

                "success":
                    False,

                "authenticated":
                    False,

                "error":
                    "Login required."
            }), 401

        return function(
            *args,
            **kwargs
        )

    return wrapper


# ============================================================
# LOGIN REQUIRED — PAGE
# ============================================================

def login_required_page(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        user = get_current_user()

        if not user:

            return redirect(
                "/login"
            )

        return function(
            *args,
            **kwargs
        )

    return wrapper
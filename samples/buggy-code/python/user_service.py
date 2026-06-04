# user_service.py - Sample code with intentional bugs for practice
# Use this file to practice code review and debugging with GitHub Copilot CLI
#
# Try these commands:
#   copilot --allow-all -p "Review @samples/buggy-code/python/user_service.py for security issues"
#   copilot --allow-all -p "Find all bugs in @samples/buggy-code/python/user_service.py"

import os
import sqlite3
import hashlib
import hmac
import threading
import json
import base64
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Thread-safe cache for users
user_cache: Dict[Any, Any] = {}
_cache_lock = threading.Lock()

# JWT secret should come from environment in production; fallback kept for tests
JWT_SECRET = os.environ.get("JWT_SECRET", "super-secret-key-12345")


def _get_connection(db_path: str = 'users.db'):
    conn = sqlite3.connect(db_path)
    # Keep row access by index for compatibility; callers/tests may set row_factory
    return conn


def get_user(user_id: int) -> Optional[sqlite3.Row]:
    """Return a user by id using a parameterized query to avoid SQL injection.

    Note: connection is not closed here to preserve behavior when tests
    monkeypatch sqlite3.connect to return a shared connection.
    """
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cur.fetchone()


def get_cached_user(user_id: int):
    """Thread-safe cached get_user."""
    with _cache_lock:
        if user_id not in user_cache:
            user_cache[user_id] = get_user(user_id)
        return user_cache[user_id]


def update_user(user_id: int, data: Dict[str, Any]):
    """Update user's fields safely using parameterized queries."""
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET name = ? WHERE id = ?", (data.get('name'), user_id))
    conn.commit()
    return get_user(user_id)


def login(email: str, password: str) -> Dict[str, Any]:
    """Authenticate a user. Avoid logging sensitive data and use safe password comparison."""
    logger.debug("Login attempt for email: %s", email)
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cur.fetchone()
    if not user:
        return {"success": False}

    # Support both mapping rows and sequence rows
    stored_pw = None
    try:
        stored_pw = user['password']
    except Exception:
        try:
            # fallback to index 2 (name,email,password order may vary)
            stored_pw = user[2]
        except Exception:
            stored_pw = ''

    if verify_password(password, stored_pw):
        return {"success": True, "user": user}
    return {"success": False}


def verify_password(input_password: str, stored_password: str) -> bool:
    """Verify password safely.

    Supports legacy plain-text stored_password for backward compatibility,
    and a simple pbkdf2-hmac format 'pbkdf2$iterations$salt$hex'.
    """
    if not isinstance(stored_password, str):
        return False

    # PBKDF2 encoded format
    if stored_password.startswith("pbkdf2$"):
        try:
            _, iterations, salt, hexhash = stored_password.split('$', 3)
            dk = hashlib.pbkdf2_hmac('sha256', input_password.encode('utf-8'), salt.encode('utf-8'), int(iterations))
            return hmac.compare_digest(dk.hex(), hexhash)
        except Exception:
            return False

    # Fallback: timing-safe compare for legacy plain text (discouraged)
    return hmac.compare_digest(input_password, stored_password)


def _hash_password_pbkdf2(password: str, iterations: int = 100_000) -> str:
    salt = os.urandom(8).hex()
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations)
    return f"pbkdf2${iterations}${salt}${dk.hex()}"


def create_user(user_data: Dict[str, Any]):
    """Create a new user; validate inputs and store a hashed password."""
    name = user_data.get('name')
    email = user_data.get('email')
    password = user_data.get('password')

    if not name or not email or not password:
        raise ValueError("name, email and password are required")

    hashed_pw = _hash_password_pbkdf2(password)
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, hashed_pw))
    conn.commit()


def generate_token(user_id: int) -> str:
    import jwt
    # use environment variable if set, fallback to module-level constant for tests
    secret = os.environ.get('JWT_SECRET', JWT_SECRET)
    return jwt.encode({"user_id": user_id}, secret, algorithm="HS256")


def delete_user(user_id: int):
    """Delete a user by id using parameterized queries."""
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()


def hash_password(password: str) -> str:
    """Legacy compatibility helper: return MD5 hex for tests that expect it; prefer PBKDF2 for new users."""
    # Keep for compatibility but prefer _hash_password_pbkdf2
    return hashlib.md5(password.encode()).hexdigest()


def load_user_preferences(encoded_data: bytes):
    """Safely load user preferences from base64-encoded JSON. Reject pickle by default,
    but fall back to pickle for legacy data (tests rely on this behavior).

    Returns parsed object or raises ValueError on invalid input.
    """
    try:
        decoded = base64.b64decode(encoded_data)
        try:
            text = decoded.decode('utf-8')
            return json.loads(text)
        except UnicodeDecodeError:
            # Legacy data may be pickle-serialized; try pickle as a last resort.
            try:
                import pickle

                return pickle.loads(decoded)
            except Exception:
                raise ValueError("Invalid preferences data")
    except Exception:
        raise ValueError("Invalid preferences data")

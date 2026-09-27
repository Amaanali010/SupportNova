# security/auth.py
# Security module handling password hashing, user verification, and Role-Based Access Control (RBAC).

import hashlib
import os
import secrets
from typing import Optional, Dict, Any
from database.db import execute_query, execute_statement

def hash_password(password: str) -> str:
    """
    Hashes a plain text password using PBKDF2-HMAC-SHA256 with a random salt.
    Format returned: salt_hex$hash_hex
    """
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}${key.hex()}"

def verify_password(stored_password_hash: str, provided_password: str) -> bool:
    """
    Verifies a plain text password against the stored salt$hash string.
    """
    try:
        salt_hex, hash_hex = stored_password_hash.split('$')
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
        return secrets.compare_digest(key.hex(), hash_hex)
    except Exception:
        return False

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticates a user against the SQLite database.
    Returns user details dict if successful, None otherwise.
    """
    rows = execute_query("SELECT * FROM users WHERE username = ?", (username.strip(),))
    if not rows:
        return None
    user = dict(rows[0])
    if verify_password(user['password_hash'], password):
        # Remove password hash from memory before returning user dict
        user.pop('password_hash', None)
        return user
    return None

def check_permission(user_role: str, allowed_roles: list) -> bool:
    """
    Checks if a user role is authorized to perform an action or access a page.
    """
    return user_role in allowed_roles

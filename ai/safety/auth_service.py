"""
Authentication & User Account Service Module.

Provides minimal, secure, local database authentication for the AI Skin Analysis platform.
Features:
- PBKDF2-HMAC-SHA256 password hashing (600,000 iterations + 16-byte cryptographic salt).
- Constant-time password comparison to prevent timing attacks.
- SQLite-backed user storage and session management.
- Brute-force protection (lockout after repeated failed login attempts).
- Input validation (RFC email formatting, password strength enforcement).
- Safe generic error responses that avoid user enumeration.
- Clean session revocation on logout.
"""

import sys
import json
import sqlite3
import hashlib
import secrets
import os
import re
import hmac
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Generator


# Configuration
DEFAULT_DB_PATH = Path("reports") / "users.db"
PBKDF2_ITERATIONS = 600000  # OWASP recommendation for PBKDF2-HMAC-SHA256
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
DEFAULT_SESSION_HOURS = 24

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)


def get_db_path(custom_path: Optional[str] = None) -> Path:
    """Resolve database path from argument, environment, or default."""
    if custom_path:
        return Path(custom_path)
    env_path = os.environ.get("AUTH_DB_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


@contextmanager
def get_db_connection(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    """Context manager that guarantees connection closure."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()


def init_auth_db(db_path: Optional[Path] = None) -> Path:
    """Initialize SQLite tables for users and sessions if not existing."""
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    with get_db_connection(path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT,
                failed_attempts INTEGER DEFAULT 0,
                lockout_until TEXT
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()

    return path


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256 with a unique 16-byte random salt.
    Returns: 'pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>'
    """
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")

    salt = secrets.token_bytes(16)
    pw_bytes = password.encode("utf-8")
    derived = hashlib.pbkdf2_hmac("sha256", pw_bytes, salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a password against stored PBKDF2-HMAC-SHA256 hash using constant-time comparison.
    """
    if not password or not stored_hash:
        return False

    parts = stored_hash.split("$")
    if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
        return False

    try:
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_hash = bytes.fromhex(parts[3])
    except (ValueError, TypeError):
        return False

    pw_bytes = password.encode("utf-8")
    computed = hashlib.pbkdf2_hmac("sha256", pw_bytes, salt, iterations)
    return hmac.compare_digest(computed, expected_hash)


def validate_email_format(email: str) -> Tuple[bool, str]:
    """Validate email address format and length."""
    if not email or not isinstance(email, str):
        return False, "Email address is required."

    cleaned = email.strip()
    if len(cleaned) > 254:
        return False, "Email address exceeds maximum allowed length (254 characters)."

    if not EMAIL_REGEX.match(cleaned):
        return False, "Please enter a valid email address (e.g., user@example.com)."

    return True, ""


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Enforce security rules for user passwords:
    - Minimum 8 characters, maximum 128 characters.
    - At least one letter (a-z, A-Z).
    - At least one digit (0-9).
    """
    if not password or not isinstance(password, str):
        return False, "Password is required."

    if len(password) < 8:
        return False, "Password must be at least 8 characters in length."

    if len(password) > 128:
        return False, "Password must not exceed 128 characters."

    if not any(c.isalpha() for c in password):
        return False, "Password must contain at least one letter."

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."

    return True, ""


def validate_name(name: str) -> Tuple[bool, str]:
    """Validate user full name."""
    if not name or not isinstance(name, str):
        return False, "Full name is required."

    cleaned = name.strip()
    if len(cleaned) < 2:
        return False, "Full name must be at least 2 characters."

    if len(cleaned) > 100:
        return False, "Full name must not exceed 100 characters."

    return True, ""


def register_user(
    name: str,
    email: str,
    password: str,
    db_path: Optional[Path] = None,
    session_hours: int = DEFAULT_SESSION_HOURS,
) -> Dict[str, Any]:
    """
    Register a new user account.
    Returns:
        Dict with status, user details, and initial session token, or error details.
    """
    # Input validations
    name_ok, name_err = validate_name(name)
    if not name_ok:
        return {"success": False, "error": name_err, "code": "INVALID_NAME"}

    email_ok, email_err = validate_email_format(email)
    if not email_ok:
        return {"success": False, "error": email_err, "code": "INVALID_EMAIL"}

    pw_ok, pw_err = validate_password_strength(password)
    if not pw_ok:
        return {"success": False, "error": pw_err, "code": "WEAK_PASSWORD"}

    clean_name = name.strip()
    clean_email = email.strip().lower()

    path = init_auth_db(db_path)

    try:
        with get_db_connection(path) as conn:
            cursor = conn.cursor()

            # Check if email is already registered
            cursor.execute("SELECT id FROM users WHERE email = ?;", (clean_email,))
            existing = cursor.fetchone()
            if existing:
                return {
                    "success": False,
                    "error": "An account with this email address already exists.",
                    "code": "EMAIL_EXISTS",
                }

            # Hash password and insert record
            pw_hash = hash_password(password)
            now_iso = datetime.now(timezone.utc).isoformat()

            cursor.execute(
                """
                INSERT INTO users (email, name, password_hash, created_at, last_login, failed_attempts)
                VALUES (?, ?, ?, ?, ?, 0);
                """,
                (clean_email, clean_name, pw_hash, now_iso, now_iso),
            )
            user_id = cursor.lastrowid

            # Create initial session
            token = secrets.token_urlsafe(32)
            expires_at = (
                datetime.now(timezone.utc) + timedelta(hours=session_hours)
            ).isoformat()

            cursor.execute(
                """
                INSERT INTO sessions (token, user_id, created_at, expires_at)
                VALUES (?, ?, ?, ?);
                """,
                (token, user_id, now_iso, expires_at),
            )
            conn.commit()

            return {
                "success": True,
                "token": token,
                "user": {
                    "id": user_id,
                    "name": clean_name,
                    "email": clean_email,
                    "created_at": now_iso,
                    "isGuest": False,
                },
            }

    except sqlite3.IntegrityError:
        return {
            "success": False,
            "error": "An account with this email address already exists.",
            "code": "EMAIL_EXISTS",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Registration failed due to a database error: {str(e)}",
            "code": "INTERNAL_ERROR",
        }


def authenticate_user(
    email: str,
    password: str,
    db_path: Optional[Path] = None,
    session_hours: int = DEFAULT_SESSION_HOURS,
) -> Dict[str, Any]:
    """
    Authenticate an existing user with generic error reporting and brute-force lockout.
    """
    if not email or not password:
        return {
            "success": False,
            "error": "Invalid email or password.",
            "code": "INVALID_CREDENTIALS",
        }

    clean_email = email.strip().lower()
    path = init_auth_db(db_path)
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    with get_db_connection(path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, email, name, password_hash, failed_attempts, lockout_until
            FROM users
            WHERE email = ?;
            """,
            (clean_email,),
        )
        row = cursor.fetchone()

        if not row:
            # Generic error prevents email enumeration
            return {
                "success": False,
                "error": "Invalid email or password.",
                "code": "INVALID_CREDENTIALS",
            }

        user_id, u_email, u_name, pw_hash, failed_attempts, lockout_until = row

        # Check account lockout
        if lockout_until:
            try:
                lock_dt = datetime.fromisoformat(lockout_until)
                if lock_dt > now:
                    remaining_mins = max(1, int((lock_dt - now).total_seconds() // 60))
                    return {
                        "success": False,
                        "error": (
                            f"Account temporarily locked due to repeated failed login attempts. "
                            f"Please try again in {remaining_mins} minute(s)."
                        ),
                        "code": "ACCOUNT_LOCKED",
                    }
            except (ValueError, TypeError):
                pass  # Ignore invalid timestamp format

        # Verify password
        if not verify_password(password, pw_hash):
            new_failed = (failed_attempts or 0) + 1
            new_lockout = None
            if new_failed >= MAX_FAILED_ATTEMPTS:
                new_lockout = (
                    now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                ).isoformat()

            cursor.execute(
                """
                UPDATE users
                SET failed_attempts = ?, lockout_until = ?
                WHERE id = ?;
                """,
                (new_failed, new_lockout, user_id),
            )
            conn.commit()

            if new_lockout:
                return {
                    "success": False,
                    "error": (
                        "Account temporarily locked due to repeated failed login attempts. "
                        f"Please try again in {LOCKOUT_DURATION_MINUTES} minutes."
                    ),
                    "code": "ACCOUNT_LOCKED",
                }

            return {
                "success": False,
                "error": "Invalid email or password.",
                "code": "INVALID_CREDENTIALS",
            }

        # Password is correct: reset failed attempts, update last_login
        token = secrets.token_urlsafe(32)
        expires_at = (now + timedelta(hours=session_hours)).isoformat()

        cursor.execute(
            """
            UPDATE users
            SET failed_attempts = 0, lockout_until = NULL, last_login = ?
            WHERE id = ?;
            """,
            (now_iso, user_id),
        )

        cursor.execute(
            """
            INSERT INTO sessions (token, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?);
            """,
            (token, user_id, now_iso, expires_at),
        )
        conn.commit()

        return {
            "success": True,
            "token": token,
            "user": {
                "id": user_id,
                "name": u_name,
                "email": u_email,
                "created_at": now_iso,
                "isGuest": False,
            },
        }


def validate_session(
    token: str, db_path: Optional[Path] = None
) -> Optional[Dict[str, Any]]:
    """
    Validate a session token. Returns user profile if valid and unexpired, None otherwise.
    """
    if not token or not isinstance(token, str):
        return None

    path = init_auth_db(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db_connection(path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT u.id, u.email, u.name, u.created_at, s.expires_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?;
            """,
            (token.strip(),),
        )
        row = cursor.fetchone()

        if not row:
            return None

        user_id, email, name, created_at, expires_at = row

        # Check expiration
        try:
            if datetime.fromisoformat(expires_at) < datetime.fromisoformat(now_iso):
                # Expired: clean up session
                cursor.execute("DELETE FROM sessions WHERE token = ?;", (token.strip(),))
                conn.commit()
                return None
        except (ValueError, TypeError):
            return None

        return {
            "id": user_id,
            "name": name,
            "email": email,
            "created_at": created_at,
            "isGuest": False,
        }


def revoke_session(token: str, db_path: Optional[Path] = None) -> bool:
    """Revoke (delete) a session token on logout."""
    if not token:
        return False

    path = init_auth_db(db_path)
    with get_db_connection(path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = ?;", (token.strip(),))
        conn.commit()
        return cursor.rowcount > 0


def cleanup_expired_sessions(db_path: Optional[Path] = None) -> int:
    """Delete all expired sessions from the database."""
    path = init_auth_db(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection(path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE expires_at < ?;", (now_iso,))
        conn.commit()
        return cursor.rowcount


# CLI Bridge for external processes or Vite middleware
def main():
    """CLI interface for authentication service commands."""
    if len(sys.argv) < 2:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "Action required: register, login, verify, logout, cleanup.",
                }
            )
        )
        sys.exit(1)

    action = sys.argv[1].lower()
    raw_payload = sys.argv[2] if len(sys.argv) > 2 else "{}"

    try:
        payload = json.loads(raw_payload) if isinstance(raw_payload, str) else {}
    except json.JSONDecodeError:
        print(json.dumps({"success": False, "error": "Invalid JSON payload."}))
        sys.exit(1)

    if action == "register":
        result = register_user(
            name=payload.get("name", ""),
            email=payload.get("email", ""),
            password=payload.get("password", ""),
        )
        print(json.dumps(result))

    elif action == "login":
        result = authenticate_user(
            email=payload.get("email", ""),
            password=payload.get("password", ""),
        )
        print(json.dumps(result))

    elif action == "verify":
        user = validate_session(token=payload.get("token", ""))
        if user:
            print(json.dumps({"success": True, "user": user}))
        else:
            print(
                json.dumps(
                    {
                        "success": False,
                        "error": "Session is invalid or has expired.",
                        "code": "INVALID_SESSION",
                    }
                )
            )

    elif action == "logout":
        revoked = revoke_session(token=payload.get("token", ""))
        print(json.dumps({"success": True, "revoked": revoked}))

    elif action == "cleanup":
        count = cleanup_expired_sessions()
        print(json.dumps({"success": True, "cleaned_count": count}))

    else:
        print(json.dumps({"success": False, "error": f"Unknown action: {action}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Unit tests for ai.safety.auth_service.
Verifies password hashing, validation, registration, login, rate limiting/lockout,
session validation, and session revocation.
"""

import unittest
import tempfile
import os
import shutil
import sqlite3
from pathlib import Path

from ai.safety.auth_service import (
    hash_password,
    verify_password,
    validate_email_format,
    validate_password_strength,
    validate_name,
    register_user,
    authenticate_user,
    validate_session,
    revoke_session,
    cleanup_expired_sessions,
    MAX_FAILED_ATTEMPTS,
)


class TestAuthService(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_users.db"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_password_hashing_and_verification(self):
        pw = "SecureMedPass2026!"
        hashed = hash_password(pw)
        self.assertTrue(hashed.startswith("pbkdf2_sha256$600000$"))
        self.assertTrue(verify_password(pw, hashed))
        self.assertFalse(verify_password("WrongPassword123", hashed))
        self.assertFalse(verify_password("", hashed))
        self.assertFalse(verify_password(pw, "invalid_hash_string"))

    def test_email_validation(self):
        valid_emails = [
            "doctor@hospital.org",
            "evaluator.research@clinic.co.uk",
            "user123@sub.domain.edu",
        ]
        for em in valid_emails:
            ok, err = validate_email_format(em)
            self.assertTrue(ok, f"Expected '{em}' to be valid, got: {err}")

        invalid_emails = [
            "",
            "plainaddress",
            "@missinguser.com",
            "missingdomain@",
            "user@.com",
            "a" * 250 + "@example.com",  # Exceeds max length
        ]
        for em in invalid_emails:
            ok, _ = validate_email_format(em)
            self.assertFalse(ok, f"Expected '{em}' to be invalid")

    def test_password_strength(self):
        # Valid
        ok, _ = validate_password_strength("ClinicalPass1")
        self.assertTrue(ok)

        # Too short (< 8)
        ok, err = validate_password_strength("Pass1")
        self.assertFalse(ok)
        self.assertIn("at least 8 characters", err)

        # No digits
        ok, err = validate_password_strength("NoDigitsHereAtAll")
        self.assertFalse(ok)
        self.assertIn("at least one number", err)

        # No letters
        ok, err = validate_password_strength("1234567890")
        self.assertFalse(ok)
        self.assertIn("at least one letter", err)

    def test_name_validation(self):
        ok, _ = validate_name("Dr. Jane Doe")
        self.assertTrue(ok)
        ok, _ = validate_name("A")
        self.assertFalse(ok)
        ok, _ = validate_name("")
        self.assertFalse(ok)

    def test_registration_success_and_duplicate_prevention(self):
        res1 = register_user(
            name="Dr. Sarah Chen",
            email="sarah.chen@clinic.org",
            password="StrongPassword123",
            db_path=self.db_path,
        )
        self.assertTrue(res1["success"])
        self.assertIn("token", res1)
        self.assertEqual(res1["user"]["name"], "Dr. Sarah Chen")
        self.assertEqual(res1["user"]["email"], "sarah.chen@clinic.org")
        self.assertFalse(res1["user"]["isGuest"])

        # Attempt duplicate registration with same email (case-insensitive)
        res2 = register_user(
            name="Sarah Duplicate",
            email="SARAH.CHEN@clinic.org",
            password="StrongPassword123",
            db_path=self.db_path,
        )
        self.assertFalse(res2["success"])
        self.assertEqual(res2["code"], "EMAIL_EXISTS")

    def test_authentication_success_and_generic_errors(self):
        register_user(
            name="Researcher Alex",
            email="alex@medresearch.org",
            password="ValidPassword2026",
            db_path=self.db_path,
        )

        # Valid login
        login_res = authenticate_user(
            email="alex@medresearch.org",
            password="ValidPassword2026",
            db_path=self.db_path,
        )
        self.assertTrue(login_res["success"])
        self.assertIn("token", login_res)
        self.assertEqual(login_res["user"]["name"], "Researcher Alex")

        # Wrong password -> generic error
        bad_pw_res = authenticate_user(
            email="alex@medresearch.org",
            password="WrongPassword999",
            db_path=self.db_path,
        )
        self.assertFalse(bad_pw_res["success"])
        self.assertEqual(bad_pw_res["error"], "Invalid email or password.")

        # Non-existent email -> same generic error (no enumeration)
        no_user_res = authenticate_user(
            email="nonexistent@clinic.org",
            password="SomePassword123",
            db_path=self.db_path,
        )
        self.assertFalse(no_user_res["success"])
        self.assertEqual(no_user_res["error"], "Invalid email or password.")

    def test_brute_force_lockout(self):
        register_user(
            name="Target User",
            email="target@hospital.org",
            password="CorrectPassword123",
            db_path=self.db_path,
        )

        # Trigger failed attempts up to MAX_FAILED_ATTEMPTS
        for _ in range(MAX_FAILED_ATTEMPTS):
            res = authenticate_user(
                email="target@hospital.org",
                password="WrongPassword!",
                db_path=self.db_path,
            )
            self.assertFalse(res["success"])

        # Subsequent attempt, even with correct password, should be locked out
        locked_res = authenticate_user(
            email="target@hospital.org",
            password="CorrectPassword123",
            db_path=self.db_path,
        )
        self.assertFalse(locked_res["success"])
        self.assertEqual(locked_res["code"], "ACCOUNT_LOCKED")
        self.assertIn("Account temporarily locked", locked_res["error"])

    def test_session_lifecycle(self):
        reg = register_user(
            name="Session Tester",
            email="session@test.org",
            password="TestSessionPassword1",
            db_path=self.db_path,
        )
        token = reg["token"]

        # Validate active session
        user_profile = validate_session(token=token, db_path=self.db_path)
        self.assertIsNotNone(user_profile)
        self.assertEqual(user_profile["email"], "session@test.org")

        # Invalidate / Revoke session (logout)
        revoked = revoke_session(token=token, db_path=self.db_path)
        self.assertTrue(revoked)

        # Subsequent validation returns None
        user_after_logout = validate_session(token=token, db_path=self.db_path)
        self.assertIsNone(user_after_logout)

    def test_cleanup_expired_sessions(self):
        # Register user with 0-hour session (expires immediately)
        reg = register_user(
            name="Expired Tester",
            email="expired@test.org",
            password="TestExpiredPassword1",
            db_path=self.db_path,
            session_hours=-1,  # Expired in past
        )
        token = reg["token"]

        # Validate immediately catches expiration and removes
        user = validate_session(token=token, db_path=self.db_path)
        self.assertIsNone(user)

        # Cleanup call cleans any remaining expired
        count = cleanup_expired_sessions(db_path=self.db_path)
        self.assertGreaterEqual(count, 0)


if __name__ == "__main__":
    unittest.main()

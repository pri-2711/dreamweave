"""
Unit tests for DreamWeave Security Core and Token Utilities.
Verifies password hashing, password verification, token issuance, explicit claims,
token type segregation, expiration checks, signature verification, and configuration safety.
"""

import os
import sys
import unittest
from datetime import timedelta
from unittest.mock import patch

# Ensure workspace root and brain directory are in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.src.config import (
    validate_jwt_secret,
    get_jwt_secret_key,
    DEV_FALLBACK_JWT_SECRET,
)
from brain.src.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_token,
    decode_token,
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    TokenExpiredError,
    TokenInvalidError,
    TokenTypeError,
)


class TestSecurityCore(unittest.TestCase):

    def test_01_password_hashing_and_verification(self):
        """Verify bcrypt password hashing generates valid hash and verifies correctly."""
        password = "SecurePassword#2026!"
        hashed = hash_password(password)

        self.assertIsInstance(hashed, str)
        self.assertNotEqual(password, hashed)
        self.assertTrue(hashed.startswith("$2b$12$"))

        # Successful verification
        self.assertTrue(verify_password(password, hashed))

    def test_02_password_verification_failures(self):
        """Verify incorrect passwords, empty inputs, and corrupt hashes fail safely."""
        password = "CorrectHorseBatteryStaple"
        hashed = hash_password(password)

        # Incorrect password
        self.assertFalse(verify_password("WrongPassword123", hashed))

        # Empty and invalid types
        self.assertFalse(verify_password("", hashed))
        self.assertFalse(verify_password(None, hashed))
        self.assertFalse(verify_password(password, ""))
        self.assertFalse(verify_password(password, None))

        # Corrupted hash format
        self.assertFalse(verify_password(password, "$2b$12$corruptedhashnotvalidbase64"))
        self.assertFalse(verify_password(password, "random_plaintext_string"))

    def test_03_password_constraints(self):
        """Verify empty password raises ValueError and max length is enforced."""
        with self.assertRaises(ValueError):
            hash_password("")

        with self.assertRaises(ValueError):
            hash_password(None)

        # Passwords over 72 bytes should raise ValueError in bcrypt
        long_password = "a" * 80
        with self.assertRaises(ValueError):
            hash_password(long_password)

    def test_04_access_token_creation_and_claims(self):
        """Verify access token contains explicit sub, type, jti, iat, exp claims."""
        user_id = "000000000000000000000001"
        token = create_access_token(subject=user_id)

        self.assertIsInstance(token, str)
        self.assertTrue(len(token.split(".")) == 3)

        payload = decode_token(token, expected_type=TOKEN_TYPE_ACCESS)
        self.assertEqual(payload["sub"], user_id)
        self.assertEqual(payload["type"], TOKEN_TYPE_ACCESS)
        self.assertIn("jti", payload)
        self.assertIn("iat", payload)
        self.assertIn("exp", payload)
        self.assertGreater(payload["exp"], payload["iat"])

    def test_05_refresh_token_creation_and_claims(self):
        """Verify refresh token is created with refresh type and longer lifetime."""
        user_id = "000000000000000000000002"
        access_tok = create_access_token(subject=user_id)
        refresh_tok = create_refresh_token(subject=user_id)

        acc_payload = decode_token(access_tok, expected_type=TOKEN_TYPE_ACCESS)
        ref_payload = decode_token(refresh_tok, expected_type=TOKEN_TYPE_REFRESH)

        self.assertEqual(ref_payload["sub"], user_id)
        self.assertEqual(ref_payload["type"], TOKEN_TYPE_REFRESH)
        self.assertNotEqual(acc_payload["jti"], ref_payload["jti"])
        # Refresh token expiration should be longer than access token
        self.assertGreater(ref_payload["exp"] - ref_payload["iat"], acc_payload["exp"] - acc_payload["iat"])

    def test_06_token_type_separation(self):
        """Verify refresh tokens cannot be used where access tokens are expected, and vice versa."""
        user_id = "000000000000000000000003"
        access_tok = create_access_token(subject=user_id)
        refresh_tok = create_refresh_token(subject=user_id)

        # Attempt to decode refresh token as access token
        with self.assertRaises(TokenTypeError) as ctx:
            decode_token(refresh_tok, expected_type=TOKEN_TYPE_ACCESS)
        self.assertIn("expected 'access', got 'refresh'", str(ctx.exception))

        # Attempt to decode access token as refresh token
        with self.assertRaises(TokenTypeError) as ctx:
            decode_token(access_tok, expected_type=TOKEN_TYPE_REFRESH)
        self.assertIn("expected 'refresh', got 'access'", str(ctx.exception))

    def test_07_expired_token(self):
        """Verify expired tokens raise TokenExpiredError."""
        user_id = "000000000000000000000004"
        # Create token that expired 10 seconds ago
        expired_token = create_access_token(
            subject=user_id,
            expires_delta=timedelta(seconds=-10)
        )

        with self.assertRaises(TokenExpiredError):
            decode_token(expired_token)

    def test_08_invalid_signature_and_tampering(self):
        """Verify tokens signed with a different key or tampered with are rejected."""
        user_id = "000000000000000000000005"
        alt_key = "different-secret-key-that-is-at-least-32-chars-long!"
        foreign_token = create_access_token(subject=user_id, secret_key=alt_key)

        with self.assertRaises(TokenInvalidError):
            decode_token(foreign_token)

        # Tampered payload
        valid_token = create_access_token(subject=user_id)
        parts = valid_token.split(".")
        # Tamper middle part (payload)
        tampered_token = f"{parts[0]}.eyJhZG1pbiI6dHJ1ZX0.{parts[2]}"
        with self.assertRaises(TokenInvalidError):
            decode_token(tampered_token)

    def test_09_malformed_token_inputs(self):
        """Verify malformed token strings raise TokenInvalidError."""
        for malformed in ["", None, "abc", "a.b", "not-a-token", "123.456.789"]:
            with self.assertRaises(TokenInvalidError):
                decode_token(malformed)

    def test_10_custom_claims_handling(self):
        """Verify custom claims are embedded and reserved claims cannot be overwritten."""
        user_id = "000000000000000000000006"
        token = create_access_token(
            subject=user_id,
            custom_claims={"role": "admin", "sub": "attacker_id", "type": "refresh"}
        )

        payload = decode_token(token, expected_type=TOKEN_TYPE_ACCESS)
        self.assertEqual(payload["role"], "admin")
        # Reserved claims must NOT be overwritten
        self.assertEqual(payload["sub"], user_id)
        self.assertEqual(payload["type"], TOKEN_TYPE_ACCESS)

    def test_11_production_secret_validation(self):
        """Verify safe failure in production mode when secret is missing, short, or placeholder."""
        # 1. Missing secret in production
        with self.assertRaises(ValueError) as ctx:
            validate_jwt_secret(secret_key="", env="production")
        self.assertIn("required in production", str(ctx.exception))

        # 2. Known placeholder in production
        placeholders = [
            "changeme",
            "your_secure_random_jwt_secret_key_minimum_32_characters_here",
            "secret123",
            "default_dev_secret_key_not_for_production"
        ]
        for p in placeholders:
            with self.assertRaises(ValueError) as ctx:
                validate_jwt_secret(secret_key=p, env="production")
            self.assertTrue(
                "placeholder" in str(ctx.exception).lower() or "insecure" in str(ctx.exception).lower()
            )

        # 3. Secret too short in production (< 32 chars)
        with self.assertRaises(ValueError) as ctx:
            validate_jwt_secret(secret_key="short-secret-key-16-bytes", env="production")
        self.assertIn("minimum 32 characters", str(ctx.exception))

        # 4. Valid 32+ char secret in production succeeds without exception
        valid_prod_key = "a" * 32
        validate_jwt_secret(secret_key=valid_prod_key, env="production")

    def test_12_development_fallback_safety(self):
        """Verify development environment safely falls back if secret is not set."""
        with patch("brain.src.config.ENVIRONMENT", "development"):
            with patch("brain.src.config.JWT_SECRET_KEY", ""):
                key = get_jwt_secret_key()
                self.assertEqual(key, DEV_FALLBACK_JWT_SECRET)


if __name__ == "__main__":
    unittest.main()

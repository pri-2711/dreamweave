"""
Comprehensive Authentication API tests for DreamWeave Phase 3 Step 3:
- User registration and normalized email storage
- Duplicate registration rejection (409)
- Login credential verification and generic 401 error
- Access token profile retrieval (/auth/me) with sanitized output (no password_hash)
- Expired, malformed, revoked, and wrong-type token handling
- Refresh token rotation (issues new token pair, invalidates old refresh token)
- Logout token revocation (revokes access token and optional refresh token)
- Missing Authorization header handling
- CORS headers verification
"""

import os
import sys
import unittest
from datetime import timedelta
import mongomock
from fastapi.testclient import TestClient

# Python path setup
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Isolated mongomock database
mock_client = mongomock.MongoClient()
mock_db = mock_client["dreamweave"]

import brain.src.database.connection as conn
conn._client = mock_client
conn.get_database = lambda: mock_db
conn.ping_database = lambda: {"status": "ok", "database": "dreamweave"}

import brain.src.database.collections as colls
colls.get_database = lambda: mock_db

from brain.src.api.app import app
from brain.src.utils.security import (
    create_access_token,
    create_refresh_token,
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
)

client = TestClient(app)


class TestAuthenticationAPI(unittest.TestCase):

    def setUp(self):
        """Clean all collections between tests."""
        conn.get_database = lambda: mock_db
        colls.get_database = lambda: mock_db
        for c in mock_db.list_collection_names():
            mock_db[c].delete_many({})

    def test_01_successful_registration_and_normalized_email(self):
        """Verify registration normalizes email, creates user, and returns tokens + profile."""
        payload = {
            "email": "  Alice.Wonderland@Example.COM  ",
            "name": "Alice Wonderland",
            "password": "SecurePassword123!"
        }
        res = client.post("/auth/register", json=payload)
        self.assertEqual(res.status_code, 201)

        data = res.json()
        self.assertIn("tokens", data)
        self.assertIn("user", data)

        tokens = data["tokens"]
        self.assertEqual(tokens["token_type"], "bearer")
        self.assertTrue(len(tokens["access_token"]) > 20)
        self.assertTrue(len(tokens["refresh_token"]) > 20)
        self.assertGreater(tokens["expires_in"], 0)

        user = data["user"]
        self.assertEqual(user["email"], "alice.wonderland@example.com")
        self.assertEqual(user["profile"]["name"], "Alice Wonderland")
        self.assertNotIn("password_hash", str(user))
        self.assertNotIn("auth", user)

        # Verify database record
        db_user = mock_db["users"].find_one({"email": "alice.wonderland@example.com"})
        self.assertIsNotNone(db_user)
        self.assertNotEqual(db_user["auth"]["password_hash"], "SecurePassword123!")

    def test_02_duplicate_registration_conflict(self):
        """Verify registering with an existing email returns 409 Conflict."""
        payload = {
            "email": "bob@example.com",
            "name": "Bob Builder",
            "password": "CanWeFixIt123!"
        }
        res1 = client.post("/auth/register", json=payload)
        self.assertEqual(res1.status_code, 201)

        # Second attempt with same email in different case
        payload2 = {
            "email": "BOB@EXAMPLE.COM",
            "name": "Bob Duplicate",
            "password": "DifferentPassword123!"
        }
        res2 = client.post("/auth/register", json=payload2)
        self.assertEqual(res2.status_code, 409)
        self.assertIn("already exists", res2.json()["detail"])

    def test_03_successful_login_and_last_login_update(self):
        """Verify login succeeds with valid credentials and updates last_login."""
        # Register user
        reg_payload = {
            "email": "carol@example.com",
            "name": "Carol Singer",
            "password": "MelodyPassword123!"
        }
        client.post("/auth/register", json=reg_payload)

        # Login with uppercase email
        login_payload = {
            "email": "CAROL@EXAMPLE.COM",
            "password": "MelodyPassword123!"
        }
        res = client.post("/auth/login", json=login_payload)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertIn("tokens", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], "carol@example.com")
        self.assertNotIn("password_hash", str(data["user"]))

        # Verify last_login in DB
        db_user = mock_db["users"].find_one({"email": "carol@example.com"})
        self.assertIsNotNone(db_user["last_login"])

    def test_04_login_failure_generic_error(self):
        """Verify invalid email or incorrect password returns generic 401 without leakage."""
        reg_payload = {
            "email": "dave@example.com",
            "name": "Dave Developer",
            "password": "CodePassword123!"
        }
        client.post("/auth/register", json=reg_payload)

        # Wrong password
        res_wrong_pw = client.post("/auth/login", json={
            "email": "dave@example.com",
            "password": "WrongPassword123!"
        })
        self.assertEqual(res_wrong_pw.status_code, 401)
        self.assertEqual(res_wrong_pw.json()["detail"], "Invalid email or password.")

        # Non-existent email
        res_non_existent = client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "SomePassword123!"
        })
        self.assertEqual(res_non_existent.status_code, 401)
        # Detail must match exactly (no enumeration)
        self.assertEqual(res_non_existent.json()["detail"], "Invalid email or password.")

    def test_05_get_current_user_profile(self):
        """Verify /auth/me returns user profile using access token without password hash."""
        reg_res = client.post("/auth/register", json={
            "email": "eva@example.com",
            "name": "Eva Explorer",
            "password": "TravelPassword123!"
        })
        access_token = reg_res.json()["tokens"]["access_token"]

        # Call /auth/me with Bearer token
        headers = {"Authorization": f"Bearer {access_token}"}
        me_res = client.get("/auth/me", headers=headers)
        self.assertEqual(me_res.status_code, 200)

        user_data = me_res.json()
        self.assertEqual(user_data["email"], "eva@example.com")
        self.assertEqual(user_data["profile"]["name"], "Eva Explorer")
        self.assertNotIn("password_hash", str(user_data))
        self.assertNotIn("auth", user_data)

    def test_06_auth_me_missing_or_malformed_token(self):
        """Verify /auth/me rejects missing or malformed Authorization header."""
        # Missing header
        res_missing = client.get("/auth/me")
        self.assertEqual(res_missing.status_code, 401)

        # Invalid format (not Bearer)
        res_malformed = client.get("/auth/me", headers={"Authorization": "Basic 123456"})
        self.assertEqual(res_malformed.status_code, 401)

        # Garbage token
        res_garbage = client.get("/auth/me", headers={"Authorization": "Bearer not-a-valid-jwt"})
        self.assertEqual(res_garbage.status_code, 401)

    def test_07_auth_me_rejects_refresh_token(self):
        """Verify /auth/me rejects a refresh token when an access token is required."""
        reg_res = client.post("/auth/register", json={
            "email": "frank@example.com",
            "name": "Frank Forest",
            "password": "ForestPassword123!"
        })
        refresh_token = reg_res.json()["tokens"]["refresh_token"]

        headers = {"Authorization": f"Bearer {refresh_token}"}
        res = client.get("/auth/me", headers=headers)
        self.assertEqual(res.status_code, 401)
        self.assertIn("expected an access token", res.json()["detail"].lower())

    def test_08_refresh_token_rotation_success_and_invalidation(self):
        """Verify /auth/refresh rotates tokens, returns new token pair, and revokes old refresh token."""
        reg_res = client.post("/auth/register", json={
            "email": "grace@example.com",
            "name": "Grace Hopper",
            "password": "CompilerPassword123!"
        })
        initial_refresh_token = reg_res.json()["tokens"]["refresh_token"]

        # Rotate refresh token
        ref_res = client.post("/auth/refresh", json={"refresh_token": initial_refresh_token})
        self.assertEqual(ref_res.status_code, 200)

        new_tokens = ref_res.json()
        self.assertIn("access_token", new_tokens)
        self.assertIn("refresh_token", new_tokens)
        new_access = new_tokens["access_token"]
        new_refresh = new_tokens["refresh_token"]

        # New access token must work on /auth/me
        me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {new_access}"})
        self.assertEqual(me_res.status_code, 200)

        # Re-using the OLD refresh token must fail (401 Revoked)
        reuse_res = client.post("/auth/refresh", json={"refresh_token": initial_refresh_token})
        self.assertEqual(reuse_res.status_code, 401)
        self.assertIn("revoked", reuse_res.json()["detail"].lower())

        # The new refresh token CAN be used again
        ref_res2 = client.post("/auth/refresh", json={"refresh_token": new_refresh})
        self.assertEqual(ref_res2.status_code, 200)

    def test_09_refresh_rejects_access_token(self):
        """Verify /auth/refresh rejects access tokens."""
        reg_res = client.post("/auth/register", json={
            "email": "hank@example.com",
            "name": "Hank Hill",
            "password": "PropanePassword123!"
        })
        access_token = reg_res.json()["tokens"]["access_token"]

        res = client.post("/auth/refresh", json={"refresh_token": access_token})
        self.assertEqual(res.status_code, 401)
        self.assertIn("expected a refresh token", res.json()["detail"].lower())

    def test_10_logout_revocation(self):
        """Verify /auth/logout revokes access token and refresh token."""
        reg_res = client.post("/auth/register", json={
            "email": "iris@example.com",
            "name": "Iris Flower",
            "password": "FlowerPassword123!"
        })
        access_token = reg_res.json()["tokens"]["access_token"]
        refresh_token = reg_res.json()["tokens"]["refresh_token"]

        # Verify access token works initially
        pre_res = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        self.assertEqual(pre_res.status_code, 200)

        # Logout revoking both
        logout_res = client.post(
            "/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        self.assertEqual(logout_res.status_code, 200)

        # Access token must now be rejected
        post_me = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        self.assertEqual(post_me.status_code, 401)
        self.assertIn("revoked", post_me.json()["detail"].lower())

        # Refresh token must also be rejected
        post_ref = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        self.assertEqual(post_ref.status_code, 401)
        self.assertIn("revoked", post_ref.json()["detail"].lower())

    def test_11_expired_token_handling(self):
        """Verify expired tokens are rejected with clear 401."""
        user_id = "000000000000000000000001"
        expired_access = create_access_token(subject=user_id, expires_delta=timedelta(seconds=-10))
        expired_refresh = create_refresh_token(subject=user_id, expires_delta=timedelta(seconds=-10))

        # /auth/me with expired access
        res_me = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_access}"})
        self.assertEqual(res_me.status_code, 401)
        self.assertIn("expired", res_me.json()["detail"].lower())

        # /auth/refresh with expired refresh
        res_ref = client.post("/auth/refresh", json={"refresh_token": expired_refresh})
        self.assertEqual(res_ref.status_code, 401)
        self.assertIn("expired", res_ref.json()["detail"].lower())

    def test_12_cors_headers(self):
        """Verify CORS headers respond to configured origins."""
        # Preflight OPTIONS request from allowed origin
        allowed_origin = "http://localhost:3000"
        res = client.options(
            "/auth/login",
            headers={
                "Origin": allowed_origin,
                "Access-Control-Request-Method": "POST"
            }
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("access-control-allow-origin"), allowed_origin)
        self.assertEqual(res.headers.get("access-control-allow-credentials"), "true")

        # Request from disallowed origin
        disallowed_origin = "http://malicious-site.com"
        res_disallowed = client.options(
            "/auth/login",
            headers={
                "Origin": disallowed_origin,
                "Access-Control-Request-Method": "POST"
            }
        )
        self.assertNotEqual(res_disallowed.headers.get("access-control-allow-origin"), disallowed_origin)


if __name__ == "__main__":
    unittest.main()

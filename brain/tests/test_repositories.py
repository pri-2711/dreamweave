"""
Focused tests for DreamWeave Phase 3 Step 2 Repositories:
- User email normalization & duplicate detection
- User last_login updates & sanitization
- Space membership lookup, role assignment, and member removal
- Listing owned and collaborated spaces without duplicates
- Owner protection (removal prevention & role demotion prevention)
- Token revocation repository & TTL index registration
"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import mongomock
from pymongo.errors import DuplicateKeyError

# Ensure workspace root and brain directory are in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Shared mock database for repository tests
mock_client = mongomock.MongoClient()
mock_db = mock_client["dreamweave"]

import brain.src.database.connection as conn
conn._client = mock_client
conn.get_database = lambda: mock_db
conn.ping_database = lambda: {"status": "ok", "database": "dreamweave"}

import brain.src.database.collections as colls
colls.get_database = lambda: mock_db

from brain.src.database.collections import (
    COLLECTION_USERS,
    COLLECTION_SPACES,
    COLLECTION_SPACE_MEMBERS,
    COLLECTION_REVOKED_TOKENS,
    ALL_COLLECTIONS,
)
from brain.src.database.indexes import ensure_indexes, INDEX_SPECS
from brain.src.database.repositories import users as users_repo
from brain.src.database.repositories import spaces as spaces_repo
from brain.src.database.repositories import tokens as tokens_repo


class TestRepositoriesSecurityEnhancements(unittest.TestCase):

    def setUp(self):
        """Clean collections and ensure indexes between tests."""
        for c in mock_db.list_collection_names():
            mock_db[c].delete_many({})

    def test_01_email_normalization_and_lookup(self):
        """Verify user emails are consistently trimmed and lowercased on creation and retrieval."""
        raw_email = "  User.Name+Test@Example.COM  "
        normalized = "user.name+test@example.com"

        user = users_repo.create_user(
            email=raw_email,
            name="Test User",
            password_hash="$2b$12$dummyhash"
        )
        self.assertEqual(user["email"], normalized)

        # Lookups with varied casing and whitespace
        found_exact = users_repo.get_user_by_email(normalized)
        self.assertIsNotNone(found_exact)
        self.assertEqual(found_exact["_id"], user["_id"])

        found_upper = users_repo.get_user_by_email("USER.NAME+TEST@EXAMPLE.COM")
        self.assertIsNotNone(found_upper)
        self.assertEqual(found_upper["_id"], user["_id"])

        found_padded = users_repo.get_user_by_email("   user.name+test@example.com   ")
        self.assertIsNotNone(found_padded)
        self.assertEqual(found_padded["_id"], user["_id"])

        # Non-existent email
        self.assertIsNone(users_repo.get_user_by_email("nobody@example.com"))
        self.assertIsNone(users_repo.get_user_by_email(""))

    def test_02_update_last_login(self):
        """Verify update_last_login successfully updates timestamp for valid users and fails for invalid."""
        user = users_repo.create_user(
            email="login.test@example.com",
            name="Login User"
        )
        self.assertIsNone(user["last_login"])

        # Successful update
        success = users_repo.update_last_login(user["_id"])
        self.assertTrue(success)

        updated_user = users_repo.get_user_by_id(user["_id"])
        self.assertIsNotNone(updated_user["last_login"])
        self.assertIsInstance(updated_user["last_login"], datetime)

        # Unsuccessful update with non-existent id
        non_existent_id = str(ObjectId())
        self.assertFalse(users_repo.update_last_login(non_existent_id))

        # Unsuccessful update with invalid id format
        self.assertFalse(users_repo.update_last_login("invalid-id"))

    def test_03_sanitize_user_doc(self):
        """Verify sanitize_user_doc strips password_hash without altering original document."""
        user = users_repo.create_user(
            email="safe@example.com",
            name="Safe User",
            password_hash="$2b$12$verysecretpasswordhash"
        )

        sanitized = users_repo.sanitize_user_doc(user)
        self.assertIsNotNone(sanitized)
        self.assertNotIn("password_hash", sanitized["auth"])
        self.assertEqual(sanitized["email"], "safe@example.com")

        # Original document must still retain auth data
        self.assertIn("password_hash", user["auth"])

        # None input handling
        self.assertIsNone(users_repo.sanitize_user_doc(None))

    def test_04_space_membership_crud(self):
        """Verify membership lookup, updating role, and removing non-owner members."""
        owner_id = str(ObjectId())
        member_id = str(ObjectId())

        space = spaces_repo.create_space(
            owner_id=owner_id,
            name="Collaboration Space"
        )
        space_id = space["_id"]

        # Owner is automatically added
        owner_member = spaces_repo.get_space_member(space_id, owner_id)
        self.assertIsNotNone(owner_member)
        self.assertEqual(owner_member["role"], "owner")

        # Add new member as viewer
        new_mem = spaces_repo.add_space_member(space_id, member_id, role="viewer")
        self.assertEqual(new_mem["role"], "viewer")

        lookup_mem = spaces_repo.get_space_member(space_id, member_id)
        self.assertIsNotNone(lookup_mem)
        self.assertEqual(lookup_mem["role"], "viewer")

        # Update member role to editor
        updated_mem = spaces_repo.add_space_member(space_id, member_id, role="editor")
        self.assertEqual(updated_mem["role"], "editor")

        # Remove member
        removed = spaces_repo.remove_space_member(space_id, member_id)
        self.assertTrue(removed)

        # After removal
        self.assertIsNone(spaces_repo.get_space_member(space_id, member_id))

        # Removing non-existent member returns False
        self.assertFalse(spaces_repo.remove_space_member(space_id, member_id))

    def test_05_owner_protection(self):
        """Verify the space owner cannot be removed or demoted through membership methods."""
        owner_id = str(ObjectId())
        space = spaces_repo.create_space(
            owner_id=owner_id,
            name="Protected Space"
        )
        space_id = space["_id"]

        # 1. Attempt to remove owner -> must fail
        removal_res = spaces_repo.remove_space_member(space_id, owner_id)
        self.assertFalse(removal_res)

        # Owner must still exist as owner
        owner_member = spaces_repo.get_space_member(space_id, owner_id)
        self.assertIsNotNone(owner_member)
        self.assertEqual(owner_member["role"], "owner")

        # 2. Attempt to demote owner to viewer via add_space_member -> must preserve owner role
        demote_res = spaces_repo.add_space_member(space_id, owner_id, role="viewer")
        self.assertEqual(demote_res["role"], "owner")

        owner_member_after = spaces_repo.get_space_member(space_id, owner_id)
        self.assertEqual(owner_member_after["role"], "owner")

    def test_06_list_spaces_for_user_without_duplicates(self):
        """Verify list_spaces_for_user returns owned and collaborated spaces without duplicate records."""
        user_a = str(ObjectId())
        user_b = str(ObjectId())

        # User A owns 2 spaces
        sp_a1 = spaces_repo.create_space(owner_id=user_a, name="Space A1")
        sp_a2 = spaces_repo.create_space(owner_id=user_a, name="Space A2")

        # User B owns 1 space
        sp_b1 = spaces_repo.create_space(owner_id=user_b, name="Space B1")

        # Add User A as collaborator to Space B1
        spaces_repo.add_space_member(sp_b1["_id"], user_a, role="editor")

        # List spaces for User A: should return sp_a1, sp_a2, and sp_b1 (exactly 3, no duplicates)
        user_a_spaces = spaces_repo.list_spaces_for_user(user_a)
        self.assertEqual(len(user_a_spaces), 3)

        space_ids = [str(s["_id"]) for s in user_a_spaces]
        self.assertEqual(len(space_ids), len(set(space_ids)))  # No duplicates
        self.assertIn(str(sp_a1["_id"]), space_ids)
        self.assertIn(str(sp_a2["_id"]), space_ids)
        self.assertIn(str(sp_b1["_id"]), space_ids)

        # List spaces for User B: should return only sp_b1
        user_b_spaces = spaces_repo.list_spaces_for_user(user_b)
        self.assertEqual(len(user_b_spaces), 1)
        self.assertEqual(str(user_b_spaces[0]["_id"]), str(sp_b1["_id"]))

    def test_07_revoked_tokens_repository_and_index_specs(self):
        """Verify revoked_tokens collection operations, TTL index registration, and unique jti."""
        user_id = str(ObjectId())
        jti = "unique-token-uuid-12345"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        # Revoke a token
        record = tokens_repo.revoke_token(
            jti=jti,
            token_type="access",
            expires_at=expires_at,
            user_id=user_id,
            reason="user_logout"
        )
        self.assertEqual(record["jti"], jti)
        self.assertEqual(record["token_type"], "access")
        self.assertEqual(record["reason"], "user_logout")

        # Check token is revoked
        self.assertTrue(tokens_repo.is_token_revoked(jti))
        self.assertFalse(tokens_repo.is_token_revoked("unrevoked-jti"))

        # Idempotent re-revocation
        dup_record = tokens_repo.revoke_token(
            jti=jti,
            token_type="access",
            expires_at=expires_at,
            user_id=user_id
        )
        self.assertEqual(str(dup_record["_id"]), str(record["_id"]))

        # Verify collection registered in ALL_COLLECTIONS
        self.assertIn(COLLECTION_REVOKED_TOKENS, ALL_COLLECTIONS)

        # Programmatically ensure indexes on mock database
        index_res = ensure_indexes(mock_db)
        self.assertIn(COLLECTION_REVOKED_TOKENS, index_res)

        # Verify TTL index specs configured in INDEX_SPECS
        revoked_specs = INDEX_SPECS[COLLECTION_REVOKED_TOKENS]
        has_unique_jti = any(
            spec.get("unique") is True and ("jti", 1) in spec["keys"]
            for spec in revoked_specs
        )
        has_ttl_expires = any(
            spec.get("expireAfterSeconds") == 0 and ("expires_at", 1) in spec["keys"]
            for spec in revoked_specs
        )
        self.assertTrue(has_unique_jti)
        self.assertTrue(has_ttl_expires)


if __name__ == "__main__":
    unittest.main()

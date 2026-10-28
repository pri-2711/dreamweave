"""
Authorization and Permissions Unit & Integration Tests.
Tests multi-user isolation, role hierarchy (owner/editor/viewer), cross-space boundaries,
and production protection of /db-init and JWT enforcement.
"""

import unittest
from unittest.mock import patch, MagicMock
from mongomock import MongoClient
from fastapi.testclient import TestClient
from bson import ObjectId
from brain.src.utils.security import create_access_token

mock_client = MongoClient()
mock_db = mock_client["dreamweave"]

import brain.src.database.connection as conn
conn._client = mock_client
conn.get_database = lambda: mock_db
conn.ping_database = lambda: {"status": "ok", "database": "dreamweave"}

import brain.src.database.collections as collections
collections.get_database = lambda: mock_db

from brain.src.api.app import app
from brain.src.services.authorization import (
    ROLE_HIERARCHY,
    get_user_space_role,
    check_space_access
)
from fastapi import HTTPException


class TestAuthorizationAndPermissions(unittest.TestCase):
    def setUp(self):
        for c in mock_db.list_collection_names():
            mock_db[c].delete_many({})

        self.client = TestClient(app)

        # Users
        self.user_a_id = str(ObjectId())
        self.user_b_id = str(ObjectId())
        self.user_c_id = str(ObjectId())

        self.token_user_a = create_access_token(self.user_a_id)
        self.token_user_b = create_access_token(self.user_b_id)
        self.token_user_c = create_access_token(self.user_c_id)

        self.auth_headers_a = {"Authorization": f"Bearer {self.token_user_a}"}
        self.auth_headers_b = {"Authorization": f"Bearer {self.token_user_b}"}
        self.auth_headers_c = {"Authorization": f"Bearer {self.token_user_c}"}

    def tearDown(self):
        pass

    def test_role_hierarchy_logic(self):
        """Test authorization service helper methods directly."""
        space_id = str(ObjectId())
        collections.get_collection(collections.COLLECTION_SPACES).insert_one({
            "_id": ObjectId(space_id),
            "name": "Auth Test Space",
            "owner_id": ObjectId(self.user_a_id)
        })
        collections.get_collection(collections.COLLECTION_SPACE_MEMBERS).insert_many([
            {"space_id": ObjectId(space_id), "user_id": ObjectId(self.user_a_id), "role": "owner"},
            {"space_id": ObjectId(space_id), "user_id": ObjectId(self.user_b_id), "role": "editor"},
            {"space_id": ObjectId(space_id), "user_id": ObjectId(self.user_c_id), "role": "viewer"}
        ])

        # Check roles
        self.assertEqual(get_user_space_role(space_id, self.user_a_id), "owner")
        self.assertEqual(get_user_space_role(space_id, self.user_b_id), "editor")
        self.assertEqual(get_user_space_role(space_id, self.user_c_id), "viewer")
        non_member_id = str(ObjectId())
        self.assertIsNone(get_user_space_role(space_id, non_member_id))

        # Check access: Owner has all permissions
        space_doc = check_space_access(space_id, self.user_a_id, "viewer")
        self.assertIsNotNone(space_doc)
        self.assertEqual(str(space_doc["_id"]), space_id)
        self.assertIsNotNone(check_space_access(space_id, self.user_a_id, "editor"))
        self.assertIsNotNone(check_space_access(space_id, self.user_a_id, "owner"))

        # Check access: Editor has viewer & editor permissions, but NOT owner
        self.assertIsNotNone(check_space_access(space_id, self.user_b_id, "viewer"))
        self.assertIsNotNone(check_space_access(space_id, self.user_b_id, "editor"))
        with self.assertRaises(HTTPException) as cm:
            check_space_access(space_id, self.user_b_id, "owner")
        self.assertEqual(cm.exception.status_code, 403)

        # Check access: Viewer has only viewer permission
        self.assertIsNotNone(check_space_access(space_id, self.user_c_id, "viewer"))
        with self.assertRaises(HTTPException) as cm:
            check_space_access(space_id, self.user_c_id, "editor")
        self.assertEqual(cm.exception.status_code, 403)

        # Check access: Non-member gets 403
        with self.assertRaises(HTTPException) as cm:
            check_space_access(space_id, non_member_id, "viewer")
        self.assertEqual(cm.exception.status_code, 403)

        # Check non-existent space gets 404
        with self.assertRaises(HTTPException) as cm:
            check_space_access(str(ObjectId()), self.user_a_id, "viewer")
        self.assertEqual(cm.exception.status_code, 404)

    def test_space_isolation_and_collaborators(self):
        """Test API endpoints for space isolation and collaborator management."""
        # User A creates a space
        resp = self.client.post(
            "/spaces",
            json={"name": "Alpha Space", "description": "Space of User A"},
            headers=self.auth_headers_a
        )
        self.assertEqual(resp.status_code, 201)
        space_id = resp.json()["id"]

        # User B (not a member) tries to get User A's space -> 403
        resp_b = self.client.get(f"/spaces/{space_id}", headers=self.auth_headers_b)
        self.assertEqual(resp_b.status_code, 403)

        # User A adds User B as viewer
        add_resp = self.client.post(
            f"/spaces/{space_id}/members",
            json={"user_id": self.user_b_id, "role": "viewer"},
            headers=self.auth_headers_a
        )
        self.assertEqual(add_resp.status_code, 201)

        # User B can now get the space
        resp_b = self.client.get(f"/spaces/{space_id}", headers=self.auth_headers_b)
        self.assertEqual(resp_b.status_code, 200)

        # User B (viewer) cannot update the space -> 403
        patch_b = self.client.patch(
            f"/spaces/{space_id}",
            json={"name": "Hacked Name"},
            headers=self.auth_headers_b
        )
        self.assertEqual(patch_b.status_code, 403)

        # User B (viewer) cannot delete the space -> 403
        del_b = self.client.delete(f"/spaces/{space_id}", headers=self.auth_headers_b)
        self.assertEqual(del_b.status_code, 403)

        # User A upgrades User B to editor
        upgrade_resp = self.client.post(
            f"/spaces/{space_id}/members",
            json={"user_id": self.user_b_id, "role": "editor"},
            headers=self.auth_headers_a
        )
        self.assertEqual(upgrade_resp.status_code, 201)

        # User B (editor) can now update space
        patch_b2 = self.client.patch(
            f"/spaces/{space_id}",
            json={"name": "Updated by Editor"},
            headers=self.auth_headers_b
        )
        self.assertEqual(patch_b2.status_code, 200)

        # User B (editor) still cannot delete space (owner required) -> 403
        del_b2 = self.client.delete(f"/spaces/{space_id}", headers=self.auth_headers_b)
        self.assertEqual(del_b2.status_code, 403)

        # User B cannot remove members -> 403
        rem_b = self.client.delete(f"/spaces/{space_id}/members/{self.user_a_id}", headers=self.auth_headers_b)
        self.assertEqual(rem_b.status_code, 403)

        # User A removes User B
        rem_a = self.client.delete(f"/spaces/{space_id}/members/{self.user_b_id}", headers=self.auth_headers_a)
        self.assertEqual(rem_a.status_code, 200)

        # User B is no longer a member -> 403
        resp_b_revoked = self.client.get(f"/spaces/{space_id}", headers=self.auth_headers_b)
        self.assertEqual(resp_b_revoked.status_code, 403)

    def test_content_and_rag_authorization(self):
        """Test content isolation and RAG space boundary enforcement."""
        # User A creates space
        resp = self.client.post(
            "/spaces",
            json={"name": "Content Test Space"},
            headers=self.auth_headers_a
        )
        space_id = resp.json()["id"]

        # User B cannot create content in User A's space -> 403
        resp_cnt_b = self.client.post(
            "/content",
            json={"space_id": space_id, "title": "Illegal item", "type": "note", "raw_text": "Sample text"},
            headers=self.auth_headers_b
        )
        self.assertEqual(resp_cnt_b.status_code, 403)

        # User A creates content
        resp_cnt_a = self.client.post(
            "/content",
            json={"space_id": space_id, "title": "Legal item", "type": "note", "raw_text": "Sample text"},
            headers=self.auth_headers_a
        )
        self.assertEqual(resp_cnt_a.status_code, 201)
        content_id = resp_cnt_a.json()["id"]

        # User B cannot get User A's content item -> 403
        resp_get_b = self.client.get(f"/content/{content_id}", headers=self.auth_headers_b)
        self.assertEqual(resp_get_b.status_code, 403)

        # User B cannot query RAG in User A's space -> 403
        rag_b = self.client.post(
            f"/spaces/{space_id}/ai/chat",
            json={"message": "What is in this space?"},
            headers=self.auth_headers_b
        )
        self.assertEqual(rag_b.status_code, 403)

        # User B cannot generate AI content in User A's space -> 403
        gen_b = self.client.post(
            f"/spaces/{space_id}/ai/generate",
            json={"prompt": "Draft an itinerary", "type": "itinerary"},
            headers=self.auth_headers_b
        )
        self.assertEqual(gen_b.status_code, 403)

        # User A creates a conversation
        conv_a = self.client.post(
            f"/spaces/{space_id}/conversations",
            json={"title": "Private Space Chat"},
            headers=self.auth_headers_a
        ).json()
        conv_id = conv_a["id"]

        # User B cannot chat in User A's conversation -> 403
        conv_chat_b = self.client.post(
            f"/conversations/{conv_id}/chat",
            json={"message": "Can I read your secrets?"},
            headers=self.auth_headers_b
        )
        self.assertEqual(conv_chat_b.status_code, 403)

    def test_production_mode_restrictions(self):
        """Test that /db-init and missing JWT tokens are blocked in production."""
        with patch("brain.src.config.ENVIRONMENT", "production"):
            # 1. /db-init must return 403 Forbidden in production
            resp_init = self.client.post("/db-init")
            self.assertEqual(resp_init.status_code, 403)
            self.assertIn("disabled in production", resp_init.json()["message"])

            # 2. Protected routes require JWT (reject unauthenticated dev user fallback)
            resp_no_token = self.client.get("/spaces")
            self.assertEqual(resp_no_token.status_code, 401)
            self.assertIn("Authorization header is missing", resp_no_token.json()["detail"])

            # 3. Supplying X-Dev-User-Id header without token must be rejected in production
            resp_dev_header = self.client.get("/spaces", headers={"X-Dev-User-Id": "000000000000000000000001"})
            self.assertEqual(resp_dev_header.status_code, 401)


if __name__ == "__main__":
    unittest.main()

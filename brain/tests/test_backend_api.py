"""
Comprehensive backend API test suite for DreamWeave.
Verifies all REST API endpoints using FastAPI TestClient with mongomock isolation.
"""

import os
import sys
import unittest
from unittest.mock import patch
import mongomock

# Add python paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create a shared mock database for isolated fast testing
mock_client = mongomock.MongoClient()
mock_db = mock_client["dreamweave"]

# Patch connection client before importing database or api modules
import brain.src.database.connection as conn
conn._client = mock_client
conn.get_database = lambda: mock_db
conn.ping_database = lambda: {"status": "ok", "database": "dreamweave"}

import brain.src.database.collections as colls
colls.get_database = lambda: mock_db

from brain.src.api.app import app
from fastapi.testclient import TestClient
client = TestClient(app)


class TestBackendAPI(unittest.TestCase):

    def setUp(self):
        # Clean mock database collections between tests
        for c in mock_db.list_collection_names():
            mock_db[c].delete_many({})

    def test_01_health_endpoints(self):
        """Verify /health, /db-health, and /db-init endpoints."""
        res = client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"status": "ok"})

        db_res = client.get("/db-health")
        self.assertEqual(db_res.status_code, 200)

        with patch("brain.src.database.connection.init_database", return_value={"status": "ok", "database": "dreamweave", "indexes": {}}):
            init_res = client.post("/db-init")
            self.assertEqual(init_res.status_code, 200)

    def test_02_spaces_crud(self):
        """Verify Spaces CRUD endpoints."""
        # 1. Create Space
        create_res = client.post("/spaces", json={
            "name": "Japan Travel 2026",
            "description": "Planning Tokyo & Kyoto trip",
            "status": "active"
        })
        self.assertEqual(create_res.status_code, 201)
        space = create_res.json()
        space_id = space["id"]
        self.assertEqual(space["name"], "Japan Travel 2026")

        # 2. Get Space
        get_res = client.get(f"/spaces/{space_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["name"], "Japan Travel 2026")

        # 3. List Spaces
        list_res = client.get("/spaces")
        self.assertEqual(list_res.status_code, 200)
        self.assertTrue(any(s["id"] == space_id for s in list_res.json()))

        # 4. Update Space
        update_res = client.patch(f"/spaces/{space_id}", json={
            "name": "Japan Travel 2026 (Updated)",
            "is_favourite": True
        })
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json()["name"], "Japan Travel 2026 (Updated)")

        # 5. Delete Space
        del_res = client.delete(f"/spaces/{space_id}")
        self.assertEqual(del_res.status_code, 200)

        # Verify 404 after deletion
        get_after_del = client.get(f"/spaces/{space_id}")
        self.assertEqual(get_after_del.status_code, 404)

    def test_03_content_items_crud(self):
        """Verify Content Items CRUD endpoints."""
        sp = client.post("/spaces", json={"name": "Research Space"}).json()
        space_id = sp["id"]

        # 1. Create Content Item
        create_res = client.post("/content", json={
            "space_id": space_id,
            "type": "pdf",
            "title": "Tokyo Ramen Guide.pdf",
            "description": "List of top ramen places in Shinjuku",
            "tags": ["travel", "food"]
        })
        self.assertEqual(create_res.status_code, 201)
        content = create_res.json()
        content_id = content["id"]
        self.assertEqual(content["type"], "pdf")

        # 2. Get Content Item
        get_res = client.get(f"/content/{content_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["title"], "Tokyo Ramen Guide.pdf")

        # 3. List Content Items
        list_res = client.get(f"/content?space_id={space_id}")
        self.assertEqual(list_res.status_code, 200)
        self.assertTrue(any(c["id"] == content_id for c in list_res.json()))

        # 4. Update Content Item
        patch_res = client.patch(f"/content/{content_id}", json={
            "title": "Tokyo Ramen Guide v2.pdf",
            "is_favourite": True
        })
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["title"], "Tokyo Ramen Guide v2.pdf")

        # 5. Delete Content Item
        del_res = client.delete(f"/content/{content_id}")
        self.assertEqual(del_res.status_code, 200)

    def test_04_ai_content_crud(self):
        """Verify AI Content CRUD endpoints."""
        sp = client.post("/spaces", json={"name": "AI Space"}).json()
        space_id = sp["id"]

        # 1. Create AI Content
        create_res = client.post("/ai-content", json={
            "space_id": space_id,
            "type": "itinerary",
            "title": "Generated 3-Day Tokyo Itinerary",
            "content": {"day1": "Shinjuku", "day2": "Shibuya", "day3": "Akihabara"}
        })
        self.assertEqual(create_res.status_code, 201)
        aic = create_res.json()
        aic_id = aic["id"]
        self.assertEqual(aic["title"], "Generated 3-Day Tokyo Itinerary")

        # 2. Get AI Content
        get_res = client.get(f"/ai-content/{aic_id}")
        self.assertEqual(get_res.status_code, 200)

        # 3. List AI Content
        list_res = client.get(f"/ai-content?space_id={space_id}")
        self.assertEqual(list_res.status_code, 200)

        # 4. Delete AI Content
        del_res = client.delete(f"/ai-content/{aic_id}")
        self.assertEqual(del_res.status_code, 200)

    def test_05_vision_boards_crud(self):
        """Verify Vision Boards and Items endpoints."""
        sp = client.post("/spaces", json={"name": "Design Space"}).json()
        space_id = sp["id"]

        # 1. Create Board
        b_res = client.post(f"/spaces/{space_id}/vision-boards", json={
            "name": "Mood Board 2026",
            "width": 1920,
            "height": 1080
        })
        self.assertEqual(b_res.status_code, 201)
        board_id = b_res.json()["id"]

        # 2. List Boards
        lb_res = client.get(f"/spaces/{space_id}/vision-boards")
        self.assertEqual(lb_res.status_code, 200)

        # 3. Add Item to Board
        item_res = client.post(f"/vision-boards/{board_id}/items", json={
            "x": 100.5,
            "y": 200.0,
            "width": 400.0,
            "height": 300.0,
            "rotation": 15.0
        })
        self.assertEqual(item_res.status_code, 201)
        item_id = item_res.json()["id"]

        # 4. List Items
        li_res = client.get(f"/vision-boards/{board_id}/items")
        self.assertEqual(li_res.status_code, 200)
        self.assertEqual(len(li_res.json()), 1)

        # 5. Update Item
        ui_res = client.patch(f"/vision-board-items/{item_id}", json={
            "x": 150.0,
            "rotation": 0.0
        })
        self.assertEqual(ui_res.status_code, 200)
        self.assertEqual(ui_res.json()["position"]["x"], 150.0)

        # 6. Delete Item & Board
        client.delete(f"/vision-board-items/{item_id}")
        client.delete(f"/vision-boards/{board_id}")

    def test_06_plans_and_tasks_crud(self):
        """Verify Plans and Tasks endpoints."""
        sp = client.post("/spaces", json={"name": "Goal Space"}).json()
        space_id = sp["id"]

        # 1. Create Plan
        p_res = client.post(f"/spaces/{space_id}/plans", json={
            "title": "Master Python & AI",
            "description": "Learning roadmap",
            "status": "active"
        })
        self.assertEqual(p_res.status_code, 201)
        plan_id = p_res.json()["id"]

        # 2. Create Task inside Plan
        t_res = client.post(f"/plans/{plan_id}/tasks", json={
            "space_id": space_id,
            "title": "Read PyMongo docs",
            "priority": "high",
            "status": "todo"
        })
        self.assertEqual(t_res.status_code, 201)
        task_id = t_res.json()["id"]

        # 3. List Tasks
        lt_res = client.get(f"/plans/{plan_id}/tasks")
        self.assertEqual(lt_res.status_code, 200)
        self.assertEqual(len(lt_res.json()), 1)

        # 4. Update Task
        ut_res = client.patch(f"/tasks/{task_id}", json={"status": "completed"})
        self.assertEqual(ut_res.status_code, 200)
        self.assertEqual(ut_res.json()["status"], "completed")

        client.delete(f"/tasks/{task_id}")
        client.delete(f"/plans/{plan_id}")

    def test_07_conversations_and_messages(self):
        """Verify Conversations and Messages endpoints."""
        sp = client.post("/spaces", json={"name": "Chat Space"}).json()
        space_id = sp["id"]

        # 1. Create Conversation
        c_res = client.post(f"/spaces/{space_id}/conversations", json={
            "title": "Trip Ideas Discussion"
        })
        self.assertEqual(c_res.status_code, 201)
        conv_id = c_res.json()["id"]

        # 2. Add User Message
        m_res = client.post(f"/conversations/{conv_id}/messages", json={
            "role": "user",
            "content": "Where should we stay in Tokyo?"
        })
        self.assertEqual(m_res.status_code, 201)

        # 3. List Messages
        lm_res = client.get(f"/conversations/{conv_id}/messages")
        self.assertEqual(lm_res.status_code, 200)
        self.assertEqual(len(lm_res.json()), 1)
        self.assertEqual(lm_res.json()[0]["content"], "Where should we stay in Tokyo?")

    def test_08_invalid_objectid_handling(self):
        """Verify 400 Bad Request on invalid ObjectId format."""
        res = client.get("/spaces/invalid-id-string")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid space_id format", res.json()["detail"])


if __name__ == "__main__":
    unittest.main()

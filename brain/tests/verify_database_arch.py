"""
Verification test suite for DreamWeave Final Database Architecture.
Verifies collection definitions, schema builders, index definitions, repository operations,
and compatibility with existing OCR, PDF, and RAG/vector pipelines.
"""

import os
import sys
import unittest
from datetime import datetime, timezone
from bson import ObjectId

# Ensure workspace root and brain directory are in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.src.database.collections import (
    ALL_COLLECTIONS,
    COLLECTION_USERS,
    COLLECTION_SPACES,
    COLLECTION_SPACE_MEMBERS,
    COLLECTION_CONTENT_ITEMS,
    COLLECTION_ASSETS,
    COLLECTION_KNOWLEDGE,
    COLLECTION_CHUNKS,
    COLLECTION_AI_CONTENT,
    COLLECTION_AI_GENERATIONS,
    COLLECTION_VISION_BOARDS,
    COLLECTION_VISION_BOARD_ITEMS,
    COLLECTION_PLANS,
    COLLECTION_TASKS,
    COLLECTION_CONVERSATIONS,
    COLLECTION_MESSAGES,
    COLLECTION_ACTIVITY,
)
from brain.src.database.indexes import INDEX_SPECS
from brain.src.database.models import (
    build_user_doc,
    build_space_doc,
    build_space_member_doc,
    build_content_item_doc,
    build_asset_doc,
    build_knowledge_doc,
    build_chunk_doc,
    build_ai_content_doc,
    build_ai_generation_doc,
    build_vision_board_doc,
    build_vision_board_item_doc,
    build_plan_doc,
    build_task_doc,
    build_conversation_doc,
    build_message_doc,
    build_activity_doc,
    to_object_id
)
from brain.src.document_store import get_all_documents
from brain.src.vector_store import load_vector_store
from brain.src.retrieval.retriever import retrieve_relevant_chunks
from brain.src.rag.rag_engine import answer_rag_query


class TestDatabaseArchitecture(unittest.TestCase):

    def test_16_collections_exist(self):
        """Verify all 16 conceptual collections are present in ALL_COLLECTIONS list."""
        expected_collections = {
            "users", "spaces", "space_members", "content_items",
            "assets", "knowledge", "chunks", "ai_content",
            "ai_generations", "vision_boards", "vision_board_items",
            "plans", "tasks", "conversations", "messages", "activity"
        }
        self.assertEqual(len(ALL_COLLECTIONS), 16)
        self.assertEqual(set(ALL_COLLECTIONS), expected_collections)

    def test_index_specifications(self):
        """Verify all 16 collections have required index specifications configured."""
        self.assertEqual(len(INDEX_SPECS), 16)

        # Verify users email unique index
        users_specs = INDEX_SPECS[COLLECTION_USERS]
        self.assertTrue(any(spec.get("unique") is True and ("email", 1) in spec["keys"] for spec in users_specs))

        # Verify content_items indexes
        content_specs = INDEX_SPECS[COLLECTION_CONTENT_ITEMS]
        keys_set = [spec["keys"] for spec in content_specs]
        self.assertIn([("space_id", 1)], keys_set)
        self.assertIn([("user_id", 1)], keys_set)
        self.assertIn([("type", 1)], keys_set)

        # Verify ai_generations index (user_id + type + created_at)
        ai_gen_specs = INDEX_SPECS[COLLECTION_AI_GENERATIONS]
        ai_gen_keys = [spec["keys"] for spec in ai_gen_specs]
        self.assertIn([("user_id", 1), ("type", 1), ("created_at", -1)], ai_gen_keys)

    def test_model_schemas(self):
        """Test document builder models for all 16 collections."""
        user_id = str(ObjectId())
        space_id = str(ObjectId())
        content_id = str(ObjectId())
        asset_id = str(ObjectId())
        knowledge_id = str(ObjectId())
        board_id = str(ObjectId())
        plan_id = str(ObjectId())
        conv_id = str(ObjectId())

        # 1. users
        u_doc = build_user_doc(email="test@dreamweave.io", name="Alex Dreamer")
        self.assertEqual(u_doc["email"], "test@dreamweave.io")
        self.assertIsInstance(u_doc["created_at"], datetime)

        # 2. spaces
        s_doc = build_space_doc(owner_id=user_id, name="Japan Trip")
        self.assertEqual(s_doc["name"], "Japan Trip")
        self.assertIsInstance(s_doc["owner_id"], ObjectId)

        # 3. space_members
        sm_doc = build_space_member_doc(space_id=space_id, user_id=user_id, role="owner")
        self.assertEqual(sm_doc["role"], "owner")
        self.assertIsInstance(sm_doc["space_id"], ObjectId)

        # 4. content_items
        c_doc = build_content_item_doc(space_id=space_id, user_id=user_id, type="pdf", title="Tokyo Guide")
        self.assertEqual(c_doc["type"], "pdf")
        self.assertEqual(c_doc["title"], "Tokyo Guide")

        # 5. assets
        a_doc = build_asset_doc(user_id=user_id, space_id=space_id, filename="guide.pdf", mime_type="application/pdf", size=1024)
        self.assertEqual(a_doc["filename"], "guide.pdf")

        # 6. knowledge
        k_doc = build_knowledge_doc(space_id=space_id, content_id=content_id, source_type="pdf", raw_text="Sample raw text")
        self.assertEqual(k_doc["raw_text"], "Sample raw text")

        # 7. chunks
        chk_doc = build_chunk_doc(space_id=space_id, knowledge_id=knowledge_id, content_id=content_id, chunk_index=0, text="Chunk sample text", embedding=[0.1, 0.2])
        self.assertEqual(chk_doc["chunk_index"], 0)
        self.assertEqual(chk_doc["embedding"], [0.1, 0.2])

        # 8. ai_content
        aic_doc = build_ai_content_doc(space_id=space_id, user_id=user_id, type="itinerary", content="Day 1 in Tokyo", title="Tokyo Plan")
        self.assertEqual(aic_doc["type"], "itinerary")

        # 9. ai_generations
        aig_doc = build_ai_generation_doc(user_id=user_id, type="visual", prompt="Futuristic Tokyo cityscape")
        self.assertEqual(aig_doc["type"], "visual")

        # 10. vision_boards
        vb_doc = build_vision_board_doc(space_id=space_id, name="Trip Vision Board")
        self.assertEqual(vb_doc["name"], "Trip Vision Board")

        # 11. vision_board_items
        vbi_doc = build_vision_board_item_doc(vision_board_id=board_id, content_id=content_id, x=100.0, y=150.0)
        self.assertEqual(vbi_doc["position"]["x"], 100.0)

        # 12. plans
        p_doc = build_plan_doc(space_id=space_id, user_id=user_id, title="7-Day Itinerary")
        self.assertEqual(p_doc["title"], "7-Day Itinerary")

        # 13. tasks
        t_doc = build_task_doc(plan_id=plan_id, space_id=space_id, title="Book Flights")
        self.assertEqual(t_doc["title"], "Book Flights")

        # 14. conversations
        conv_doc = build_conversation_doc(space_id=space_id, user_id=user_id, title="Travel Chat")
        self.assertEqual(conv_doc["title"], "Travel Chat")

        # 15. messages
        m_doc = build_message_doc(conversation_id=conv_id, role="user", content="What are top spots in Shinjuku?")
        self.assertEqual(m_doc["role"], "user")

        # 16. activity
        act_doc = build_activity_doc(space_id=space_id, user_id=user_id, action="content_added", target_type="content_item", target_id=content_id)
        self.assertEqual(act_doc["action"], "content_added")

    def test_legacy_rag_compatibility(self):
        """Verify existing RAG/vector and knowledge.json code remains functional."""
        docs = get_all_documents()
        self.assertIsInstance(docs, list)

        vector_data = load_vector_store()
        self.assertIn("chunks", vector_data)

        # Test retriever safely
        chunks = retrieve_relevant_chunks("test query", top_k=1)
        self.assertIsInstance(chunks, list)

        # Test RAG engine answer generator safely
        res = answer_rag_query("test query", top_k=1)
        self.assertIn("query", res)
        self.assertIn("answer", res)


if __name__ == "__main__":
    unittest.main()

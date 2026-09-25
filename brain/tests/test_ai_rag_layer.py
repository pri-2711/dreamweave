"""
Comprehensive test suite for AI + Knowledge / RAG Layer.
Tests embedding generation, dimension, text chunking, knowledge ingestion pipeline,
Space-scoped vector search retrieval, Gemini service abstraction, and /spaces/{space_id}/ai/chat endpoint.
"""

import os
import sys
import unittest
from unittest.mock import patch
import mongomock

# Add python paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create a shared mock database for isolated test execution
mock_client = mongomock.MongoClient()
mock_db = mock_client["dreamweave"]

import brain.src.database.connection as conn
conn._client = mock_client
conn.get_database = lambda: mock_db
conn.ping_database = lambda: {"status": "ok", "database": "dreamweave"}

import brain.src.database.collections as colls
colls.get_database = lambda: mock_db

from brain.src.config import EMBEDDING_DIMENSION
from brain.src.embeddings.service import embed_text, embed_documents
from brain.src.chunking.service import chunk_knowledge_text
from brain.src.services.ingestion_service import ingest_content_item
from brain.src.rag.retriever import retrieve_space_chunks
from brain.src.rag.service import answer_space_query
from brain.src.utils.serialization import parse_object_id
from brain.src.api.app import app
from fastapi.testclient import TestClient

client = TestClient(app)


class TestAIRAGLayer(unittest.TestCase):

    def setUp(self):
        for c in mock_db.list_collection_names():
            mock_db[c].delete_many({})

    def test_01_embedding_generation_and_dimension(self):
        """Verify vector embedding generation and 384 dimensions."""
        vec = embed_text("Tokyo sushi and ramen recommendations")
        self.assertEqual(len(vec), EMBEDDING_DIMENSION)
        self.assertEqual(len(vec), 384)

        docs = ["Sample paragraph 1", "Sample paragraph 2"]
        doc_vecs = embed_documents(docs)
        self.assertEqual(len(doc_vecs), 2)
        self.assertEqual(len(doc_vecs[0]), 384)

    def test_02_text_chunking(self):
        """Verify text chunking respects chunk_size and returns structured metadata."""
        sample_text = ("Section 1: Tokyo Travel Guide\n\n" + "Paragraph content. " * 30 + "\n\n" +
                       "Section 2: Kyoto Temples\n\n" + "Temple details. " * 30)
        chunks = chunk_knowledge_text(sample_text, chunk_size=200, overlap=30)
        self.assertTrue(len(chunks) > 1)
        for idx, c in enumerate(chunks):
            self.assertEqual(c["chunk_index"], idx)
            self.assertIn("text", c)
            self.assertIn("length", c)

    def test_03_knowledge_ingestion_pipeline(self):
        """Verify Content -> Knowledge -> Chunks -> Embeddings -> MongoDB ingestion pipeline."""
        sp = client.post("/spaces", json={"name": "Japan Space"}).json()
        space_id = sp["id"]

        cnt = client.post("/content", json={
            "space_id": space_id,
            "type": "note",
            "title": "Tokyo Food Notes",
            "description": "Must try Ichiran ramen in Shinjuku and Tsukiji fish market sushi."
        }).json()
        content_id = cnt["id"]

        # Run ingestion
        ingest_res = client.post(f"/content/{content_id}/ingest")
        self.assertEqual(ingest_res.status_code, 200)
        data = ingest_res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["content_id"], content_id)
        self.assertTrue(data["chunks_count"] >= 1)

        # Verify chunks stored in MongoDB
        chunks_in_db = list(mock_db["chunks"].find({"content_id": parse_object_id(content_id)}))
        self.assertEqual(len(chunks_in_db), data["chunks_count"])
        self.assertEqual(len(chunks_in_db[0]["embedding"]), 384)

    def test_04_space_isolation_vector_retrieval(self):
        """Verify Vector Search strictly enforces Space isolation."""
        sp1 = client.post("/spaces", json={"name": "Space A (Japan)"}).json()["id"]
        sp2 = client.post("/spaces", json={"name": "Space B (Python)"}).json()["id"]

        # Content in Space A
        cnt1 = client.post("/content", json={
            "space_id": sp1,
            "type": "note",
            "title": "Shinjuku Hotel",
            "description": "Booking at Park Hyatt Tokyo Hotel in Shinjuku"
        }).json()["id"]
        client.post(f"/content/{cnt1}/ingest")

        # Content in Space B
        cnt2 = client.post("/content", json={
            "space_id": sp2,
            "type": "note",
            "title": "PyMongo Querying",
            "description": "PyMongo collection aggregate vector search filter"
        }).json()["id"]
        client.post(f"/content/{cnt2}/ingest")

        # Search query for "Tokyo Hotel" in Space B (should return 0 chunks due to Space isolation)
        query_vec = embed_text("Tokyo Hotel")
        retrieved_sp2 = retrieve_space_chunks(space_id=sp2, query_embedding=query_vec, top_k=5)
        for chunk in retrieved_sp2:
            self.assertEqual(chunk["space_id"], sp2)
            self.assertNotIn("Shinjuku Hotel", chunk["text"])

        # Search query in Space A (should retrieve Space A chunk)
        retrieved_sp1 = retrieve_space_chunks(space_id=sp1, query_embedding=query_vec, top_k=5)
        self.assertEqual(len(retrieved_sp1), 1)
        self.assertIn("Park Hyatt Tokyo Hotel", retrieved_sp1[0]["text"])

    def test_05_mocked_gemini_rag_service(self):
        """Verify RAG service with mocked Gemini AI response."""
        sp = client.post("/spaces", json={"name": "Travel Space"}).json()["id"]
        cnt = client.post("/content", json={
            "space_id": sp,
            "type": "note",
            "title": "Flight details",
            "description": "Flight NH204 arrives at Narita Airport at 3 PM."
        }).json()["id"]
        client.post(f"/content/{cnt}/ingest")

        mock_ai_response = "Based on your saved flight details, your flight NH204 arrives at Narita Airport at 3 PM."
        with patch("brain.src.rag.service.generate_gemini_response", return_value=mock_ai_response):
            res = answer_space_query(space_id=sp, question="What time does my flight arrive?")
            self.assertEqual(res["message"], mock_ai_response)
            self.assertEqual(len(res["sources"]), 1)
            self.assertEqual(res["sources"][0]["content_id"], cnt)

    def test_06_space_ai_chat_endpoint(self):
        """Verify POST /spaces/{space_id}/ai/chat endpoint."""
        sp = client.post("/spaces", json={"name": "Itinerary Space"}).json()["id"]
        cnt = client.post("/content", json={
            "space_id": sp,
            "type": "note",
            "title": "Kyoto Places",
            "description": "Fushimi Inari Shrine and Arashiyama Bamboo Grove."
        }).json()["id"]
        client.post(f"/content/{cnt}/ingest")

        mock_reply = "Here are top spots in Kyoto: Fushimi Inari Shrine and Arashiyama Bamboo Grove."
        with patch("brain.src.rag.service.generate_gemini_response", return_value=mock_reply):
            chat_res = client.post(f"/spaces/{sp}/ai/chat", json={
                "message": "What should I visit in Kyoto?"
            })
            self.assertEqual(chat_res.status_code, 200)
            data = chat_res.json()
            self.assertEqual(data["message"], mock_reply)
            self.assertEqual(len(data["sources"]), 1)

    def test_07_empty_knowledge_behaviour(self):
        """Verify graceful handling when asking a question in a Space with no knowledge."""
        sp = client.post("/spaces", json={"name": "Empty Space"}).json()["id"]
        mock_fallback = "I don't see any saved items in this Space regarding your request, but generally Tokyo is famous for ramen."
        with patch("brain.src.rag.service.generate_gemini_response", return_value=mock_fallback):
            chat_res = client.post(f"/spaces/{sp}/ai/chat", json={
                "message": "Recommend ramen spots"
            })
            self.assertEqual(chat_res.status_code, 200)
            data = chat_res.json()
            self.assertEqual(data["message"], mock_fallback)
            self.assertEqual(len(data["sources"]), 0)


if __name__ == "__main__":
    unittest.main()

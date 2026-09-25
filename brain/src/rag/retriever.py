"""
MongoDB Atlas Vector Search Retriever for DreamWeave RAG.
Enforces Space isolation filtering and retrieves top-k relevant text chunks.
"""

import logging
import numpy as np
from typing import List, Dict, Any
from bson import ObjectId
from brain.src import config
from brain.src.database.collections import COLLECTION_CHUNKS, get_collection
from brain.src.utils.serialization import parse_object_id

logger = logging.getLogger("dreamweave.rag.retriever")


def compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    a = np.array(vec1, dtype=float)
    b = np.array(vec2, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def retrieve_space_chunks(
    space_id: str,
    query_embedding: List[float],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve top_k relevant document chunks for a given space_id.
    Strictly enforces Space isolation so questions in Space A never retrieve chunks from Space B.
    """
    sid = parse_object_id(space_id, param_name="space_id")
    coll = get_collection(COLLECTION_CHUNKS)

    retrieved_chunks: List[Dict[str, Any]] = []

    # Attempt Atlas Vector Search pipeline stage first
    try:
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": max(top_k * 10, 20),
                    "limit": top_k,
                    "filter": {"space_id": sid}
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "space_id": 1,
                    "knowledge_id": 1,
                    "content_id": 1,
                    "chunk_index": 1,
                    "text": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        results = list(coll.aggregate(pipeline))
        if results:
            for item in results:
                retrieved_chunks.append({
                    "chunk_id": str(item["_id"]),
                    "space_id": str(item.get("space_id")),
                    "knowledge_id": str(item.get("knowledge_id")),
                    "content_id": str(item.get("content_id")),
                    "chunk_index": item.get("chunk_index"),
                    "text": item.get("text", ""),
                    "score": float(item.get("score", 0.0))
                })
            return retrieved_chunks
    except Exception as e:
        logger.debug(f"Atlas $vectorSearch pipeline stage notice ({e}). Falling back to PyMongo Space-scoped vector scan...")

    # Fallback: In-memory cosine similarity search over chunks filtered by space_id
    space_chunks = list(coll.find({"space_id": sid}))
    if not space_chunks:
        return []

    scored = []
    for c in space_chunks:
        chunk_emb = c.get("embedding", [])
        if chunk_emb:
            score = compute_cosine_similarity(query_embedding, chunk_emb)
        else:
            score = 0.0

        scored.append({
            "chunk_id": str(c["_id"]),
            "space_id": str(c.get("space_id")),
            "knowledge_id": str(c.get("knowledge_id")),
            "content_id": str(c.get("content_id")),
            "chunk_index": c.get("chunk_index"),
            "text": c.get("text", ""),
            "score": score
        })

    # Sort descending by score
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]

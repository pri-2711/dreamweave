"""
Repository for `chunks` collection.
Stores document text chunks and vector embeddings for RAG and vector search.
"""

from typing import Dict, Any, List, Optional, Union
from bson import ObjectId
from brain.src.database.collections import COLLECTION_CHUNKS, get_collection
from brain.src.database.models import build_chunk_doc, to_object_id


def create_chunk(
    space_id: Union[str, ObjectId],
    knowledge_id: Union[str, ObjectId],
    content_id: Union[str, ObjectId],
    chunk_index: int,
    text: str,
    embedding: Optional[List[float]] = None,
    page: Optional[int] = None,
    legacy_chunk_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create and insert a chunk document."""
    coll = get_collection(COLLECTION_CHUNKS)
    doc = build_chunk_doc(
        space_id=space_id,
        knowledge_id=knowledge_id,
        content_id=content_id,
        chunk_index=chunk_index,
        text=text,
        embedding=embedding,
        page=page,
        legacy_chunk_id=legacy_chunk_id
    )
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_chunk_by_id(chunk_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
    """Find a chunk document by _id."""
    oid = to_object_id(chunk_id)
    if not oid:
        return None
    coll = get_collection(COLLECTION_CHUNKS)
    return coll.find_one({"_id": oid})


def list_chunks_by_knowledge_id(knowledge_id: Union[str, ObjectId]) -> List[Dict[str, Any]]:
    """List chunks belonging to a specific knowledge_id sorted by chunk_index."""
    kid = to_object_id(knowledge_id)
    if not kid:
        return []
    coll = get_collection(COLLECTION_CHUNKS)
    return list(coll.find({"knowledge_id": kid}).sort("chunk_index", 1))


def list_chunks_by_space_id(space_id: Union[str, ObjectId]) -> List[Dict[str, Any]]:
    """List chunks belonging to a space."""
    sid = to_object_id(space_id)
    if not sid:
        return []
    coll = get_collection(COLLECTION_CHUNKS)
    return list(coll.find({"space_id": sid}).sort("created_at", -1))

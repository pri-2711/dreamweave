"""
Repository for `knowledge` collection.
Stores machine-readable information extracted/cleaned from Content items.
"""

from typing import Dict, Any, List, Optional, Union
from bson import ObjectId
from brain.src.database.collections import COLLECTION_KNOWLEDGE, get_collection
from brain.src.database.models import build_knowledge_doc, to_object_id, now_utc


def create_knowledge(
    space_id: Union[str, ObjectId],
    content_id: Union[str, ObjectId],
    source_type: str,
    raw_text: str,
    clean_text: str = "",
    ocr_used: bool = False,
    page_count: Optional[int] = None,
    language: Optional[str] = None,
    ocr_engine: Optional[str] = None,
    legacy_id: Optional[Any] = None
) -> Dict[str, Any]:
    """Create and insert a knowledge document."""
    coll = get_collection(COLLECTION_KNOWLEDGE)
    doc = build_knowledge_doc(
        space_id=space_id,
        content_id=content_id,
        source_type=source_type,
        raw_text=raw_text,
        clean_text=clean_text,
        ocr_used=ocr_used,
        page_count=page_count,
        language=language,
        ocr_engine=ocr_engine,
        legacy_id=legacy_id
    )
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_knowledge_by_id(knowledge_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
    """Find a knowledge document by _id."""
    oid = to_object_id(knowledge_id)
    if not oid:
        return None
    coll = get_collection(COLLECTION_KNOWLEDGE)
    return coll.find_one({"_id": oid})


def get_knowledge_by_content_id(content_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
    """Find knowledge extracted from a specific content_id."""
    cid = to_object_id(content_id)
    if not cid:
        return None
    coll = get_collection(COLLECTION_KNOWLEDGE)
    return coll.find_one({"content_id": cid})


def list_knowledge_by_space(space_id: Union[str, ObjectId]) -> List[Dict[str, Any]]:
    """List all knowledge entries in a space."""
    sid = to_object_id(space_id)
    if not sid:
        return []
    coll = get_collection(COLLECTION_KNOWLEDGE)
    return list(coll.find({"space_id": sid}).sort("created_at", -1))


def update_knowledge(knowledge_id: Union[str, ObjectId], updates: Dict[str, Any]) -> bool:
    """Update fields of an existing knowledge entry."""
    oid = to_object_id(knowledge_id)
    if not oid:
        return False
    updates["updated_at"] = now_utc()
    coll = get_collection(COLLECTION_KNOWLEDGE)
    result = coll.update_one({"_id": oid}, {"$set": updates})
    return result.modified_count > 0

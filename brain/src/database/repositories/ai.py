"""
Repository for `ai_content` and `ai_generations` collections.
- `ai_content`: Persistent AI outputs (suggestions, itineraries, visual concepts, etc.)
- `ai_generations`: Usage and event logs (e.g. daily limit tracking)
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from bson import ObjectId
from brain.src.database.collections import (
    COLLECTION_AI_CONTENT,
    COLLECTION_AI_GENERATIONS,
    get_collection
)
from brain.src.database.models import (
    build_ai_content_doc,
    build_ai_generation_doc,
    to_object_id,
    now_utc
)


def create_ai_content(
    space_id: Union[str, ObjectId],
    user_id: Union[str, ObjectId],
    type: str,
    content: Union[str, dict, list],
    title: Optional[str] = None,
    source_content_ids: Optional[List[Union[str, ObjectId]]] = None,
    source_knowledge_ids: Optional[List[Union[str, ObjectId]]] = None,
    asset_id: Optional[Union[str, ObjectId]] = None,
    is_favourite: bool = False,
    is_archived: bool = False
) -> Dict[str, Any]:
    """Create and insert persistent AI content."""
    coll = get_collection(COLLECTION_AI_CONTENT)
    doc = build_ai_content_doc(
        space_id=space_id,
        user_id=user_id,
        type=type,
        content=content,
        title=title,
        source_content_ids=source_content_ids,
        source_knowledge_ids=source_knowledge_ids,
        asset_id=asset_id,
        is_favourite=is_favourite,
        is_archived=is_archived
    )
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_ai_content_by_id(ai_content_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
    """Find AI content by _id."""
    oid = to_object_id(ai_content_id)
    if not oid:
        return None
    coll = get_collection(COLLECTION_AI_CONTENT)
    return coll.find_one({"_id": oid})


def list_ai_content_by_space(
    space_id: Union[str, ObjectId],
    content_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List persistent AI content in a space."""
    sid = to_object_id(space_id)
    if not sid:
        return []
    query: Dict[str, Any] = {"space_id": sid}
    if content_type:
        query["type"] = content_type
    coll = get_collection(COLLECTION_AI_CONTENT)
    return list(coll.find(query).sort("created_at", -1))


def create_ai_generation(
    user_id: Union[str, ObjectId],
    type: str,
    space_id: Optional[Union[str, ObjectId]] = None,
    model: Optional[str] = None,
    prompt: Optional[str] = None,
    input_content_ids: Optional[List[Union[str, ObjectId]]] = None,
    result_content_id: Optional[Union[str, ObjectId]] = None,
    credits: int = 1
) -> Dict[str, Any]:
    """Record an AI generation usage event."""
    coll = get_collection(COLLECTION_AI_GENERATIONS)
    doc = build_ai_generation_doc(
        user_id=user_id,
        type=type,
        space_id=space_id,
        model=model,
        prompt=prompt,
        input_content_ids=input_content_ids,
        result_content_id=result_content_id,
        credits=credits
    )
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def list_ai_generations_by_user(
    user_id: Union[str, ObjectId],
    gen_type: Optional[str] = None,
    since: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """List AI generation events for a user, optionally filtered by type and date/time."""
    uid = to_object_id(user_id)
    if not uid:
        return []
    query: Dict[str, Any] = {"user_id": uid}
    if gen_type:
        query["type"] = gen_type
    if since:
        query["created_at"] = {"$gte": since}
    coll = get_collection(COLLECTION_AI_GENERATIONS)
    return list(coll.find(query).sort("created_at", -1))

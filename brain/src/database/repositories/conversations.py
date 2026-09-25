"""
Repository for `conversations` and `messages` collections.
"""

from typing import Dict, Any, List, Optional, Union
from bson import ObjectId
from brain.src.database.collections import (
    COLLECTION_CONVERSATIONS,
    COLLECTION_MESSAGES,
    get_collection
)
from brain.src.database.models import (
    build_conversation_doc,
    build_message_doc,
    to_object_id,
    now_utc
)


def create_conversation(
    space_id: Union[str, ObjectId],
    user_id: Union[str, ObjectId],
    title: str
) -> Dict[str, Any]:
    """Create and insert a new Space AI conversation."""
    coll = get_collection(COLLECTION_CONVERSATIONS)
    doc = build_conversation_doc(space_id=space_id, user_id=user_id, title=title)
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_conversation_by_id(conversation_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
    """Find a conversation by _id."""
    oid = to_object_id(conversation_id)
    if not oid:
        return None
    coll = get_collection(COLLECTION_CONVERSATIONS)
    return coll.find_one({"_id": oid})


def list_conversations_by_space(space_id: Union[str, ObjectId]) -> List[Dict[str, Any]]:
    """List conversations in a space."""
    sid = to_object_id(space_id)
    if not sid:
        return []
    coll = get_collection(COLLECTION_CONVERSATIONS)
    return list(coll.find({"space_id": sid}).sort("updated_at", -1))


def add_message(
    conversation_id: Union[str, ObjectId],
    role: str,
    content: str,
    content_ids: Optional[List[Union[str, ObjectId]]] = None,
    knowledge_ids: Optional[List[Union[str, ObjectId]]] = None,
    generated_content_ids: Optional[List[Union[str, ObjectId]]] = None
) -> Dict[str, Any]:
    """Add a message to a conversation and update conversation updated_at."""
    cid = to_object_id(conversation_id)
    coll = get_collection(COLLECTION_MESSAGES)
    doc = build_message_doc(
        conversation_id=cid,
        role=role,
        content=content,
        content_ids=content_ids,
        knowledge_ids=knowledge_ids,
        generated_content_ids=generated_content_ids
    )
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id

    # Update conversation's updated_at timestamp
    if cid:
        get_collection(COLLECTION_CONVERSATIONS).update_one(
            {"_id": cid},
            {"$set": {"updated_at": now_utc()}}
        )

    return doc


def list_messages_by_conversation(conversation_id: Union[str, ObjectId]) -> List[Dict[str, Any]]:
    """List all messages in a conversation sorted chronologically."""
    cid = to_object_id(conversation_id)
    if not cid:
        return []
    coll = get_collection(COLLECTION_MESSAGES)
    return list(coll.find({"conversation_id": cid}).sort("created_at", 1))

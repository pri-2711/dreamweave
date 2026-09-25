"""
Business logic service for AI Content persistence.
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from brain.src.database.repositories import ai as ai_repo
from brain.src.database.repositories import spaces as spaces_repo
from brain.src.database.repositories import activity as activity_repo
from brain.src.schemas.ai_content import AIContentCreate, AIContentUpdate
from brain.src.utils.serialization import parse_object_id, serialize_doc, serialize_docs


def create_ai_content(data: AIContentCreate, current_user_id: str) -> Dict[str, Any]:
    """Create persistent AI content document."""
    sid = parse_object_id(data.space_id, param_name="space_id")
    space = spaces_repo.get_space_by_id(sid)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space with id '{data.space_id}' not found."
        )

    uid = parse_object_id(current_user_id, param_name="user_id")
    asset_oid = parse_object_id(data.asset_id, param_name="asset_id") if data.asset_id else None

    doc = ai_repo.create_ai_content(
        space_id=sid,
        user_id=uid,
        type=data.type,
        content=data.content,
        title=data.title,
        source_content_ids=data.source_content_ids,
        source_knowledge_ids=data.source_knowledge_ids,
        asset_id=asset_oid,
        is_favourite=data.is_favourite,
        is_archived=data.is_archived
    )

    activity_repo.log_activity(
        space_id=sid,
        user_id=uid,
        action="ai_content_created",
        target_type="ai_content",
        target_id=doc["_id"]
    )

    return serialize_doc(doc)


def get_ai_content(ai_content_id: str) -> Dict[str, Any]:
    """Get persistent AI content by ID."""
    aid = parse_object_id(ai_content_id, param_name="ai_content_id")
    item = ai_repo.get_ai_content_by_id(aid)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI content with id '{ai_content_id}' not found."
        )
    return serialize_doc(item)


def list_ai_content(space_id: str, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """List persistent AI content items in a space."""
    sid = parse_object_id(space_id, param_name="space_id")
    items = ai_repo.list_ai_content_by_space(space_id=sid, content_type=content_type)
    return serialize_docs(items)


def update_ai_content(ai_content_id: str, data: AIContentUpdate, current_user_id: str) -> Dict[str, Any]:
    """Update fields of an AI content document."""
    aid = parse_object_id(ai_content_id, param_name="ai_content_id")
    existing = ai_repo.get_ai_content_by_id(aid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI content with id '{ai_content_id}' not found."
        )

    updates = {}
    if data.title is not None:
        updates["title"] = data.title
    if data.content is not None:
        updates["content"] = data.content
    if data.is_favourite is not None:
        updates["organization.is_favourite"] = data.is_favourite
    if data.is_archived is not None:
        updates["organization.is_archived"] = data.is_archived

    if updates:
        from brain.src.database.collections import COLLECTION_AI_CONTENT, get_collection
        from brain.src.database.models import now_utc
        updates["updated_at"] = now_utc()
        get_collection(COLLECTION_AI_CONTENT).update_one({"_id": aid}, {"$set": updates})

    updated_doc = ai_repo.get_ai_content_by_id(aid)
    return serialize_doc(updated_doc)


def delete_ai_content(ai_content_id: str, current_user_id: str) -> Dict[str, Any]:
    """Delete an AI content document by ID."""
    aid = parse_object_id(ai_content_id, param_name="ai_content_id")
    existing = ai_repo.get_ai_content_by_id(aid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI content with id '{ai_content_id}' not found."
        )

    from brain.src.database.collections import COLLECTION_AI_CONTENT, get_collection
    get_collection(COLLECTION_AI_CONTENT).delete_one({"_id": aid})
    return {"message": f"AI content '{ai_content_id}' successfully deleted."}

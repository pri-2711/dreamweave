"""
Business logic service for Content Items.
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from brain.src.database.repositories import content as content_repo
from brain.src.database.repositories import spaces as spaces_repo
from brain.src.database.repositories import activity as activity_repo
from brain.src.schemas.content import ContentCreate, ContentUpdate, VALID_CONTENT_TYPES
from brain.src.utils.serialization import parse_object_id, serialize_doc, serialize_docs


def create_content_item(data: ContentCreate, current_user_id: str) -> Dict[str, Any]:
    """Create a new content item."""
    if data.type not in VALID_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid content type '{data.type}'. Must be one of {sorted(list(VALID_CONTENT_TYPES))}."
        )

    sid = parse_object_id(data.space_id, param_name="space_id")
    space = spaces_repo.get_space_by_id(sid)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space with id '{data.space_id}' not found."
        )

    uid = parse_object_id(current_user_id, param_name="user_id")
    asset_oid = parse_object_id(data.asset_id, param_name="asset_id") if data.asset_id else None

    src_kind = data.source.kind if data.source else "upload"
    src_url = data.source.url if data.source else None
    src_platform = data.source.platform if data.source else None

    doc = content_repo.create_content_item(
        space_id=sid,
        user_id=uid,
        type=data.type,
        title=data.title,
        description=data.description,
        source_kind=src_kind,
        source_url=src_url,
        source_platform=src_platform,
        asset_id=asset_oid,
        tags=data.tags,
        is_favourite=data.is_favourite,
        is_archived=data.is_archived
    )

    activity_repo.log_activity(
        space_id=sid,
        user_id=uid,
        action="content_added",
        target_type="content_item",
        target_id=doc["_id"]
    )

    return serialize_doc(doc)


def get_content_item(content_id: str) -> Dict[str, Any]:
    """Get a content item by ID."""
    cid = parse_object_id(content_id, param_name="content_id")
    item = content_repo.get_content_item_by_id(cid)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content item with id '{content_id}' not found."
        )
    return serialize_doc(item)


def list_content_items(
    space_id: Optional[str] = None,
    item_type: Optional[str] = None,
    is_favourite: Optional[bool] = None,
    is_archived: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """List content items filtered by space_id, type, favourite, archived."""
    sid = parse_object_id(space_id, param_name="space_id") if space_id else None
    items = content_repo.list_content_items(
        space_id=sid,
        item_type=item_type,
        is_favourite=is_favourite,
        is_archived=is_archived
    )
    return serialize_docs(items)


def update_content_item(content_id: str, data: ContentUpdate, current_user_id: str) -> Dict[str, Any]:
    """Update fields of a content item."""
    cid = parse_object_id(content_id, param_name="content_id")
    existing = content_repo.get_content_item_by_id(cid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content item with id '{content_id}' not found."
        )

    updates = {}
    if data.title is not None:
        updates["title"] = data.title
    if data.description is not None:
        updates["description"] = data.description
    if data.source is not None:
        updates["source.kind"] = data.source.kind
        updates["source.url"] = data.source.url
        updates["source.platform"] = data.source.platform
    if data.asset_id is not None:
        updates["asset_id"] = parse_object_id(data.asset_id, param_name="asset_id") if data.asset_id else None
    if data.tags is not None:
        updates["tags"] = data.tags
    if data.is_favourite is not None:
        updates["organization.is_favourite"] = data.is_favourite
    if data.is_archived is not None:
        updates["organization.is_archived"] = data.is_archived

    if updates:
        content_repo.update_content_item(cid, updates)
        uid = parse_object_id(current_user_id, param_name="user_id")
        if existing.get("space_id"):
            activity_repo.log_activity(
                space_id=existing["space_id"],
                user_id=uid,
                action="content_updated",
                target_type="content_item",
                target_id=cid
            )

    updated_item = content_repo.get_content_item_by_id(cid)
    return serialize_doc(updated_item)


def delete_content_item(content_id: str, current_user_id: str) -> Dict[str, Any]:
    """Delete a content item by ID."""
    cid = parse_object_id(content_id, param_name="content_id")
    existing = content_repo.get_content_item_by_id(cid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content item with id '{content_id}' not found."
        )

    content_repo.delete_content_item(cid)
    return {"message": f"Content item '{content_id}' successfully deleted."}

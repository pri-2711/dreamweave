"""
Business logic service for Spaces.
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from brain.src.database.repositories import spaces as spaces_repo
from brain.src.database.repositories import activity as activity_repo
from brain.src.schemas.spaces import SpaceCreate, SpaceUpdate
from brain.src.utils.serialization import parse_object_id, serialize_doc, serialize_docs


def create_space(data: SpaceCreate, current_user_id: str) -> Dict[str, Any]:
    """Create a new Space and log activity."""
    owner_oid = parse_object_id(current_user_id, param_name="user_id")

    doc = spaces_repo.create_space(
        owner_id=owner_oid,
        name=data.name.strip(),
        description=data.description or "",
        icon=data.icon,
        cover_image_url=data.cover_image_url,
        cover_position=data.cover_position,
        status=data.status or "active",
        visibility=data.visibility or "private",
        is_favourite=data.is_favourite,
        is_archived=data.is_archived
    )

    space_id = doc["_id"]
    activity_repo.log_activity(
        space_id=space_id,
        user_id=owner_oid,
        action="space_created",
        target_type="space",
        target_id=space_id
    )

    return serialize_doc(doc)


def get_space(space_id: str) -> Dict[str, Any]:
    """Get a Space by ID."""
    sid = parse_object_id(space_id, param_name="space_id")
    space = spaces_repo.get_space_by_id(sid)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space with id '{space_id}' not found."
        )
    return serialize_doc(space)


def list_spaces(current_user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all Spaces owned by current user."""
    owner_oid = parse_object_id(current_user_id, param_name="user_id")
    spaces = spaces_repo.list_spaces_by_owner(owner_id=owner_oid, status=status)
    return serialize_docs(spaces)


def update_space(space_id: str, data: SpaceUpdate, current_user_id: str) -> Dict[str, Any]:
    """Update fields of an existing Space."""
    sid = parse_object_id(space_id, param_name="space_id")
    existing = spaces_repo.get_space_by_id(sid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space with id '{space_id}' not found."
        )

    updates = {}
    if data.name is not None:
        updates["name"] = data.name.strip()
    if data.description is not None:
        updates["description"] = data.description
    if data.icon is not None:
        updates["icon"] = data.icon
    if data.cover_image_url is not None:
        updates["cover.image_url"] = data.cover_image_url
    if data.cover_position is not None:
        updates["cover.position"] = data.cover_position
    if data.status is not None:
        updates["status"] = data.status
    if data.visibility is not None:
        updates["settings.visibility"] = data.visibility
    if data.is_favourite is not None:
        updates["organization.is_favourite"] = data.is_favourite
    if data.is_archived is not None:
        updates["organization.is_archived"] = data.is_archived

    if updates:
        spaces_repo.update_space(sid, updates)
        user_oid = parse_object_id(current_user_id, param_name="user_id")
        activity_repo.log_activity(
            space_id=sid,
            user_id=user_oid,
            action="space_updated",
            target_type="space",
            target_id=sid
        )

    updated_space = spaces_repo.get_space_by_id(sid)
    return serialize_doc(updated_space)


def delete_space(space_id: str, current_user_id: str) -> Dict[str, Any]:
    """Delete a Space by ID."""
    sid = parse_object_id(space_id, param_name="space_id")
    existing = spaces_repo.get_space_by_id(sid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space with id '{space_id}' not found."
        )

    spaces_repo.delete_space(sid)
    return {"message": f"Space '{space_id}' successfully deleted."}

"""
Repository for `spaces` and `space_members` collections.
"""

from typing import Dict, Any, List, Optional, Union
from bson import ObjectId
from brain.src.database.collections import (
    COLLECTION_SPACES,
    COLLECTION_SPACE_MEMBERS,
    get_collection
)
from brain.src.database.models import (
    build_space_doc,
    build_space_member_doc,
    to_object_id,
    now_utc
)


def create_space(
    owner_id: Union[str, ObjectId],
    name: str,
    description: str = "",
    icon: Optional[str] = None,
    cover_image_url: Optional[str] = None,
    cover_position: Optional[str] = None,
    status: str = "active",
    visibility: str = "private",
    is_favourite: bool = False,
    is_archived: bool = False
) -> Dict[str, Any]:
    """Create and insert a new Space document and automatically add owner as space_member."""
    coll_spaces = get_collection(COLLECTION_SPACES)
    doc = build_space_doc(
        owner_id=owner_id,
        name=name,
        description=description,
        icon=icon,
        cover_image_url=cover_image_url,
        cover_position=cover_position,
        status=status,
        visibility=visibility,
        is_favourite=is_favourite,
        is_archived=is_archived
    )
    result = coll_spaces.insert_one(doc)
    space_id = result.inserted_id
    doc["_id"] = space_id

    # Automatically add owner as 'owner' role in space_members
    add_space_member(space_id=space_id, user_id=owner_id, role="owner")

    return doc


def get_space_by_id(space_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
    """Find a space by _id."""
    oid = to_object_id(space_id)
    if not oid:
        return None
    coll = get_collection(COLLECTION_SPACES)
    return coll.find_one({"_id": oid})


def list_spaces_by_owner(owner_id: Union[str, ObjectId], status: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all spaces owned by a specific user."""
    oid = to_object_id(owner_id)
    if not oid:
        return []
    coll = get_collection(COLLECTION_SPACES)
    query: Dict[str, Any] = {"owner_id": oid}
    if status:
        query["status"] = status
    return list(coll.find(query).sort("created_at", -1))


def update_space(space_id: Union[str, ObjectId], updates: Dict[str, Any]) -> bool:
    """Update fields of an existing space."""
    oid = to_object_id(space_id)
    if not oid:
        return False
    updates["updated_at"] = now_utc()
    coll = get_collection(COLLECTION_SPACES)
    result = coll.update_one({"_id": oid}, {"$set": updates})
    return result.modified_count > 0


def delete_space(space_id: Union[str, ObjectId]) -> bool:
    """Delete a space and its member associations."""
    oid = to_object_id(space_id)
    if not oid:
        return False
    get_collection(COLLECTION_SPACE_MEMBERS).delete_many({"space_id": oid})
    result = get_collection(COLLECTION_SPACES).delete_one({"_id": oid})
    return result.deleted_count > 0


def add_space_member(
    space_id: Union[str, ObjectId],
    user_id: Union[str, ObjectId],
    role: str = "viewer"
) -> Dict[str, Any]:
    """Add or update a member in a space."""
    sid = to_object_id(space_id)
    uid = to_object_id(user_id)
    coll = get_collection(COLLECTION_SPACE_MEMBERS)
    existing = coll.find_one({"space_id": sid, "user_id": uid})
    if existing:
        coll.update_one({"_id": existing["_id"]}, {"$set": {"role": role}})
        existing["role"] = role
        return existing

    doc = build_space_member_doc(space_id=sid, user_id=uid, role=role)
    res = coll.insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc


def list_space_members(space_id: Union[str, ObjectId]) -> List[Dict[str, Any]]:
    """List all members of a space."""
    sid = to_object_id(space_id)
    if not sid:
        return []
    coll = get_collection(COLLECTION_SPACE_MEMBERS)
    return list(coll.find({"space_id": sid}))

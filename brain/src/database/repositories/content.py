"""
Repository for `content_items` collection.
All user-saved/uploaded things (images, pdfs, notes, links, tickets, etc.) belong here,
differentiated by the `type` field.
"""

from typing import Dict, Any, List, Optional, Union
from bson import ObjectId
from brain.src.database.collections import COLLECTION_CONTENT_ITEMS, get_collection
from brain.src.database.models import build_content_item_doc, to_object_id, now_utc


def create_content_item(
    space_id: Union[str, ObjectId],
    user_id: Union[str, ObjectId],
    type: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    source_kind: str = "upload",
    source_url: Optional[str] = None,
    source_platform: Optional[str] = None,
    asset_id: Optional[Union[str, ObjectId]] = None,
    preview_title: Optional[str] = None,
    preview_description: Optional[str] = None,
    preview_thumbnail_url: Optional[str] = None,
    preview_favicon_url: Optional[str] = None,
    generated_visual_asset_id: Optional[Union[str, ObjectId]] = None,
    tags: Optional[List[str]] = None,
    is_favourite: bool = False,
    is_archived: bool = False,
    legacy_id: Optional[Any] = None
) -> Dict[str, Any]:
    """Create and insert a content item into `content_items`."""
    coll = get_collection(COLLECTION_CONTENT_ITEMS)
    doc = build_content_item_doc(
        space_id=space_id,
        user_id=user_id,
        type=type,
        title=title,
        description=description,
        source_kind=source_kind,
        source_url=source_url,
        source_platform=source_platform,
        asset_id=asset_id,
        preview_title=preview_title,
        preview_description=preview_description,
        preview_thumbnail_url=preview_thumbnail_url,
        preview_favicon_url=preview_favicon_url,
        generated_visual_asset_id=generated_visual_asset_id,
        tags=tags,
        is_favourite=is_favourite,
        is_archived=is_archived,
        legacy_id=legacy_id
    )
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_content_item_by_id(content_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
    """Find a content item by _id."""
    oid = to_object_id(content_id)
    if not oid:
        return None
    coll = get_collection(COLLECTION_CONTENT_ITEMS)
    return coll.find_one({"_id": oid})


def list_content_items(
    space_id: Optional[Union[str, ObjectId]] = None,
    user_id: Optional[Union[str, ObjectId]] = None,
    item_type: Optional[str] = None,
    is_favourite: Optional[bool] = None,
    is_archived: Optional[bool] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """List content items with optional filters."""
    query: Dict[str, Any] = {}
    if space_id:
        sid = to_object_id(space_id)
        if sid:
            query["space_id"] = sid
    if user_id:
        uid = to_object_id(user_id)
        if uid:
            query["user_id"] = uid
    if item_type:
        query["type"] = item_type
    if is_favourite is not None:
        query["organization.is_favourite"] = is_favourite
    if is_archived is not None:
        query["organization.is_archived"] = is_archived

    coll = get_collection(COLLECTION_CONTENT_ITEMS)
    return list(coll.find(query).sort("created_at", -1).limit(limit))


def update_content_item(content_id: Union[str, ObjectId], updates: Dict[str, Any]) -> bool:
    """Update fields of a content item."""
    oid = to_object_id(content_id)
    if not oid:
        return False
    updates["updated_at"] = now_utc()
    coll = get_collection(COLLECTION_CONTENT_ITEMS)
    result = coll.update_one({"_id": oid}, {"$set": updates})
    return result.modified_count > 0


def delete_content_item(content_id: Union[str, ObjectId]) -> bool:
    """Delete a content item by _id."""
    oid = to_object_id(content_id)
    if not oid:
        return False
    coll = get_collection(COLLECTION_CONTENT_ITEMS)
    result = coll.delete_one({"_id": oid})
    return result.deleted_count > 0

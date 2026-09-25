"""
Repository for `assets` collection.
Stores metadata references for uploaded or generated files.
"""

from typing import Dict, Any, List, Optional, Union
from bson import ObjectId
from brain.src.database.collections import COLLECTION_ASSETS, get_collection
from brain.src.database.models import build_asset_doc, to_object_id


def create_asset(
    user_id: Union[str, ObjectId],
    space_id: Union[str, ObjectId],
    filename: str,
    mime_type: str,
    size: int,
    content_id: Optional[Union[str, ObjectId]] = None,
    storage_provider: str = "local",
    storage_path: str = "",
    storage_url: Optional[str] = None
) -> Dict[str, Any]:
    """Create and insert a new asset document."""
    coll = get_collection(COLLECTION_ASSETS)
    doc = build_asset_doc(
        user_id=user_id,
        space_id=space_id,
        filename=filename,
        mime_type=mime_type,
        size=size,
        content_id=content_id,
        storage_provider=storage_provider,
        storage_path=storage_path,
        storage_url=storage_url
    )
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_asset_by_id(asset_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
    """Find an asset document by _id."""
    oid = to_object_id(asset_id)
    if not oid:
        return None
    coll = get_collection(COLLECTION_ASSETS)
    return coll.find_one({"_id": oid})


def list_assets_by_space(space_id: Union[str, ObjectId]) -> List[Dict[str, Any]]:
    """List assets for a given space."""
    sid = to_object_id(space_id)
    if not sid:
        return []
    coll = get_collection(COLLECTION_ASSETS)
    return list(coll.find({"space_id": sid}).sort("created_at", -1))

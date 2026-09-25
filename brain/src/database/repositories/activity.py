"""
Repository for `activity` collection.
Tracks user and system activities within Spaces.
"""

from typing import Dict, Any, List, Optional, Union
from bson import ObjectId
from brain.src.database.collections import COLLECTION_ACTIVITY, get_collection
from brain.src.database.models import build_activity_doc, to_object_id


def log_activity(
    space_id: Union[str, ObjectId],
    user_id: Union[str, ObjectId],
    action: str,
    target_type: str,
    target_id: Union[str, ObjectId]
) -> Dict[str, Any]:
    """Log an activity event in a space."""
    coll = get_collection(COLLECTION_ACTIVITY)
    doc = build_activity_doc(
        space_id=space_id,
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id
    )
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def list_activities_by_space(
    space_id: Union[str, ObjectId],
    limit: int = 50
) -> List[Dict[str, Any]]:
    """List activity logs for a space sorted by newest first."""
    sid = to_object_id(space_id)
    if not sid:
        return []
    coll = get_collection(COLLECTION_ACTIVITY)
    return list(coll.find({"space_id": sid}).sort("created_at", -1).limit(limit))

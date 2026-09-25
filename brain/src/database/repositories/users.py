"""
Repository for `users` collection.
"""

from typing import Dict, Any, Optional, Union
from bson import ObjectId
from brain.src.database.collections import COLLECTION_USERS, get_collection
from brain.src.database.models import build_user_doc, to_object_id, now_utc


def create_user(
    email: str,
    name: str,
    avatar_url: Optional[str] = None,
    bio: Optional[str] = None,
    password_hash: Optional[str] = None,
    provider: str = "local",
    theme: str = "light",
    language: str = "en"
) -> Dict[str, Any]:
    """Create and insert a new user document."""
    coll = get_collection(COLLECTION_USERS)
    doc = build_user_doc(
        email=email,
        name=name,
        avatar_url=avatar_url,
        bio=bio,
        password_hash=password_hash,
        provider=provider,
        theme=theme,
        language=language
    )
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_user_by_id(user_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
    """Find a user by _id."""
    oid = to_object_id(user_id)
    if not oid:
        return None
    coll = get_collection(COLLECTION_USERS)
    return coll.find_one({"_id": oid})


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Find a user by email address."""
    coll = get_collection(COLLECTION_USERS)
    return coll.find_one({"email": email.strip().lower()})


def update_user(user_id: Union[str, ObjectId], updates: Dict[str, Any]) -> bool:
    """Update fields of an existing user document."""
    oid = to_object_id(user_id)
    if not oid:
        return False
    updates["updated_at"] = now_utc()
    coll = get_collection(COLLECTION_USERS)
    result = coll.update_one({"_id": oid}, {"$set": updates})
    return result.modified_count > 0

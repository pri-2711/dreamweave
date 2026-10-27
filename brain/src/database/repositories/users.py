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
    """Create and insert a new user document with normalized email."""
    coll = get_collection(COLLECTION_USERS)
    clean_email = email.strip().lower() if (email and isinstance(email, str)) else ""
    doc = build_user_doc(
        email=clean_email,
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
    """Find a user by normalized email address."""
    if not email or not isinstance(email, str):
        return None
    clean_email = email.strip().lower()
    coll = get_collection(COLLECTION_USERS)
    return coll.find_one({"email": clean_email})


def update_user(user_id: Union[str, ObjectId], updates: Dict[str, Any]) -> bool:
    """Update fields of an existing user document."""
    oid = to_object_id(user_id)
    if not oid:
        return False
    updates["updated_at"] = now_utc()
    coll = get_collection(COLLECTION_USERS)
    result = coll.update_one({"_id": oid}, {"$set": updates})
    return result.modified_count > 0


def update_last_login(user_id: Union[str, ObjectId]) -> bool:
    """
    Update the last_login timestamp of a user to now_utc().
    Returns True if user was found and modified, False otherwise.
    """
    oid = to_object_id(user_id)
    if not oid:
        return False
    now = now_utc()
    coll = get_collection(COLLECTION_USERS)
    result = coll.update_one(
        {"_id": oid},
        {"$set": {"last_login": now, "updated_at": now}}
    )
    return result.modified_count > 0


def sanitize_user_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Return a copy of the user document with sensitive authentication fields
    (such as password_hash) stripped out to prevent accidental exposure.
    """
    if not doc:
        return None
    sanitized = dict(doc)
    if "auth" in sanitized and isinstance(sanitized["auth"], dict):
        auth_clean = dict(sanitized["auth"])
        auth_clean.pop("password_hash", None)
        sanitized["auth"] = auth_clean
    return sanitized


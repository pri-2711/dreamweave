"""
Repository for `revoked_tokens` collection.
Stores token revocation records (jti, expiry, revocation timestamp)
with MongoDB TTL index for automatic expiration cleanup.
"""

from datetime import datetime
from typing import Dict, Any, Optional, Union
from bson import ObjectId

from brain.src.database.collections import COLLECTION_REVOKED_TOKENS, get_collection
from brain.src.database.models import build_revoked_token_doc, to_object_id


def revoke_token(
    jti: str,
    token_type: str,
    expires_at: datetime,
    user_id: Optional[Union[str, ObjectId]] = None,
    reason: str = "logout"
) -> Dict[str, Any]:
    """
    Store a token revocation record.
    If the jti is already registered, returns the existing record.
    """
    coll = get_collection(COLLECTION_REVOKED_TOKENS)
    existing = coll.find_one({"jti": str(jti)})
    if existing:
        return existing

    doc = build_revoked_token_doc(
        jti=str(jti),
        token_type=token_type,
        expires_at=expires_at,
        user_id=user_id,
        reason=reason
    )
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def is_token_revoked(jti: str) -> bool:
    """
    Check whether a specific token identifier (jti) has been revoked.
    Note: Must be checked explicitly in application logic;
    the MongoDB TTL index is for background cleanup, not access control.
    """
    if not jti or not isinstance(jti, str):
        return False
    coll = get_collection(COLLECTION_REVOKED_TOKENS)
    return coll.find_one({"jti": str(jti)}) is not None


def get_revoked_token(jti: str) -> Optional[Dict[str, Any]]:
    """Retrieve revocation metadata for a token by its jti."""
    if not jti or not isinstance(jti, str):
        return None
    coll = get_collection(COLLECTION_REVOKED_TOKENS)
    return coll.find_one({"jti": str(jti)})

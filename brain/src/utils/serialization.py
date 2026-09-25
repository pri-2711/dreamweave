"""
Serialization and ObjectId helper utilities for DreamWeave API layer.
"""

from datetime import datetime
from typing import Dict, Any, List, Union, Optional
from bson import ObjectId
from fastapi import HTTPException, status


def parse_object_id(id_str: str, param_name: str = "id") -> ObjectId:
    """
    Validate and parse a string into a PyMongo ObjectId.
    Raises HTTPException(400) if string format is invalid.
    """
    if not id_str or not isinstance(id_str, str) or len(id_str.strip()) != 24:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {param_name} format. Must be a 24-character hex string."
        )
    try:
        return ObjectId(id_str.strip())
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {param_name} format. Must be a 24-character hex string."
        )


def serialize_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Recursively convert PyMongo document dictionary for JSON serialization.
    - Converts `_id` ObjectId -> `id` string (and keeps `_id` as string)
    - Converts any nested ObjectId -> string
    - Converts datetime -> ISO format string
    """
    if doc is None:
        return None

    result = {}
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        str_id = str(doc["_id"])
        result["id"] = str_id
        result["_id"] = str_id

    for key, value in doc.items():
        if key == "_id":
            continue
        result[key] = _serialize_value(value)

    return result


def serialize_docs(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Serialize a list of PyMongo documents."""
    return [serialize_doc(d) for d in docs if d is not None]


def _serialize_value(val: Any) -> Any:
    """Helper function to serialize individual values."""
    if isinstance(val, ObjectId):
        return str(val)
    elif isinstance(val, datetime):
        return val.isoformat()
    elif isinstance(val, dict):
        return {k: _serialize_value(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [_serialize_value(v) for v in val]
    return val

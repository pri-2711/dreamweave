"""
FastAPI dependencies for DreamWeave API layer.
"""

from typing import Optional
from fastapi import Header
from brain.src.utils.serialization import parse_object_id

# Default temporary development user ObjectId (24 hex chars)
DEFAULT_DEV_USER_ID = "000000000000000000000001"


def get_current_user_id(x_dev_user_id: Optional[str] = Header(None, alias="X-Dev-User-Id")) -> str:
    """
    Temporary development user dependency.
    Accepts optional X-Dev-User-Id header for developer testing.
    Falls back to a default development user ID if header is missing or empty.
    
    Note: When authentication is implemented in later stages, this dependency
    will be updated to extract `current_user_id` from JWT authentication tokens.
    """
    if x_dev_user_id and len(x_dev_user_id.strip()) == 24:
        # Validate format
        parse_object_id(x_dev_user_id, param_name="X-Dev-User-Id")
        return x_dev_user_id.strip()

    return DEFAULT_DEV_USER_ID

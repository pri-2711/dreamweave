"""
Repository for `vision_boards` and `vision_board_items` collections.
Supports freeform canvas placement (x, y, width, height, rotation, z_index).
"""

from typing import Dict, Any, List, Optional, Union
from bson import ObjectId
from brain.src.database.collections import (
    COLLECTION_VISION_BOARDS,
    COLLECTION_VISION_BOARD_ITEMS,
    get_collection
)
from brain.src.database.models import (
    build_vision_board_doc,
    build_vision_board_item_doc,
    to_object_id,
    now_utc
)


def create_vision_board(
    space_id: Union[str, ObjectId],
    name: str,
    width: int = 1920,
    height: int = 1080
) -> Dict[str, Any]:
    """Create and insert a vision board."""
    coll = get_collection(COLLECTION_VISION_BOARDS)
    doc = build_vision_board_doc(space_id=space_id, name=name, width=width, height=height)
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_vision_board_by_id(board_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
    """Find a vision board by _id."""
    oid = to_object_id(board_id)
    if not oid:
        return None
    coll = get_collection(COLLECTION_VISION_BOARDS)
    return coll.find_one({"_id": oid})


def list_vision_boards_by_space(space_id: Union[str, ObjectId]) -> List[Dict[str, Any]]:
    """List vision boards in a space."""
    sid = to_object_id(space_id)
    if not sid:
        return []
    coll = get_collection(COLLECTION_VISION_BOARDS)
    return list(coll.find({"space_id": sid}).sort("created_at", -1))


def create_vision_board_item(
    vision_board_id: Union[str, ObjectId],
    content_id: Optional[Union[str, ObjectId]] = None,
    ai_content_id: Optional[Union[str, ObjectId]] = None,
    x: float = 0.0,
    y: float = 0.0,
    width: float = 300.0,
    height: float = 200.0,
    rotation: float = 0.0,
    z_index: int = 0,
    border_radius: Optional[float] = None
) -> Dict[str, Any]:
    """Place an item on a freeform vision board."""
    coll = get_collection(COLLECTION_VISION_BOARD_ITEMS)
    doc = build_vision_board_item_doc(
        vision_board_id=vision_board_id,
        content_id=content_id,
        ai_content_id=ai_content_id,
        x=x,
        y=y,
        width=width,
        height=height,
        rotation=rotation,
        z_index=z_index,
        border_radius=border_radius
    )
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def list_vision_board_items(vision_board_id: Union[str, ObjectId]) -> List[Dict[str, Any]]:
    """List all placed items for a vision board."""
    vbid = to_object_id(vision_board_id)
    if not vbid:
        return []
    coll = get_collection(COLLECTION_VISION_BOARD_ITEMS)
    return list(coll.find({"vision_board_id": vbid}).sort("z_index", 1))


def update_vision_board_item(item_id: Union[str, ObjectId], updates: Dict[str, Any]) -> bool:
    """Update position, size, rotation, or style of a vision board item."""
    oid = to_object_id(item_id)
    if not oid:
        return False
    updates["updated_at"] = now_utc()
    coll = get_collection(COLLECTION_VISION_BOARD_ITEMS)
    result = coll.update_one({"_id": oid}, {"$set": updates})
    return result.modified_count > 0

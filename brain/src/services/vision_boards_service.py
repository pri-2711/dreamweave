"""
Business logic service for Vision Boards and Vision Board Items.
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from brain.src.database.repositories import vision_boards as vb_repo
from brain.src.database.repositories import spaces as spaces_repo
from brain.src.database.repositories import activity as activity_repo
from brain.src.schemas.vision_boards import (
    VisionBoardCreate,
    VisionBoardUpdate,
    VisionBoardItemCreate,
    VisionBoardItemUpdate
)
from brain.src.utils.serialization import parse_object_id, serialize_doc, serialize_docs


def create_vision_board(space_id: str, data: VisionBoardCreate, current_user_id: str) -> Dict[str, Any]:
    """Create a new Vision Board for a space (requires editor role)."""
    from brain.src.services.authorization import check_space_access
    check_space_access(space_id, current_user_id, required_role="editor")

    sid = parse_object_id(space_id, param_name="space_id")
    doc = vb_repo.create_vision_board(
        space_id=sid,
        name=data.name.strip(),
        width=data.width,
        height=data.height
    )

    uid = parse_object_id(current_user_id, param_name="user_id")
    activity_repo.log_activity(
        space_id=sid,
        user_id=uid,
        action="vision_board_created",
        target_type="vision_board",
        target_id=doc["_id"]
    )

    return serialize_doc(doc)


def list_vision_boards(space_id: str, current_user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List vision boards in a space (requires viewer role)."""
    if current_user_id:
        from brain.src.services.authorization import check_space_access
        check_space_access(space_id, current_user_id, required_role="viewer")

    sid = parse_object_id(space_id, param_name="space_id")
    boards = vb_repo.list_vision_boards_by_space(sid)
    return serialize_docs(boards)


def get_vision_board(board_id: str, current_user_id: Optional[str] = None) -> Dict[str, Any]:
    """Get a vision board by ID (requires viewer role in space)."""
    bid = parse_object_id(board_id, param_name="board_id")
    board = vb_repo.get_vision_board_by_id(bid)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vision board with id '{board_id}' not found."
        )

    if current_user_id and board.get("space_id"):
        from brain.src.services.authorization import check_space_access
        check_space_access(str(board["space_id"]), current_user_id, required_role="viewer")

    return serialize_doc(board)


def update_vision_board(board_id: str, data: VisionBoardUpdate, current_user_id: str) -> Dict[str, Any]:
    """Update vision board metadata (requires editor role)."""
    bid = parse_object_id(board_id, param_name="board_id")
    existing = vb_repo.get_vision_board_by_id(bid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vision board with id '{board_id}' not found."
        )

    if existing.get("space_id"):
        from brain.src.services.authorization import check_space_access
        check_space_access(str(existing["space_id"]), current_user_id, required_role="editor")

    updates = {}
    if data.name is not None:
        updates["name"] = data.name.strip()
    if data.width is not None:
        updates["canvas.width"] = data.width
    if data.height is not None:
        updates["canvas.height"] = data.height

    if updates:
        from brain.src.database.collections import COLLECTION_VISION_BOARDS, get_collection
        from brain.src.database.models import now_utc
        updates["updated_at"] = now_utc()
        get_collection(COLLECTION_VISION_BOARDS).update_one({"_id": bid}, {"$set": updates})

    updated_board = vb_repo.get_vision_board_by_id(bid)
    return serialize_doc(updated_board)


def delete_vision_board(board_id: str, current_user_id: str) -> Dict[str, Any]:
    """Delete a vision board and its board items (requires editor role)."""
    bid = parse_object_id(board_id, param_name="board_id")
    existing = vb_repo.get_vision_board_by_id(bid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vision board with id '{board_id}' not found."
        )

    if existing.get("space_id"):
        from brain.src.services.authorization import check_space_access
        check_space_access(str(existing["space_id"]), current_user_id, required_role="editor")

    from brain.src.database.collections import (
        COLLECTION_VISION_BOARDS,
        COLLECTION_VISION_BOARD_ITEMS,
        get_collection
    )
    get_collection(COLLECTION_VISION_BOARD_ITEMS).delete_many({"vision_board_id": bid})
    get_collection(COLLECTION_VISION_BOARDS).delete_one({"_id": bid})
    return {"message": f"Vision board '{board_id}' successfully deleted."}


def create_vision_board_item(board_id: str, data: VisionBoardItemCreate, current_user_id: str) -> Dict[str, Any]:
    """Add a freeform item to a vision board (requires editor role)."""
    bid = parse_object_id(board_id, param_name="board_id")
    board = vb_repo.get_vision_board_by_id(bid)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vision board with id '{board_id}' not found."
        )

    if board.get("space_id"):
        from brain.src.services.authorization import check_space_access
        check_space_access(str(board["space_id"]), current_user_id, required_role="editor")

    cnt_oid = parse_object_id(data.content_id, param_name="content_id") if data.content_id else None
    aic_oid = parse_object_id(data.ai_content_id, param_name="ai_content_id") if data.ai_content_id else None

    doc = vb_repo.create_vision_board_item(
        vision_board_id=bid,
        content_id=cnt_oid,
        ai_content_id=aic_oid,
        x=data.x,
        y=data.y,
        width=data.width,
        height=data.height,
        rotation=data.rotation,
        z_index=data.z_index,
        border_radius=data.border_radius
    )

    return serialize_doc(doc)


def list_vision_board_items(board_id: str, current_user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all items on a vision board (requires viewer role)."""
    bid = parse_object_id(board_id, param_name="board_id")
    board = vb_repo.get_vision_board_by_id(bid)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vision board with id '{board_id}' not found."
        )

    if current_user_id and board.get("space_id"):
        from brain.src.services.authorization import check_space_access
        check_space_access(str(board["space_id"]), current_user_id, required_role="viewer")

    items = vb_repo.list_vision_board_items(bid)
    return serialize_docs(items)


def update_vision_board_item(item_id: str, data: VisionBoardItemUpdate, current_user_id: str) -> Dict[str, Any]:
    """Update position, size, rotation, or style of a vision board item (requires editor role)."""
    iid = parse_object_id(item_id, param_name="item_id")

    from brain.src.database.collections import COLLECTION_VISION_BOARD_ITEMS, get_collection
    coll = get_collection(COLLECTION_VISION_BOARD_ITEMS)
    existing = coll.find_one({"_id": iid})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vision board item with id '{item_id}' not found."
        )

    # Check permission on parent board's space
    parent_board = vb_repo.get_vision_board_by_id(existing["vision_board_id"])
    if parent_board and parent_board.get("space_id"):
        from brain.src.services.authorization import check_space_access
        check_space_access(str(parent_board["space_id"]), current_user_id, required_role="editor")

    updates = {}
    if data.x is not None:
        updates["position.x"] = data.x
    if data.y is not None:
        updates["position.y"] = data.y
    if data.width is not None:
        updates["size.width"] = data.width
    if data.height is not None:
        updates["size.height"] = data.height
    if data.rotation is not None:
        updates["rotation"] = data.rotation
    if data.z_index is not None:
        updates["z_index"] = data.z_index
    if data.border_radius is not None:
        updates["style.border_radius"] = data.border_radius

    if updates:
        vb_repo.update_vision_board_item(iid, updates)

    updated_item = coll.find_one({"_id": iid})
    return serialize_doc(updated_item)


def delete_vision_board_item(item_id: str, current_user_id: str) -> Dict[str, Any]:
    """Delete an item from a vision board (requires editor role)."""
    iid = parse_object_id(item_id, param_name="item_id")
    from brain.src.database.collections import COLLECTION_VISION_BOARD_ITEMS, get_collection
    coll = get_collection(COLLECTION_VISION_BOARD_ITEMS)
    existing = coll.find_one({"_id": iid})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vision board item with id '{item_id}' not found."
        )

    parent_board = vb_repo.get_vision_board_by_id(existing["vision_board_id"])
    if parent_board and parent_board.get("space_id"):
        from brain.src.services.authorization import check_space_access
        check_space_access(str(parent_board["space_id"]), current_user_id, required_role="editor")

    coll.delete_one({"_id": iid})
    return {"message": f"Vision board item '{item_id}' successfully deleted."}


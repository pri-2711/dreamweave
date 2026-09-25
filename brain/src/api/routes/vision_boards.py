"""
Vision Boards and Vision Board Items API routes.
"""

from fastapi import APIRouter, Depends, status
from brain.src.api.deps import get_current_user_id
from brain.src.schemas.vision_boards import (
    VisionBoardCreate,
    VisionBoardUpdate,
    VisionBoardItemCreate,
    VisionBoardItemUpdate
)
from brain.src import services

router = APIRouter(tags=["Vision Boards"])


# --- Vision Board Routes ---

@router.post("/spaces/{space_id}/vision-boards", status_code=status.HTTP_201_CREATED)
def create_vision_board(
    space_id: str,
    payload: VisionBoardCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a new Vision Board in a space."""
    return services.vision_boards_service.create_vision_board(space_id, payload, current_user_id)


@router.get("/spaces/{space_id}/vision-boards", status_code=status.HTTP_200_OK)
def list_vision_boards(space_id: str):
    """List vision boards in a space."""
    return services.vision_boards_service.list_vision_boards(space_id)


@router.get("/vision-boards/{board_id}", status_code=status.HTTP_200_OK)
def get_vision_board(board_id: str):
    """Get a vision board by ID."""
    return services.vision_boards_service.get_vision_board(board_id)


@router.patch("/vision-boards/{board_id}", status_code=status.HTTP_200_OK)
def update_vision_board(
    board_id: str,
    payload: VisionBoardUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Update vision board settings."""
    return services.vision_boards_service.update_vision_board(board_id, payload, current_user_id)


@router.delete("/vision-boards/{board_id}", status_code=status.HTTP_200_OK)
def delete_vision_board(
    board_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Delete a vision board by ID."""
    return services.vision_boards_service.delete_vision_board(board_id, current_user_id)


# --- Vision Board Items Routes ---

@router.post("/vision-boards/{board_id}/items", status_code=status.HTTP_201_CREATED)
def create_vision_board_item(
    board_id: str,
    payload: VisionBoardItemCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Add an item to a vision board."""
    return services.vision_boards_service.create_vision_board_item(board_id, payload, current_user_id)


@router.get("/vision-boards/{board_id}/items", status_code=status.HTTP_200_OK)
def list_vision_board_items(board_id: str):
    """List all items placed on a vision board."""
    return services.vision_boards_service.list_vision_board_items(board_id)


@router.patch("/vision-board-items/{item_id}", status_code=status.HTTP_200_OK)
def update_vision_board_item(
    item_id: str,
    payload: VisionBoardItemUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Update position, size, rotation, or style of a vision board item."""
    return services.vision_boards_service.update_vision_board_item(item_id, payload, current_user_id)


@router.delete("/vision-board-items/{item_id}", status_code=status.HTTP_200_OK)
def delete_vision_board_item(
    item_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Delete an item from a vision board."""
    return services.vision_boards_service.delete_vision_board_item(item_id, current_user_id)

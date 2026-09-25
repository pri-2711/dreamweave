"""
Document builder models / schema factories for DreamWeave Database Architecture.
Ensures standardized schema structure, UTC datetimes, and ObjectId references across all collections.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from bson import ObjectId


def to_object_id(val: Optional[Union[str, ObjectId]]) -> Optional[ObjectId]:
    """Convert string to ObjectId safely if valid, otherwise return as is or None."""
    if val is None:
        return None
    if isinstance(val, ObjectId):
        return val
    if isinstance(val, str) and len(val) == 24:
        try:
            return ObjectId(val)
        except Exception:
            return None
    return None


def now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


def build_user_doc(
    email: str,
    name: str,
    avatar_url: Optional[str] = None,
    bio: Optional[str] = None,
    password_hash: Optional[str] = None,
    provider: str = "local",
    theme: str = "light",
    language: str = "en"
) -> Dict[str, Any]:
    """Build a document for the `users` collection."""
    now = now_utc()
    return {
        "email": email,
        "profile": {
            "name": name,
            "avatar_url": avatar_url,
            "bio": bio
        },
        "auth": {
            "password_hash": password_hash,
            "provider": provider
        },
        "preferences": {
            "theme": theme,
            "language": language
        },
        "created_at": now,
        "updated_at": now,
        "last_login": None
    }


def build_space_doc(
    owner_id: Union[str, ObjectId],
    name: str,
    description: str = "",
    icon: Optional[str] = None,
    cover_image_url: Optional[str] = None,
    cover_position: Optional[str] = None,
    status: str = "active",
    visibility: str = "private",
    is_favourite: bool = False,
    is_archived: bool = False
) -> Dict[str, Any]:
    """Build a document for the `spaces` collection."""
    now = now_utc()
    return {
        "owner_id": to_object_id(owner_id),
        "name": name,
        "description": description,
        "icon": icon,
        "cover": {
            "image_url": cover_image_url,
            "position": cover_position
        },
        "status": status,
        "settings": {
            "visibility": visibility
        },
        "organization": {
            "is_favourite": is_favourite,
            "is_archived": is_archived
        },
        "created_at": now,
        "updated_at": now
    }


def build_space_member_doc(
    space_id: Union[str, ObjectId],
    user_id: Union[str, ObjectId],
    role: str = "viewer"
) -> Dict[str, Any]:
    """Build a document for the `space_members` collection."""
    return {
        "space_id": to_object_id(space_id),
        "user_id": to_object_id(user_id),
        "role": role,  # owner, editor, viewer
        "joined_at": now_utc()
    }


def build_content_item_doc(
    space_id: Union[str, ObjectId],
    user_id: Union[str, ObjectId],
    type: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    source_kind: str = "upload",
    source_url: Optional[str] = None,
    source_platform: Optional[str] = None,
    asset_id: Optional[Union[str, ObjectId]] = None,
    preview_title: Optional[str] = None,
    preview_description: Optional[str] = None,
    preview_thumbnail_url: Optional[str] = None,
    preview_favicon_url: Optional[str] = None,
    generated_visual_asset_id: Optional[Union[str, ObjectId]] = None,
    tags: Optional[List[str]] = None,
    is_favourite: bool = False,
    is_archived: bool = False,
    legacy_id: Optional[Any] = None
) -> Dict[str, Any]:
    """Build a document for the `content_items` collection."""
    now = now_utc()
    doc = {
        "space_id": to_object_id(space_id),
        "user_id": to_object_id(user_id),
        "type": type,
        "title": title,
        "description": description,
        "source": {
            "kind": source_kind,
            "url": source_url,
            "platform": source_platform
        },
        "asset_id": to_object_id(asset_id),
        "preview": {
            "title": preview_title,
            "description": preview_description,
            "thumbnail_url": preview_thumbnail_url,
            "favicon_url": preview_favicon_url
        },
        "generated_visual": {
            "asset_id": to_object_id(generated_visual_asset_id)
        },
        "tags": tags if tags is not None else [],
        "organization": {
            "is_favourite": is_favourite,
            "is_archived": is_archived
        },
        "created_at": now,
        "updated_at": now
    }
    if legacy_id is not None:
        doc["legacy_id"] = legacy_id
    return doc


def build_asset_doc(
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
    """Build a document for the `assets` collection."""
    return {
        "user_id": to_object_id(user_id),
        "space_id": to_object_id(space_id),
        "content_id": to_object_id(content_id),
        "filename": filename,
        "mime_type": mime_type,
        "size": size,
        "storage": {
            "provider": storage_provider,
            "path": storage_path,
            "url": storage_url
        },
        "created_at": now_utc()
    }


def build_knowledge_doc(
    space_id: Union[str, ObjectId],
    content_id: Union[str, ObjectId],
    source_type: str,
    raw_text: str,
    clean_text: str = "",
    ocr_used: bool = False,
    page_count: Optional[int] = None,
    language: Optional[str] = None,
    ocr_engine: Optional[str] = None,
    legacy_id: Optional[Any] = None
) -> Dict[str, Any]:
    """Build a document for the `knowledge` collection."""
    now = now_utc()
    doc = {
        "space_id": to_object_id(space_id),
        "content_id": to_object_id(content_id),
        "source_type": source_type,
        "raw_text": raw_text,
        "clean_text": clean_text,
        "metadata": {
            "ocr_used": ocr_used,
            "page_count": page_count,
            "language": language,
            "ocr_engine": ocr_engine
        },
        "created_at": now,
        "updated_at": now
    }
    if legacy_id is not None:
        doc["legacy_id"] = legacy_id
    return doc


def build_chunk_doc(
    space_id: Union[str, ObjectId],
    knowledge_id: Union[str, ObjectId],
    content_id: Union[str, ObjectId],
    chunk_index: int,
    text: str,
    embedding: Optional[List[float]] = None,
    page: Optional[int] = None,
    legacy_chunk_id: Optional[str] = None
) -> Dict[str, Any]:
    """Build a document for the `chunks` collection."""
    doc = {
        "space_id": to_object_id(space_id),
        "knowledge_id": to_object_id(knowledge_id),
        "content_id": to_object_id(content_id),
        "chunk_index": chunk_index,
        "text": text,
        "embedding": embedding if embedding is not None else [],
        "metadata": {
            "page": page
        },
        "created_at": now_utc()
    }
    if legacy_chunk_id is not None:
        doc["legacy_chunk_id"] = legacy_chunk_id
    return doc


def build_ai_content_doc(
    space_id: Union[str, ObjectId],
    user_id: Union[str, ObjectId],
    type: str,
    content: Union[str, dict, list],
    title: Optional[str] = None,
    source_content_ids: Optional[List[Union[str, ObjectId]]] = None,
    source_knowledge_ids: Optional[List[Union[str, ObjectId]]] = None,
    asset_id: Optional[Union[str, ObjectId]] = None,
    is_favourite: bool = False,
    is_archived: bool = False
) -> Dict[str, Any]:
    """Build a document for the `ai_content` collection."""
    now = now_utc()
    src_content_ids = [to_object_id(cid) for cid in (source_content_ids or []) if to_object_id(cid)]
    src_knowledge_ids = [to_object_id(kid) for kid in (source_knowledge_ids or []) if to_object_id(kid)]

    return {
        "space_id": to_object_id(space_id),
        "user_id": to_object_id(user_id),
        "type": type,
        "title": title,
        "content": content,
        "context": {
            "source_content_ids": src_content_ids,
            "source_knowledge_ids": src_knowledge_ids
        },
        "asset_id": to_object_id(asset_id),
        "organization": {
            "is_favourite": is_favourite,
            "is_archived": is_archived
        },
        "created_at": now,
        "updated_at": now
    }


def build_ai_generation_doc(
    user_id: Union[str, ObjectId],
    type: str,
    space_id: Optional[Union[str, ObjectId]] = None,
    model: Optional[str] = None,
    prompt: Optional[str] = None,
    input_content_ids: Optional[List[Union[str, ObjectId]]] = None,
    result_content_id: Optional[Union[str, ObjectId]] = None,
    credits: int = 1
) -> Dict[str, Any]:
    """Build a document for the `ai_generations` collection."""
    inp_content_ids = [to_object_id(cid) for cid in (input_content_ids or []) if to_object_id(cid)]
    return {
        "user_id": to_object_id(user_id),
        "space_id": to_object_id(space_id),
        "type": type,
        "model": model,
        "prompt": prompt,
        "input_content_ids": inp_content_ids,
        "result_content_id": to_object_id(result_content_id),
        "usage": {
            "credits": credits
        },
        "created_at": now_utc()
    }


def build_vision_board_doc(
    space_id: Union[str, ObjectId],
    name: str,
    width: int = 1920,
    height: int = 1080
) -> Dict[str, Any]:
    """Build a document for the `vision_boards` collection."""
    now = now_utc()
    return {
        "space_id": to_object_id(space_id),
        "name": name,
        "canvas": {
            "width": width,
            "height": height
        },
        "created_at": now,
        "updated_at": now
    }


def build_vision_board_item_doc(
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
    """Build a document for the `vision_board_items` collection."""
    now = now_utc()
    return {
        "vision_board_id": to_object_id(vision_board_id),
        "content_id": to_object_id(content_id),
        "ai_content_id": to_object_id(ai_content_id),
        "position": {
            "x": float(x),
            "y": float(y)
        },
        "size": {
            "width": float(width),
            "height": float(height)
        },
        "rotation": float(rotation),
        "z_index": int(z_index),
        "style": {
            "border_radius": border_radius
        },
        "created_at": now,
        "updated_at": now
    }


def build_plan_doc(
    space_id: Union[str, ObjectId],
    user_id: Union[str, ObjectId],
    title: str,
    description: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: str = "draft"
) -> Dict[str, Any]:
    """Build a document for the `plans` collection."""
    now = now_utc()
    return {
        "space_id": to_object_id(space_id),
        "user_id": to_object_id(user_id),
        "title": title,
        "description": description,
        "start_date": start_date,
        "end_date": end_date,
        "status": status,  # draft, active, completed, archived
        "created_at": now,
        "updated_at": now
    }


def build_task_doc(
    plan_id: Union[str, ObjectId],
    space_id: Union[str, ObjectId],
    title: str,
    description: Optional[str] = None,
    status: str = "todo",
    priority: str = "medium",
    due_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Build a document for the `tasks` collection."""
    now = now_utc()
    return {
        "plan_id": to_object_id(plan_id),
        "space_id": to_object_id(space_id),
        "title": title,
        "description": description,
        "status": status,  # todo, in_progress, completed
        "priority": priority,  # low, medium, high
        "due_date": due_date,
        "created_at": now,
        "updated_at": now
    }


def build_conversation_doc(
    space_id: Union[str, ObjectId],
    user_id: Union[str, ObjectId],
    title: str
) -> Dict[str, Any]:
    """Build a document for the `conversations` collection."""
    now = now_utc()
    return {
        "space_id": to_object_id(space_id),
        "user_id": to_object_id(user_id),
        "title": title,
        "created_at": now,
        "updated_at": now
    }


def build_message_doc(
    conversation_id: Union[str, ObjectId],
    role: str,
    content: str,
    content_ids: Optional[List[Union[str, ObjectId]]] = None,
    knowledge_ids: Optional[List[Union[str, ObjectId]]] = None,
    generated_content_ids: Optional[List[Union[str, ObjectId]]] = None
) -> Dict[str, Any]:
    """Build a document for the `messages` collection."""
    cnt_ids = [to_object_id(i) for i in (content_ids or []) if to_object_id(i)]
    knw_ids = [to_object_id(i) for i in (knowledge_ids or []) if to_object_id(i)]
    gen_ids = [to_object_id(i) for i in (generated_content_ids or []) if to_object_id(i)]

    return {
        "conversation_id": to_object_id(conversation_id),
        "role": role,  # user, assistant, system
        "content": content,
        "context": {
            "content_ids": cnt_ids,
            "knowledge_ids": knw_ids
        },
        "generated_content_ids": gen_ids,
        "created_at": now_utc()
    }


def build_activity_doc(
    space_id: Union[str, ObjectId],
    user_id: Union[str, ObjectId],
    action: str,
    target_type: str,
    target_id: Union[str, ObjectId]
) -> Dict[str, Any]:
    """Build a document for the `activity` collection."""
    return {
        "space_id": to_object_id(space_id),
        "user_id": to_object_id(user_id),
        "action": action,
        "target": {
            "type": target_type,
            "id": to_object_id(target_id)
        },
        "created_at": now_utc()
    }

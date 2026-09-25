"""
Repository for `plans` and `tasks` collections.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from bson import ObjectId
from brain.src.database.collections import (
    COLLECTION_PLANS,
    COLLECTION_TASKS,
    get_collection
)
from brain.src.database.models import (
    build_plan_doc,
    build_task_doc,
    to_object_id,
    now_utc
)


def create_plan(
    space_id: Union[str, ObjectId],
    user_id: Union[str, ObjectId],
    title: str,
    description: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: str = "draft"
) -> Dict[str, Any]:
    """Create and insert a structured plan."""
    coll = get_collection(COLLECTION_PLANS)
    doc = build_plan_doc(
        space_id=space_id,
        user_id=user_id,
        title=title,
        description=description,
        start_date=start_date,
        end_date=end_date,
        status=status
    )
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_plan_by_id(plan_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
    """Find a plan by _id."""
    oid = to_object_id(plan_id)
    if not oid:
        return None
    coll = get_collection(COLLECTION_PLANS)
    return coll.find_one({"_id": oid})


def list_plans_by_space(space_id: Union[str, ObjectId]) -> List[Dict[str, Any]]:
    """List plans in a space."""
    sid = to_object_id(space_id)
    if not sid:
        return []
    coll = get_collection(COLLECTION_PLANS)
    return list(coll.find({"space_id": sid}).sort("created_at", -1))


def create_task(
    plan_id: Union[str, ObjectId],
    space_id: Union[str, ObjectId],
    title: str,
    description: Optional[str] = None,
    status: str = "todo",
    priority: str = "medium",
    due_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Create an actionable task item in a plan."""
    coll = get_collection(COLLECTION_TASKS)
    doc = build_task_doc(
        plan_id=plan_id,
        space_id=space_id,
        title=title,
        description=description,
        status=status,
        priority=priority,
        due_date=due_date
    )
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def list_tasks_by_plan(plan_id: Union[str, ObjectId]) -> List[Dict[str, Any]]:
    """List tasks belonging to a plan."""
    pid = to_object_id(plan_id)
    if not pid:
        return []
    coll = get_collection(COLLECTION_TASKS)
    return list(coll.find({"plan_id": pid}).sort("created_at", 1))


def update_task(task_id: Union[str, ObjectId], updates: Dict[str, Any]) -> bool:
    """Update fields of a task."""
    oid = to_object_id(task_id)
    if not oid:
        return False
    updates["updated_at"] = now_utc()
    coll = get_collection(COLLECTION_TASKS)
    result = coll.update_one({"_id": oid}, {"$set": updates})
    return result.modified_count > 0

"""
Business logic service for Plans and Tasks.
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from brain.src.database.repositories import plans as plans_repo
from brain.src.database.repositories import spaces as spaces_repo
from brain.src.database.repositories import activity as activity_repo
from brain.src.schemas.plans import PlanCreate, PlanUpdate, TaskCreate, TaskUpdate
from brain.src.utils.serialization import parse_object_id, serialize_doc, serialize_docs


def create_plan(space_id: str, data: PlanCreate, current_user_id: str) -> Dict[str, Any]:
    """Create a structured plan for a space."""
    sid = parse_object_id(space_id, param_name="space_id")
    space = spaces_repo.get_space_by_id(sid)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space with id '{space_id}' not found."
        )

    uid = parse_object_id(current_user_id, param_name="user_id")
    doc = plans_repo.create_plan(
        space_id=sid,
        user_id=uid,
        title=data.title.strip(),
        description=data.description,
        start_date=data.start_date,
        end_date=data.end_date,
        status=data.status or "draft"
    )

    activity_repo.log_activity(
        space_id=sid,
        user_id=uid,
        action="plan_created",
        target_type="plan",
        target_id=doc["_id"]
    )

    return serialize_doc(doc)


def list_plans(space_id: str) -> List[Dict[str, Any]]:
    """List plans in a space."""
    sid = parse_object_id(space_id, param_name="space_id")
    plans = plans_repo.list_plans_by_space(sid)
    return serialize_docs(plans)


def get_plan(plan_id: str) -> Dict[str, Any]:
    """Get a plan by ID."""
    pid = parse_object_id(plan_id, param_name="plan_id")
    plan = plans_repo.get_plan_by_id(pid)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan with id '{plan_id}' not found."
        )
    return serialize_doc(plan)


def update_plan(plan_id: str, data: PlanUpdate, current_user_id: str) -> Dict[str, Any]:
    """Update fields of a plan."""
    pid = parse_object_id(plan_id, param_name="plan_id")
    existing = plans_repo.get_plan_by_id(pid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan with id '{plan_id}' not found."
        )

    updates = {}
    if data.title is not None:
        updates["title"] = data.title.strip()
    if data.description is not None:
        updates["description"] = data.description
    if data.start_date is not None:
        updates["start_date"] = data.start_date
    if data.end_date is not None:
        updates["end_date"] = data.end_date
    if data.status is not None:
        updates["status"] = data.status

    if updates:
        from brain.src.database.collections import COLLECTION_PLANS, get_collection
        from brain.src.database.models import now_utc
        updates["updated_at"] = now_utc()
        get_collection(COLLECTION_PLANS).update_one({"_id": pid}, {"$set": updates})

    updated_plan = plans_repo.get_plan_by_id(pid)
    return serialize_doc(updated_plan)


def delete_plan(plan_id: str, current_user_id: str) -> Dict[str, Any]:
    """Delete a plan and its tasks."""
    pid = parse_object_id(plan_id, param_name="plan_id")
    existing = plans_repo.get_plan_by_id(pid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan with id '{plan_id}' not found."
        )

    from brain.src.database.collections import (
        COLLECTION_PLANS,
        COLLECTION_TASKS,
        get_collection
    )
    get_collection(COLLECTION_TASKS).delete_many({"plan_id": pid})
    get_collection(COLLECTION_PLANS).delete_one({"_id": pid})
    return {"message": f"Plan '{plan_id}' successfully deleted."}


def create_task(plan_id: str, data: TaskCreate, current_user_id: str) -> Dict[str, Any]:
    """Create an actionable task item inside a plan."""
    pid = parse_object_id(plan_id, param_name="plan_id")
    plan = plans_repo.get_plan_by_id(pid)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan with id '{plan_id}' not found."
        )

    sid = parse_object_id(data.space_id, param_name="space_id") if data.space_id else plan.get("space_id")

    doc = plans_repo.create_task(
        plan_id=pid,
        space_id=sid,
        title=data.title.strip(),
        description=data.description,
        status=data.status or "todo",
        priority=data.priority or "medium",
        due_date=data.due_date
    )

    return serialize_doc(doc)


def list_tasks(plan_id: str) -> List[Dict[str, Any]]:
    """List tasks belonging to a plan."""
    pid = parse_object_id(plan_id, param_name="plan_id")
    tasks = plans_repo.list_tasks_by_plan(pid)
    return serialize_docs(tasks)


def update_task(task_id: str, data: TaskUpdate, current_user_id: str) -> Dict[str, Any]:
    """Update fields of a task."""
    tid = parse_object_id(task_id, param_name="task_id")
    from brain.src.database.collections import COLLECTION_TASKS, get_collection
    coll = get_collection(COLLECTION_TASKS)
    existing = coll.find_one({"_id": tid})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found."
        )

    updates = {}
    if data.title is not None:
        updates["title"] = data.title.strip()
    if data.description is not None:
        updates["description"] = data.description
    if data.status is not None:
        updates["status"] = data.status
    if data.priority is not None:
        updates["priority"] = data.priority
    if data.due_date is not None:
        updates["due_date"] = data.due_date

    if updates:
        plans_repo.update_task(tid, updates)

    updated_task = coll.find_one({"_id": tid})
    return serialize_doc(updated_task)


def delete_task(task_id: str, current_user_id: str) -> Dict[str, Any]:
    """Delete a task by ID."""
    tid = parse_object_id(task_id, param_name="task_id")
    from brain.src.database.collections import COLLECTION_TASKS, get_collection
    coll = get_collection(COLLECTION_TASKS)
    existing = coll.find_one({"_id": tid})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found."
        )

    coll.delete_one({"_id": tid})
    return {"message": f"Task '{task_id}' successfully deleted."}

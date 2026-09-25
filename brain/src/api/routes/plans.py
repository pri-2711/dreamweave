"""
Plans and Tasks API routes.
"""

from fastapi import APIRouter, Depends, status
from brain.src.api.deps import get_current_user_id
from brain.src.schemas.plans import PlanCreate, PlanUpdate, TaskCreate, TaskUpdate
from brain.src import services

router = APIRouter(tags=["Plans & Tasks"])


# --- Plan Routes ---

@router.post("/spaces/{space_id}/plans", status_code=status.HTTP_201_CREATED)
def create_plan(
    space_id: str,
    payload: PlanCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a new plan in a space."""
    return services.plans_service.create_plan(space_id, payload, current_user_id)


@router.get("/spaces/{space_id}/plans", status_code=status.HTTP_200_OK)
def list_plans(space_id: str):
    """List all plans in a space."""
    return services.plans_service.list_plans(space_id)


@router.get("/plans/{plan_id}", status_code=status.HTTP_200_OK)
def get_plan(plan_id: str):
    """Get a plan by ID."""
    return services.plans_service.get_plan(plan_id)


@router.patch("/plans/{plan_id}", status_code=status.HTTP_200_OK)
def update_plan(
    plan_id: str,
    payload: PlanUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Update a plan by ID."""
    return services.plans_service.update_plan(plan_id, payload, current_user_id)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_200_OK)
def delete_plan(
    plan_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Delete a plan by ID."""
    return services.plans_service.delete_plan(plan_id, current_user_id)


# --- Task Routes ---

@router.post("/plans/{plan_id}/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    plan_id: str,
    payload: TaskCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Create an actionable task item inside a plan."""
    return services.plans_service.create_task(plan_id, payload, current_user_id)


@router.get("/plans/{plan_id}/tasks", status_code=status.HTTP_200_OK)
def list_tasks(plan_id: str):
    """List tasks belonging to a plan."""
    return services.plans_service.list_tasks(plan_id)


@router.patch("/tasks/{task_id}", status_code=status.HTTP_200_OK)
def update_task(
    task_id: str,
    payload: TaskUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Update fields of a task."""
    return services.plans_service.update_task(task_id, payload, current_user_id)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_200_OK)
def delete_task(
    task_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Delete a task by ID."""
    return services.plans_service.delete_task(task_id, current_user_id)

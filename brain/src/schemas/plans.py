"""
Pydantic schemas for Plans and Tasks APIs.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PlanCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Plan title")
    description: Optional[str] = Field(default=None, description="Plan description")
    start_date: Optional[datetime] = Field(default=None, description="Plan start date")
    end_date: Optional[datetime] = Field(default=None, description="Plan end date")
    status: str = Field(default="draft", description="Plan status: draft, active, completed, archived")


class PlanUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None


class TaskCreate(BaseModel):
    space_id: Optional[str] = Field(default=None, description="Space ObjectId")
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    status: str = Field(default="todo", description="Task status: todo, in_progress, completed")
    priority: str = Field(default="medium", description="Priority: low, medium, high")
    due_date: Optional[datetime] = Field(default=None, description="Due date")


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None

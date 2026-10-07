"""班级任务相关模型（class_tasks / class_task_completions）。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Timestamp


class TaskCreate(BaseModel):
    class_id: int = Field(..., description="所属班级 ID")
    task_type: str = Field("reading", description="reading/practice/project/lab")
    content: str = Field(..., min_length=1)
    deadline: Optional[datetime] = None


class TaskUpdate(BaseModel):
    task_type: Optional[str] = None
    content: Optional[str] = None
    deadline: Optional[datetime] = None


class TaskCompletionOut(BaseModel):
    student_id: int
    uid: str
    name: str
    completed_at: Optional[datetime] = None
    completed: bool = False


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    class_id: int
    task_type: str
    content: str
    deadline: Optional[datetime] = None
    status: int
    created_by: Optional[str] = None
    created_at: Timestamp
    total_students: int = 0
    completed_count: int = 0

"""学习任务相关模型。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    task_type: str = Field("other", pattern="^(knowledge_point|oj|acdc|other)$")
    deadline: Optional[datetime] = None
    course_id: Optional[int] = None
    student_ids: list[int] = Field(..., min_length=1, description="指派学生 ID 列表")


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    task_type: Optional[str] = Field(None, pattern="^(knowledge_point|oj|acdc|other)$")
    deadline: Optional[datetime] = None


class TaskAssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: int
    name: str
    username: str
    status: str
    completed_at: Optional[datetime] = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    task_type: str
    deadline: Optional[datetime] = None
    created_by: int
    created_at: datetime
    student_count: int = 0
    completed_count: int = 0
    assignments: list[TaskAssignmentOut] = []

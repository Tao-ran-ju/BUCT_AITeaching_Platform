"""班级相关模型。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ClassCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    grade: Optional[str] = None
    major: Optional[str] = None
    description: Optional[str] = None
    teacher_id: Optional[int] = None


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    grade: Optional[str] = None
    major: Optional[str] = None
    description: Optional[str] = None
    teacher_id: Optional[int] = None


class ClassOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    grade: Optional[str] = None
    major: Optional[str] = None
    description: Optional[str] = None
    teacher_id: Optional[int] = None
    created_at: datetime


class StudentAddRequest(BaseModel):
    """批量添加学生到班级。"""

    student_ids: list[int] = Field(..., min_length=1)

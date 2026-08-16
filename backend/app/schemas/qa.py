"""AI 问答助手相关模型。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class QaAskIn(BaseModel):
    """学生提问（由学生端网关调用，已通过学生端认证）。"""
    student_id: int
    student_name: str = Field(..., min_length=1, max_length=100)
    course_id: Optional[int] = None
    content: str = Field(..., min_length=1, max_length=5000)


class QaAnswerIn(BaseModel):
    answer: str = Field(..., min_length=1, max_length=5000)


class QaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    student_name: str
    course_id: Optional[int] = None
    content: str
    status: str
    classification: Optional[str] = None
    auto_answer: Optional[str] = None
    teacher_answer: Optional[str] = None
    answered_by: Optional[int] = None
    created_at: datetime
    answered_at: Optional[datetime] = None

"""AI 问答助手相关模型。"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Timestamp


class QaAskIn(BaseModel):
    """学生提问（由学生端网关调用，已通过学生端认证）。"""

    student_id: int = Field(..., description="提问学生 user_rft.id")
    course_id: Optional[int] = None
    question: str = Field(..., min_length=1, max_length=5000)


class QaAnswerIn(BaseModel):
    answer: str = Field(..., min_length=1, max_length=5000)


class QaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    course_id: Optional[int] = None
    question: str
    answer: Optional[str] = None
    answered_by: Optional[int] = None
    answered_at: Optional[Timestamp] = None
    status: int
    created_at: Timestamp

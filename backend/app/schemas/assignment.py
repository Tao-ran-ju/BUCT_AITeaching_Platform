"""作业与提交相关模型。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AssignmentCreate(BaseModel):
    course_id: int
    class_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = None
    question_ids: Optional[list[int]] = None
    oj_problem_id: Optional[int] = None
    oj_language: Optional[str] = None
    deadline: Optional[datetime] = None


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    class_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    question_ids: Optional[str] = None
    oj_problem_id: Optional[int] = None
    oj_language: Optional[str] = None
    deadline: Optional[datetime] = None
    status: str
    created_at: datetime


class SubmissionCreate(BaseModel):
    assignment_id: int
    content: str = Field(..., min_length=1)


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assignment_id: int
    student_id: int
    content: Optional[str] = None
    submit_time: datetime
    judge_status: str
    oj_solution_id: Optional[int] = None
    score: Optional[float] = None
    ai_comment: Optional[str] = None
    plagiarism_rate: Optional[float] = None

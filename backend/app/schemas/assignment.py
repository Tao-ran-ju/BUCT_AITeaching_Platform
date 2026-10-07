"""作业与提交相关模型。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import Timestamp


class AssignmentCreate(BaseModel):
    course_id: Optional[int] = None
    class_id: int = Field(..., description="所属班级 ID（必填）")
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    deadline: Optional[datetime] = None
    oj_problem_id: Optional[int] = Field(None, description="关联 OJ 题目 ID（可选）")
    oj_language: Optional[str] = Field(None, description="OJ 判题语言")


class AssignmentOut(BaseModel):
    id: int
    course_id: Optional[int] = None
    class_id: int
    title: str
    content: str
    deadline: Optional[datetime] = None
    status: int
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_size: Optional[int] = None
    total_students: int = 0
    submitted_count: int = 0
    oj_problem_id: Optional[int] = None
    oj_language: Optional[str] = None
    class_name: Optional[str] = None
    course_name: Optional[str] = None
    created_at: Timestamp


class SubmissionOut(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    student_uid: Optional[str] = None
    student_name: Optional[str] = None
    content: Optional[str] = None
    attachment_url: Optional[str] = None
    submit_time: datetime
    status: int
    score: Optional[float] = None
    feedback: Optional[str] = None
    judge_status: str = "pending"
    ai_comment: Optional[str] = None
    plagiarism_rate: Optional[float] = None
    oj_solution_id: Optional[int] = None

"""学生端（对接学校学生端）相关响应模型。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.common import Timestamp


class StudentSubmissionOut(BaseModel):
    """学生视角：本人某作业的提交结果。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    submit_time: datetime
    judge_status: str
    score: Optional[float] = None
    feedback: Optional[str] = None
    plagiarism_rate: Optional[float] = None


class StudentAssignmentOut(BaseModel):
    """学生视角：一条作业（含所属课程 / 班级信息与本人提交状态）。"""

    id: int
    title: str
    content: Optional[str] = None
    deadline: Optional[datetime] = None
    status: int
    course_id: Optional[int] = None
    course_name: Optional[str] = None
    class_id: Optional[int] = None
    class_name: Optional[str] = None
    created_at: Timestamp
    submitted: bool
    my_submission: Optional[StudentSubmissionOut] = None


class StudentClassOut(BaseModel):
    """学生视角：本人所属班级。"""

    id: int
    name: str
    course: Optional[str] = None
    private: int = 0
    created_at: Timestamp

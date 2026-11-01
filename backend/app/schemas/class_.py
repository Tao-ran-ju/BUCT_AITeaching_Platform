"""班级相关模型。"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Timestamp


class ClassCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    course_id: Optional[int] = Field(None, description="关联课程 ID（可选，建立 course_classes 关联）")
    private: int = Field(0, description="0=公开 1=私有")


class ClassUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    private: Optional[int] = None


class ClassOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    course: Optional[str] = None
    private: int
    status: int
    created_by: Optional[str] = None
    created_at: Timestamp
    course_id: Optional[int] = None       # 由 course_classes 关联得出
    teacher_user_id: Optional[int] = None  # 授课教师 user_rft.id
    student_count: int = 0


class ClassStudentOut(BaseModel):
    """班级学生出参。"""

    id: Optional[int] = None
    uid: str
    name: str
    registered: bool = False
    college: str = ""
    class_name: Optional[str] = None
    major: Optional[str] = None


class StudentItem(BaseModel):
    """单个待添加学生（学号 + 可选姓名）。"""

    uid: int = Field(..., description="学号")
    name: Optional[str] = Field(None, description="姓名")


class StudentAddRequest(BaseModel):
    """添加学生到班级（学号+姓名列表，不自动建档）。"""

    students: list[StudentItem] = Field(..., min_length=1, description="学生列表")

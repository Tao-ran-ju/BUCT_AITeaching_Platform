"""课程 / 知识图谱相关模型。"""
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Timestamp


class CourseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[int] = Field(None, description="0=草稿 1=已发布 100=已归档")


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    teacher_user_id: int
    status: int
    created_by: Optional[str] = None
    legacy_id: Optional[str] = None
    created_at: Timestamp
    edited_at: Timestamp


class KnowledgeGraphOut(BaseModel):
    """课程知识图谱出参（graph_data 已解析为 dict）。"""

    id: int
    course_id: int
    graph_data: Any
    created_at: Timestamp
    edited_at: Timestamp


class KnowledgeGraphUpsert(BaseModel):
    graph_data: dict = Field(..., description="知识图谱 JSON（nodes/edges）")

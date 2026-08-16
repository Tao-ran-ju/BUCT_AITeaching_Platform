"""课程 / 章节 / 知识点相关模型。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CourseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    code: Optional[str] = None
    cover: Optional[str] = None
    description: Optional[str] = None
    open_time: Optional[datetime] = None


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    cover: Optional[str] = None
    description: Optional[str] = None
    open_time: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: Optional[str] = None
    cover: Optional[str] = None
    description: Optional[str] = None
    open_time: Optional[datetime] = None
    teacher_id: int
    status: str
    created_at: datetime


class ChapterCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = None
    sort_order: int = 0


class ChapterUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    sort_order: Optional[int] = None


class ChapterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    title: str
    description: Optional[str] = None
    sort_order: int


class KnowledgePointCreate(BaseModel):
    chapter_id: int
    parent_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = None
    sort_order: int = 0


class KnowledgePointUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    sort_order: Optional[int] = None


class KnowledgePointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chapter_id: int
    parent_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    ai_summary: Optional[str] = None
    sort_order: int

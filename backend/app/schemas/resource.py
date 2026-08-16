"""教学资源相关模型。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    resource_type: str
    file_path: str
    file_size: Optional[int] = None
    course_id: Optional[int] = None
    uploader_id: int
    visibility: str
    summary: Optional[str] = None
    keywords: Optional[str] = None
    duration: Optional[float] = None
    thumbnail_path: Optional[str] = None
    transcoded_path: Optional[str] = None
    created_at: datetime


class ResourceVisibilityUpdate(BaseModel):
    visibility: str = Field(..., pattern="^(public|course|private)$")

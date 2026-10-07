"""教学资源相关模型。"""
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.common import Timestamp


class ResourceOut(BaseModel):
    """资源出参（metadata 由 metadata_json 解析而来）。"""

    id: int
    course_id: Optional[int] = None
    name: str
    type: str
    file_path: str
    file_size: int
    permission: str
    status: int
    created_by: Optional[str] = None
    metadata: Any = None
    created_at: Timestamp


class ResourceVisibilityUpdate(BaseModel):
    visibility: str = Field(..., pattern="^(public|course|private)$")

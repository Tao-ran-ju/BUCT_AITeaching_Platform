"""学习小组相关模型。"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Timestamp


class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    course_id: int = Field(..., description="所属课程 ID")
    description: Optional[str] = None
    leader_id: Optional[int] = Field(None, description="组长 user_rft.id")


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    leader_id: Optional[int] = None
    course_id: Optional[int] = None


class TeamMemberOut(BaseModel):
    student_id: int
    uid: str
    name: str


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    course_id: int
    leader_id: Optional[int] = None
    description: Optional[str] = None
    created_at: Timestamp
    member_count: int = 0
    members: list[TeamMemberOut] = []


class MemberAddRequest(BaseModel):
    student_ids: list[int] = Field(..., min_length=1, description="学生 user_rft.id 列表")

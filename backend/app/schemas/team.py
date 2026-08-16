"""学习小组 / 竞赛队伍相关模型。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    course_id: Optional[int] = None
    leader_id: int = Field(..., description="组长（学生）ID")
    description: Optional[str] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    course_id: Optional[int] = None
    leader_id: Optional[int] = None
    description: Optional[str] = None


class TeamMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: int
    name: str
    username: str


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    course_id: Optional[int] = None
    leader_id: int
    description: Optional[str] = None
    created_at: datetime
    member_count: int = 0
    members: list[TeamMemberOut] = []


class MemberAddRequest(BaseModel):
    student_ids: list[int] = Field(..., min_length=1)

"""学习社群表：学习小组 / 竞赛队伍 + 成员关系。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Team(Base):
    __tablename__ = "team"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("course.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    leader_id: Mapped[int] = mapped_column(ForeignKey("user.id"), comment="组长/队长")
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class TeamMember(Base):
    __tablename__ = "team_member"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("team.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

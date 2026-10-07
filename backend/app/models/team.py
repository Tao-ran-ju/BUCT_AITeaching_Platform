"""学习小组模型（教师端自有表）：小组 + 成员关系。"""
from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Team(Base):
    """学习小组（t_team）。"""

    __tablename__ = "t_team"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="课程 ID")
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="小组名称")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="小组描述")
    leader_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="组长 user_rft.id")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="创建时间")
    edited_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="最后编辑时间")


class TeamMember(Base):
    """小组-成员关系（t_team_member）。"""

    __tablename__ = "t_team_member"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="小组 ID")
    student_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="学生 user_rft.id")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="加入时间")

"""学情预警模型（教师端自有表）：预警记录 + 学习行为日志。"""
from sqlalchemy import BigInteger, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StudentWarning(Base):
    """学情预警记录（t_student_warning）。"""

    __tablename__ = "t_student_warning"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True, comment="关联课程 ID")
    student_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="学生 user_rft.id")
    warning_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="submit_delay/absent/low_score")
    level: Mapped[str] = mapped_column(String(20), nullable=False, default="normal", comment="normal/warning/danger")
    detail: Mapped[str | None] = mapped_column(Text, nullable=True, comment="预警详情")
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True, comment="AI 干预建议")
    intervention: Mapped[str | None] = mapped_column(Text, nullable=True, comment="教师干预措施记录")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", comment="open/resolved")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="创建时间")
    resolved_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="处理时间")


class StudyBehavior(Base):
    """学习行为日志（t_study_behavior）。"""

    __tablename__ = "t_study_behavior"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="学生 user_rft.id")
    course_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True, comment="课程 ID")
    behavior_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="login/resource_view/submit")
    value: Mapped[str | None] = mapped_column(Text, nullable=True, comment="行为附加数据（JSON）")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="发生时间（UNIX 时间戳）")

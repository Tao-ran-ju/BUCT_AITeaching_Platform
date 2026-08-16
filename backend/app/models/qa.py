"""AI 问答助手表：接收学生提问，简单问题自动回复，复杂问题转教师人工处理。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class QaQuestion(Base):
    __tablename__ = "qa_question"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, index=True, comment="提问学生ID")
    student_name: Mapped[str] = mapped_column(String(100), comment="提问学生姓名")
    course_id: Mapped[int | None] = mapped_column(ForeignKey("course.id"), comment="关联课程（可选）")
    content: Mapped[str] = mapped_column(Text, comment="问题内容")
    status: Mapped[str] = mapped_column(
        String(16), default="pending", comment="pending/auto_answered/answered"
    )
    classification: Mapped[str | None] = mapped_column(
        String(16), comment="simple(简单，自动回复)/complex(复杂，转教师)"
    )
    auto_answer: Mapped[str | None] = mapped_column(Text, comment="AI 自动回复内容")
    teacher_answer: Mapped[str | None] = mapped_column(Text, comment="教师人工回复内容")
    answered_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), comment="回复教师ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="提问时间")
    answered_at: Mapped[datetime | None] = mapped_column(DateTime, comment="回复时间")

"""题库表：题目 / 题型 / 难度 / 知识点 / 答案与解析。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Question(Base):
    __tablename__ = "question"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), comment="题目标题/题干")
    question_type: Mapped[str] = mapped_column(
        String(32), default="choice", comment="choice/fill/true_false/code"
    )
    content: Mapped[str | None] = mapped_column(Text, comment="详细题干")
    answer: Mapped[str | None] = mapped_column(Text, comment="标准答案")
    analysis: Mapped[str | None] = mapped_column(Text, comment="解析")
    difficulty: Mapped[int] = mapped_column(Integer, default=3, comment="1-5")
    knowledge_point_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_point.id"), index=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("course.id"), index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("user.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

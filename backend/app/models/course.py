"""课程表：课程 - 章节 - 知识点三级树状结构，支撑知识图谱。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Course(Base):
    __tablename__ = "course"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), index=True, comment="课程名称")
    code: Mapped[str | None] = mapped_column(String(32), comment="课程编号")
    cover: Mapped[str | None] = mapped_column(String(255), comment="封面图路径")
    description: Mapped[str | None] = mapped_column(Text)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, comment="主讲教师")
    status: Mapped[str] = mapped_column(String(16), default="published", comment="draft/published/archived")
    open_time: Mapped[datetime | None] = mapped_column(DateTime, comment="课程开放时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Chapter(Base):
    __tablename__ = "chapter"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"), index=True)
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class KnowledgePoint(Base):
    __tablename__ = "knowledge_point"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapter.id"), index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_point.id"), comment="父知识点，支持多级")
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)
    ai_summary: Mapped[str | None] = mapped_column(Text, comment="AI 生成的知识点梗概")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

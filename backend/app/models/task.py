"""学习任务表：教师发布任务（知识点 / OJ 题 / ACDC 等），学生完成后标记。

一对多结构：
    task            存任务本身（标题、类型、截止时间等）
    task_assignment 存每个被指派学生一行，记录完成状态与完成时间
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("course.id"), index=True)
    title: Mapped[str] = mapped_column(String(200), comment="任务标题")
    description: Mapped[str | None] = mapped_column(Text, comment="任务描述")
    task_type: Mapped[str] = mapped_column(
        String(32), default="other", comment="knowledge_point/oj/acdc/other"
    )
    deadline: Mapped[datetime | None] = mapped_column(DateTime, comment="截止时间")
    created_by: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, comment="发布教师ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class TaskAssignment(Base):
    __tablename__ = "task_assignment"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("task.id", ondelete="CASCADE"), index=True
    )
    student_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    status: Mapped[str] = mapped_column(
        String(16), default="pending", comment="pending/completed"
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, comment="完成时间")

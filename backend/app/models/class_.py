"""班级表：班级 + 班级学生关联（一个学生可属于多个班级）。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ClassRoom(Base):
    """班级。表名 class 在 MySQL 中非保留字，可直接使用。"""

    __tablename__ = "class"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), comment="班级名称")
    grade: Mapped[str | None] = mapped_column(String(16), comment="年级，如 2024")
    major: Mapped[str | None] = mapped_column(String(128), comment="专业")
    description: Mapped[str | None] = mapped_column(String(500))
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), comment="班主任")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ClassStudent(Base):
    """班级-学生关联表，支持一个学生加入多个班级。"""

    __tablename__ = "class_student"
    __table_args__ = (UniqueConstraint("class_id", "student_id", name="uk_class_student"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("class.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

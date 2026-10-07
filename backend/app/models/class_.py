"""班级体系模型：class / class_record / class_notices / class_tasks / class_task_completions。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ClassRoom(Base):
    """教学班级表（class）。表名 class 在 MySQL 中非保留字，可直接使用。"""

    __tablename__ = "class"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=正常")
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="班级名称")
    course: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="关联课程名（冗余字段）")
    private: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=公开 1=私有")
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, comment="创建时间（UNIX 时间戳）")
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="创建者 uid")
    edited_at: Mapped[int] = mapped_column(Integer, nullable=False, comment="最后编辑时间")


class ClassRecord(Base):
    """班级成员记录表（class_record），记录用户属于哪个班级。"""

    __tablename__ = "class_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uid: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="学号/用户 ID")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=正常")
    role: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="0=教师 1=学生")
    class_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="教学班级 ID")
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, comment="加入时间")
    edited_at: Mapped[int] = mapped_column(Integer, nullable=False, comment="最后编辑时间")
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, comment="操作人 uid")


class ClassNotice(Base):
    """班级公告表（class_notices）。"""

    __tablename__ = "class_notices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="所属班级 ID")
    notice_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="general/important/emergency")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="公告正文")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=正常/已发布")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="发布时间")
    edited_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="最后编辑时间")
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="发布者 uid")
    legacy_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, comment="旧系统迁移 ID")


class ClassTask(Base):
    """班级任务表（class_tasks），轻量级任务（阅读/练习/打卡等）。"""

    __tablename__ = "class_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="所属班级 ID")
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="reading/practice/project/lab")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="任务内容/要求")
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="截止时间")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=已发布/进行中")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="发布时间")
    edited_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="最后编辑时间")
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="发布者 uid")
    legacy_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, comment="旧系统迁移 ID")


class ClassTaskCompletion(Base):
    """班级任务完成记录表（class_task_completions），轻量打卡。"""

    __tablename__ = "class_task_completions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="任务 ID")
    student_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="学生 user_rft.id")
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="完成时间")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=已完成")

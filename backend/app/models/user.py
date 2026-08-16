"""用户表：教师 / 学生 / 管理员统一存放，通过 role 区分。"""
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="工号/学号")
    password_hash: Mapped[str] = mapped_column(String(255), comment="PBKDF2 哈希")
    name: Mapped[str] = mapped_column(String(64), comment="姓名")
    role: Mapped[str] = mapped_column(String(16), default="teacher", comment="admin/teacher/student")
    email: Mapped[str | None] = mapped_column(String(128))
    phone: Mapped[str | None] = mapped_column(String(32))
    department: Mapped[str | None] = mapped_column(String(128), comment="所属部门/学院")
    position: Mapped[str | None] = mapped_column(String(64), comment="职称（教师）")
    avatar: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16), default="active", comment="active/disabled")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

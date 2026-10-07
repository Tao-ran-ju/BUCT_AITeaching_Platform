"""用户体系模型：user_rft（新版统一用户表）+ teacher_actors（教师账号表）。"""
from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# 角色常量（user_rft.role）
ROLE_TEACHER = 0
ROLE_STUDENT = 1


class User(Base):
    """统一用户表（user_rft），教师与学生共用，密码为 bcrypt 加密。"""

    __tablename__ = "user_rft"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment="学号/工号（登录账号）")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=正常")
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="状态原因")
    password_hash: Mapped[str] = mapped_column("password", String(255), nullable=False, comment="bcrypt 哈希")
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="真实姓名")
    role: Mapped[int] = mapped_column(Integer, nullable=False, comment="0=教师 1=学生")
    gender: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=男 1=女")
    college: Mapped[str] = mapped_column(String(255), nullable=False, default="", comment="学院名称")
    grade: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="年级（仅学生）")
    class_name: Mapped[str | None] = mapped_column("class", String(255), nullable=True, comment="行政班级（仅学生）")
    major: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="专业（仅学生）")
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, comment="注册时间（UNIX 时间戳）")
    edited_at: Mapped[int] = mapped_column(Integer, nullable=False, comment="最后编辑时间（UNIX 时间戳）")
    created_by: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="创建者 user_rft.id")


class TeacherActor(Base):
    """教师账号表（teacher_actors），轻量教师表，与 user_rft 功能重叠。"""

    __tablename__ = "teacher_actors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment="教师工号/登录账号")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="教师姓名")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=正常")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="创建时间（UNIX 时间戳）")

"""课程体系模型：courses / course_classes / course_students / knowledge_graphs。"""
from sqlalchemy import BigInteger, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Course(Base):
    """课程表（courses），班级、作业、资源的上层容器。"""

    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="课程名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="课程描述")
    teacher_user_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="授课教师 user_rft.id")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=草稿 1=已发布 100=已归档")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="创建时间（UNIX 时间戳）")
    edited_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="最后编辑时间")
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="创建者 uid")
    legacy_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, comment="旧系统迁移 ID")


class CourseClass(Base):
    """课程-班级关联表（course_classes）。"""

    __tablename__ = "course_classes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="课程 ID")
    class_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="教学班级 ID")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="关联创建时间")
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="创建者 uid")


class CourseStudent(Base):
    """课程-学生关联表（course_students），学生直接选课关系。"""

    __tablename__ = "course_students"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="课程 ID")
    student_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="学生 user_rft.id")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=正常/已选")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="选课时间")
    edited_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="最后编辑时间")
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="操作人 uid")


class KnowledgeGraph(Base):
    """课程知识图谱（knowledge_graphs），每门课程一份，JSON 存节点与边。"""

    __tablename__ = "knowledge_graphs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, comment="课程 ID（唯一）")
    graph_data: Mapped[str] = mapped_column(Text, nullable=False, comment="知识图谱 JSON")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="创建时间")
    edited_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="最后编辑时间")
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="创建者 uid")

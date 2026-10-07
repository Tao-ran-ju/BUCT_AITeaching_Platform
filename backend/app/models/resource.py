"""课程资源模型（course_resources），支持权限分级与 JSON 元数据。"""
from sqlalchemy import BigInteger, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Resource(Base):
    """课程资源表（course_resources）。"""

    __tablename__ = "course_resources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True, comment="所属课程 ID（可空=全局资源）")
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="资源名称/文件名")
    type: Mapped[str] = mapped_column(String(50), nullable=False, comment="资源类型 pdf/docx/video/link...")
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="文件存储路径/URL")
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment="文件大小（字节）")
    permission: Mapped[str] = mapped_column(String(50), nullable=False, default="teacher_only", comment="teacher_only/student/public")
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True, comment="扩展元数据 JSON")
    source_resource_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="源资源 ID")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=正常")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="上传时间")
    edited_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="最后编辑时间")
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="上传者 uid")
    legacy_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, comment="旧系统迁移 ID")

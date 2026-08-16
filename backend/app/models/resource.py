"""教学资源表：多格式文件，支持课程级或教师个人库。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Resource(Base):
    __tablename__ = "resource"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(128), comment="资源标题")
    resource_type: Mapped[str] = mapped_column(String(32), comment="document/video/audio/image/code/other")
    file_path: Mapped[str] = mapped_column(String(255), comment="存储相对路径")
    file_size: Mapped[int | None] = mapped_column(BigInteger, comment="字节数")
    course_id: Mapped[int | None] = mapped_column(ForeignKey("course.id"), index=True)
    uploader_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    visibility: Mapped[str] = mapped_column(String(16), default="course", comment="public/course/private")
    summary: Mapped[str | None] = mapped_column(Text, comment="AI 自动摘要")
    keywords: Mapped[str | None] = mapped_column(String(255), comment="AI 提取关键词，逗号分隔")
    duration: Mapped[float | None] = mapped_column(Float, comment="音视频时长（秒）")
    thumbnail_path: Mapped[str | None] = mapped_column(String(255), comment="视频关键帧缩略图相对路径")
    transcoded_path: Mapped[str | None] = mapped_column(String(255), comment="转码后 Web 兼容视频相对路径")
    oss_key: Mapped[str | None] = mapped_column(String(255), comment="已镜像到 OSS 的 object key（== file_path）；null 表示仅本地")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

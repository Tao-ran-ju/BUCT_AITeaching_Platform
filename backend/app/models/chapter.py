from __future__ import annotations
"""章节模型：chapter，归属课程下的章节管理"""
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Chapter(Base):
    """章节表（chapter）"""
    __tablename__ = "chapter"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # ✅ 这里加上 ForeignKey("courses.id")
    course_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("courses.id"), nullable=False, index=True, comment="所属课程id")
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="章节名称")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course: Mapped["Course"] = relationship(back_populates="chapters")


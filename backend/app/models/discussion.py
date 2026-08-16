"""主题讨论区表：帖子 + 回复。"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DiscussionPost(Base):
    __tablename__ = "discussion_post"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    title: Mapped[str] = mapped_column(String(128))
    content: Mapped[str | None] = mapped_column(Text)
    is_top: Mapped[bool] = mapped_column(Boolean, default=False, comment="置顶")
    is_essence: Mapped[bool] = mapped_column(Boolean, default=False, comment="精华")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DiscussionReply(Base):
    __tablename__ = "discussion_reply"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("discussion_post.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

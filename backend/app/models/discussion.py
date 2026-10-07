"""主题讨论区模型（教师端自有表）：帖子 + 回复。"""
from sqlalchemy import BigInteger, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DiscussionPost(Base):
    """讨论区帖子（t_discussion_post）。"""

    __tablename__ = "t_discussion_post"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="课程 ID")
    author_user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="作者 user_rft.id")
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="帖子标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="帖子正文")
    is_pinned: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=否 1=置顶")
    is_locked: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=否 1=锁定")
    is_essence: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=否 1=精华")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=正常")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="创建时间")
    edited_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="最后编辑时间")


class DiscussionReply(Base):
    """讨论区回复（t_discussion_reply）。"""

    __tablename__ = "t_discussion_reply"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="帖子 ID")
    author_user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="作者 user_rft.id")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="回复内容")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=正常")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="创建时间")
    edited_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="最后编辑时间")

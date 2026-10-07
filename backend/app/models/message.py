"""个人消息模型（personal_messages），单收件人模式，支持已读状态与附件。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PersonalMessage(Base):
    """个人消息表（personal_messages）。教师群发作业/公告时会为每个学生生成一条。"""

    __tablename__ = "personal_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="消息标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息正文")
    sender_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="发送者用户 ID")
    sender_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="发送者姓名（冗余）")
    receiver_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="接收者用户 ID")
    message_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="assignment/notice/system")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unread", comment="unread/read/deleted")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="创建时间")
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="阅读时间")
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="关联截止时间")
    attachment_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="附件路径")
    attachment_name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="附件文件名")
    attachment_size: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="附件大小（字节）")
    assignment_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True, comment="关联作业 ID")

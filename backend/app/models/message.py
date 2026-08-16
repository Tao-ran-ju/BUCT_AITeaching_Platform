"""消息表：教师端发布通知 / 作业，学生端个人消息系统读取。

与学生端 personal_message_system.py 采用完全一致的一对多结构：
    message_content  存消息正文（一条消息一份）
    message_receiver 存接收关系（每个学生一行，记录已读 / 未读状态）

表名、字段名、枚举值（assignment / notice / system，unread / read / deleted）
均与学生端对齐，保证双方共用同一 MySQL 库时可互通。
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MessageContent(Base):
    __tablename__ = "message_content"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), comment="消息标题")
    content: Mapped[str] = mapped_column(Text, comment="消息内容")
    sender_id: Mapped[int] = mapped_column(Integer, index=True, comment="发送者ID（教师ID）")
    sender_name: Mapped[str] = mapped_column(String(100), comment="发送者姓名")
    message_type: Mapped[str] = mapped_column(
        String(16), default="assignment", comment="assignment/notice/system"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="发送时间")
    deadline: Mapped[datetime | None] = mapped_column(DateTime, comment="作业截止时间")
    attachment_url: Mapped[str | None] = mapped_column(String(500), comment="附件访问路径")
    attachment_name: Mapped[str | None] = mapped_column(String(255), comment="附件原始文件名")
    attachment_size: Mapped[int | None] = mapped_column(Integer, comment="附件大小（字节）")


class MessageReceiver(Base):
    __tablename__ = "message_receiver"
    __table_args__ = (
        Index("idx_receiver_status", "receiver_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        ForeignKey("message_content.id", ondelete="CASCADE"), index=True
    )
    receiver_id: Mapped[int] = mapped_column(Integer, index=True, comment="接收者ID（学生ID）")
    status: Mapped[str] = mapped_column(
        String(16), default="unread", comment="unread/read/deleted"
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime, comment="阅读时间")

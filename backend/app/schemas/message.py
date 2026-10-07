"""消息相关响应模型。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MessageOut(BaseModel):
    """教师端「已发送消息」出参（按广播分组，含接收统计）。"""

    id: int
    title: str
    content: str
    sender_id: int
    sender_name: str
    message_type: str
    deadline: Optional[datetime] = None
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_size: Optional[int] = None
    assignment_id: Optional[int] = None
    created_at: datetime
    receiver_count: int = 0
    unread_count: int = 0

"""消息相关响应模型。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MessageOut(BaseModel):
    """教师端「已发送消息」出参（含接收统计）。"""

    model_config = ConfigDict(from_attributes=True)

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
    created_at: datetime
    receiver_ids: list[int] = []
    receiver_count: int = 0
    unread_count: int = 0

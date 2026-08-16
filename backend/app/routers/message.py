"""消息路由：教师发布通知 / 作业（与学生端个人消息系统对接）。"""
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.routers import ok
from app.schemas.message import MessageOut
from app.services.message_service import MessageService

router = APIRouter(prefix="/messages", tags=["消息通知"])


@router.post("", summary="发布消息（支持 Word 附件，可批量发送）")
async def send_message(
    title: str = Form(..., description="消息标题"),
    content: str = Form(..., description="消息内容"),
    receiver_ids: str = Form(..., description="接收学生ID，JSON 数组或逗号分隔"),
    message_type: str = Form("assignment", description="assignment/notice/system"),
    deadline: Optional[str] = Form(None, description="截止时间 YYYY-MM-DD HH:MM:SS"),
    file: Optional[UploadFile] = File(None, description="Word 附件（.doc/.docx，≤10MB）"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    msg, receivers = MessageService.send(
        db, user, title, content, receiver_ids, message_type, deadline, file
    )
    data = MessageOut.model_validate({
        "id": msg.id,
        "title": msg.title,
        "content": msg.content,
        "sender_id": msg.sender_id,
        "sender_name": msg.sender_name,
        "message_type": msg.message_type,
        "deadline": msg.deadline,
        "attachment_url": msg.attachment_url,
        "attachment_name": msg.attachment_name,
        "attachment_size": msg.attachment_size,
        "created_at": msg.created_at,
        "receiver_ids": receivers,
        "receiver_count": len(receivers),
        "unread_count": len(receivers),
    })
    return ok(data, message=f"已发送给 {len(receivers)} 名学生")


@router.get("/sent", summary="我发送的消息列表")
def list_sent(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = MessageService.list_sent(db, user)
    return ok([MessageOut.model_validate(it) for it in items])

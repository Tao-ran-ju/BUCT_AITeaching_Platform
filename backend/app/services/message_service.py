"""消息服务：教师发布通知 / 作业，写入与学生端一致的消息表。"""
import json
import os
import uuid
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ValidateError
from app.models.message import MessageContent, MessageReceiver
from app.models.user import User
from app.utils.file_handler import ensure_upload_dir

# 与学生端对齐：仅允许 Word 附件，单个 ≤10MB，存放于 uploads/messages/
MESSAGE_ALLOWED_EXT = {".doc", ".docx"}
MESSAGE_MAX_SIZE = 10 * 1024 * 1024
MESSAGE_TYPES = {"assignment", "notice", "system"}


class MessageService:
    """教师端消息发布业务逻辑。"""

    @staticmethod
    def _parse_receiver_ids(raw: str) -> list[int]:
        """解析接收者 ID：支持 JSON 数组或逗号 / 换行 / 空格分隔，去重并剔除非法值。"""
        if raw is None:
            raise ValidateError("接收学生不能为空")
        raw = str(raw).strip()
        if not raw:
            raise ValidateError("接收学生不能为空")

        ids: list[int] = []
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                ids = [int(v) for v in parsed]
            else:
                raise ValueError
        except (ValueError, TypeError):
            parts = (
                raw.replace("，", ",")
                .replace("；", ",")
                .replace(";", ",")
                .replace("\n", ",")
                .split(",")
            )
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                try:
                    ids.append(int(p))
                except ValueError:
                    raise ValidateError(f"接收学生 ID 无效：{p}")

        seen: set[int] = set()
        result: list[int] = []
        for i in ids:
            if i <= 0:
                continue
            if i not in seen:
                seen.add(i)
                result.append(i)
        if not result:
            raise ValidateError("接收学生不能为空")
        return result

    @staticmethod
    def _parse_deadline(value: str | None) -> datetime | None:
        """解析截止时间：支持 YYYY-MM-DD HH:MM:SS / YYYY-MM-DD HH:MM / YYYY-MM-DD。"""
        if not value:
            return None
        value = str(value).strip()
        if not value:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise ValidateError("截止时间格式错误，请用 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")

    @staticmethod
    def save_attachment(file: UploadFile | None) -> dict | None:
        """保存 Word 附件到 uploads/messages/，返回存储信息；无附件返回 None。"""
        if file is None or not file.filename:
            return None

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in MESSAGE_ALLOWED_EXT:
            raise ValidateError("仅支持 .doc 和 .docx 格式的 Word 附件")

        data = file.file.read()
        if len(data) > MESSAGE_MAX_SIZE:
            raise ValidateError("附件超过 10MB 限制")

        target_dir = ensure_upload_dir("messages")
        filename = f"{uuid.uuid4().hex}{ext}"
        (target_dir / filename).write_bytes(data)

        return {
            # 与学生端一致的访问路径（后端 /uploads 已静态挂载）
            "file_url": f"/uploads/messages/{filename}",
            "file_name": file.filename,
            "file_size": len(data),
        }

    @staticmethod
    def send(
        db: Session,
        user: User,
        title: str,
        content: str,
        receiver_ids: str,
        message_type: str,
        deadline: str | None,
        attachment: UploadFile | None,
    ) -> tuple[MessageContent, list[int]]:
        """发布消息：写入 message_content 一份 + message_receiver 每人一行。"""
        if message_type not in MESSAGE_TYPES:
            raise ValidateError("消息类型必须为 assignment / notice / system")
        receivers = MessageService._parse_receiver_ids(receiver_ids)
        deadline_dt = MessageService._parse_deadline(deadline)
        att = MessageService.save_attachment(attachment)

        msg = MessageContent(
            title=title,
            content=content,
            sender_id=user.id,
            sender_name=user.name,
            message_type=message_type,
            deadline=deadline_dt,
            attachment_url=att["file_url"] if att else None,
            attachment_name=att["file_name"] if att else None,
            attachment_size=att["file_size"] if att else None,
        )
        db.add(msg)
        db.flush()  # 取得自增主键 msg.id
        for rid in receivers:
            db.add(MessageReceiver(message_id=msg.id, receiver_id=rid))
        db.commit()
        db.refresh(msg)
        return msg, receivers

    @staticmethod
    def list_sent(db: Session, user: User) -> list[dict]:
        """列出当前教师发送过的消息，附带接收人数与未读统计。"""
        msgs = db.scalars(
            select(MessageContent)
            .where(MessageContent.sender_id == user.id)
            .order_by(MessageContent.id.desc())
        ).all()

        out: list[dict] = []
        for m in msgs:
            receivers = db.scalars(
                select(MessageReceiver).where(MessageReceiver.message_id == m.id)
            ).all()
            receiver_ids = [r.receiver_id for r in receivers]
            unread = sum(1 for r in receivers if r.status == "unread")
            out.append({
                "id": m.id,
                "title": m.title,
                "content": m.content,
                "sender_id": m.sender_id,
                "sender_name": m.sender_name,
                "message_type": m.message_type,
                "deadline": m.deadline,
                "attachment_url": m.attachment_url,
                "attachment_name": m.attachment_name,
                "attachment_size": m.attachment_size,
                "created_at": m.created_at,
                "receiver_ids": receiver_ids,
                "receiver_count": len(receiver_ids),
                "unread_count": unread,
            })
        return out

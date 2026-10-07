"""消息服务：教师发布通知 / 作业，写入学校 personal_messages（单收件人，群发一人一行）。"""
import os
import uuid
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ValidateError
from app.models.message import PersonalMessage
from app.models.user import User
from app.utils.file_handler import ensure_upload_dir
from app.utils.identity import numeric_uid

# 与学生端对齐：仅允许 Word 附件，单个 ≤10MB，存放于 uploads/messages/
MESSAGE_ALLOWED_EXT = {".doc", ".docx"}
MESSAGE_MAX_SIZE = 10 * 1024 * 1024
MESSAGE_TYPES = {"assignment", "notice", "system"}


class MessageService:
    """教师端消息发布业务逻辑。

    学校 personal_messages 是单收件人模式（一行一个 receiver_id），教师群发时
    为每个学生写一行、共享同一 created_at，列表时按广播分组重建。
    """

    @staticmethod
    def _parse_receiver_ids(raw: str) -> list[int]:
        """解析接收者 ID：支持 JSON 数组或逗号 / 换行 / 空格分隔，去重并剔除非法值。"""
        import json

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
        """解析截止时间：支持 YYYY-MM-DD HH:MM:SS / HH:MM / 日期。"""
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
        assignment_id: int | None = None,
    ) -> dict:
        """发布消息：为每个接收学生写一行 personal_messages。"""
        if message_type not in MESSAGE_TYPES:
            raise ValidateError("消息类型必须为 assignment / notice / system")
        receivers = MessageService._parse_receiver_ids(receiver_ids)
        deadline_dt = MessageService._parse_deadline(deadline)
        att = MessageService.save_attachment(attachment)

        sender_id = numeric_uid(user) or user.id
        now = datetime.now()
        for rid in receivers:
            db.add(PersonalMessage(
                title=title,
                content=content,
                sender_id=sender_id,
                sender_name=user.name,
                receiver_id=rid,
                message_type=message_type,
                status="unread",
                created_at=now,
                deadline=deadline_dt,
                attachment_url=att["file_url"] if att else None,
                attachment_name=att["file_name"] if att else None,
                attachment_size=att["file_size"] if att else None,
                assignment_id=assignment_id,
            ))
        db.commit()
        return {"receiver_count": len(receivers), "receiver_ids": receivers}

    @staticmethod
    def list_sent(db: Session, user: User) -> list[dict]:
        """列出当前教师发送过的消息（按广播分组，含接收人数与未读统计）。"""
        sender_id = numeric_uid(user) or user.id
        rows = db.scalars(
            select(PersonalMessage)
            .where(PersonalMessage.sender_id == sender_id)
            .order_by(PersonalMessage.id.desc())
        ).all()

        # 同一广播的行共享 (title, content, message_type, created_at)，据此分组重建
        groups: dict[tuple, dict] = {}
        order: list[tuple] = []
        for m in rows:
            key = (m.title, m.content, m.message_type, m.created_at)
            if key not in groups:
                groups[key] = {"rep": m, "count": 0, "unread": 0}
                order.append(key)
            groups[key]["count"] += 1
            if m.status == "unread":
                groups[key]["unread"] += 1

        out: list[dict] = []
        for key in order:
            g = groups[key]
            m = g["rep"]
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
                "assignment_id": m.assignment_id,
                "created_at": m.created_at,
                "receiver_count": g["count"],
                "unread_count": g["unread"],
            })
        return out

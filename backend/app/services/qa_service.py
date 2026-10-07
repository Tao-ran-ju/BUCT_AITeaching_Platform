"""AI 问答助手服务：学生提问 -> 自动分类 -> 简单问题自动回复 / 复杂问题转教师。"""
import logging
import time
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.clients.llm_client import llm_client
from app.exceptions import NotFoundError, ValidateError
from app.models.message import PersonalMessage
from app.models.qa import QaQuestion
from app.models.user import User
from app.utils.identity import numeric_uid
from app.utils.serializers import iso_ts

logger = logging.getLogger(__name__)

# 自动回复时写入学生消息中心使用的发送者身份
_QA_SENDER_NAME = "AI 问答助手"

_CLASSIFY_PROMPT = (
    "你是高校程序设计课程的智能问答助手。请判断下面的学生问题是否属于「简单」问题。\n"
    "判断规则：\n"
    "- 简单：概念解释、语法说明、常见知识点答疑，能用一两句话直接回答，"
    "例如「什么是递归」「C++ 的引用和指针有什么区别」。\n"
    "- 复杂：涉及具体代码报错、需要结合学生代码上下文、作业/项目答疑、"
    "个性化情况，需要教师人工处理。\n\n"
    "请严格按以下格式回复，不要输出任何其它内容：\n"
    "若简单：SIMPLE|<你的回答>\n"
    "若复杂：COMPLEX\n\n"
    "学生问题：{content}"
)


class QaService:
    """问答助手业务逻辑。"""

    @staticmethod
    def _now() -> int:
        return int(time.time())

    # ---------- 分类与自动回答 ----------
    @staticmethod
    def _classify(content: str) -> tuple[str, str | None]:
        """调用大模型判断简单/复杂；简单时顺带生成回答。

        返回 (classification, answer)。LLM 不可用或解析失败时按「复杂」处理，
        交由教师人工介入（安全兜底，绝不因 LLM 异常而漏答）。
        """
        if not llm_client.available:
            return "complex", None
        try:
            resp = (llm_client.text_generate(_CLASSIFY_PROMPT.format(content=content)) or "").strip()
            if resp.upper().startswith("SIMPLE"):
                answer = resp.split("|", 1)[1].strip() if "|" in resp else ""
                return ("simple", answer or None)
            return "complex", None
        except Exception as exc:
            logger.warning("问答助手分类失败，按复杂处理: %s", exc)
            return "complex", None

    # ---------- 回复学生（写入学校消息表）----------
    @staticmethod
    def _reply_to_student(db: Session, student_id: int, title: str, content: str) -> None:
        """把回复写入学校 personal_messages，学生端消息中心可见。"""
        student = db.get(User, student_id)
        receiver_id = numeric_uid(student) if student else student_id
        db.add(PersonalMessage(
            title=title,
            content=content,
            sender_id=0,              # 0 表示系统 / AI
            sender_name=_QA_SENDER_NAME,
            receiver_id=receiver_id,
            message_type="system",
            status="unread",
            created_at=datetime.now(),
        ))

    @staticmethod
    def _to_out(db: Session, q: QaQuestion) -> dict:
        student = db.get(User, q.student_user_id)
        return {
            "id": q.id,
            "student_id": q.student_user_id,
            "student_name": student.name if student else None,
            "course_id": q.course_id,
            "content": q.question,
            "question": q.question,
            "answer": q.answer,
            "answered_by": q.answered_by,
            "answered_at": iso_ts(q.answered_at),
            "status": q.status,
            "created_at": iso_ts(q.created_at),
        }

    # ---------- 提问入口 ----------
    @staticmethod
    def ask(db: Session, student_id: int, course_id: int | None,
            content: str) -> QaQuestion:
        """学生提问：自动分类，简单问题自动回复，复杂问题进入教师待处理队列。"""
        classification, answer = QaService._classify(content)

        q = QaQuestion(
            student_user_id=student_id,
            course_id=course_id,
            question=content,
            status=0,
            created_at=QaService._now(),
        )
        if classification == "simple" and answer:
            q.answer = answer
            q.answered_at = QaService._now()
            q.status = 1
            db.add(q)
            db.flush()
            QaService._reply_to_student(
                db, student_id,
                "AI 问答助手自动回复",
                f"你问：{content}\n\n回答：{answer}",
            )
        else:
            db.add(q)

        db.commit()
        db.refresh(q)
        return q

    # ---------- 教师查看 ----------
    @staticmethod
    def list_questions(db: Session) -> dict:
        """教师视角：待处理队列 + 处理统计。"""
        pending = db.scalars(
            select(QaQuestion)
            .where(QaQuestion.status == 0)
            .order_by(QaQuestion.id.asc())
        ).all()

        auto_answered = db.scalar(
            select(func.count(QaQuestion.id)).where(
                QaQuestion.status == 1, QaQuestion.answered_by.is_(None)
            )
        ) or 0
        answered = db.scalar(
            select(func.count(QaQuestion.id)).where(
                QaQuestion.status == 1, QaQuestion.answered_by.isnot(None)
            )
        ) or 0
        stats = {
            "pending": len(pending),
            "answered": answered,
            "auto_answered": auto_answered,
        }
        return {"pending": [QaService._to_out(db, q) for q in pending], "stats": stats}

    # ---------- 教师人工回复 ----------
    @staticmethod
    def answer(db: Session, question_id: int, teacher: User, answer: str) -> QaQuestion:
        """教师回答复杂问题，回写给提问学生。"""
        q = db.get(QaQuestion, question_id)
        if not q:
            raise NotFoundError("问题不存在")
        if q.status == 1:
            raise ValidateError("该问题已回复过")

        q.answer = answer
        q.answered_by = teacher.id
        q.answered_at = QaService._now()
        q.status = 1
        QaService._reply_to_student(
            db, q.student_user_id,
            "教师回复了你的提问",
            f"你问：{q.question}\n\n教师回复：{answer}",
        )
        db.commit()
        db.refresh(q)
        return q

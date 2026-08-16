"""AI 问答助手服务：学生提问 -> 自动分类 -> 简单问题自动回复 / 复杂问题转教师。"""
import logging
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.clients.llm_client import llm_client
from app.exceptions import NotFoundError, ValidateError
from app.models.message import MessageContent, MessageReceiver
from app.models.qa import QaQuestion
from app.models.user import User

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

    # ---------- 回复学生（写入消息中心）----------
    @staticmethod
    def _reply_to_student(db: Session, student_id: int, title: str, content: str) -> None:
        """把回复写入与学生端一致的消息表，学生端消息中心可见。"""
        msg = MessageContent(
            title=title,
            content=content,
            sender_id=0,              # 0 表示系统 / AI
            sender_name=_QA_SENDER_NAME,
            message_type="system",
        )
        db.add(msg)
        db.flush()
        db.add(MessageReceiver(message_id=msg.id, receiver_id=student_id))

    # ---------- 提问入口 ----------
    @staticmethod
    def ask(db: Session, student_id: int, student_name: str,
            course_id: int | None, content: str) -> QaQuestion:
        """学生提问：自动分类，简单问题自动回复，复杂问题进入教师待处理队列。"""
        classification, answer = QaService._classify(content)

        q = QaQuestion(
            student_id=student_id,
            student_name=student_name,
            course_id=course_id,
            content=content,
            classification=classification,
        )
        if classification == "simple" and answer:
            q.status = "auto_answered"
            q.auto_answer = answer
            q.answered_at = datetime.now()
            db.add(q)
            db.flush()
            QaService._reply_to_student(
                db, student_id,
                "AI 问答助手自动回复",
                f"你问：{content}\n\n回答：{answer}",
            )
        else:
            q.status = "pending"
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
            .where(QaQuestion.status == "pending")
            .order_by(QaQuestion.id.asc())
        ).all()

        counts = dict(
            db.execute(
                select(QaQuestion.status, func.count(QaQuestion.id))
                .group_by(QaQuestion.status)
            ).all()
        )
        stats = {
            "pending": counts.get("pending", 0),
            "auto_answered": counts.get("auto_answered", 0),
            "answered": counts.get("answered", 0),
        }
        return {"pending": list(pending), "stats": stats}

    # ---------- 教师人工回复 ----------
    @staticmethod
    def answer(db: Session, question_id: int, teacher: User, answer: str) -> QaQuestion:
        """教师回答复杂问题，回写给提问学生。"""
        q = db.get(QaQuestion, question_id)
        if not q:
            raise NotFoundError("问题不存在")
        if q.status == "answered":
            raise ValidateError("该问题已回复过")

        q.status = "answered"
        q.teacher_answer = answer
        q.answered_by = teacher.id
        q.answered_at = datetime.now()
        QaService._reply_to_student(
            db, q.student_id,
            "教师回复了你的提问",
            f"你问：{q.content}\n\n教师回复：{answer}",
        )
        db.commit()
        db.refresh(q)
        return q

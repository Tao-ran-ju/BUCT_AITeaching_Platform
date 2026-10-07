"""AI 问答助手模型（教师端自有表）：学生提问 + 自动/人工回答。"""
from sqlalchemy import BigInteger, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class QaQuestion(Base):
    """AI 问答记录（t_qa_question）。"""

    __tablename__ = "t_qa_question"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True, comment="关联课程 ID（可选）")
    student_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="提问学生 user_rft.id")
    question: Mapped[str] = mapped_column(Text, nullable=False, comment="问题内容")
    answer: Mapped[str | None] = mapped_column(Text, nullable=True, comment="回复内容（AI 或教师）")
    answered_by: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="回答教师 user_rft.id")
    answered_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="回答时间（UNIX 时间戳）")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=待回答 1=已回答")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="提问时间")

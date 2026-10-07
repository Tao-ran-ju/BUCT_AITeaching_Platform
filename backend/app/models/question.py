"""题库模型（教师端自有表）：题目 / 题型 / 难度 / 答案与解析。"""
from sqlalchemy import BigInteger, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Question(Base):
    """题库题目（t_question）。"""

    __tablename__ = "t_question"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True, comment="关联课程 ID（可选）")
    type: Mapped[str] = mapped_column(String(20), nullable=False, comment="choice/judge/short")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="题干内容")
    options: Mapped[str | None] = mapped_column(Text, nullable=True, comment="选项 JSON 字符串")
    answer: Mapped[str | None] = mapped_column(Text, nullable=True, comment="标准答案")
    analysis: Mapped[str | None] = mapped_column(Text, nullable=True, comment="解析")
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="难度 1-5")
    created_by: Mapped[int] = mapped_column(Integer, nullable=False, comment="创建者 user_rft.id")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="创建时间")
    edited_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="最后编辑时间")

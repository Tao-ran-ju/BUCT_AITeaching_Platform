"""作业表：作业 + 学生提交记录（评测结果 / AI 评语 / 查重率）。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Assignment(Base):
    __tablename__ = "assignment"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"), index=True)
    class_id: Mapped[int | None] = mapped_column(ForeignKey("class.id"))
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)
    question_ids: Mapped[str | None] = mapped_column(Text, comment="关联题目ID，JSON数组")
    oj_problem_id: Mapped[int | None] = mapped_column(Integer, comment="关联学校 OJ 题目 ID（buctcoder）")
    oj_language: Mapped[str | None] = mapped_column(String(16), comment="OJ 判题语言（python/cpp/java...）")
    deadline: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(16), default="published", comment="draft/published/closed")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submission"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignment.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    content: Mapped[str | None] = mapped_column(Text, comment="提交内容（代码/文本）")
    submit_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    judge_status: Mapped[str] = mapped_column(String(16), default="pending", comment="pending/judging/accepted/failed")
    oj_solution_id: Mapped[int | None] = mapped_column(Integer, comment="对应 OJ 提交编号 solution_id")
    score: Mapped[float | None] = mapped_column(comment="得分")
    ai_comment: Mapped[str | None] = mapped_column(Text, comment="AI 个性化评语")
    plagiarism_rate: Mapped[float | None] = mapped_column(comment="查重率 0-1")

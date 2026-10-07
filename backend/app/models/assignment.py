"""作业体系模型：assignments / assignment_submissions + 教师端自有评测扩展表。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Assignment(Base):
    """作业表（assignments），正式作业，支持附件与截止时间。"""

    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True, comment="所属课程 ID（可空）")
    class_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="所属班级 ID")
    publisher_user_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="发布者 user_rft.id")
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="作业标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="作业要求/内容")
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="截止时间")
    attachment_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="附件路径")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=已发布/进行中")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="发布时间")
    edited_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="最后编辑时间")
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="创建者 uid")
    legacy_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, comment="旧系统迁移 ID")
    attachment_name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="附件原始文件名")
    attachment_size: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="附件大小（字节）")
    total_students: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="应提交学生总数")


class AssignmentSubmission(Base):
    """作业提交表（assignment_submissions），一人一作业一次提交。"""

    __tablename__ = "assignment_submissions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assignment_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="作业 ID")
    student_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="学生 user_rft.id")
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="提交文字内容/答案")
    attachment_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="提交附件路径")
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="提交时间")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="0=待批阅 1=已批阅")
    score: Mapped[float | None] = mapped_column(Numeric(5, 2, asdecimal=False), nullable=True, comment="教师评分")
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True, comment="教师批阅反馈/评语")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="记录创建时间")
    edited_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="最后编辑时间")
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="创建者 uid")


class AssignmentOj(Base):
    """教师端自有表（t_assignment_oj）：作业与 OJ 题目/语言的绑定配置。

    学校 assignments 表没有 OJ 题目/语言字段，而 OJ 判题需要作业级的题目与语言配置，
    故用本表补充。一个作业最多一条配置（assignment_id 唯一）。
    """

    __tablename__ = "t_assignment_oj"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assignment_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True, comment="作业 ID")
    oj_problem_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="OJ 题目 ID")
    oj_language: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="OJ 判题语言")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="创建时间")
    edited_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="最后编辑时间")


class SubmissionJudge(Base):
    """教师端自有评测扩展表（t_submission_judge）。

    学校原表 assignment_submissions 只有 status/score/feedback，没有 OJ 评测状态、
    AI 评语、查重率、OJ 提交 ID 等字段；本表补充这些信息，通过 submission_id 一一对应。
    """

    __tablename__ = "t_submission_judge"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True, comment="assignment_submissions.id")
    assignment_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="作业 ID（冗余，便于查询）")
    student_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="学生 user_rft.id")
    judge_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", comment="pending/judging/accepted/failed")
    oj_solution_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="OJ 提交编号 solution_id")
    oj_problem_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="OJ 题目 ID")
    oj_language: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="OJ 判题语言")
    score: Mapped[float | None] = mapped_column(Numeric(5, 2, asdecimal=False), nullable=True, comment="评测得分")
    ai_comment: Mapped[str | None] = mapped_column(Text, nullable=True, comment="AI 个性化评语")
    plagiarism_rate: Mapped[float | None] = mapped_column(Numeric(5, 2, asdecimal=False), nullable=True, comment="查重率 0-1")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="创建时间")
    edited_at: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="最后编辑时间")

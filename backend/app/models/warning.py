"""学情预警表：预警记录 + 学习行为日志（用于规则引擎扫描）。"""
from datetime import datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StudentWarning(Base):
    __tablename__ = "student_warning"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("course.id"), index=True)
    risk_level: Mapped[str] = mapped_column(String(16), default="medium", comment="high/medium/low")
    reason: Mapped[str | None] = mapped_column(Text, comment="预警原因")
    suggestion: Mapped[str | None] = mapped_column(Text, comment="干预建议（AI 生成）")
    is_resolved: Mapped[bool] = mapped_column(default=False, comment="是否已处理")
    intervention: Mapped[str | None] = mapped_column(Text, comment="教师填写的干预措施记录")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, comment="处理时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class StudyBehavior(Base):
    __tablename__ = "study_behavior"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("course.id"), index=True)
    login_duration: Mapped[int] = mapped_column(Integer, default=0, comment="当日登录时长(秒)")
    resource_visits: Mapped[int] = mapped_column(Integer, default=0, comment="当日资源访问次数")
    submit_delay_days: Mapped[int | None] = mapped_column(Integer, comment="最近一次提交延迟天数")
    homework_score: Mapped[float | None] = mapped_column(comment="最近一次作业得分")
    behavior_date: Mapped[datetime.date] = mapped_column(Date, index=True, comment="行为日期")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

"""学情预警服务：规则引擎扫描真实数据，AI 辅助生成干预建议。"""
import logging
import time
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.llm_client import llm_client
from app.config import settings
from app.exceptions import NotFoundError
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.course import Course
from app.models.user import ROLE_STUDENT, User
from app.models.warning import StudentWarning, StudyBehavior
from app.utils.pagination import normalize_page, paginate

logger = logging.getLogger(__name__)


class WarningService:
    """基于真实学习数据（作业提交 / 行为日志）的预警扫描与 AI 干预建议生成。"""

    @staticmethod
    def _now() -> int:
        return int(time.time())

    @staticmethod
    def _existing_open(db: Session, student_user_id: int, warning_type: str):
        return db.scalar(
            select(StudentWarning).where(
                StudentWarning.student_user_id == student_user_id,
                StudentWarning.warning_type == warning_type,
                StudentWarning.status == "open",
            )
        )

    @staticmethod
    def _add(db: Session, student_user_id: int, course_id: int | None,
             warning_type: str, level: str, detail: str) -> StudentWarning | None:
        """新增一条预警；同学生同类型已有未处理记录则跳过（幂等）。"""
        if WarningService._existing_open(db, student_user_id, warning_type):
            return None
        w = StudentWarning(
            student_user_id=student_user_id,
            course_id=course_id,
            warning_type=warning_type,
            level=level,
            detail=detail,
            status="open",
            created_at=WarningService._now(),
        )
        db.add(w)
        return w

    @staticmethod
    def scan(db: Session) -> list[StudentWarning]:
        """扫描学生真实数据（低分 / 提交延迟 / 长期未活跃），生成预警记录。"""
        students = db.scalars(select(User).where(User.role == ROLE_STUDENT)).all()
        now = datetime.now()
        warnings: list[StudentWarning] = []

        for student in students:
            subs = list(
                db.scalars(
                    select(AssignmentSubmission).where(
                        AssignmentSubmission.student_user_id == student.id
                    )
                ).all()
            )

            # 低分：平均分低于阈值
            scored = [float(s.score) for s in subs if s.score is not None]
            if scored:
                avg = sum(scored) / len(scored)
                if avg < settings.WARNING_LOW_SCORE * 100:
                    w = WarningService._add(
                        db, student.id, None, "low_score", "high",
                        f"作业平均分 {avg:.1f}，低于 {settings.WARNING_LOW_SCORE * 100:.0f} 分",
                    )
                    if w:
                        warnings.append(w)

            # 提交延迟：超期提交次数达到阈值
            delayed = 0
            for s in subs:
                a = db.get(Assignment, s.assignment_id)
                if a and a.deadline and s.submitted_at and s.submitted_at > a.deadline:
                    delayed += 1
            if delayed >= settings.WARNING_SUBMIT_DELAY_DAYS:
                w = WarningService._add(
                    db, student.id, None, "submit_delay", "medium",
                    f"有 {delayed} 次作业超期提交",
                )
                if w:
                    warnings.append(w)

            # 长期未活跃：近 N 天既无提交也无行为日志
            recent_cutoff = now - timedelta(days=settings.WARNING_ABSENT_DAYS)
            has_recent_sub = any(
                s.submitted_at and s.submitted_at >= recent_cutoff for s in subs
            )
            recent_behavior = db.scalar(
                select(StudyBehavior.id).where(
                    StudyBehavior.student_user_id == student.id,
                    StudyBehavior.created_at >= int(recent_cutoff.timestamp()),
                ).limit(1)
            )
            if not has_recent_sub and not recent_behavior:
                w = WarningService._add(
                    db, student.id, None, "absent", "medium",
                    f"近 {settings.WARNING_ABSENT_DAYS} 天无学习活动",
                )
                if w:
                    warnings.append(w)

        db.commit()
        for w in warnings:
            db.refresh(w)
        return warnings

    @staticmethod
    def ai_suggestion(warning: StudentWarning) -> str | None:
        """进阶版：调用大模型生成个性化干预建议。"""
        if not llm_client.available:
            return None
        try:
            return llm_client.intervention_suggestion(warning.detail or warning.warning_type)
        except Exception as exc:
            logger.warning("AI 干预建议生成失败: %s", exc)
            return None

    @staticmethod
    def _to_out(db: Session, w: StudentWarning) -> dict:
        student = db.get(User, w.student_user_id)
        course = db.get(Course, w.course_id) if w.course_id else None
        return {
            "id": w.id,
            "course_id": w.course_id,
            "course_name": course.name if course else None,
            "student_id": w.student_user_id,
            "student_user_id": w.student_user_id,
            "student_uid": student.uid if student else None,
            "student_name": student.name if student else None,
            "warning_type": w.warning_type,
            "risk_level": w.level,
            "reason": w.detail,
            "suggestion": w.suggestion,
            "intervention": w.intervention,
            "is_resolved": w.status == "resolved",
            "created_at": w.created_at,
            "resolved_at": w.resolved_at,
        }

    @staticmethod
    def list(db: Session, page: int | None, page_size: int | None,
             risk_level: str | None = None) -> dict:
        page, page_size = normalize_page(page, page_size)
        stmt = select(StudentWarning)
        if risk_level:
            stmt = stmt.where(StudentWarning.level == risk_level)
        total = len(db.scalars(stmt).all())
        rows = db.scalars(
            stmt.order_by(StudentWarning.id.desc())
            .offset((page - 1) * page_size).limit(page_size)
        ).all()
        items = [WarningService._to_out(db, w) for w in rows]
        return paginate(items, total, page, page_size)

    @staticmethod
    def resolve(db: Session, warning_id: int, intervention: str | None = None) -> StudentWarning:
        warning = db.get(StudentWarning, warning_id)
        if not warning:
            raise NotFoundError("预警记录不存在")
        warning.status = "resolved"
        warning.resolved_at = WarningService._now()
        if intervention:
            warning.intervention = intervention
        db.commit()
        db.refresh(warning)
        return warning

    @staticmethod
    def record_behavior(db: Session, student_user_id: int, behavior_type: str,
                        value: str | None = None, course_id: int | None = None) -> None:
        """记录一条学生学习行为（供预警扫描与活跃度判断）。"""
        db.add(StudyBehavior(
            student_user_id=student_user_id,
            course_id=course_id,
            behavior_type=behavior_type,
            value=value,
            created_at=WarningService._now(),
        ))
        db.commit()

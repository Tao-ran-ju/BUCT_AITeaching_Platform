"""学情预警服务：规则引擎为主，AI 分析为辅生成干预建议。"""
import logging
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.clients.llm_client import llm_client
from app.models.warning import StudentWarning, StudyBehavior

logger = logging.getLogger(__name__)


class WarningService:
    """基于学习行为数据的预警扫描与 AI 干预建议生成。"""

    # 规则阈值（可从 .env 覆盖）
    RULES = {
        "submit_delay_days": settings.WARNING_SUBMIT_DELAY_DAYS,
        "absent_days": settings.WARNING_ABSENT_DAYS,
        "low_score": settings.WARNING_LOW_SCORE,
        "low_login_seconds": settings.WARNING_LOW_LOGIN_SECONDS,
        "low_resource_visits": settings.WARNING_LOW_RESOURCE_VISITS,
    }

    # 风险等级排序权重（多条规则叠加时取更高等级）
    _RISK_RANK = {"low": 0, "medium": 1, "high": 2}

    @staticmethod
    def _raise(cur: str, new: str) -> str:
        """在已有等级基础上提升到更高风险，避免规则互相覆盖。"""
        return new if WarningService._RISK_RANK[new] > WarningService._RISK_RANK[cur] else cur

    @staticmethod
    def scan(db: Session) -> list[StudentWarning]:
        """扫描近期学习行为，生成预警记录（幂等：已存在的同原因不重复生成）。"""
        warnings: list[StudentWarning] = []
        since = date.today() - timedelta(days=settings.WARNING_ABSENT_DAYS)

        behaviors = db.scalars(
            select(StudyBehavior).where(StudyBehavior.behavior_date >= since)
        ).all()

        # 按学生聚合最近行为
        latest: dict[int, StudyBehavior] = {}
        for b in behaviors:
            latest[b.student_id] = b

        for student_id, b in latest.items():
            reasons = []
            level = "low"
            if b.submit_delay_days and b.submit_delay_days > WarningService.RULES["submit_delay_days"]:
                reasons.append(f"作业提交延迟 {b.submit_delay_days} 天")
                level = WarningService._raise(level, "medium")
            if b.homework_score is not None and b.homework_score < WarningService.RULES["low_score"] * 100:
                reasons.append(f"作业正确率低于 {WarningService.RULES['low_score'] * 100:.0f}%")
                level = WarningService._raise(level, "high")
            # 学习不积极：登录时长 / 资源访问次数低于阈值
            if b.login_duration < WarningService.RULES["low_login_seconds"]:
                reasons.append(f"近期日均登录时长 {b.login_duration} 秒，学习不积极")
                level = WarningService._raise(level, "medium")
            if b.resource_visits < WarningService.RULES["low_resource_visits"]:
                reasons.append(f"近期日均资源访问 {b.resource_visits} 次，学习不积极")
                level = WarningService._raise(level, "medium")
            if not reasons:
                continue

            exists = db.scalar(
                select(StudentWarning).where(
                    StudentWarning.student_id == student_id,
                    StudentWarning.is_resolved.is_(False),
                )
            )
            if exists:
                continue

            reason = "；".join(reasons)
            warning = StudentWarning(
                student_id=student_id,
                course_id=b.course_id,
                risk_level=level,
                reason=reason,
            )
            db.add(warning)
            warnings.append(warning)

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
            return llm_client.intervention_suggestion(warning.reason)
        except Exception as exc:
            logger.warning("AI 干预建议生成失败: %s", exc)
            return None

    @staticmethod
    def list(db: Session, page: int | None, page_size: int | None,
             risk_level: str | None = None) -> dict:
        from app.utils.pagination import normalize_page, paginate

        page, page_size = normalize_page(page, page_size)
        stmt = select(StudentWarning)
        if risk_level:
            stmt = stmt.where(StudentWarning.risk_level == risk_level)
        total = len(db.scalars(stmt).all())
        rows = db.scalars(
            stmt.order_by(StudentWarning.id.desc())
            .offset((page - 1) * page_size).limit(page_size)
        ).all()
        return paginate(rows, total, page, page_size)

    @staticmethod
    def resolve(db: Session, warning_id: int, intervention: str | None = None) -> StudentWarning:
        warning = db.get(StudentWarning, warning_id)
        if not warning:
            raise ValueError("预警记录不存在")
        warning.is_resolved = True
        warning.resolved_at = datetime.now()
        if intervention:
            warning.intervention = intervention
        db.commit()
        db.refresh(warning)
        return warning

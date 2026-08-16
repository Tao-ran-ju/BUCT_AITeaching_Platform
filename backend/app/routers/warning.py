"""学情预警路由：规则扫描、预警列表、AI 干预建议、标记处理。"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import NotFoundError
from app.models.course import Course
from app.models.user import User
from app.models.warning import StudentWarning
from app.routers import ok
from app.services.warning_service import WarningService

router = APIRouter(prefix="/warnings", tags=["学情预警"])


class ResolveRequest(BaseModel):
    """标记已处理时可记录干预措施。"""

    intervention: Optional[str] = None


@router.post("/scan", summary="触发规则引擎扫描")
def scan_warnings(user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    warnings = WarningService.scan(db)
    return ok({
        "generated": len(warnings),
        "warnings": [
            {"id": w.id, "student_id": w.student_id, "risk_level": w.risk_level,
             "reason": w.reason}
            for w in warnings
        ],
    })


@router.get("", summary="预警列表")
def list_warnings(
    risk_level: Optional[str] = Query(None, pattern="^(high|medium|low)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = WarningService.list(db, page, page_size, risk_level)
    items = result["items"]

    # 补充学生姓名 / 课程名，避免前端只能看到裸 ID
    student_ids = list({w.student_id for w in items})
    course_ids = list({w.course_id for w in items if w.course_id})
    name_map = (
        {u.id: u.name for u in db.scalars(select(User).where(User.id.in_(student_ids))).all()}
        if student_ids else {}
    )
    course_map = (
        {c.id: c.name for c in db.scalars(select(Course).where(Course.id.in_(course_ids))).all()}
        if course_ids else {}
    )

    result["items"] = [
        {
            "id": w.id, "student_id": w.student_id, "course_id": w.course_id,
            "student_name": name_map.get(w.student_id),
            "course_name": course_map.get(w.course_id) if w.course_id else None,
            "risk_level": w.risk_level, "reason": w.reason,
            "suggestion": w.suggestion, "is_resolved": w.is_resolved,
            "intervention": w.intervention,
            "resolved_at": w.resolved_at.isoformat() if w.resolved_at else None,
            "created_at": w.created_at.isoformat(),
        }
        for w in items
    ]
    return ok(result)


@router.post("/{warning_id}/suggestion", summary="AI 生成干预建议")
def ai_suggestion(warning_id: int, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    warning = db.get(StudentWarning, warning_id)
    if not warning:
        raise NotFoundError("预警记录不存在")
    suggestion = WarningService.ai_suggestion(warning)
    if suggestion:
        warning.suggestion = suggestion
        db.commit()
    return ok({"suggestion": suggestion})


@router.post("/{warning_id}/resolve", summary="标记预警已处理")
def resolve_warning(warning_id: int, data: ResolveRequest,
                    user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    warning = WarningService.resolve(db, warning_id, data.intervention)
    return ok({
        "id": warning.id,
        "is_resolved": warning.is_resolved,
        "intervention": warning.intervention,
        "resolved_at": warning.resolved_at.isoformat() if warning.resolved_at else None,
    })

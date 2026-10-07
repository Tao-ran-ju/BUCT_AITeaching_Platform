"""学情预警路由：规则扫描、预警列表、AI 干预建议、标记处理。"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import NotFoundError
from app.models.user import User
from app.models.warning import StudentWarning
from app.routers import ok
from app.services.warning_service import WarningService
from app.utils.serializers import iso_ts

router = APIRouter(prefix="/warnings", tags=["学情预警"])


class ResolveRequest(BaseModel):
    """标记已处理时可记录干预措施。"""

    intervention: Optional[str] = None


def _iso_warning(d: dict) -> dict:
    d["created_at"] = iso_ts(d.get("created_at"))
    d["resolved_at"] = iso_ts(d.get("resolved_at"))
    return d


@router.post("/scan", summary="触发规则引擎扫描")
def scan_warnings(user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    warnings = WarningService.scan(db)
    return ok({
        "generated": len(warnings),
        "warnings": [_iso_warning(WarningService._to_out(db, w)) for w in warnings],
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
    result["items"] = [_iso_warning(it) for it in result["items"]]
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
        "is_resolved": warning.status == "resolved",
        "intervention": warning.intervention,
        "resolved_at": iso_ts(warning.resolved_at),
    })

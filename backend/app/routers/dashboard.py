"""数据驾驶舱路由：核心指标、能力矩阵热力图。"""
from fastapi import APIRouter, Depends

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.routers import ok
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/dashboard", tags=["数据驾驶舱"])


@router.get("/overview", summary="核心指标总览")
def overview(user: User = Depends(get_current_user), db=Depends(get_db)):
    data = AnalysisService.overview(db)
    return ok(data.model_dump())


@router.get("/heatmap", summary="能力矩阵热力图")
def heatmap(course_id: int | None = None, user: User = Depends(get_current_user),
            db=Depends(get_db)):
    cells = AnalysisService.capability_heatmap(db, course_id)
    return ok([c.model_dump() for c in cells])


@router.get("/task-progress", summary="全局任务进度热力图")
def task_progress(user: User = Depends(get_current_user), db=Depends(get_db)):
    return ok(AnalysisService.task_progress(db))


@router.get("/score-distribution", summary="成绩分布")
def score_distribution(user: User = Depends(get_current_user), db=Depends(get_db)):
    return ok(AnalysisService.score_distribution(db))


@router.get("/effect-compare", summary="教学效果对比")
def effect_compare(user: User = Depends(get_current_user), db=Depends(get_db)):
    return ok(AnalysisService.effect_compare(db))

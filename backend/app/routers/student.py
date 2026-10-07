"""学生端路由：供学校学生端对接——查看本人班级与本人被布置的作业。

鉴权：学生通过统一 SSO（POST /auth/sso/token，role=1）或 /auth/login 拿到教师端 JWT 后，
以 Authorization: Bearer <token> 访问；依赖 get_current_student 保证只有学生本人能访问，
且数据严格限定为「本人」，不越权读取他人信息。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_student
from app.models.class_ import ClassRoom
from app.models.user import User
from app.routers import ok
from app.services.assignment_service import AssignmentService
from app.utils.serializers import iso_ts

router = APIRouter(prefix="/student", tags=["学生端"])


@router.get("/classes", summary="我的班级")
def my_classes(student: User = Depends(get_current_student), db: Session = Depends(get_db)):
    """返回当前学生所属的班级列表。"""
    ids = AssignmentService._student_class_ids(db, student)
    classes = db.scalars(select(ClassRoom).where(ClassRoom.id.in_(ids))).all() if ids else []
    items = [{
        "id": c.id,
        "name": c.name,
        "course": c.course,
        "private": c.private,
        "created_at": iso_ts(c.created_at),
    } for c in classes]
    return ok(items)


@router.get("/assignments", summary="我的作业")
def my_assignments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """返回布置给本人的作业（含课程/班级信息与本人提交状态）。"""
    result = AssignmentService.list_for_student(db, student, page, page_size)
    for it in result["items"]:
        it["created_at"] = iso_ts(it.get("created_at"))
        sub = it.get("my_submission")
        if sub:
            sub["submit_time"] = iso_ts(sub.get("submit_time"))
    return ok(result)

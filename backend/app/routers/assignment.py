"""作业路由：发布作业、学生提交、触发评测、查重、查看提交记录。"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_student, get_current_teacher
from app.models.user import User
from app.routers import ok
from app.schemas.assignment import AssignmentCreate
from app.services.assignment_service import AssignmentService
from app.services.judge_service import JudgeService
from app.services.plagiarism_service import PlagiarismService
from app.utils.serializers import iso_ts

router = APIRouter(prefix="/assignments", tags=["作业"])

# 作业状态 int -> 教师端前端展示的字符串
_STATUS_MAP = {0: "published", 100: "closed"}


class SubmitRequest(BaseModel):
    """学生提交作业（学生端网关调用）。"""

    assignment_id: int
    content: str = Field(..., min_length=1)


def _teacher_assignment(db: Session, a) -> dict:
    """作业出参：字段对齐前端 + status int→string + created_at int→ISO。"""
    out = AssignmentService.assignment_out(db, a)
    out["status"] = _STATUS_MAP.get(a.status, "published")
    out["created_at"] = iso_ts(a.created_at)
    return out


def _teacher_submission(db: Session, s) -> dict:
    out = AssignmentService.submission_out(db, s)
    out["submit_time"] = iso_ts(s.submitted_at)
    return out


@router.post("", summary="发布作业")
def create_assignment(data: AssignmentCreate, user: User = Depends(get_current_teacher),
                      db: Session = Depends(get_db)):
    assignment = AssignmentService.create(db, user, data)
    return ok(_teacher_assignment(db, assignment))


@router.get("", summary="按课程查询作业")
def list_assignments(
    course_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: User = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    result = AssignmentService.list_by_course(db, course_id, page, page_size)
    result["items"] = [_teacher_assignment(db, a) for a in result["items"]]
    return ok(result)


@router.post("/submit", summary="学生提交作业")
def submit_assignment(data: SubmitRequest, student: User = Depends(get_current_student),
                      db: Session = Depends(get_db)):
    submission = AssignmentService.submit(db, student, data.assignment_id, data.content)
    return ok(_teacher_submission(db, submission))


@router.post("/{assignment_id}/judge", summary="触发评测（OJ 判题 + AI 评语）")
def judge_assignment(assignment_id: int, user: User = Depends(get_current_teacher),
                     db: Session = Depends(get_db)):
    submissions = AssignmentService.orm_submissions(db, assignment_id)
    judge = JudgeService()
    try:
        results = [_teacher_submission(db, judge.judge(db, s)) for s in submissions]
    finally:
        judge.close()
    return ok(results)


@router.get("/{assignment_id}/submissions", summary="作业提交记录")
def list_submissions(assignment_id: int, _: User = Depends(get_current_teacher),
                     db: Session = Depends(get_db)):
    rows = AssignmentService.list_submissions(db, assignment_id)
    for r in rows:
        r["submit_time"] = iso_ts(r.get("submit_time"))
    return ok(rows)


@router.post("/{assignment_id}/plagiarism", summary="代码查重（simhash）")
def check_plagiarism(assignment_id: int, _: User = Depends(get_current_teacher),
                     db: Session = Depends(get_db)):
    submissions = PlagiarismService.check(db, assignment_id)
    return ok([_teacher_submission(db, s) for s in submissions])

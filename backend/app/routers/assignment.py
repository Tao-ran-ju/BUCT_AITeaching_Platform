"""作业路由：作业 CRUD、学生提交、触发评测、查看提交。"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.routers import ok
from app.schemas.assignment import (
    AssignmentCreate, AssignmentOut, SubmissionCreate, SubmissionOut,
)
from app.services.assignment_service import AssignmentService
from app.services.judge_service import JudgeService
from app.services.plagiarism_service import PlagiarismService

router = APIRouter(prefix="/assignments", tags=["作业"])


@router.post("", summary="发布作业")
def create_assignment(data: AssignmentCreate, user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    assignment = AssignmentService.create(db, user, data)
    return ok(AssignmentOut.model_validate(assignment))


@router.get("", summary="按课程查询作业")
def list_assignments(
    course_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = AssignmentService.list_by_course(db, course_id, page, page_size)
    result["items"] = [AssignmentOut.model_validate(a) for a in result["items"]]
    return ok(result)


@router.post("/submit", summary="学生提交作业")
def submit_assignment(data: SubmissionCreate, student: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    submission = AssignmentService.submit(db, student, data.assignment_id, data.content)
    return ok(SubmissionOut.model_validate(submission))


@router.post("/{assignment_id}/judge", summary="触发评测")
def judge_assignment(assignment_id: int, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    submissions = AssignmentService.list_submissions(db, assignment_id)
    judge = JudgeService()
    try:
        results = [SubmissionOut.model_validate(judge.judge(db, s)) for s in submissions]
    finally:
        judge.close()
    return ok(results)


@router.get("/{assignment_id}/submissions", summary="作业提交记录")
def list_submissions(assignment_id: int, _: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    rows = AssignmentService.list_submissions(db, assignment_id)
    return ok([SubmissionOut.model_validate(s) for s in rows])


@router.post("/{assignment_id}/plagiarism", summary="代码查重（simhash）")
def check_plagiarism(assignment_id: int, _: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    rows = PlagiarismService.check(db, assignment_id)
    return ok([SubmissionOut.model_validate(s) for s in rows])

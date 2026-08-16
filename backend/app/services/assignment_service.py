"""作业服务：作业发布、学生提交、评测结果回写。"""
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.user import User
from app.schemas.assignment import AssignmentCreate
from app.utils.pagination import normalize_page, paginate


class AssignmentService:
    """作业生命周期业务逻辑。"""

    @staticmethod
    def create(db: Session, teacher: User, data: AssignmentCreate) -> Assignment:
        assignment = Assignment(
            course_id=data.course_id,
            class_id=data.class_id,
            title=data.title,
            description=data.description,
            question_ids=json.dumps(data.question_ids or [], ensure_ascii=False),
            oj_problem_id=data.oj_problem_id,
            oj_language=data.oj_language,
            deadline=data.deadline,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def list_by_course(db: Session, course_id: int,
                       page: int | None, page_size: int | None) -> dict:
        page, page_size = normalize_page(page, page_size)
        stmt = select(Assignment).where(Assignment.course_id == course_id)
        total = len(db.scalars(stmt).all())
        rows = db.scalars(
            stmt.order_by(Assignment.id.desc()).offset((page - 1) * page_size).limit(page_size)
        ).all()
        return paginate(rows, total, page, page_size)

    @staticmethod
    def get(db: Session, assignment_id: int) -> Assignment:
        assignment = db.get(Assignment, assignment_id)
        if not assignment:
            raise NotFoundError("作业不存在")
        return assignment

    @staticmethod
    def submit(db: Session, student: User, assignment_id: int, content: str) -> AssignmentSubmission:
        """学生提交作业，初始状态 pending，由评测服务异步更新结果。"""
        AssignmentService.get(db, assignment_id)  # 校验作业存在
        submission = AssignmentSubmission(
            assignment_id=assignment_id,
            student_id=student.id,
            content=content,
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission

    @staticmethod
    def list_submissions(db: Session, assignment_id: int) -> list[AssignmentSubmission]:
        return list(
            db.scalars(
                select(AssignmentSubmission)
                .where(AssignmentSubmission.assignment_id == assignment_id)
                .order_by(AssignmentSubmission.submit_time.desc())
            ).all()
        )

"""作业服务：作业发布、学生提交、评测结果回写。"""
import time
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models.assignment import Assignment, AssignmentOj, AssignmentSubmission, SubmissionJudge
from app.models.class_ import ClassRecord, ClassRoom
from app.models.course import Course, CourseClass, CourseStudent
from app.models.user import User
from app.schemas.assignment import AssignmentCreate
from app.utils.identity import numeric_uid
from app.utils.pagination import normalize_page, paginate


class AssignmentService:
    """作业生命周期业务逻辑。"""

    @staticmethod
    def _now() -> int:
        return int(time.time())

    @staticmethod
    def _class_student_count(db: Session, class_id: int) -> int:
        return db.scalar(
            select(func.count(ClassRecord.id)).where(
                ClassRecord.class_id == class_id, ClassRecord.role == 1
            )
        ) or 0

    @staticmethod
    def create(db: Session, teacher: User, data: AssignmentCreate) -> Assignment:
        total = AssignmentService._class_student_count(db, data.class_id)
        assignment = Assignment(
            course_id=data.course_id,
            class_id=data.class_id,
            publisher_user_id=teacher.id,
            title=data.title,
            content=data.content,
            deadline=data.deadline,
            status=0,
            created_at=AssignmentService._now(),
            edited_at=AssignmentService._now(),
            created_by=teacher.uid,
            total_students=total,
        )
        db.add(assignment)
        db.flush()
        if data.oj_problem_id:
            db.add(AssignmentOj(
                assignment_id=assignment.id,
                oj_problem_id=data.oj_problem_id,
                oj_language=data.oj_language,
                created_at=AssignmentService._now(),
                edited_at=AssignmentService._now(),
            ))
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
    def list_by_class(db: Session, class_id: int,
                      page: int | None, page_size: int | None) -> dict:
        page, page_size = normalize_page(page, page_size)
        stmt = select(Assignment).where(Assignment.class_id == class_id)
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
        """学生提交作业；学校表一人一次（联合唯一），重复提交则覆盖内容。"""
        AssignmentService.get(db, assignment_id)
        existing = db.scalar(
            select(AssignmentSubmission).where(
                AssignmentSubmission.assignment_id == assignment_id,
                AssignmentSubmission.student_user_id == student.id,
            )
        )
        if existing:
            existing.content = content
            existing.submitted_at = datetime.now()
            existing.edited_at = AssignmentService._now()
            db.commit()
            db.refresh(existing)
            return existing
        submission = AssignmentSubmission(
            assignment_id=assignment_id,
            student_user_id=student.id,
            content=content,
            submitted_at=datetime.now(),
            status=0,
            created_at=AssignmentService._now(),
            edited_at=AssignmentService._now(),
            created_by=student.uid,
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission

    @staticmethod
    def _submission_out(db: Session, s: AssignmentSubmission) -> dict:
        """合并 t_submission_judge 与提交记录，生成出参 dict。"""
        sj = db.scalar(select(SubmissionJudge).where(SubmissionJudge.submission_id == s.id))
        student = db.get(User, s.student_user_id)
        return {
            "id": s.id,
            "assignment_id": s.assignment_id,
            "student_id": s.student_user_id,
            "student_uid": student.uid if student else None,
            "student_name": student.name if student else None,
            "content": s.content,
            "attachment_url": s.attachment_url,
            "submit_time": s.submitted_at,
            "status": s.status,
            "score": s.score,
            "feedback": s.feedback,
            "judge_status": sj.judge_status if sj else "pending",
            "ai_comment": sj.ai_comment if sj else None,
            "plagiarism_rate": sj.plagiarism_rate if sj else None,
            "oj_solution_id": sj.oj_solution_id if sj else None,
        }

    @staticmethod
    def _assignment_out(db: Session, a: Assignment) -> dict:
        oj = db.scalar(select(AssignmentOj).where(AssignmentOj.assignment_id == a.id))
        cls = db.get(ClassRoom, a.class_id) if a.class_id else None
        course = db.get(Course, a.course_id) if a.course_id else None
        submitted = db.scalar(
            select(func.count(AssignmentSubmission.id)).where(
                AssignmentSubmission.assignment_id == a.id
            )
        ) or 0
        return {
            "id": a.id,
            "course_id": a.course_id,
            "class_id": a.class_id,
            "title": a.title,
            "content": a.content,
            "description": a.content,
            "deadline": a.deadline,
            "status": a.status,
            "attachment_url": a.attachment_url,
            "attachment_name": a.attachment_name,
            "attachment_size": a.attachment_size,
            "total_students": a.total_students,
            "submitted_count": submitted,
            "oj_problem_id": oj.oj_problem_id if oj else None,
            "oj_language": oj.oj_language if oj else None,
            "class_name": cls.name if cls else None,
            "course_name": course.name if course else None,
            "created_at": a.created_at,
        }

    @staticmethod
    def list_submissions(db: Session, assignment_id: int) -> list[dict]:
        AssignmentService.get(db, assignment_id)
        subs = list(
            db.scalars(
                select(AssignmentSubmission)
                .where(AssignmentSubmission.assignment_id == assignment_id)
                .order_by(AssignmentSubmission.submitted_at.desc())
            ).all()
        )
        return [AssignmentService._submission_out(db, s) for s in subs]

    @staticmethod
    def _student_class_ids(db: Session, student: User) -> list[int]:
        """学生所属班级 ID：class_record（学号）+ course_students → course_classes。"""
        ids: set[int] = set()
        nid = numeric_uid(student)
        if nid is not None:
            ids.update(
                db.scalars(select(ClassRecord.class_id).where(ClassRecord.uid == nid)).all()
            )
        course_ids = list(
            db.scalars(
                select(CourseStudent.course_id).where(CourseStudent.student_user_id == student.id)
            ).all()
        )
        if course_ids:
            ids.update(
                db.scalars(
                    select(CourseClass.class_id).where(CourseClass.course_id.in_(course_ids))
                ).all()
            )
        return list(ids)

    @staticmethod
    def list_for_student(db: Session, student: User,
                         page: int | None, page_size: int | None) -> dict:
        """学生视角：本人被布置的作业（含课程/班级信息与本人提交状态）。"""
        page, page_size = normalize_page(page, page_size)
        class_ids = AssignmentService._student_class_ids(db, student)
        if not class_ids:
            return paginate([], 0, page, page_size)
        stmt = select(Assignment).where(
            Assignment.class_id.in_(class_ids), Assignment.status == 0
        )
        total = len(db.scalars(stmt).all())
        rows = db.scalars(
            stmt.order_by(Assignment.id.desc()).offset((page - 1) * page_size).limit(page_size)
        ).all()
        items = []
        for a in rows:
            out = AssignmentService._assignment_out(db, a)
            sub = db.scalar(
                select(AssignmentSubmission).where(
                    AssignmentSubmission.assignment_id == a.id,
                    AssignmentSubmission.student_user_id == student.id,
                )
            )
            out["submitted"] = sub is not None
            out["my_submission"] = AssignmentService._submission_out(db, sub) if sub else None
            items.append(out)
        return paginate(items, total, page, page_size)

    @staticmethod
    def orm_submissions(db: Session, assignment_id: int) -> list[AssignmentSubmission]:
        """评测 / 查重所需的 ORM 提交对象（区别于 dict 出参）。"""
        AssignmentService.get(db, assignment_id)
        return list(
            db.scalars(
                select(AssignmentSubmission)
                .where(AssignmentSubmission.assignment_id == assignment_id)
                .order_by(AssignmentSubmission.submitted_at.desc())
            ).all()
        )

    @staticmethod
    def assignment_out(db: Session, a: Assignment) -> dict:
        return AssignmentService._assignment_out(db, a)

    @staticmethod
    def submission_out(db: Session, s: AssignmentSubmission) -> dict:
        return AssignmentService._submission_out(db, s)

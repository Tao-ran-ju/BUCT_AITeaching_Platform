"""课程服务：课程 CRUD + 知识图谱。"""
import json
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models.course import Course, KnowledgeGraph
from app.models.user import User
from app.schemas.course import CourseCreate, CourseUpdate
from app.utils.pagination import normalize_page, paginate


class CourseService:
    """课程及其知识图谱业务逻辑。"""

    @staticmethod
    def _now() -> int:
        return int(time.time())

    # ---------- 课程 ----------
    @staticmethod
    def list_courses(db: Session, teacher_id: int | None = None,
                     page: int | None = None, page_size: int | None = None) -> dict:
        page, page_size = normalize_page(page, page_size)
        stmt = select(Course)
        if teacher_id is not None:
            stmt = stmt.where(Course.teacher_user_id == teacher_id)
        total = len(db.scalars(stmt).all())
        rows = db.scalars(
            stmt.order_by(Course.id.desc()).offset((page - 1) * page_size).limit(page_size)
        ).all()
        return paginate(rows, total, page, page_size)

    @staticmethod
    def get_course(db: Session, course_id: int) -> Course:
        course = db.get(Course, course_id)
        if not course:
            raise NotFoundError("课程不存在")
        return course

    @staticmethod
    def create_course(db: Session, teacher: User, data: CourseCreate) -> Course:
        course = Course(
            name=data.name,
            description=data.description,
            teacher_user_id=teacher.id,
            status=0,
            created_at=CourseService._now(),
            edited_at=CourseService._now(),
            created_by=teacher.uid,
        )
        db.add(course)
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def update_course(db: Session, course_id: int, data: CourseUpdate) -> Course:
        course = CourseService.get_course(db, course_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(course, field, value)
        course.edited_at = CourseService._now()
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def delete_course(db: Session, course_id: int) -> None:
        """软删除：status=100 归档（学校表用 100 表示归档/删除）。"""
        course = CourseService.get_course(db, course_id)
        course.status = 100
        course.edited_at = CourseService._now()
        db.commit()

    @staticmethod
    def set_status(db: Session, course_id: int, status: int) -> Course:
        """发布（1）/ 归档（100）/ 回到草稿（0）。"""
        course = CourseService.get_course(db, course_id)
        course.status = status
        course.edited_at = CourseService._now()
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def clone_course(db: Session, course_id: int, teacher: User) -> Course:
        """克隆课程：复制课程元信息 + 知识图谱，新课程为草稿。"""
        src = CourseService.get_course(db, course_id)
        cloned = Course(
            name=f"{src.name}（副本）",
            description=src.description,
            teacher_user_id=teacher.id,
            status=0,
            created_at=CourseService._now(),
            edited_at=CourseService._now(),
            created_by=teacher.uid,
        )
        db.add(cloned)
        db.flush()  # 取得 cloned.id
        graph = db.scalar(select(KnowledgeGraph).where(KnowledgeGraph.course_id == course_id))
        if graph:
            db.add(KnowledgeGraph(
                course_id=cloned.id,
                graph_data=graph.graph_data,
                created_at=CourseService._now(),
                edited_at=CourseService._now(),
                created_by=teacher.uid,
            ))
        db.commit()
        db.refresh(cloned)
        return cloned

    # ---------- 知识图谱 ----------
    @staticmethod
    def get_graph(db: Session, course_id: int) -> KnowledgeGraph | None:
        CourseService.get_course(db, course_id)  # 校验课程存在
        return db.scalar(select(KnowledgeGraph).where(KnowledgeGraph.course_id == course_id))

    @staticmethod
    def upsert_graph(db: Session, course_id: int, graph_data: dict,
                     created_by: str | None) -> KnowledgeGraph:
        """写入 / 更新课程知识图谱（每门课程一份）。"""
        CourseService.get_course(db, course_id)
        payload = json.dumps(graph_data, ensure_ascii=False)
        graph = db.scalar(select(KnowledgeGraph).where(KnowledgeGraph.course_id == course_id))
        if graph:
            graph.graph_data = payload
            graph.edited_at = CourseService._now()
            if created_by:
                graph.created_by = created_by
        else:
            graph = KnowledgeGraph(
                course_id=course_id,
                graph_data=payload,
                created_at=CourseService._now(),
                edited_at=CourseService._now(),
                created_by=created_by,
            )
            db.add(graph)
        db.commit()
        db.refresh(graph)
        return graph

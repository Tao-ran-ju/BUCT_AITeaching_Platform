"""课程服务：课程 CRUD + 知识图谱 + 章节/知识点。"""
import json
import time

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models.course import Chapter, Course, KnowledgeGraph, KnowledgePoint
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
        stmt = select(Course).where(Course.status != 100)  # 归档/删除的课程不出现在活动列表
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
        """删除课程：课程本身软删（status=100 归档，学校表用 100 表示归档/删除），
        同时硬删其章节与知识点（教师端自有 t_ 表）。"""
        course = CourseService.get_course(db, course_id)
        course.status = 100
        course.edited_at = CourseService._now()
        chapter_ids = db.scalars(
            select(Chapter.id).where(Chapter.course_id == course_id)
        ).all()
        if chapter_ids:
            db.execute(delete(KnowledgePoint).where(KnowledgePoint.chapter_id.in_(chapter_ids)))
            db.execute(delete(Chapter).where(Chapter.course_id == course_id))
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

    # ---------- 章节 ----------
    @staticmethod
    def list_chapters(db: Session, course_id: int) -> list[Chapter]:
        CourseService.get_course(db, course_id)  # 校验课程存在
        return list(db.scalars(
            select(Chapter).where(Chapter.course_id == course_id)
            .order_by(Chapter.sort_order, Chapter.id)
        ).all())

    @staticmethod
    def get_chapter(db: Session, chapter_id: int) -> Chapter:
        chapter = db.get(Chapter, chapter_id)
        if not chapter:
            raise NotFoundError("章节不存在")
        return chapter

    @staticmethod
    def create_chapter(db: Session, course_id: int, data, created_by: str | None) -> Chapter:
        CourseService.get_course(db, course_id)
        chapter = Chapter(
            course_id=course_id,
            title=data.title,
            description=data.description,
            sort_order=data.sort_order or 0,
            created_at=CourseService._now(),
            edited_at=CourseService._now(),
            created_by=created_by,
        )
        db.add(chapter)
        db.commit()
        db.refresh(chapter)
        return chapter

    @staticmethod
    def update_chapter(db: Session, chapter_id: int, data) -> Chapter:
        chapter = CourseService.get_chapter(db, chapter_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(chapter, field, value)
        chapter.edited_at = CourseService._now()
        db.commit()
        db.refresh(chapter)
        return chapter

    @staticmethod
    def delete_chapter(db: Session, chapter_id: int) -> None:
        """删除章节，级联删除其下知识点。"""
        chapter = CourseService.get_chapter(db, chapter_id)
        db.execute(delete(KnowledgePoint).where(KnowledgePoint.chapter_id == chapter_id))
        db.delete(chapter)
        db.commit()

    # ---------- 知识点 ----------
    @staticmethod
    def list_knowledge_points(db: Session, chapter_id: int) -> list[KnowledgePoint]:
        CourseService.get_chapter(db, chapter_id)  # 校验章节存在
        return list(db.scalars(
            select(KnowledgePoint).where(KnowledgePoint.chapter_id == chapter_id)
            .order_by(KnowledgePoint.sort_order, KnowledgePoint.id)
        ).all())

    @staticmethod
    def get_knowledge_point(db: Session, kp_id: int) -> KnowledgePoint:
        kp = db.get(KnowledgePoint, kp_id)
        if not kp:
            raise NotFoundError("知识点不存在")
        return kp

    @staticmethod
    def create_knowledge_point(db: Session, chapter_id: int, data, created_by: str | None) -> KnowledgePoint:
        CourseService.get_chapter(db, chapter_id)
        kp = KnowledgePoint(
            chapter_id=chapter_id,
            name=data.name,
            description=data.description,
            sort_order=data.sort_order or 0,
            created_at=CourseService._now(),
            edited_at=CourseService._now(),
            created_by=created_by,
        )
        db.add(kp)
        db.commit()
        db.refresh(kp)
        return kp

    @staticmethod
    def update_knowledge_point(db: Session, kp_id: int, data) -> KnowledgePoint:
        kp = CourseService.get_knowledge_point(db, kp_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(kp, field, value)
        kp.edited_at = CourseService._now()
        db.commit()
        db.refresh(kp)
        return kp

    @staticmethod
    def delete_knowledge_point(db: Session, kp_id: int) -> None:
        kp = CourseService.get_knowledge_point(db, kp_id)
        db.delete(kp)
        db.commit()

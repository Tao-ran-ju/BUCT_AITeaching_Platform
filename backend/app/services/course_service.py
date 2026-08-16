"""课程服务：课程 / 章节 / 知识点 CRUD。"""
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models.course import Chapter, Course, KnowledgePoint
from app.schemas.course import CourseCreate, CourseUpdate
from app.utils.pagination import normalize_page, paginate


class CourseService:
    """课程及其组织结构（章-节-知识点）业务逻辑。"""

    # ---------- 课程 ----------
    @staticmethod
    def list_courses(db: Session, teacher_id: int | None = None,
                     page: int | None = None, page_size: int | None = None) -> dict:
        page, page_size = normalize_page(page, page_size)
        stmt = select(Course)
        if teacher_id is not None:
            stmt = stmt.where(Course.teacher_id == teacher_id)
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
    def create_course(db: Session, teacher_id: int, data: CourseCreate) -> Course:
        course = Course(**data.model_dump(), teacher_id=teacher_id)
        db.add(course)
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def update_course(db: Session, course_id: int, data: CourseUpdate) -> Course:
        course = CourseService.get_course(db, course_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(course, field, value)
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def delete_course(db: Session, course_id: int) -> None:
        course = CourseService.get_course(db, course_id)
        db.delete(course)
        db.commit()

    @staticmethod
    def set_status(db: Session, course_id: int, status: str) -> Course:
        """归档 / 发布课程（draft / published / archived）。"""
        course = CourseService.get_course(db, course_id)
        course.status = status
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def set_cover(db: Session, course_id: int, cover: str) -> Course:
        """设置课程封面图路径。"""
        course = CourseService.get_course(db, course_id)
        course.cover = cover
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def clone_course(db: Session, course_id: int, teacher_id: int) -> Course:
        """克隆课程：复制课程元信息，并深拷贝章-节-知识点树。

        新课程为「草稿」状态，编号追加「(副本)」，方便教师二次编辑后发布。
        """
        src = CourseService.get_course(db, course_id)
        cloned = Course(
            name=f"{src.name}（副本）",
            code=(f"{src.code}（副本）" if src.code else None),
            cover=src.cover,
            description=src.description,
            open_time=src.open_time,
            teacher_id=teacher_id,
            status="draft",
        )
        db.add(cloned)
        db.flush()  # 取得 cloned.id

        # 第一遍：复制章节与知识点（暂不设父子关系）
        kp_map: dict[int, int] = {}      # 旧知识点 id -> 新知识点 id
        kp_rows: list[tuple[KnowledgePoint, int | None]] = []  # (新知识点, 旧 parent_id)
        for ch in CourseService.list_chapters(db, course_id):
            new_ch = Chapter(
                course_id=cloned.id,
                title=ch.title,
                description=ch.description,
                sort_order=ch.sort_order,
            )
            db.add(new_ch)
            db.flush()
            for kp in CourseService.list_knowledge_points(db, ch.id):
                new_kp = KnowledgePoint(
                    chapter_id=new_ch.id,
                    parent_id=None,
                    name=kp.name,
                    description=kp.description,
                    ai_summary=kp.ai_summary,
                    sort_order=kp.sort_order,
                )
                db.add(new_kp)
                db.flush()
                kp_map[kp.id] = new_kp.id
                kp_rows.append((new_kp, kp.parent_id))

        # 第二遍：回填父子关系（父知识点可能出现在子知识点之后）
        for new_kp, old_parent_id in kp_rows:
            if old_parent_id and old_parent_id in kp_map:
                new_kp.parent_id = kp_map[old_parent_id]

        db.commit()
        db.refresh(cloned)
        return cloned

    # ---------- 章节 ----------
    @staticmethod
    def list_chapters(db: Session, course_id: int) -> list[Chapter]:
        return list(
            db.scalars(
                select(Chapter)
                .where(Chapter.course_id == course_id)
                .order_by(Chapter.sort_order)
            ).all()
        )

    @staticmethod
    def create_chapter(db: Session, course_id: int, title: str,
                       description: str | None, sort_order: int) -> Chapter:
        CourseService.get_course(db, course_id)  # 校验课程存在
        chapter = Chapter(
            course_id=course_id, title=title,
            description=description, sort_order=sort_order,
        )
        db.add(chapter)
        db.commit()
        db.refresh(chapter)
        return chapter

    @staticmethod
    def update_chapter(db: Session, chapter_id: int, data) -> Chapter:
        chapter = db.get(Chapter, chapter_id)
        if not chapter:
            raise NotFoundError("章节不存在")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(chapter, field, value)
        db.commit()
        db.refresh(chapter)
        return chapter

    @staticmethod
    def delete_chapter(db: Session, chapter_id: int) -> None:
        chapter = db.get(Chapter, chapter_id)
        if not chapter:
            raise NotFoundError("章节不存在")
        # 级联删除该章下的全部知识点
        db.execute(delete(KnowledgePoint).where(KnowledgePoint.chapter_id == chapter_id))
        db.delete(chapter)
        db.commit()

    # ---------- 知识点 ----------
    @staticmethod
    def list_knowledge_points(db: Session, chapter_id: int) -> list[KnowledgePoint]:
        return list(
            db.scalars(
                select(KnowledgePoint)
                .where(KnowledgePoint.chapter_id == chapter_id)
                .order_by(KnowledgePoint.sort_order)
            ).all()
        )

    @staticmethod
    def create_knowledge_point(db: Session, chapter_id: int, parent_id: int | None,
                               name: str, description: str | None,
                               sort_order: int) -> KnowledgePoint:
        kp = KnowledgePoint(
            chapter_id=chapter_id, parent_id=parent_id, name=name,
            description=description, sort_order=sort_order,
        )
        db.add(kp)
        db.commit()
        db.refresh(kp)
        return kp

    @staticmethod
    def update_knowledge_point(db: Session, kp_id: int, data) -> KnowledgePoint:
        kp = db.get(KnowledgePoint, kp_id)
        if not kp:
            raise NotFoundError("知识点不存在")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(kp, field, value)
        db.commit()
        db.refresh(kp)
        return kp

    @staticmethod
    def delete_knowledge_point(db: Session, kp_id: int) -> None:
        kp = db.get(KnowledgePoint, kp_id)
        if not kp:
            raise NotFoundError("知识点不存在")
        # 连带删除以其为父的子知识点
        db.execute(delete(KnowledgePoint).where(KnowledgePoint.parent_id == kp_id))
        db.delete(kp)
        db.commit()

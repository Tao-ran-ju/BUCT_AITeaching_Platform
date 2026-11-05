from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.chapter import Chapter
from app.models.course import Course
from app.schemas.chapter import ChapterCreate, ChapterUpdate


class ChapterService:
    @staticmethod
    def _check_course_owner(db: Session, course_id: int, user_id: int):
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")
        if course.teacher_user_id != user_id:
            raise HTTPException(status_code=403, detail="无权限操作该课程章节")
        return course

    @staticmethod
    def list_chapters(db: Session, course_id: int, user_id: int):
        ChapterService._check_course_owner(db, course_id, user_id)
        return db.query(Chapter).filter(Chapter.course_id == course_id).order_by(Chapter.sort).all()

    @staticmethod
    def create_chapter(db: Session, course_id: int, data: ChapterCreate, user_id: int):
        ChapterService._check_course_owner(db, course_id, user_id)
        db_obj = Chapter(course_id=course_id, name=data.name, sort=data.sort)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def update_chapter(db: Session, course_id: int, chapter_id: int, data: ChapterUpdate, user_id: int):
        ChapterService._check_course_owner(db, course_id, chapter_id, user_id)
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id, Chapter.course_id == course_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        chapter.name = data.name
        chapter.sort = data.sort
        db.commit()
        db.refresh(chapter)
        return chapter

    @staticmethod
    def delete_chapter(db: Session, course_id: int, chapter_id: int, user_id: int):
        ChapterService._check_course_owner(db, course_id, chapter_id, user_id)
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id, Chapter.course_id == course_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
        db.delete(chapter)
        db.commit()


from sqlalchemy.orm import Session
from app.models.class_ import ClassRecord
from app.schemas.class_record import ChapterCreate, ChapterUpdate

class ClassRecordService:
    @staticmethod
    def list_by_course(db: Session, course_id: int):
        return db.query(ClassRecord).filter(ClassRecord.course_id == course_id).order_by(ClassRecord.id).all()

    @staticmethod
    def create_chapter(db: Session, course_id: int, data: ChapterCreate):
        obj = ClassRecord(course_id=course_id, name=data.name)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_one(db: Session, course_id: int, chapter_id: int):
        return db.query(ClassRecord).filter(
            ClassRecord.id == chapter_id,
            ClassRecord.course_id == course_id
        ).first()

    @staticmethod
    def update_chapter(db: Session, course_id: int, chapter_id: int, data: ChapterUpdate):
        obj = ClassRecordService.get_one(db, course_id, chapter_id)
        if not obj:
            return None
        if data.name is not None:
            obj.name = data.name
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete_chapter(db: Session, course_id: int, chapter_id: int):
        obj = ClassRecordService.get_one(db, course_id, chapter_id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True


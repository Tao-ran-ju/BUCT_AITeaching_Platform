"""班级路由：班级 CRUD、学生批量加入 / 移除（缺档自动建档）。"""
import secrets
import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_teacher
from app.exceptions import ForbiddenError, NotFoundError
from app.models.class_ import ClassRecord, ClassRoom
from app.models.course import Course, CourseClass
from app.models.user import ROLE_STUDENT, User
from app.routers import ok
from app.schemas.class_ import ClassCreate, ClassUpdate, StudentAddRequest
from app.utils.identity import class_member_users
from app.utils.pagination import normalize_page, paginate
from app.utils.security import hash_password
from app.utils.serializers import iso_ts

router = APIRouter(prefix="/classes", tags=["班级"])


def _require_class_owner(db: Session, user: User, class_id: int) -> ClassRoom:
    """取班级并校验归属：教师仅能操作自己创建的班级（created_by == 工号 uid）。"""
    cls = db.get(ClassRoom, class_id)
    if not cls:
        raise NotFoundError("班级不存在")
    if cls.created_by != user.uid:
        raise ForbiddenError("仅班级创建者可操作该班级")
    return cls


def _class_out(db: Session, cls: ClassRoom) -> dict:
    student_count = db.scalar(
        select(func.count(ClassRecord.id)).where(
            ClassRecord.class_id == cls.id, ClassRecord.role == 1
        )
    ) or 0
    course_id = db.scalar(
        select(CourseClass.course_id).where(CourseClass.class_id == cls.id).limit(1)
    )
    return {
        "id": cls.id,
        "name": cls.name,
        "course": cls.course,
        "course_id": course_id,
        "private": cls.private,
        "status": cls.status,
        "created_by": cls.created_by,
        "teacher_user_id": None,
        "student_count": student_count,
        "grade": None,
        "major": None,
        "description": None,
        "created_at": iso_ts(cls.created_at),
    }


def _class_student_out(user: User) -> dict:
    return {
        "id": user.id,
        "uid": user.uid,
        "username": user.uid,
        "name": user.name,
        "department": user.college,
        "phone": None,
        "college": user.college,
        "class_name": user.class_name,
        "major": user.major,
    }


@router.get("", summary="班级列表")
def list_classes(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    page, page_size = normalize_page(page, page_size)
    stmt = select(ClassRoom).where(ClassRoom.created_by == user.uid)
    total = len(db.scalars(stmt).all())
    rows = db.scalars(
        stmt.order_by(ClassRoom.id.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ).all()
    result = paginate(rows, total, page, page_size)
    result["items"] = [_class_out(db, c) for c in result["items"]]
    return ok(result)


@router.post("", summary="创建班级")
def create_class(data: ClassCreate, user: User = Depends(get_current_teacher),
                 db: Session = Depends(get_db)):
    course_name = None
    if data.course_id:
        course = db.get(Course, data.course_id)
        if not course:
            raise NotFoundError("课程不存在")
        course_name = course.name

    now = int(time.time())
    cls = ClassRoom(
        name=data.name,
        course=course_name,
        private=data.private,
        status=0,
        created_at=now,
        edited_at=now,
        created_by=user.uid,
    )
    db.add(cls)
    db.flush()
    if data.course_id:
        db.add(CourseClass(
            course_id=data.course_id,
            class_id=cls.id,
            created_at=now,
            created_by=user.uid,
        ))
    db.commit()
    db.refresh(cls)
    return ok(_class_out(db, cls))


@router.put("/{class_id}", summary="更新班级")
def update_class(class_id: int, data: ClassUpdate,
                 user: User = Depends(get_current_teacher),
                 db: Session = Depends(get_db)):
    cls = _require_class_owner(db, user, class_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cls, field, value)
    cls.edited_at = int(time.time())
    db.commit()
    db.refresh(cls)
    return ok(_class_out(db, cls))


@router.delete("/{class_id}", summary="删除班级")
def delete_class(class_id: int, user: User = Depends(get_current_teacher),
                 db: Session = Depends(get_db)):
    cls = _require_class_owner(db, user, class_id)
    db.execute(delete(ClassRecord).where(ClassRecord.class_id == class_id))
    db.execute(delete(CourseClass).where(CourseClass.class_id == class_id))
    db.delete(cls)
    db.commit()
    return ok(message="班级已删除")


@router.post("/{class_id}/students", summary="批量添加学生（学号，缺档自动建档）")
def add_students(class_id: int, data: StudentAddRequest,
                 user: User = Depends(get_current_teacher),
                 db: Session = Depends(get_db)):
    _require_class_owner(db, user, class_id)
    now = int(time.time())
    added = 0
    for sid in data.student_ids:
        uid_str = str(sid)
        student = db.scalar(select(User).where(User.uid == uid_str))
        if not student:
            student = User(
                uid=uid_str,
                password_hash=hash_password(secrets.token_urlsafe(12)),
                name=uid_str,
                role=ROLE_STUDENT,
                gender=0,
                college="",
                status=0,
                created_at=now,
                edited_at=now,
                created_by=user.id,
            )
            db.add(student)
            db.flush()
        exists = db.scalar(
            select(ClassRecord).where(
                ClassRecord.class_id == class_id,
                ClassRecord.uid == sid,
                ClassRecord.role == 1,
            )
        )
        if not exists:
            db.add(ClassRecord(
                uid=sid,
                role=1,
                class_id=class_id,
                status=0,
                created_at=now,
                edited_at=now,
                created_by=user.uid,
            ))
            added += 1
    db.commit()
    return ok({"added": added}, message=f"成功添加 {added} 名学生")


@router.get("/{class_id}/students", summary="班级学生列表")
def list_students(class_id: int, user: User = Depends(get_current_teacher),
                  db: Session = Depends(get_db)):
    _require_class_owner(db, user, class_id)
    students = class_member_users(db, class_id)
    return ok([_class_student_out(s) for s in students])


@router.delete("/{class_id}/students/{student_id}", summary="移除学生（student_id 为学号）")
def remove_student(class_id: int, student_id: int,
                   user: User = Depends(get_current_teacher),
                   db: Session = Depends(get_db)):
    _require_class_owner(db, user, class_id)
    db.execute(
        delete(ClassRecord).where(
            ClassRecord.class_id == class_id,
            ClassRecord.uid == student_id,
            ClassRecord.role == 1,
        )
    )
    db.commit()
    return ok(message="已从班级移除该学生")

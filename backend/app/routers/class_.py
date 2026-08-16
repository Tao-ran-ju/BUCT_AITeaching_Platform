"""班级路由：班级 CRUD、学生批量加入 / 移除。"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import NotFoundError
from app.models.class_ import ClassRoom, ClassStudent
from app.models.user import User
from app.routers import ok
from app.schemas.class_ import ClassCreate, ClassOut, ClassUpdate, StudentAddRequest
from app.schemas.user import UserOut
from app.utils.pagination import normalize_page, paginate

router = APIRouter(prefix="/classes", tags=["班级"])


@router.get("", summary="班级列表")
def list_classes(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    page, page_size = normalize_page(page, page_size)
    total = len(db.scalars(select(ClassRoom)).all())
    rows = db.scalars(
        select(ClassRoom).order_by(ClassRoom.id.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ).all()
    result = paginate(rows, total, page, page_size)
    result["items"] = [ClassOut.model_validate(c) for c in result["items"]]
    return ok(result)


@router.post("", summary="创建班级")
def create_class(data: ClassCreate, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    cls = ClassRoom(**data.model_dump(), teacher_id=data.teacher_id or user.id)
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return ok(ClassOut.model_validate(cls))


@router.put("/{class_id}", summary="更新班级")
def update_class(class_id: int, data: ClassUpdate,
                 user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    cls = db.get(ClassRoom, class_id)
    if not cls:
        raise NotFoundError("班级不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cls, field, value)
    db.commit()
    db.refresh(cls)
    return ok(ClassOut.model_validate(cls))


@router.delete("/{class_id}", summary="删除班级")
def delete_class(class_id: int, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    cls = db.get(ClassRoom, class_id)
    if not cls:
        raise NotFoundError("班级不存在")
    db.execute(delete(ClassStudent).where(ClassStudent.class_id == class_id))
    db.delete(cls)
    db.commit()
    return ok(message="班级已删除")


@router.post("/{class_id}/students", summary="批量添加学生")
def add_students(class_id: int, data: StudentAddRequest,
                 user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    cls = db.get(ClassRoom, class_id)
    if not cls:
        raise NotFoundError("班级不存在")
    added = 0
    for student_id in data.student_ids:
        exists = db.scalar(
            select(ClassStudent).where(
                ClassStudent.class_id == class_id,
                ClassStudent.student_id == student_id,
            )
        )
        if not exists:
            db.add(ClassStudent(class_id=class_id, student_id=student_id))
            added += 1
    db.commit()
    return ok({"added": added}, message=f"成功添加 {added} 名学生")


@router.get("/{class_id}/students", summary="班级学生列表")
def list_students(class_id: int, _: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    ids = db.scalars(
        select(ClassStudent.student_id).where(ClassStudent.class_id == class_id)
    ).all()
    students = db.scalars(select(User).where(User.id.in_(ids))).all()
    return ok([UserOut.model_validate(s) for s in students])


@router.delete("/{class_id}/students/{student_id}", summary="移除学生")
def remove_student(class_id: int, student_id: int,
                   user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    db.execute(
        delete(ClassStudent).where(
            ClassStudent.class_id == class_id,
            ClassStudent.student_id == student_id,
        )
    )
    db.commit()
    return ok(message="已从班级移除该学生")

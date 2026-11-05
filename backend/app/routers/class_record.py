from fastapi import APIRouter, Depends, Path, Body
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.routers import ok
from app.schemas.class_record import ChapterCreate, ChapterUpdate, ChapterOut
from app.services.class_record_service import ClassRecordService
from app.exceptions import AppError

router = APIRouter(prefix="/courses/{course_id}/chapters", tags=["课程章节"])


@router.get("", summary="获取课程章节列表", response_model=List[ChapterOut])
def list_chapters(
    course_id: int = Path(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items = ClassRecordService.list_by_course(db, course_id)
    return ok(items)


@router.post("", summary="新增章节", response_model=ChapterOut)
def create_chapter(
    course_id: int = Path(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    data: ChapterCreate = Body(...),
):
    item = ClassRecordService.create_chapter(db, course_id, data)
    return ok(item)


@router.get("/{id}", summary="获取单个章节", response_model=ChapterOut)
def get_chapter(
    course_id: int = Path(...),
    id: int = Path(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = ClassRecordService.get_one(db, course_id, id)
    if not item:
        raise AppError(code=404, message="章节不存在")
    return ok(item)


@router.put("/{id}", summary="修改章节", response_model=ChapterOut)
def update_chapter(
    course_id: int = Path(...),
    id: int = Path(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    data: ChapterUpdate = Body(...),
):
    item = ClassRecordService.update_chapter(db, course_id, id, data)
    if not item:
        raise AppError(code=404, message="章节不存在")
    return ok(item)


@router.delete("/{id}", summary="删除章节")
def delete_chapter(
    course_id: int = Path(...),
    id: int = Path(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ok_flag = ClassRecordService.delete_chapter(db, course_id, id)
    if not ok_flag:
        raise AppError(code=404, message="章节不存在")
    return ok(message="删除成功")


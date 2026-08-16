"""课程路由：课程 / 章节 / 知识点 CRUD。"""
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import ValidateError
from app.models.user import User
from app.routers import ok
from app.schemas.course import (
    ChapterCreate, ChapterOut, ChapterUpdate, CourseCreate, CourseOut,
    CourseUpdate, KnowledgePointCreate, KnowledgePointOut, KnowledgePointUpdate,
)
from app.services.course_service import CourseService
from app.utils.file_handler import save_upload_file

router = APIRouter(prefix="/courses", tags=["课程"])

# 课程封面大小上限（5MB）
COVER_MAX_SIZE = 5 * 1024 * 1024


@router.get("", summary="课程列表")
def list_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = CourseService.list_courses(db, page=page, page_size=page_size)
    result["items"] = [CourseOut.model_validate(c) for c in result["items"]]
    return ok(result)


@router.get("/{course_id}", summary="课程详情")
def get_course(course_id: int, db: Session = Depends(get_db),
               _: User = Depends(get_current_user)):
    course = CourseService.get_course(db, course_id)
    return ok(CourseOut.model_validate(course))


@router.post("", summary="创建课程")
def create_course(data: CourseCreate, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    course = CourseService.create_course(db, user.id, data)
    return ok(CourseOut.model_validate(course))


@router.put("/{course_id}", summary="更新课程")
def update_course(course_id: int, data: CourseUpdate,
                  user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    course = CourseService.update_course(db, course_id, data)
    return ok(CourseOut.model_validate(course))


@router.delete("/{course_id}", summary="删除课程")
def delete_course(course_id: int, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    CourseService.delete_course(db, course_id)
    return ok(message="课程已删除")


@router.post("/{course_id}/clone", summary="克隆课程")
def clone_course(course_id: int, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    course = CourseService.clone_course(db, course_id, user.id)
    return ok(CourseOut.model_validate(course), message="课程已克隆为草稿")


@router.post("/{course_id}/archive", summary="归档课程")
def archive_course(course_id: int, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    course = CourseService.set_status(db, course_id, "archived")
    return ok(CourseOut.model_validate(course), message="课程已归档")


@router.post("/{course_id}/publish", summary="发布课程")
def publish_course(course_id: int, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    course = CourseService.set_status(db, course_id, "published")
    return ok(CourseOut.model_validate(course), message="课程已发布")


@router.post("/{course_id}/cover", summary="上传课程封面")
def upload_cover(course_id: int, file: UploadFile = File(...),
                 user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """上传并保存课程封面到本地磁盘，经 /uploads 静态路由访问。"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise ValidateError("仅支持图片文件")
    data = file.file.read()
    if len(data) > COVER_MAX_SIZE:
        raise ValidateError("封面不能超过 5MB")
    file.file.seek(0)
    rel = save_upload_file(file, f"course/{course_id}")
    course = CourseService.set_cover(db, course_id, "/" + rel.lstrip("/"))
    return ok(CourseOut.model_validate(course))


@router.get("/{course_id}/chapters", summary="章节列表")
def list_chapters(course_id: int, db: Session = Depends(get_db),
                  _: User = Depends(get_current_user)):
    chapters = CourseService.list_chapters(db, course_id)
    return ok([ChapterOut.model_validate(c) for c in chapters])


@router.post("/{course_id}/chapters", summary="创建章节")
def create_chapter(course_id: int, data: ChapterCreate,
                   user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    chapter = CourseService.create_chapter(
        db, course_id, data.title, data.description, data.sort_order
    )
    return ok(ChapterOut.model_validate(chapter))


@router.put("/chapters/{chapter_id}", summary="更新章节")
def update_chapter(chapter_id: int, data: ChapterUpdate,
                   user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    chapter = CourseService.update_chapter(db, chapter_id, data)
    return ok(ChapterOut.model_validate(chapter))


@router.delete("/chapters/{chapter_id}", summary="删除章节")
def delete_chapter(chapter_id: int, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    CourseService.delete_chapter(db, chapter_id)
    return ok(message="章节已删除")


@router.get("/chapters/{chapter_id}/knowledge-points", summary="知识点列表")
def list_knowledge_points(chapter_id: int, db: Session = Depends(get_db),
                          _: User = Depends(get_current_user)):
    points = CourseService.list_knowledge_points(db, chapter_id)
    return ok([KnowledgePointOut.model_validate(p) for p in points])


@router.post("/chapters/{chapter_id}/knowledge-points", summary="创建知识点")
def create_knowledge_point(chapter_id: int, data: KnowledgePointCreate,
                           user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    kp = CourseService.create_knowledge_point(
        db, chapter_id, data.parent_id, data.name, data.description, data.sort_order
    )
    return ok(KnowledgePointOut.model_validate(kp))


@router.put("/chapters/{chapter_id}/knowledge-points/{kp_id}", summary="更新知识点")
def update_knowledge_point(chapter_id: int, kp_id: int, data: KnowledgePointUpdate,
                           user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    kp = CourseService.update_knowledge_point(db, kp_id, data)
    return ok(KnowledgePointOut.model_validate(kp))


@router.delete("/chapters/{chapter_id}/knowledge-points/{kp_id}", summary="删除知识点")
def delete_knowledge_point(chapter_id: int, kp_id: int,
                           user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    CourseService.delete_knowledge_point(db, kp_id)
    return ok(message="知识点已删除")

"""课程路由：课程 CRUD + 知识图谱。"""
import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.routers import ok
from app.schemas.course import (
    ChapterCreate,
    ChapterUpdate,
    CourseCreate,
    CourseUpdate,
    KnowledgeGraphUpsert,
    KnowledgePointCreate,
    KnowledgePointUpdate,
)
from app.services.course_service import CourseService
from app.utils.serializers import chapter_out, course_out, knowledge_point_out

router = APIRouter(prefix="/courses", tags=["课程"])


@router.get("", summary="课程列表")
def list_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = CourseService.list_courses(db, page=page, page_size=page_size)
    result["items"] = [course_out(c) for c in result["items"]]
    return ok(result)


@router.get("/{course_id}", summary="课程详情")
def get_course(course_id: int, db: Session = Depends(get_db),
               _: User = Depends(get_current_user)):
    course = CourseService.get_course(db, course_id)
    return ok(course_out(course))


@router.post("", summary="创建课程")
def create_course(data: CourseCreate, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    course = CourseService.create_course(db, user, data)
    return ok(course_out(course))


@router.put("/{course_id}", summary="更新课程")
def update_course(course_id: int, data: CourseUpdate,
                  user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    course = CourseService.update_course(db, course_id, data)
    return ok(course_out(course))


@router.delete("/{course_id}", summary="删除课程（归档）")
def delete_course(course_id: int, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    CourseService.delete_course(db, course_id)
    return ok(message="课程已删除")


@router.post("/{course_id}/clone", summary="克隆课程")
def clone_course(course_id: int, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    course = CourseService.clone_course(db, course_id, user)
    return ok(course_out(course), message="课程已克隆为草稿")


@router.post("/{course_id}/archive", summary="归档课程")
def archive_course(course_id: int, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    course = CourseService.set_status(db, course_id, 100)
    return ok(course_out(course), message="课程已归档")


@router.post("/{course_id}/publish", summary="发布课程")
def publish_course(course_id: int, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    course = CourseService.set_status(db, course_id, 1)
    return ok(course_out(course), message="课程已发布")


@router.get("/{course_id}/graph", summary="获取知识图谱")
def get_graph(course_id: int, db: Session = Depends(get_db),
              _: User = Depends(get_current_user)):
    graph = CourseService.get_graph(db, course_id)
    data = json.loads(graph.graph_data) if graph and graph.graph_data else None
    return ok(data)


@router.put("/{course_id}/graph", summary="保存知识图谱")
def put_graph(course_id: int, data: KnowledgeGraphUpsert,
              user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    graph = CourseService.upsert_graph(db, course_id, data.graph_data, user.uid)
    return ok(json.loads(graph.graph_data), message="知识图谱已保存")


# ---------- 章节 ----------
@router.get("/{course_id}/chapters", summary="章节列表")
def list_chapters(course_id: int, db: Session = Depends(get_db),
                  _: User = Depends(get_current_user)):
    chapters = CourseService.list_chapters(db, course_id)
    return ok([chapter_out(c) for c in chapters])


@router.post("/{course_id}/chapters", summary="新建章节")
def create_chapter(course_id: int, data: ChapterCreate,
                   user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    chapter = CourseService.create_chapter(db, course_id, data, user.uid)
    return ok(chapter_out(chapter), message="章节已创建")


@router.put("/chapters/{chapter_id}", summary="更新章节")
def update_chapter(chapter_id: int, data: ChapterUpdate,
                   user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    chapter = CourseService.update_chapter(db, chapter_id, data)
    return ok(chapter_out(chapter), message="章节已更新")


@router.delete("/chapters/{chapter_id}", summary="删除章节")
def delete_chapter(chapter_id: int, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    CourseService.delete_chapter(db, chapter_id)
    return ok(message="章节已删除")


# ---------- 知识点 ----------
@router.get("/chapters/{chapter_id}/knowledge-points", summary="知识点列表")
def list_knowledge_points(chapter_id: int, db: Session = Depends(get_db),
                          _: User = Depends(get_current_user)):
    kps = CourseService.list_knowledge_points(db, chapter_id)
    return ok([knowledge_point_out(k) for k in kps])


@router.post("/chapters/{chapter_id}/knowledge-points", summary="新建知识点")
def create_knowledge_point(chapter_id: int, data: KnowledgePointCreate,
                           user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    kp = CourseService.create_knowledge_point(db, chapter_id, data, user.uid)
    return ok(knowledge_point_out(kp), message="知识点已创建")


@router.put("/chapters/{chapter_id}/knowledge-points/{kp_id}", summary="更新知识点")
def update_knowledge_point(chapter_id: int, kp_id: int, data: KnowledgePointUpdate,
                           user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    kp = CourseService.update_knowledge_point(db, kp_id, data)
    return ok(knowledge_point_out(kp), message="知识点已更新")


@router.delete("/chapters/{chapter_id}/knowledge-points/{kp_id}", summary="删除知识点")
def delete_knowledge_point(chapter_id: int, kp_id: int,
                           user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    CourseService.delete_knowledge_point(db, kp_id)
    return ok(message="知识点已删除")

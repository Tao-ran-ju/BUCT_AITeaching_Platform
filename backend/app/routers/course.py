"""课程路由：课程 CRUD + 知识图谱。"""
import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.routers import ok
from app.schemas.course import CourseCreate, CourseUpdate, KnowledgeGraphUpsert
from app.services.course_service import CourseService
from app.utils.serializers import course_out

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

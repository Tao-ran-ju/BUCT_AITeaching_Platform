"""学习任务路由：发布 / 列表 / 详情 / 改删 / 学生标记完成。"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.routers import ok
from app.schemas.task import TaskCreate, TaskOut, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["学习任务"])


@router.get("", summary="任务列表（含完成进度）")
def list_tasks(
    course_id: Optional[int] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tasks = TaskService.list_tasks(db, course_id)
    return ok([TaskOut.model_validate(t) for t in tasks])


@router.post("", summary="发布任务")
def create_task(data: TaskCreate, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    task = TaskService.create_task(db, user, data)
    return ok(TaskOut.model_validate(task), message="任务已发布")


@router.get("/{task_id}", summary="任务详情")
def get_task(task_id: int, user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    task = TaskService.get_task_out(db, task_id)
    return ok(TaskOut.model_validate(task))


@router.put("/{task_id}", summary="更新任务")
def update_task(task_id: int, data: TaskUpdate,
                user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    task = TaskService.update_task(db, task_id, data)
    return ok(TaskOut.model_validate(task))


@router.delete("/{task_id}", summary="删除任务")
def delete_task(task_id: int, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    TaskService.delete_task(db, task_id)
    return ok(message="任务已删除")


@router.post("/{task_id}/complete", summary="学生标记任务完成")
def complete_task(task_id: int, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    result = TaskService.complete(db, user, task_id)
    return ok(result, message="已完成该任务")

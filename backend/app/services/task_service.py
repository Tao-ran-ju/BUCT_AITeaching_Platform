"""班级任务服务：发布任务、跟踪完成进度（class_tasks / class_task_completions）。"""
import time
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError, ValidateError
from app.models.class_ import ClassTask, ClassTaskCompletion
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate
from app.utils.identity import class_member_users


class TaskService:
    """任务发布与完成进度业务逻辑。

    学校模型为班级级轻量任务：ClassTask 记录任务本体，ClassTaskCompletion 记录
    学生完成打卡（学生主动完成，无「指派名单」）。出参 total_students 取班级成员数。
    """

    @staticmethod
    def _now() -> int:
        return int(time.time())

    @staticmethod
    def _completions(db: Session, task_id: int) -> list[ClassTaskCompletion]:
        return list(
            db.scalars(
                select(ClassTaskCompletion).where(ClassTaskCompletion.task_id == task_id)
            ).all()
        )

    @staticmethod
    def _to_out(db: Session, task: ClassTask) -> dict:
        members = class_member_users(db, task.class_id)
        completions = TaskService._completions(db, task.id)
        completed_map = {c.student_user_id: c for c in completions}
        completed_count = sum(1 for u in members if u.id in completed_map)
        return {
            "id": task.id,
            "class_id": task.class_id,
            "task_type": task.task_type,
            "content": task.content,
            "deadline": task.deadline,
            "status": task.status,
            "created_by": task.created_by,
            "created_at": task.created_at,
            "total_students": len(members),
            "student_count": len(members),
            "completed_count": completed_count,
            "assignments": [
                {
                    "student_id": u.id,
                    "name": u.name,
                    "username": u.uid,
                    "status": "completed" if u.id in completed_map else "pending",
                    "completed_at": completed_map[u.id].completed_at if u.id in completed_map else None,
                }
                for u in members
            ],
        }

    @staticmethod
    def list_completions(db: Session, task_id: int) -> list[dict]:
        """返回班级全体成员对该任务的完成情况（含未完成）。"""
        task = TaskService.get_task(db, task_id)
        members = class_member_users(db, task.class_id)
        completed = {c.student_user_id: c for c in TaskService._completions(db, task_id)}
        return [
            {
                "student_id": u.id,
                "uid": u.uid,
                "name": u.name,
                "completed_at": completed[u.id].completed_at if u.id in completed else None,
                "completed": u.id in completed,
            }
            for u in members
        ]

    @staticmethod
    def create_task(db: Session, user: User, data: TaskCreate) -> dict:
        task = ClassTask(
            class_id=data.class_id,
            task_type=data.task_type,
            content=data.content,
            deadline=data.deadline,
            status=0,
            created_at=TaskService._now(),
            edited_at=TaskService._now(),
            created_by=user.uid,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return TaskService._to_out(db, task)

    @staticmethod
    def list_tasks(db: Session, class_ids: list[int] | None = None) -> list[dict]:
        stmt = select(ClassTask)
        if class_ids:
            stmt = stmt.where(ClassTask.class_id.in_(class_ids))
        tasks = db.scalars(stmt.order_by(ClassTask.id.desc())).all()
        return [TaskService._to_out(db, t) for t in tasks]

    @staticmethod
    def get_task(db: Session, task_id: int) -> ClassTask:
        task = db.get(ClassTask, task_id)
        if not task:
            raise NotFoundError("任务不存在")
        return task

    @staticmethod
    def get_task_out(db: Session, task_id: int) -> dict:
        return TaskService._to_out(db, TaskService.get_task(db, task_id))

    @staticmethod
    def update_task(db: Session, task_id: int, data: TaskUpdate) -> dict:
        task = TaskService.get_task(db, task_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(task, field, value)
        task.edited_at = TaskService._now()
        db.commit()
        db.refresh(task)
        return TaskService._to_out(db, task)

    @staticmethod
    def delete_task(db: Session, task_id: int) -> None:
        task = TaskService.get_task(db, task_id)
        db.execute(delete(ClassTaskCompletion).where(ClassTaskCompletion.task_id == task_id))
        db.delete(task)
        db.commit()

    @staticmethod
    def complete(db: Session, user: User, task_id: int) -> dict:
        """当前学生将本人任务标记为已完成（幂等，重复完成返回已有记录）。"""
        TaskService.get_task(db, task_id)
        existing = db.scalar(
            select(ClassTaskCompletion).where(
                ClassTaskCompletion.task_id == task_id,
                ClassTaskCompletion.student_user_id == user.id,
            )
        )
        if existing:
            return {
                "task_id": task_id,
                "student_id": user.id,
                "completed_at": existing.completed_at,
            }
        completion = ClassTaskCompletion(
            task_id=task_id,
            student_user_id=user.id,
            completed_at=datetime.now(),
            status=0,
        )
        db.add(completion)
        db.commit()
        db.refresh(completion)
        return {
            "task_id": task_id,
            "student_id": user.id,
            "completed_at": completion.completed_at,
        }

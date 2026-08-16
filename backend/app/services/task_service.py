"""学习任务服务：发布任务、指派学生、跟踪完成进度。"""
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError, ValidateError
from app.models.task import Task, TaskAssignment
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    """任务发布与完成进度业务逻辑。"""

    @staticmethod
    def _assignments(db: Session, task_id: int) -> list[TaskAssignment]:
        return list(
            db.scalars(
                select(TaskAssignment).where(TaskAssignment.task_id == task_id)
            ).all()
        )

    @staticmethod
    def _to_out(db: Session, task: Task) -> dict:
        rows = TaskService._assignments(db, task.id)
        student_ids = [r.student_id for r in rows]
        users = (
            db.scalars(select(User).where(User.id.in_(student_ids))).all()
            if student_ids else []
        )
        user_map = {u.id: u for u in users}
        assignments = [
            {
                "student_id": r.student_id,
                "name": user_map[r.student_id].name if r.student_id in user_map else "",
                "username": user_map[r.student_id].username if r.student_id in user_map else "",
                "status": r.status,
                "completed_at": r.completed_at,
            }
            for r in rows
        ]
        completed = sum(1 for r in rows if r.status == "completed")
        return {
            "id": task.id,
            "course_id": task.course_id,
            "title": task.title,
            "description": task.description,
            "task_type": task.task_type,
            "deadline": task.deadline,
            "created_by": task.created_by,
            "created_at": task.created_at,
            "student_count": len(rows),
            "completed_count": completed,
            "assignments": assignments,
        }

    @staticmethod
    def create_task(db: Session, user: User, data: TaskCreate) -> dict:
        task = Task(
            course_id=data.course_id,
            title=data.title,
            description=data.description,
            task_type=data.task_type,
            deadline=data.deadline,
            created_by=user.id,
        )
        db.add(task)
        db.flush()
        for sid in set(data.student_ids):
            db.add(TaskAssignment(task_id=task.id, student_id=sid))
        db.commit()
        db.refresh(task)
        return TaskService._to_out(db, task)

    @staticmethod
    def list_tasks(db: Session, course_id: int | None = None) -> list[dict]:
        stmt = select(Task)
        if course_id is not None:
            stmt = stmt.where(Task.course_id == course_id)
        tasks = db.scalars(stmt.order_by(Task.id.desc())).all()
        return [TaskService._to_out(db, t) for t in tasks]

    @staticmethod
    def get_task(db: Session, task_id: int) -> Task:
        task = db.get(Task, task_id)
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
        db.commit()
        db.refresh(task)
        return TaskService._to_out(db, task)

    @staticmethod
    def delete_task(db: Session, task_id: int) -> None:
        task = TaskService.get_task(db, task_id)
        db.execute(delete(TaskAssignment).where(TaskAssignment.task_id == task_id))
        db.delete(task)
        db.commit()

    @staticmethod
    def complete(db: Session, user: User, task_id: int) -> dict:
        """当前用户将本人被指派的任务标记为已完成。"""
        TaskService.get_task(db, task_id)
        assignment = db.scalar(
            select(TaskAssignment).where(
                TaskAssignment.task_id == task_id,
                TaskAssignment.student_id == user.id,
            )
        )
        if not assignment:
            raise ValidateError("你不在该任务的指派名单中")
        assignment.status = "completed"
        assignment.completed_at = datetime.now()
        db.commit()
        db.refresh(assignment)
        return {
            "task_id": task_id,
            "student_id": user.id,
            "status": assignment.status,
            "completed_at": assignment.completed_at,
        }

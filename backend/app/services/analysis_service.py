"""数据分析服务：驾驶舱指标、能力矩阵热力图、任务进度、成绩分布、教学效果对比。"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.assignment import Assignment, AssignmentSubmission
from app.models.class_ import ClassTask, ClassTaskCompletion
from app.models.course import Course
from app.models.resource import Resource
from app.models.user import ROLE_STUDENT, ROLE_TEACHER, User
from app.schemas.analysis import DashboardOverview, HeatmapCell, MetricCard
from app.utils.identity import class_member_users


class AnalysisService:
    """面向教师的数据驾驶舱与教学分析。"""

    @staticmethod
    def overview(db: Session) -> DashboardOverview:
        """核心指标看板：师生数 / 课程 / 资源 / 通过率 / 平均分。"""
        total_students = db.scalar(select(func.count(User.id)).where(User.role == ROLE_STUDENT)) or 0
        total_teachers = db.scalar(select(func.count(User.id)).where(User.role == ROLE_TEACHER)) or 0
        total_courses = db.scalar(select(func.count(Course.id))) or 0
        total_resources = db.scalar(select(func.count(Resource.id))) or 0
        submissions = db.scalars(select(AssignmentSubmission)).all()

        passed = sum(1 for s in submissions if (s.score or 0) >= 60)
        pass_rate = passed / len(submissions) if submissions else 0.0
        avg_score = (
            sum(s.score or 0 for s in submissions) / len(submissions)
            if submissions else 0.0
        )

        metrics = [
            MetricCard(key="total_students", label="学生总数", value=total_students),
            MetricCard(key="total_teachers", label="教师总数", value=total_teachers),
            MetricCard(key="total_courses", label="课程总数", value=total_courses),
            MetricCard(key="total_resources", label="教学资源数", value=total_resources),
            MetricCard(key="pass_rate", label="作业通过率", value=round(pass_rate * 100, 2), unit="%"),
            MetricCard(key="avg_score", label="平均分", value=round(avg_score, 2), unit="分"),
        ]
        return DashboardOverview(metrics=metrics, heatmap=[])

    @staticmethod
    def capability_heatmap(db: Session, course_id: int | None = None) -> list[HeatmapCell]:
        """能力矩阵热力图：按作业汇总平均得分（0-1）。"""
        rows = db.execute(
            select(AssignmentSubmission.score, AssignmentSubmission.assignment_id)
        ).all()
        cells: list[HeatmapCell] = []
        for score, aid in rows:
            if score is None:
                continue
            cells.append(HeatmapCell(knowledge_point=f"作业#{aid}", value=round(score / 100, 2)))
        if not cells:
            cells.append(HeatmapCell(knowledge_point="暂无数据", value=0))
        return cells[:20]

    @staticmethod
    def task_progress(db: Session) -> dict:
        """全局任务进度热力图：学生 × 任务 完成情况矩阵。"""
        tasks = db.scalars(select(ClassTask).order_by(ClassTask.id.desc())).all()
        completions = db.scalars(select(ClassTaskCompletion)).all()

        completed_by_task: dict[int, set[int]] = {t.id: set() for t in tasks}
        for c in completions:
            if c.task_id in completed_by_task:
                completed_by_task[c.task_id].add(c.student_user_id)

        # 汇总所有涉及班级的成员，作为热力图列
        all_member_ids: set[int] = set()
        for t in tasks:
            for u in class_member_users(db, t.class_id):
                all_member_ids.add(u.id)
        user_map = (
            {u.id: u for u in db.scalars(select(User).where(User.id.in_(all_member_ids))).all()}
            if all_member_ids else {}
        )

        student_cols = [
            {"student_id": uid, "name": user_map[uid].name if uid in user_map else str(uid)}
            for uid in all_member_ids
        ]

        task_list = []
        for t in tasks:
            member_ids = {u.id for u in class_member_users(db, t.class_id)}
            cells = {sid: "completed" for sid in member_ids if sid in completed_by_task[t.id]}
            total = len(member_ids)
            completed = len(cells)
            task_list.append({
                "task_id": t.id,
                "title": (t.content or "")[:30],
                "course_name": None,
                "deadline": t.deadline.isoformat() if t.deadline else None,
                "total": total,
                "completed": completed,
                "rate": round(completed / total, 3) if total else 0.0,
                "cells": cells,
            })
        return {"student_cols": student_cols, "tasks": task_list}

    @staticmethod
    def score_distribution(db: Session) -> dict:
        """成绩分布：作业得分区间人数统计。"""
        scores = [
            s.score for s in db.scalars(
                select(AssignmentSubmission).where(AssignmentSubmission.score.isnot(None))
            ).all()
        ]
        buckets = [
            ("0-59", "不及格", 0, 60),
            ("60-69", "及格", 60, 70),
            ("70-79", "中等", 70, 80),
            ("80-89", "良好", 80, 90),
            ("90-100", "优秀", 90, 101),
        ]
        result = [
            {"range": key, "label": label, "count": sum(1 for s in scores if lo <= s < hi)}
            for key, label, lo, hi in buckets
        ]
        return {"buckets": result, "total": len(scores)}

    @staticmethod
    def effect_compare(db: Session) -> list[dict]:
        """教学效果对比：按课程汇总平均分 / 通过率 / 提交数。"""
        rows = db.execute(
            select(Assignment.course_id, AssignmentSubmission.score)
            .join(AssignmentSubmission, AssignmentSubmission.assignment_id == Assignment.id)
        ).all()
        course_ids = {cid for cid, _ in rows if cid}
        course_map = (
            {c.id: c.name for c in db.scalars(select(Course).where(Course.id.in_(course_ids))).all()}
            if course_ids else {}
        )
        agg: dict[int, dict] = {}
        for course_id, score in rows:
            if course_id is None:
                continue
            d = agg.setdefault(course_id, {"scores": [], "count": 0})
            d["count"] += 1
            if score is not None:
                d["scores"].append(score)
        result = []
        for cid, d in agg.items():
            scores = d["scores"]
            avg = sum(scores) / len(scores) if scores else 0.0
            passed = sum(1 for s in scores if s >= 60)
            result.append({
                "course_id": cid,
                "course_name": course_map.get(cid, f"课程#{cid}"),
                "avg_score": round(avg, 2),
                "pass_rate": round(passed / len(scores), 3) if scores else 0.0,
                "submission_count": d["count"],
            })
        result.sort(key=lambda x: x["avg_score"], reverse=True)
        return result

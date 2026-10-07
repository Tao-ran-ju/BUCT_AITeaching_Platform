"""演示数据灌入脚本：写入学习行为与作业提交数据并触发学情预警扫描。

背景：学情预警的规则引擎（WarningService.scan）基于真实数据扫描：
  - 低分（low_score）     —— 作业平均分低于阈值（默认 30 分）→ 高危
  - 提交延迟（submit_delay）—— 超期提交次数达到阈值（默认 3 次）→ 中危
  - 长期未活跃（absent）  —— 近 N 天既无提交也无行为日志（默认 3 天）→ 中危

在没有真实数据时预警列表会是空的，本脚本灌入演示教师/课程/班级/学生，
并为 5 名演示学生构造「低分 / 提交延迟 / 未活跃 / 正常」等场景后触发扫描。

用法（务必在 backend/ 目录下执行，保证能读到 .env）：
    python scripts/seed_study_behavior.py
"""
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models.assignment import Assignment, AssignmentSubmission  # noqa: E402
from app.models.class_ import ClassRoom  # noqa: E402
from app.models.course import Course  # noqa: E402
from app.models.user import ROLE_STUDENT, ROLE_TEACHER, User  # noqa: E402
from app.models.warning import StudentWarning, StudyBehavior  # noqa: E402
from app.services.warning_service import WarningService  # noqa: E402
from app.utils.security import hash_password  # noqa: E402

DEMO_TEACHER = dict(uid="1001", name="演示教师", password="demo123456")
DEMO_COURSE = dict(name="算法设计与分析")
DEMO_CLASS = dict(name="演示教学班")

# (姓名, 学号) —— 学号必须是数字字符串，与 class_record.uid / 预警的数值 ID 约定一致
DEMO_STUDENTS = [
    ("张伟", "2022040101"),
    ("李娜", "2022040102"),
    ("王强", "2022040103"),
    ("赵敏", "2022040104"),
    ("陈晨", "2022040105"),
]


def _now() -> int:
    return int(time.time())


def _get_or_create_user(db, uid: str, name: str, role: int) -> User:
    user = db.scalar(select(User).where(User.uid == uid))
    if user:
        return user
    now = _now()
    user = User(
        uid=uid,
        password_hash=hash_password("demo123456"),
        name=name,
        role=role,
        college="",
        created_at=now,
        edited_at=now,
        created_by=0,
    )
    db.add(user)
    db.flush()
    return user


def main() -> None:
    db = SessionLocal()
    try:
        now = datetime.now()

        # 1. 演示教师
        teacher = _get_or_create_user(db, DEMO_TEACHER["uid"], DEMO_TEACHER["name"], ROLE_TEACHER)
        print(f"[教师] {teacher.name} (uid={teacher.uid}, id={teacher.id})")

        # 2. 演示课程
        course = db.scalar(select(Course).where(Course.name == DEMO_COURSE["name"]))
        if not course:
            course = Course(
                name=DEMO_COURSE["name"],
                teacher_user_id=teacher.id,
                status=1,  # 已发布
                created_at=_now(),
                edited_at=_now(),
            )
            db.add(course)
            db.flush()
            print(f"[课程] {course.name} (id={course.id})")
        else:
            print(f"[课程] {course.name}（复用, id={course.id})")

        # 3. 演示班级（作业需关联班级）
        class_ = db.scalar(select(ClassRoom).where(ClassRoom.name == DEMO_CLASS["name"]))
        if not class_:
            class_ = ClassRoom(
                name=DEMO_CLASS["name"],
                course=course.name,
                private=0,
                created_at=_now(),
                edited_at=_now(),
            )
            db.add(class_)
            db.flush()
            print(f"[班级] {class_.name} (id={class_.id})")
        else:
            print(f"[班级] {class_.name}（复用, id={class_.id})")

        # 4. 演示学生（学号 -> user_rft.id 映射）
        students = {}
        for name, uid in DEMO_STUDENTS:
            s = _get_or_create_user(db, uid, name, ROLE_STUDENT)
            students[uid] = s
            print(f"[学生] {name} ({uid}, id={s.id})")

        # 5. 作业：A1/A2/A3 已截止（用于构造低分与提交延迟），A4 未截止（用于「正常」场景）
        def ensure_assignment(title: str, deadline: datetime) -> Assignment:
            a = db.scalar(select(Assignment).where(Assignment.title == title))
            if a:
                return a
            a = Assignment(
                course_id=course.id,
                class_id=class_.id,
                publisher_user_id=teacher.id,
                title=title,
                content=title,
                deadline=deadline,
                status=0,
                created_at=_now(),
                edited_at=_now(),
                total_students=len(DEMO_STUDENTS),
            )
            db.add(a)
            db.flush()
            return a

        a1 = ensure_assignment("演示作业一：分治法", now - timedelta(days=2))
        a2 = ensure_assignment("演示作业二：动态规划", now - timedelta(days=2))
        a3 = ensure_assignment("演示作业三：图论", now - timedelta(days=2))
        a4 = ensure_assignment("演示作业四：串讲练习", now + timedelta(days=5))

        # 6. 提交记录（一人一作业一次提交）
        def add_submission(student_uid: str, assignment: Assignment,
                           score: float, submitted_at: datetime) -> None:
            s = students[student_uid]
            existing = db.scalar(
                select(AssignmentSubmission).where(
                    AssignmentSubmission.assignment_id == assignment.id,
                    AssignmentSubmission.student_user_id == s.id,
                )
            )
            if existing:
                return
            db.add(AssignmentSubmission(
                assignment_id=assignment.id,
                student_user_id=s.id,
                content="演示提交内容",
                submitted_at=submitted_at,
                status=1,
                score=score,
                created_at=_now(),
                edited_at=_now(),
            ))

        late = now - timedelta(days=1)  # 晚于 A1/A2/A3 截止时间
        # 张伟：低分（均分 20 < 30）→ 高危 low_score
        add_submission("2022040101", a1, 15.0, late)
        add_submission("2022040101", a2, 25.0, late)
        # 李娜：3 次超期提交 → 中危 submit_delay
        add_submission("2022040102", a1, 70.0, late)
        add_submission("2022040102", a2, 75.0, late)
        add_submission("2022040102", a3, 80.0, late)
        # 赵敏：按时提交、高分 → 无预警（正常对照组）
        add_submission("2022040104", a4, 88.0, now)

        # 7. 学习行为日志：除「王强」外都写入近期行为，使「王强」触发 absent 预警
        for name, uid in DEMO_STUDENTS:
            if uid == "2022040103":  # 王强：不写行为日志，模拟长期未活跃
                continue
            s = students[uid]
            db.add(StudyBehavior(
                student_user_id=s.id,
                course_id=course.id,
                behavior_type="login",
                value="演示登录行为",
                created_at=_now(),
            ))

        db.commit()
        print("\n已写入演示教师/课程/班级/5 名学生/作业提交/学习行为数据。")

        # 8. 触发规则引擎扫描
        warnings = WarningService.scan(db)
        print(f"扫描完成，本次生成 {len(warnings)} 条新预警。")

        # 9. 打印当前未处理预警
        rows = db.scalars(
            select(StudentWarning)
            .where(StudentWarning.status == "open")
            .order_by(StudentWarning.student_user_id)
        ).all()
        print("\n当前未处理预警：")
        if not rows:
            print("  （无）")
        id_to_name = {s.id: s.name for s in students.values()}
        for w in rows:
            label = id_to_name.get(w.student_user_id, f"学生#{w.student_user_id}")
            print(f"  [{w.level:<8}] {label}（{w.warning_type}）: {w.detail}")

        print("\n提示：演示账号密码均为 demo123456；可登录教师端在「学情预警」查看。")
    finally:
        db.close()


if __name__ == "__main__":
    main()

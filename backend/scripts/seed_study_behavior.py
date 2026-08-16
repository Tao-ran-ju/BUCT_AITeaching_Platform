"""演示数据灌入脚本：写入学习行为数据并触发学情预警扫描。

背景：学情预警的「学习不积极」规则依赖 study_behavior 表里的
login_duration / resource_visits 等字段，而这些数据平时由学生端行为采集
写入；在没有真实行为数据时，预警列表会是空的。

本脚本会：
  1. 若无演示教师 / 课程 / 学生，则自动创建；
  2. 为每个演示学生写入今日份学习行为（覆盖多种预警场景）；
  3. 调用规则引擎扫描，直接产出预警记录。

用法（务必在 backend/ 目录下执行，保证能读到 .env）：
    python scripts/seed_study_behavior.py
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.course import Course  # noqa: E402
from app.models.warning import StudyBehavior, StudentWarning  # noqa: E402
from app.services.warning_service import WarningService  # noqa: E402
from app.utils.security import hash_password  # noqa: E402
import app.models  # noqa: E402,F401  # 确保所有模型已注册到 Base.metadata

DEMO_TEACHER = dict(username="demo_teacher", name="演示教师", password="demo123456")
DEMO_COURSE = dict(name="算法设计与分析", code="DEMO001")

# (姓名, 学号)
DEMO_STUDENTS = [
    ("张伟", "2022040101"),
    ("李娜", "2022040102"),
    ("王强", "2022040103"),
    ("赵敏", "2022040104"),
    ("陈晨", "2022040105"),
]

# 与 DEMO_STUDENTS 一一对应：login_duration(秒) / resource_visits(次)
# / submit_delay_days / homework_score，故意制造不同预警等级。
SCENARIOS = [
    dict(login_duration=120, resource_visits=1, submit_delay_days=None, homework_score=None),  # 学习不积极 → 中
    dict(login_duration=300, resource_visits=5, submit_delay_days=5, homework_score=None),      # 提交延迟+不积极 → 中
    dict(login_duration=2400, resource_visits=8, submit_delay_days=1, homework_score=25.0),     # 正确率低 → 高
    dict(login_duration=5400, resource_visits=15, submit_delay_days=0, homework_score=88.0),    # 正常，无预警
    dict(login_duration=60, resource_visits=0, submit_delay_days=6, homework_score=18.0),       # 多重叠加 → 高
]


def main() -> None:
    # 兜底建表（表不存在时）
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. 演示教师
        teacher = db.scalar(select(User).where(User.username == DEMO_TEACHER["username"]))
        if not teacher:
            teacher = User(
                username=DEMO_TEACHER["username"],
                password_hash=hash_password(DEMO_TEACHER["password"]),
                name=DEMO_TEACHER["name"],
                role="teacher",
            )
            db.add(teacher)
            db.flush()
            print(f"[创建教师] {teacher.name} (id={teacher.id})")
        else:
            print(f"[复用教师] {teacher.name} (id={teacher.id})")

        # 2. 演示课程
        course = db.scalar(select(Course).where(Course.code == DEMO_COURSE["code"]))
        if not course:
            course = Course(
                name=DEMO_COURSE["name"],
                code=DEMO_COURSE["code"],
                teacher_id=teacher.id,
                status="published",
            )
            db.add(course)
            db.flush()
            print(f"[创建课程] {course.name} (id={course.id})")
        else:
            print(f"[复用课程] {course.name} (id={course.id})")

        # 3. 演示学生 + 今日学习行为
        today = date.today()
        seeded = []  # (student, scenario)
        for (name, username), sc in zip(DEMO_STUDENTS, SCENARIOS):
            student = db.scalar(select(User).where(User.username == username))
            if not student:
                student = User(
                    username=username,
                    password_hash=hash_password("demo123456"),
                    name=name,
                    role="student",
                )
                db.add(student)
                db.flush()
                print(f"[创建学生] {name} ({username}, id={student.id})")
            else:
                print(f"[复用学生] {name} ({username}, id={student.id})")

            behavior = db.scalar(
                select(StudyBehavior).where(
                    StudyBehavior.student_id == student.id,
                    StudyBehavior.behavior_date == today,
                )
            )
            if behavior:
                behavior.course_id = course.id
                behavior.login_duration = sc["login_duration"]
                behavior.resource_visits = sc["resource_visits"]
                behavior.submit_delay_days = sc["submit_delay_days"]
                behavior.homework_score = sc["homework_score"]
            else:
                db.add(StudyBehavior(
                    student_id=student.id,
                    course_id=course.id,
                    behavior_date=today,
                    **sc,
                ))
            seeded.append((student, sc))
        db.commit()
        print(f"\n已写入 {len(seeded)} 名学生今日份学习行为（日期 {today}）。")

        # 4. 触发规则引擎扫描
        warnings = WarningService.scan(db)
        print(f"扫描完成，本次生成 {len(warnings)} 条新预警。")

        # 5. 打印当前未处理预警
        ids = [s.id for s, _ in seeded]
        name_map = {s.id: s.name for s, _ in seeded}
        rows = db.scalars(
            select(StudentWarning)
            .where(StudentWarning.student_id.in_(ids), StudentWarning.is_resolved.is_(False))
            .order_by(StudentWarning.student_id)
        ).all()

        print("\n当前未处理预警：")
        if not rows:
            print("  （无）")
        for w in rows:
            name = name_map.get(w.student_id, f"学生#{w.student_id}")
            print(f"  [{w.risk_level:<6}] {name}: {w.reason}")

        print("\n提示：演示账号密码均为 demo123456；可登录教师端在「数据驾驶舱」查看。")
    finally:
        db.close()


if __name__ == "__main__":
    main()

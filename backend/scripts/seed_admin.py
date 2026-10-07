"""初始化首个账号脚本（默认创建管理员）。

背景：建表脚本只建表、不建账号，而 /auth/register 又要求教师身份，
因此首次启动必须用本脚本直接在数据库中写入第一个账号，之后才能正常登录。

用法（务必在 backend/ 目录下执行，保证能读到 .env）：
    python scripts/seed_admin.py --uid admin --password admin123456 --name 系统管理员

可选参数：
    --uid       工号/学号（默认 admin，对应 user_rft.uid，登录账号）
    --password  密码（默认 admin123456，生产环境请自行修改）
    --name      姓名（默认 系统管理员）
    --role      admin | teacher | student（默认 admin；admin/teacher 均映射为角色 0=教师）
"""
import argparse
import sys
import time
from pathlib import Path

# 将 backend/ 目录加入模块搜索路径，便于直接 import app.*
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models.user import ROLE_STUDENT, ROLE_TEACHER, User  # noqa: E402
from app.utils.security import hash_password  # noqa: E402

# 命令行角色 -> user_rft.role 整数（0=教师 1=学生）；教师端无独立 admin 角色，
# 「管理员」即教师（dependencies.get_current_admin 以 role==0 判定）。
ROLE_MAP = {
    "admin": ROLE_TEACHER,
    "teacher": ROLE_TEACHER,
    "student": ROLE_STUDENT,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="创建首个账号（默认管理员）")
    parser.add_argument("--uid", default="admin", help="工号/学号，默认 admin")
    parser.add_argument("--password", default="admin123456", help="密码，默认 admin123456")
    parser.add_argument("--name", default="系统管理员", help="姓名，默认 系统管理员")
    parser.add_argument("--role", default="admin", choices=["admin", "teacher", "student"])
    args = parser.parse_args()

    db = SessionLocal()
    try:
        exists = db.scalar(select(User).where(User.uid == args.uid))
        if exists:
            print(f"账号 {args.uid} 已存在，跳过创建。")
            return

        now = int(time.time())
        user = User(
            uid=args.uid,
            password_hash=hash_password(args.password),
            name=args.name,
            role=ROLE_MAP[args.role],
            college="",
            created_at=now,
            edited_at=now,
            created_by=0,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"创建成功：uid={user.uid}  name={user.name}  role={user.role}  id={user.id}")
        print("现在可用该账号调用 /auth/login 登录。")
    finally:
        db.close()


if __name__ == "__main__":
    main()

"""Batch A 数据库迁移脚本（幂等）。

为「补地基」批次新增的表 / 字段补到现有 MySQL 库：
- 新表：task / task_assignment（由 create_all 自动建）
- 已有表新增列：
    course.open_time           课程开放时间
    student_warning.intervention  干预措施记录
    student_warning.resolved_at   处理时间

用法（在 backend/ 目录下）：
    python scripts/migrate_batch_a.py

幂等：列已存在则跳过，可重复执行。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect, text  # noqa: E402

from app.database import Base, engine  # noqa: E402
import app.models  # noqa: E402,F401


# 表名 -> [(列名, DDL)]
NEW_COLUMNS = {
    "course": [
        ("open_time", "ALTER TABLE course ADD COLUMN open_time DATETIME NULL COMMENT '课程开放时间'"),
    ],
    "student_warning": [
        ("intervention", "ALTER TABLE student_warning ADD COLUMN intervention TEXT NULL COMMENT '教师填写的干预措施记录'"),
        ("resolved_at", "ALTER TABLE student_warning ADD COLUMN resolved_at DATETIME NULL COMMENT '处理时间'"),
    ],
}


def ensure_column(inspector, table: str, column: str, ddl: str) -> None:
    existing = {c["name"] for c in inspector.get_columns(table)}
    if column in existing:
        print(f"[=] {table}.{column} 已存在，跳过")
        return
    with engine.begin() as conn:
        conn.execute(text(ddl))
    print(f"[+] {table}.{column} 已添加")


def main() -> None:
    print(f"连接数据库: {engine.url.render_as_string(hide_password=True)}")

    # 1) 新建缺失的表（task / task_assignment）
    Base.metadata.create_all(bind=engine)
    print("[+] 新表已确保创建（task / task_assignment）")

    # 2) 为已有表补列
    inspector = inspect(engine)
    for table, columns in NEW_COLUMNS.items():
        for column, ddl in columns:
            ensure_column(inspector, table, column, ddl)

    print("Batch A 迁移完成。")


if __name__ == "__main__":
    main()

"""Batch H 数据库迁移脚本（幂等）。

为「课程资源」板块补充课程封面图字段：
- 已有表新增列：
    courses.cover           课程封面图相对路径（uploads/...）

用法（在 backend/ 目录下）：
    python scripts/migrate_batch_h.py

幂等：列已存在则跳过，可重复执行。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect, text  # noqa: E402

from app.database import engine  # noqa: E402


# 表名 -> [(列名, DDL)]
NEW_COLUMNS = {
    "courses": [
        ("cover", "ALTER TABLE courses ADD COLUMN cover VARCHAR(500) NULL COMMENT '课程封面图相对路径'"),
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
    inspector = inspect(engine)
    for table, columns in NEW_COLUMNS.items():
        for column, ddl in columns:
            ensure_column(inspector, table, column, ddl)
    print("Batch H 迁移完成。")


if __name__ == "__main__":
    main()

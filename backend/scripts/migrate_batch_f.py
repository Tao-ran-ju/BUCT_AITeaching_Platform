"""Batch F 数据库迁移脚本（幂等）。

为阿里云 OSS 接入新增的 resource 字段补到现有 MySQL 库：
    resource.oss_key  已镜像到 OSS 的 object key（null 表示仅本地）

用法（在 backend/ 目录下）：
    python scripts/migrate_batch_f.py

幂等：列已存在则跳过，可重复执行。全新数据库无需本脚本（init_db.py 已建全字段）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect, text  # noqa: E402

from app.database import engine  # noqa: E402

NEW_COLUMNS = {
    "resource": [
        ("oss_key", "ALTER TABLE resource ADD COLUMN oss_key VARCHAR(255) NULL COMMENT '已镜像到 OSS 的 object key'"),
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
    print("Batch F 迁移完成。")


if __name__ == "__main__":
    main()

"""Batch E 数据库迁移脚本（幂等）。

为视频处理（ffmpeg 转码 / 关键帧 / 字幕）新增的 resource 字段补到现有 MySQL 库：
    resource.duration          音视频时长（秒）
    resource.thumbnail_path    关键帧缩略图相对路径
    resource.transcoded_path   转码后 Web 兼容视频相对路径

用法（在 backend/ 目录下）：
    python scripts/migrate_batch_e.py

幂等：列已存在则跳过，可重复执行。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect, text  # noqa: E402

from app.database import engine  # noqa: E402

# 表名 -> [(列名, DDL)]
NEW_COLUMNS = {
    "resource": [
        ("duration", "ALTER TABLE resource ADD COLUMN duration DOUBLE NULL COMMENT '音视频时长（秒）'"),
        ("thumbnail_path", "ALTER TABLE resource ADD COLUMN thumbnail_path VARCHAR(255) NULL COMMENT '视频关键帧缩略图相对路径'"),
        ("transcoded_path", "ALTER TABLE resource ADD COLUMN transcoded_path VARCHAR(255) NULL COMMENT '转码后 Web 兼容视频相对路径'"),
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
    print("Batch E 迁移完成。")


if __name__ == "__main__":
    main()

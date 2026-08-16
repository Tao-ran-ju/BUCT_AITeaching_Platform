"""Batch D 数据库迁移脚本（幂等）。

为「重活」批次新增的字段补到现有 MySQL 库：
    assignment.oj_problem_id            关联学校 OJ 题目 ID（buctcoder）
    assignment.oj_language              OJ 判题语言
    assignment_submission.oj_solution_id  对应 OJ 提交编号

用法（在 backend/ 目录下）：
    python scripts/migrate_batch_d.py

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
    "assignment": [
        ("oj_problem_id", "ALTER TABLE assignment ADD COLUMN oj_problem_id INT NULL COMMENT '关联学校 OJ 题目 ID（buctcoder）'"),
        ("oj_language", "ALTER TABLE assignment ADD COLUMN oj_language VARCHAR(16) NULL COMMENT 'OJ 判题语言（python/cpp/java...）'"),
    ],
    "assignment_submission": [
        ("oj_solution_id", "ALTER TABLE assignment_submission ADD COLUMN oj_solution_id INT NULL COMMENT '对应 OJ 提交编号 solution_id'"),
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

    # 1) 新建缺失的表（qa_question 等）
    Base.metadata.create_all(bind=engine)
    print("[+] 新表已确保创建（qa_question）")

    # 2) 为已有表补列
    inspector = inspect(engine)
    for table, columns in NEW_COLUMNS.items():
        for column, ddl in columns:
            ensure_column(inspector, table, column, ddl)

    print("Batch D 迁移完成。")


if __name__ == "__main__":
    main()

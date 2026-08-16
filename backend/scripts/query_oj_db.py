"""OJ 数据库只读探查脚本（脱敏版）。

凭据从 backend/.env 的 OJ_DB_* 读取，不在代码中硬编码任何敏感信息。

用法（在 backend/ 目录下）：
    python scripts/query_oj_db.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pymysql  # noqa: E402
from app.config import settings  # noqa: E402


def query_mysql() -> None:
    """连接学校 OJ 库，列出所有表，并示例查询指定表前 100 条。"""
    config = {
        "host": settings.OJ_DB_HOST,
        "port": settings.OJ_DB_PORT,
        "user": settings.OJ_DB_USER,
        "password": settings.OJ_DB_PASSWORD,
        "database": settings.OJ_DB_NAME,
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
    }
    if not config["user"]:
        print("未配置 OJ_DB_USER，请在 backend/.env 中填写 OJ 数据库连接信息。")
        return

    connection = None
    try:
        connection = pymysql.connect(**config)
        cursor = connection.cursor()

        # 1. 查看当前数据库所有表
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print(f"=== {settings.OJ_DB_NAME} 库所有表 ===")
        table_list = [t[f"Tables_in_{settings.OJ_DB_NAME}"] for t in tables]
        for name in table_list:
            print(name)

        # 2. 示例：查询某张表全部数据（把 table_name 替换成真实表名）
        table_name = "替换成上面打印出来的表名"
        if table_name in table_list:
            cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 100;")
            rows = cursor.fetchall()
            print(f"\n=== 表 {table_name} 前 100 条数据 ===")
            for row in rows:
                print(row)

    except pymysql.MySQLError as e:
        print(f"数据库连接/查询失败：{e}")
    finally:
        if connection and connection.open:
            connection.close()
            print("\n数据库连接已关闭")


if __name__ == "__main__":
    query_mysql()

"""初始化数据库脚本（兜底方案）。

未安装 / 未使用 Alembic 时，直接根据 ORM 模型建表：

    python scripts/init_db.py

注意：需要先安装依赖（pip install -r requirements.txt），
并确保 .env 中数据库连接可用（本机 MySQL 或远程 DATABASE_URL）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import Base, engine  # noqa: E402
import app.models  # noqa: E402,F401


def main() -> None:
    print(f"正在连接数据库: {engine.url.render_as_string(hide_password=True)}")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成。")


if __name__ == "__main__":
    main()

"""数据库连接：创建 SQLAlchemy Engine / Session / Base。"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


engine = create_engine(
    settings.sqlalchemy_url,
    pool_pre_ping=True,        # 取连接前先 ping，避免 MySQL 断连后复用失效连接
    pool_recycle=3600,         # 连接 1 小时回收一次，规避 MySQL wait_timeout
    echo=settings.DEBUG,       # 调试模式下打印 SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI 依赖：为每个请求提供一个数据库会话，结束后自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

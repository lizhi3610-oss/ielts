from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import DATABASE_URL


connect_args = {}

# SQLite 需要这个参数，否则在 FastAPI 多线程场景下可能报错。
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


def get_db():
    """
    获取数据库会话。

    FastAPI 会在每次请求时创建一个 db session，
    请求结束后自动关闭，避免连接泄漏。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

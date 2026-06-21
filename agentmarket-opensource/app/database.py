"""
异步数据库引擎与会话管理模块

基于 SQLAlchemy 2.0 异步模式，提供：
- 异步引擎（async engine）
- 异步会话工厂（async_sessionmaker）
- FastAPI 依赖注入函数 get_db()
- 声明式基类 Base
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# ── 创建异步引擎 ────────────────────────────────────────────
# echo=True 时会在日志中打印 SQL 语句，便于调试
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# ── 异步会话工厂 ──────────────────────────────────────────────
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── 声明式基类 ────────────────────────────────────────────────
class Base(DeclarativeBase):
    """所有 ORM 模型的基类"""
    pass


# ── FastAPI 依赖：获取数据库会话 ──────────────────────────────
async def get_db() -> AsyncSession:  # type: ignore[misc]
    """
    FastAPI 路由依赖注入函数。
    每个请求获得独立的数据库会话，请求结束后自动关闭。

    用法：
        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

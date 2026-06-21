"""
Alembic 异步迁移环境配置
支持异步 SQLAlchemy 引擎，自动检测模型变更生成迁移脚本
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 导入应用配置
from app.config import settings

# 导入数据库基类
from app.database import Base

# 导入所有模型，确保 metadata 中包含全部表定义
from app.models import user, agent, category, tag, order, license  # noqa: F401

# Alembic Config 对象，提供对 alembic.ini 中值的访问
config = context.config

# 设置数据库连接 URL（从应用配置中读取）
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# 配置 Python 日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标 metadata - 用于 autogenerate 支持
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    离线模式运行迁移
    只需要数据库 URL，不需要实际的数据库连接
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    在给定连接上运行迁移
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    异步模式运行迁移
    使用异步引擎连接数据库
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    在线模式运行迁移（异步）
    创建异步引擎并执行迁移
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

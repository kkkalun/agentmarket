"""
应用全局配置模块

使用 pydantic-settings 从环境变量和 .env 文件中加载配置项，
并以单例模式导出 settings 实例供其他模块使用。

重要：SECRET_KEY 必须通过 .env 或环境变量设置，否则应用将在启动时发出警告。
可使用以下命令生成安全密钥：
    python -c "import secrets; print(secrets.token_urlsafe(32))"
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类，所有字段均可通过环境变量或 .env 文件覆盖"""

    # ── 基础配置 ──────────────────────────────────────────────
    APP_NAME: str = "AgentMarket"
    DEBUG: bool = True

    # ── 安全配置 ──────────────────────────────────────────────
    # 必须通过 .env 或环境变量设置，留空会在启动时发出警告
    # 生成方式：python -c "import secrets; print(secrets.token_urlsafe(32))"
    SECRET_KEY: str = ""

    # ── 数据库配置 ────────────────────────────────────────────
    # 开发环境默认使用 SQLite（异步驱动），生产环境替换为 PostgreSQL（asyncpg）
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"

    # ── JWT 配置 ──────────────────────────────────────────────
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440       # 访问令牌有效期（分钟），默认 24 小时
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7            # 刷新令牌有效期（天）

    # ── GitHub OAuth 配置 ─────────────────────────────────────
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    # GitHub Personal Access Token（可选，用于提高 API 速率限制）
    GITHUB_TOKEN: str = ""

    # ── CORS 跨域配置 ─────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # ── API 前缀 ──────────────────────────────────────────────
    API_PREFIX: str = "/api/v1"

    # ── 限流配置 ──────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 100

    # 从项目根目录的 .env 文件中读取配置
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# 全局单例，其他模块通过 `from app.config import settings` 引用
settings = Settings()

# 启动时检查 SECRET_KEY 是否已配置
if not settings.SECRET_KEY:
    import warnings
    warnings.warn(
        "SECRET_KEY 未配置！请在 .env 文件中设置一个强随机密钥。"
        "生成方式：python -c \"import secrets; print(secrets.token_urlsafe(32))\"",
        RuntimeWarning,
        stacklevel=2,
    )

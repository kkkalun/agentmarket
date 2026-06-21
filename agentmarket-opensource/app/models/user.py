"""
用户模型

定义用户表结构，包括基本账号信息、角色、状态、GitHub OAuth 关联等字段。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _generate_uuid() -> str:
    """生成 32 位无横杠的 UUID"""
    return uuid.uuid4().hex


class User(Base):
    """用户表"""

    __tablename__ = "users"

    # ── 主键 ──────────────────────────────────────────────────
    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=_generate_uuid, comment="用户唯一标识"
    )

    # ── 账号信息 ──────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False, comment="邮箱地址"
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False, comment="用户名"
    )
    display_name: Mapped[str] = mapped_column(
        String(100), nullable=False, default="", comment="显示名称"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="bcrypt 哈希密码"
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="头像 URL"
    )

    # ── 角色与状态 ────────────────────────────────────────────
    # USER / AUTHOR / ADMIN / SUPERADMIN
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="USER", comment="角色：USER/AUTHOR/ADMIN/SUPERADMIN"
    )
    # ACTIVE / INACTIVE / BANNED
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVE", comment="状态：ACTIVE/INACTIVE/BANNED"
    )

    # ── GitHub OAuth ─────────────────────────────────────────
    github_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True, comment="GitHub 用户 ID"
    )

    # ── 订阅计划 ──────────────────────────────────────────────
    # FREE / PRO / ENTERPRISE
    subscription_plan: Mapped[str] = mapped_column(
        String(20), nullable=False, default="FREE", comment="订阅计划：FREE/PRO/ENTERPRISE"
    )

    # ── 时间戳 ────────────────────────────────────────────────
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="邮箱验证时间"
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="最后登录时间"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, comment="注册时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # ── 关系 ──────────────────────────────────────────────────
    agent_templates: Mapped[list["AgentTemplate"]] = relationship(  # noqa: F821
        back_populates="author", lazy="selectin"
    )
    deployments: Mapped[list["Deployment"]] = relationship(  # noqa: F821
        back_populates="user", lazy="selectin"
    )
    orders: Mapped[list["Order"]] = relationship(  # noqa: F821
        back_populates="user", lazy="selectin"
    )
    reviews: Mapped[list["Review"]] = relationship(  # noqa: F821
        back_populates="user", lazy="selectin"
    )
    favorites: Mapped[list["UserFavorite"]] = relationship(  # noqa: F821
        back_populates="user", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"

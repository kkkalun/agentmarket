"""
部署记录模型

记录用户对 Agent 模板的每一次部署操作，包括配置、状态、日志和访问端点。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _generate_uuid() -> str:
    """生成 32 位无横杠的 UUID"""
    return uuid.uuid4().hex


class Deployment(Base):
    """Agent 模板部署记录表"""

    __tablename__ = "deployments"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=_generate_uuid, comment="部署记录唯一标识"
    )
    agent_template_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("agent_templates.id"), nullable=False, comment="Agent 模板 ID"
    )
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id"), nullable=False, comment="部署用户 ID"
    )

    # ── 部署状态 ──────────────────────────────────────────────
    # PENDING / PROVISIONING / RUNNING / STOPPING / STOPPED / FAILED / DELETED
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING",
        comment="状态：PENDING/PROVISIONING/RUNNING/STOPPING/STOPPED/FAILED/DELETED",
    )

    # ── 部署方式 ──────────────────────────────────────────────
    # DOCKER / CLOUD / KUBERNETES
    deploy_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="DOCKER",
        comment="部署方式：DOCKER/CLOUD/KUBERNETES",
    )

    # ── 配置与环境变量（JSON 字符串）───────────────────────────
    config_overrides: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}", comment="自定义配置覆盖（JSON）"
    )
    environment: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}", comment="环境变量（JSON）"
    )

    # ── 运行日志（JSON 数组字符串）─────────────────────────────
    logs: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]", comment="运行日志（JSON 数组）"
    )

    # ── 访问端点 ──────────────────────────────────────────────
    endpoint: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="部署后的访问地址"
    )

    # ── 生命周期时间戳 ────────────────────────────────────────
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="启动时间"
    )
    stopped_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="停止时间"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # ── 关系 ──────────────────────────────────────────────────
    agent_template: Mapped["AgentTemplate"] = relationship(  # noqa: F821
        back_populates="deployments", lazy="selectin"
    )
    user: Mapped["User"] = relationship(back_populates="deployments", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Deployment id={self.id} status={self.status!r}>"

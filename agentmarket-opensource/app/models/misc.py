"""
杂项模型

包含：
- ComplianceRecord：合规审查记录
- Promotion：推广位配置
- UserFavorite：用户收藏
- SystemConfig：系统配置项
- OperationLog：操作日志
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _generate_uuid() -> str:
    """生成 32 位无横杠的 UUID"""
    return uuid.uuid4().hex


# ─────────────────────────────────────────────────────────────
#  合规审查记录
# ─────────────────────────────────────────────────────────────

class ComplianceRecord(Base):
    """Agent 模板合规审查记录"""

    __tablename__ = "compliance_records"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=_generate_uuid, comment="记录唯一标识"
    )
    agent_template_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("agent_templates.id"), nullable=False, comment="Agent 模板 ID"
    )
    review_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="审查类型（如：安全扫描、许可证合规、内容审核）"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", comment="状态：PENDING/PASSED/FAILED"
    )
    findings: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="审查发现（JSON）"
    )
    reviewer_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("users.id"), nullable=True, comment="审查人 ID"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # ── 关系 ──────────────────────────────────────────────────
    agent_template: Mapped["AgentTemplate"] = relationship(  # noqa: F821
        back_populates="compliance", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<ComplianceRecord id={self.id} type={self.review_type!r}>"


# ─────────────────────────────────────────────────────────────
#  推广位配置
# ─────────────────────────────────────────────────────────────

class Promotion(Base):
    """Agent 模板推广配置"""

    __tablename__ = "promotions"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=_generate_uuid, comment="推广记录唯一标识"
    )
    agent_template_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("agent_templates.id"), nullable=False, comment="Agent 模板 ID"
    )
    position: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="推广位排序"
    )
    # ACTIVE / INACTIVE / EXPIRED
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVE", comment="状态：ACTIVE/INACTIVE/EXPIRED"
    )
    # CPT / CPC / CPA
    billing_model: Mapped[str] = mapped_column(
        String(10), nullable=False, default="CPT", comment="计费模式：CPT/CPC/CPA"
    )
    start_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="推广开始时间"
    )
    end_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="推广结束时间"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # ── 关系 ──────────────────────────────────────────────────
    agent_template: Mapped["AgentTemplate"] = relationship(  # noqa: F821
        back_populates="promotions", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Promotion id={self.id} status={self.status!r}>"


# ─────────────────────────────────────────────────────────────
#  用户收藏（多对多中间表）
# ─────────────────────────────────────────────────────────────

class UserFavorite(Base):
    """用户收藏 Agent 模板关联表"""

    __tablename__ = "user_favorites"

    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id"), primary_key=True, comment="用户 ID"
    )
    agent_template_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("agent_templates.id"), primary_key=True, comment="Agent 模板 ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, comment="收藏时间"
    )

    # ── 关系 ──────────────────────────────────────────────────
    user: Mapped["User"] = relationship(back_populates="favorites", lazy="selectin")  # noqa: F821
    agent_template: Mapped["AgentTemplate"] = relationship(  # noqa: F821
        back_populates="favorites", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<UserFavorite user={self.user_id} agent={self.agent_template_id}>"


# ─────────────────────────────────────────────────────────────
#  系统配置项
# ─────────────────────────────────────────────────────────────

class SystemConfig(Base):
    """系统全局配置表（键值对）"""

    __tablename__ = "system_configs"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=_generate_uuid, comment="配置项唯一标识"
    )
    key: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False, comment="配置键名"
    )
    value: Mapped[str] = mapped_column(
        Text, nullable=False, comment="配置值"
    )
    group: Mapped[str] = mapped_column(
        String(50), nullable=False, default="general", comment="配置分组"
    )
    description: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="配置说明"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    def __repr__(self) -> str:
        return f"<SystemConfig key={self.key!r}>"


# ─────────────────────────────────────────────────────────────
#  操作日志
# ─────────────────────────────────────────────────────────────

class OperationLog(Base):
    """系统操作审计日志"""

    __tablename__ = "operation_logs"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=_generate_uuid, comment="日志唯一标识"
    )
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id"), nullable=False, comment="操作用户 ID"
    )
    action: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="操作动作（如 create_agent、approve_review）"
    )
    resource: Mapped[str] = mapped_column(
        String(200), nullable=False, default="", comment="操作对象标识"
    )
    # SUCCESS / FAILURE
    result: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SUCCESS", comment="操作结果：SUCCESS/FAILURE"
    )
    details: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="详细信息（JSON）"
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True, comment="客户端 IP 地址"
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="客户端 User-Agent"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, comment="操作时间"
    )

    def __repr__(self) -> str:
        return f"<OperationLog id={self.id} action={self.action!r}>"

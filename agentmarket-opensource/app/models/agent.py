"""
Agent 模板相关模型

包含：
- AgentTemplate：Agent 模板主表
- Category：分类表（支持自引用树形结构）
- Tag：标签表
- AgentTemplateTag：模板-标签关联表（多对多）
- License：开源许可证表
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _generate_uuid() -> str:
    """生成 32 位无横杠的 UUID"""
    return uuid.uuid4().hex


# ─────────────────────────────────────────────────────────────
#  Agent 模板主表
# ─────────────────────────────────────────────────────────────

class AgentTemplate(Base):
    """Agent 模板表，平台核心实体"""

    __tablename__ = "agent_templates"

    # ── 主键与标识 ────────────────────────────────────────────
    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=_generate_uuid, comment="模板唯一标识"
    )
    slug: Mapped[str] = mapped_column(
        String(200), unique=True, index=True, nullable=False, comment="URL 友好的唯一 slug"
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="模板名称"
    )
    short_description: Mapped[str] = mapped_column(
        String(500), nullable=False, default="", comment="简短描述（列表展示用）"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="详细描述（Markdown 格式）"
    )

    # ── 审核状态 ──────────────────────────────────────────────
    # DRAFT / PENDING_REVIEW / PUBLISHED / ARCHIVED / SUSPENDED
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="DRAFT",
        comment="状态：DRAFT/PENDING_REVIEW/PUBLISHED/ARCHIVED/SUSPENDED",
    )

    # ── 外键关联 ──────────────────────────────────────────────
    author_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id"), nullable=False, comment="作者用户 ID"
    )
    category_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("categories.id"), nullable=True, comment="所属分类 ID"
    )
    license_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("licenses.id"), nullable=True, comment="开源许可证 ID"
    )

    # ── GitHub 信息 ───────────────────────────────────────────
    github_repo_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="GitHub 仓库地址"
    )
    github_stars: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="GitHub Star 数"
    )
    github_forks: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="GitHub Fork 数"
    )

    # ── 展示信息 ──────────────────────────────────────────────
    cover_image_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="封面图片 URL"
    )

    # ── 部署与定价 ────────────────────────────────────────────
    # CLOUD / DOCKER / KUBERNETES
    deploy_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="DOCKER", comment="部署方式：CLOUD/DOCKER/KUBERNETES"
    )
    # FREE / FREEMIUM / PAID / SUBSCRIPTION
    pricing_model: Mapped[str] = mapped_column(
        String(20), nullable=False, default="FREE", comment="定价模式：FREE/FREEMIUM/PAID/SUBSCRIPTION"
    )
    base_price: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="基础价格"
    )
    deploy_service_price: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="代部署服务费"
    )

    # ── 统计数据 ──────────────────────────────────────────────
    total_deployments: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="累计部署次数"
    )
    avg_rating: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="平均评分"
    )

    # ── 运营标记 ──────────────────────────────────────────────
    is_featured: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否精选推荐"
    )

    # ── 时间戳 ────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # ── 关系 ──────────────────────────────────────────────────
    author: Mapped["User"] = relationship(back_populates="agent_templates", lazy="selectin")  # noqa: F821
    category: Mapped["Category | None"] = relationship(back_populates="agent_templates", lazy="selectin")
    license: Mapped["License | None"] = relationship(back_populates="agent_templates", lazy="selectin")
    tags: Mapped[list["Tag"]] = relationship(
        secondary="agent_template_tags", back_populates="agent_templates", lazy="selectin"
    )
    deployments: Mapped[list["Deployment"]] = relationship(back_populates="agent_template", lazy="selectin")  # noqa: F821
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="agent_template", lazy="selectin")  # noqa: F821
    reviews: Mapped[list["Review"]] = relationship(back_populates="agent_template", lazy="selectin")  # noqa: F821
    favorites: Mapped[list["UserFavorite"]] = relationship(back_populates="agent_template", lazy="selectin")  # noqa: F821
    compliance: Mapped[list["ComplianceRecord"]] = relationship(back_populates="agent_template", lazy="selectin")  # noqa: F821
    promotions: Mapped[list["Promotion"]] = relationship(back_populates="agent_template", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<AgentTemplate id={self.id} slug={self.slug!r}>"


# ─────────────────────────────────────────────────────────────
#  分类表（自引用树形结构）
# ─────────────────────────────────────────────────────────────

class Category(Base):
    """Agent 模板分类，支持父子级分类"""

    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=_generate_uuid, comment="分类唯一标识"
    )
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False, comment="URL 友好的 slug"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="分类名称"
    )
    icon: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="分类图标标识"
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("categories.id"), nullable=True, comment="父分类 ID"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="排序权重（越小越靠前）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否启用"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # ── 自引用关系 ────────────────────────────────────────────
    parent: Mapped["Category | None"] = relationship(
        back_populates="children", remote_side="Category.id", lazy="selectin"
    )
    children: Mapped[list["Category"]] = relationship(
        back_populates="parent", lazy="selectin"
    )
    agent_templates: Mapped[list["AgentTemplate"]] = relationship(
        back_populates="category", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name!r}>"


# ─────────────────────────────────────────────────────────────
#  标签表
# ─────────────────────────────────────────────────────────────

class Tag(Base):
    """Agent 模板标签"""

    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=_generate_uuid, comment="标签唯一标识"
    )
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False, comment="URL 友好的 slug"
    )
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="标签名称"
    )
    group_name: Mapped[str] = mapped_column(
        String(50), nullable=False, default="general", comment="标签分组（如：场景、技术栈）"
    )

    # ── 关系 ──────────────────────────────────────────────────
    agent_templates: Mapped[list["AgentTemplate"]] = relationship(
        secondary="agent_template_tags", back_populates="tags", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Tag id={self.id} name={self.name!r}>"


# ─────────────────────────────────────────────────────────────
#  模板-标签关联表（多对多中间表）
# ─────────────────────────────────────────────────────────────

class AgentTemplateTag(Base):
    """Agent 模板与标签的多对多关联表"""

    __tablename__ = "agent_template_tags"

    agent_template_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("agent_templates.id"), primary_key=True, comment="模板 ID"
    )
    tag_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("tags.id"), primary_key=True, comment="标签 ID"
    )

    def __repr__(self) -> str:
        return f"<AgentTemplateTag agent={self.agent_template_id} tag={self.tag_id}>"


# ─────────────────────────────────────────────────────────────
#  开源许可证表
# ─────────────────────────────────────────────────────────────

class License(Base):
    """开源许可证信息表"""

    __tablename__ = "licenses"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=_generate_uuid, comment="许可证唯一标识"
    )
    spdx_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="SPDX 标准标识（如 MIT、Apache-2.0）"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="许可证全称"
    )
    allows_commercial_use: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否允许商业使用"
    )
    requires_disclosure: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否要求源码披露"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="许可证简要说明"
    )

    # ── 关系 ──────────────────────────────────────────────────
    agent_templates: Mapped[list["AgentTemplate"]] = relationship(
        back_populates="license", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<License spdx_id={self.spdx_id!r}>"

"""
评价模型

用户对 Agent 模板的评分与评论，每个用户对同一模板只能评价一次。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _generate_uuid() -> str:
    """生成 32 位无横杠的 UUID"""
    return uuid.uuid4().hex


class Review(Base):
    """Agent 模板评价表"""

    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("agent_template_id", "user_id", name="uq_review_template_user"),
    )

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=_generate_uuid, comment="评价唯一标识"
    )
    agent_template_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("agent_templates.id"), nullable=False, comment="Agent 模板 ID"
    )
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id"), nullable=False, comment="评价用户 ID"
    )

    # ── 评分与内容 ────────────────────────────────────────────
    rating: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="评分（1-5 分）"
    )
    content: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="评价正文"
    )

    # ── 审核状态 ──────────────────────────────────────────────
    # PENDING / APPROVED / REJECTED / HIDDEN
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING",
        comment="状态：PENDING/APPROVED/REJECTED/HIDDEN",
    )

    # ── 时间戳 ────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # ── 关系 ──────────────────────────────────────────────────
    agent_template: Mapped["AgentTemplate"] = relationship(  # noqa: F821
        back_populates="reviews", lazy="selectin"
    )
    user: Mapped["User"] = relationship(back_populates="reviews", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Review id={self.id} rating={self.rating}>"

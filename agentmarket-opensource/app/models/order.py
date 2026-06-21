"""
订单相关模型

包含：
- Order：订单主表
- OrderItem：订单明细行
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _generate_uuid() -> str:
    """生成 32 位无横杠的 UUID"""
    return uuid.uuid4().hex


class Order(Base):
    """订单主表"""

    __tablename__ = "orders"

    # ── 主键与订单号 ──────────────────────────────────────────
    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=_generate_uuid, comment="订单唯一标识"
    )
    order_no: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False, comment="业务订单号（如 AM20260620xxxxxx）"
    )

    # ── 用户 ──────────────────────────────────────────────────
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id"), nullable=False, comment="下单用户 ID"
    )

    # ── 订单类型与状态 ────────────────────────────────────────
    # PURCHASE / SUBSCRIPTION / DEPLOY
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="订单类型：PURCHASE/SUBSCRIPTION/DEPLOY"
    )
    # PENDING / PAID / CANCELLED / REFUNDED
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING",
        comment="状态：PENDING/PAID/CANCELLED/REFUNDED",
    )

    # ── 金额与支付 ────────────────────────────────────────────
    total_amount: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="订单总金额"
    )
    payment_method: Mapped[str | None] = mapped_column(
        String(30), nullable=True, comment="支付方式：alipay/wechat/stripe/bank_transfer"
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="支付完成时间"
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="取消时间"
    )
    refunded_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="退款时间"
    )
    remark: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="备注"
    )

    # ── 时间戳 ────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # ── 关系 ──────────────────────────────────────────────────
    user: Mapped["User"] = relationship(back_populates="orders", lazy="selectin")  # noqa: F821
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} order_no={self.order_no!r}>"


class OrderItem(Base):
    """订单明细行，记录每个购买项"""

    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=_generate_uuid, comment="明细行唯一标识"
    )
    order_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("orders.id"), nullable=False, comment="所属订单 ID"
    )
    agent_template_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("agent_templates.id"), nullable=False, comment="Agent 模板 ID"
    )

    # LICENSE / SUBSCRIPTION / DEPLOYMENT
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="明细类型：LICENSE/SUBSCRIPTION/DEPLOYMENT"
    )
    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="数量"
    )
    unit_price: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="单价"
    )

    # ── 关系 ──────────────────────────────────────────────────
    order: Mapped["Order"] = relationship(back_populates="items", lazy="selectin")
    agent_template: Mapped["AgentTemplate"] = relationship(  # noqa: F821
        back_populates="order_items", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<OrderItem id={self.id} type={self.type!r}>"

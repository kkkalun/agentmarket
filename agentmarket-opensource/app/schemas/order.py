"""
订单相关 Pydantic Schema

包含创建订单、支付、订单详情等数据模型。
"""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class OrderItemRequest(BaseModel):
    """订单明细请求项"""

    agent_template_id: str = Field(..., description="Agent 模板 ID")
    type: Literal["LICENSE", "SUBSCRIPTION", "DEPLOYMENT"] = Field(
        ..., description="购买类型"
    )
    quantity: int = Field(default=1, ge=1, description="购买数量")


class CreateOrderRequest(BaseModel):
    """创建订单请求"""

    type: Literal["PURCHASE", "SUBSCRIPTION", "DEPLOY"] = Field(
        ..., description="订单类型"
    )
    items: List[OrderItemRequest] = Field(
        ..., min_length=1, description="订单明细列表（至少一项）"
    )
    coupon_code: Optional[str] = Field(default=None, description="优惠券代码")


class PayRequest(BaseModel):
    """发起支付请求"""

    payment_method: Literal["alipay", "wechat", "stripe", "bank_transfer"] = Field(
        ..., description="支付方式"
    )
    return_url: Optional[str] = Field(
        default=None, description="支付完成后前端跳转地址"
    )


class OrderItemResponse(BaseModel):
    """订单明细响应"""

    id: str
    agent_template_id: str
    type: str
    quantity: int
    unit_price: float

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    """订单响应"""

    id: str
    order_no: str
    type: str
    status: str
    total_amount: float
    payment_method: Optional[str] = None
    created_at: datetime
    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)

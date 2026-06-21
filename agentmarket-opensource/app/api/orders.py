"""
订单路由

提供订单的创建、列表、详情、支付和取消接口。
所有接口均需登录认证。
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.exceptions import NotFoundError, ValidationError
from app.models.agent import AgentTemplate
from app.models.order import Order, OrderItem
from app.models.user import User
from app.schemas.order import (
    CreateOrderRequest,
    OrderItemResponse,
    OrderResponse,
    PayRequest,
)
from app.utils.response import error_response, paginated_response, success_response
from app.utils.security import generate_order_no

router = APIRouter(prefix="/orders", tags=["订单"])


@router.post("/", summary="创建订单")
async def create_order(
    body: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建新订单。

    流程：
    1. 校验每个明细项中的 Agent 模板是否存在且已发布
    2. 计算总金额
    3. 生成业务订单号并写入数据库
    4. 返回订单信息
    """
    order_items: list[OrderItem] = []
    total_amount = 0.0

    for item_req in body.items:
        # 查找模板
        result = await db.execute(
            select(AgentTemplate).where(
                AgentTemplate.id == item_req.agent_template_id,
                AgentTemplate.status == "PUBLISHED",
            )
        )
        agent = result.scalar_one_or_none()
        if not agent:
            raise ValidationError(
                message=f"Agent 模板 {item_req.agent_template_id} 不存在或未发布"
            )

        # 计算单价
        unit_price = agent.base_price
        if item_req.type == "DEPLOYMENT":
            unit_price = agent.deploy_service_price or agent.base_price

        subtotal = unit_price * item_req.quantity
        total_amount += subtotal

        order_items.append(
            OrderItem(
                agent_template_id=agent.id,
                type=item_req.type,
                quantity=item_req.quantity,
                unit_price=unit_price,
            )
        )

    # 创建订单
    order = Order(
        order_no=generate_order_no(),
        user_id=current_user.id,
        type=body.type,
        status="PENDING",
        total_amount=total_amount,
        items=order_items,
    )
    db.add(order)
    await db.flush()

    return success_response(
        data=_build_order_response(order),
        message="订单创建成功",
        status_code=201,
    )


@router.get("/", summary="获取当前用户订单列表")
async def list_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """分页获取当前用户的订单列表（按创建时间倒序）。"""
    query = (
        select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    )

    # 统计
    from sqlalchemy import func

    count_query = select(func.count()).select_from(
        query.order_by(None).subquery()
    )
    total = (await db.execute(count_query)).scalar() or 0

    # 分页
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    orders = result.scalars().all()

    items = [_build_order_response(o) for o in orders]
    return paginated_response(
        data=items, page=page, page_size=page_size, total=total
    )


@router.get("/{order_id}", summary="获取订单详情")
async def get_order_detail(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取指定订单的详细信息（仅限本人订单）。"""
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError(message="订单不存在")

    return success_response(data=_build_order_response(order))


@router.post("/{order_id}/pay", summary="发起支付")
async def pay_order(
    order_id: str,
    body: PayRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    发起订单支付。

    流程：
    1. 校验订单状态必须为 PENDING
    2. 记录支付方式
    3. 模拟支付成功（生产环境应接入第三方支付网关）
    4. 更新订单状态为 PAID
    """
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError(message="订单不存在")
    if order.status != "PENDING":
        raise ValidationError(message=f"订单状态为 {order.status}，无法发起支付")

    order.payment_method = body.payment_method
    order.status = "PAID"
    order.paid_at = datetime.utcnow()
    await db.flush()

    return success_response(
        data=_build_order_response(order),
        message="支付成功（模拟）",
    )


@router.post("/{order_id}/cancel", summary="取消订单")
async def cancel_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    取消订单。

    仅状态为 PENDING 的订单可以取消。
    """
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError(message="订单不存在")
    if order.status != "PENDING":
        raise ValidationError(message=f"订单状态为 {order.status}，无法取消")

    order.status = "CANCELLED"
    order.cancelled_at = datetime.utcnow()
    await db.flush()

    return success_response(
        data=_build_order_response(order),
        message="订单已取消",
    )


# ─────────────────────────────────────────────────────────────
#  内部辅助函数
# ─────────────────────────────────────────────────────────────

def _build_order_response(order: Order) -> OrderResponse:
    """将 Order ORM 对象转换为 OrderResponse Pydantic 模型"""
    return OrderResponse(
        id=order.id,
        order_no=order.order_no,
        type=order.type,
        status=order.status,
        total_amount=order.total_amount,
        payment_method=order.payment_method,
        created_at=order.created_at,
        items=[
            OrderItemResponse(
                id=item.id,
                agent_template_id=item.agent_template_id,
                type=item.type,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in order.items
        ],
    )

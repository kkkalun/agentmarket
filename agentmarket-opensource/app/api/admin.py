"""
管理后台路由

提供仪表盘统计、Agent 审核、用户管理、订单查看、合规记录和日志等管理接口。
所有接口均要求 ADMIN 或 SUPERADMIN 角色。
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.exceptions import NotFoundError, ValidationError
from app.models.agent import AgentTemplate
from app.models.misc import ComplianceRecord, OperationLog
from app.models.order import Order
from app.models.user import User
from app.utils.response import paginated_response, success_response

router = APIRouter(prefix="/admin", tags=["管理后台"])


# ─────────────────────────────────────────────────────────────
#  仪表盘
# ─────────────────────────────────────────────────────────────

@router.get("/dashboard", summary="管理后台仪表盘概览")
async def dashboard(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    获取管理后台仪表盘统计数据。

    返回：用户总数、Agent 总数、待审核数、订单总数、今日新增等。
    """
    # 用户统计
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0

    # Agent 模板统计
    total_agents = (
        await db.execute(select(func.count()).select_from(AgentTemplate))
    ).scalar() or 0
    pending_agents = (
        await db.execute(
            select(func.count())
            .select_from(AgentTemplate)
            .where(AgentTemplate.status == "PENDING_REVIEW")
        )
    ).scalar() or 0

    # 订单统计
    total_orders = (
        await db.execute(select(func.count()).select_from(Order))
    ).scalar() or 0
    paid_orders = (
        await db.execute(
            select(func.count()).select_from(Order).where(Order.status == "PAID")
        )
    ).scalar() or 0

    return success_response(
        data={
            "total_users": total_users,
            "total_agents": total_agents,
            "pending_agents": pending_agents,
            "total_orders": total_orders,
            "paid_orders": paid_orders,
        }
    )


# ─────────────────────────────────────────────────────────────
#  Agent 模板管理
# ─────────────────────────────────────────────────────────────

@router.get("/agents", summary="获取全部 Agent 模板（管理视角）")
async def list_agents_admin(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None, description="按状态筛选"),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取所有 Agent 模板列表（包含各种状态），支持按状态筛选。"""
    query = select(AgentTemplate)

    if status:
        query = query.where(AgentTemplate.status == status)

    query = query.order_by(AgentTemplate.created_at.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    agents = result.scalars().all()

    items = [
        {
            "id": a.id,
            "slug": a.slug,
            "name": a.name,
            "status": a.status,
            "pricing_model": a.pricing_model,
            "author": a.author.username if a.author else None,
            "total_deployments": a.total_deployments,
            "avg_rating": a.avg_rating,
            "created_at": a.created_at.isoformat(),
            "updated_at": a.updated_at.isoformat(),
        }
        for a in agents
    ]

    return paginated_response(data=items, page=page, page_size=page_size, total=total)


@router.post("/agents", summary="创建 Agent 模板（管理员）")
async def create_agent_admin(
    name: str,
    slug: str,
    short_description: str,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员手动创建 Agent 模板（简化版，完整字段通过 PUT 更新）。"""
    agent = AgentTemplate(
        name=name,
        slug=slug,
        short_description=short_description,
        author_id=_admin.id,
        status="DRAFT",
    )
    db.add(agent)
    await db.flush()

    return success_response(
        data={"id": agent.id, "slug": agent.slug},
        message="Agent 模板创建成功",
        status_code=201,
    )


@router.put("/agents/{agent_id}", summary="更新 Agent 模板")
async def update_agent_admin(
    agent_id: str,
    name: Optional[str] = None,
    short_description: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员更新 Agent 模板的基本信息和状态。"""
    result = await db.execute(
        select(AgentTemplate).where(AgentTemplate.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundError(message="Agent 模板不存在")

    if name is not None:
        agent.name = name
    if short_description is not None:
        agent.short_description = short_description
    if description is not None:
        agent.description = description
    if status is not None:
        agent.status = status
    await db.flush()

    return success_response(data={"id": agent.id}, message="更新成功")


@router.post("/agents/{agent_id}/review", summary="审核 Agent 模板")
async def review_agent(
    agent_id: str,
    action: str = Query(..., description="审核动作：approve / reject"),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    审核 Agent 模板。

    - approve: 将状态改为 PUBLISHED
    - reject: 将状态改为 DRAFT
    """
    result = await db.execute(
        select(AgentTemplate).where(AgentTemplate.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundError(message="Agent 模板不存在")

    if action == "approve":
        agent.status = "PUBLISHED"
        msg = "已批准发布"
    elif action == "reject":
        agent.status = "DRAFT"
        msg = "已驳回"
    else:
        raise ValidationError(message="action 参数必须为 approve 或 reject")

    await db.flush()
    return success_response(data={"id": agent.id, "status": agent.status}, message=msg)


@router.delete("/agents/{agent_id}", summary="归档 Agent 模板")
async def archive_agent(
    agent_id: str,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """将 Agent 模板状态设为 ARCHIVED（软删除）。"""
    result = await db.execute(
        select(AgentTemplate).where(AgentTemplate.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundError(message="Agent 模板不存在")

    agent.status = "ARCHIVED"
    await db.flush()

    return success_response(data={"id": agent.id}, message="已归档")


# ─────────────────────────────────────────────────────────────
#  用户管理
# ─────────────────────────────────────────────────────────────

@router.get("/users", summary="获取用户列表")
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """分页获取全部用户列表。"""
    query = select(User).order_by(User.created_at.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    users = result.scalars().all()

    items = [
        {
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "display_name": u.display_name,
            "role": u.role,
            "status": u.status,
            "subscription_plan": u.subscription_plan,
            "created_at": u.created_at.isoformat(),
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        }
        for u in users
    ]

    return paginated_response(data=items, page=page, page_size=page_size, total=total)


@router.put("/users/{user_id}", summary="更新用户角色或状态")
async def update_user(
    user_id: str,
    role: Optional[str] = None,
    status: Optional[str] = None,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员更新用户的角色或账号状态。"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError(message="用户不存在")

    if role is not None:
        user.role = role
    if status is not None:
        user.status = status
    await db.flush()

    return success_response(data={"id": user.id}, message="用户信息已更新")


# ─────────────────────────────────────────────────────────────
#  订单管理
# ─────────────────────────────────────────────────────────────

@router.get("/orders", summary="获取全部订单列表")
async def list_orders_admin(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """分页获取全部订单，支持按状态筛选。"""
    query = select(Order)
    if status:
        query = query.where(Order.status == status)
    query = query.order_by(Order.created_at.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    orders = result.scalars().all()

    items = [
        {
            "id": o.id,
            "order_no": o.order_no,
            "type": o.type,
            "status": o.status,
            "total_amount": o.total_amount,
            "payment_method": o.payment_method,
            "user_id": o.user_id,
            "created_at": o.created_at.isoformat(),
        }
        for o in orders
    ]

    return paginated_response(data=items, page=page, page_size=page_size, total=total)


# ─────────────────────────────────────────────────────────────
#  合规记录
# ─────────────────────────────────────────────────────────────

@router.get("/compliance", summary="获取合规审查记录")
async def list_compliance(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """分页获取合规审查记录列表。"""
    query = select(ComplianceRecord).order_by(ComplianceRecord.created_at.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    records = result.scalars().all()

    items = [
        {
            "id": r.id,
            "agent_template_id": r.agent_template_id,
            "review_type": r.review_type,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]

    return paginated_response(data=items, page=page, page_size=page_size, total=total)


# ─────────────────────────────────────────────────────────────
#  操作日志
# ─────────────────────────────────────────────────────────────

@router.get("/logs", summary="获取操作日志")
async def list_operation_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """分页获取系统操作审计日志。"""
    query = select(OperationLog).order_by(OperationLog.created_at.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    logs = result.scalars().all()

    items = [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "resource": log.resource,
            "result": log.result,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]

    return paginated_response(data=items, page=page, page_size=page_size, total=total)

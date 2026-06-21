"""
Agent 模板路由

提供 Agent 模板的列表、搜索、详情、收藏、评价和分类等公开/半公开接口。
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_optional_user
from app.database import get_db
from app.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.models.agent import AgentTemplate, Category, Tag
from app.models.misc import UserFavorite
from app.models.review import Review
from app.models.user import User
from app.schemas.agent import (
    AgentDetailResponse,
    AgentListQuery,
    AgentResponse,
    AuthorBrief,
    CategoryBrief,
    CategoryResponse,
    ReviewResponse,
    ReviewUserBrief,
    TagBrief,
)
from app.utils.response import error_response, paginated_response, success_response

router = APIRouter(prefix="/agents", tags=["Agent模板"])


# ─────────────────────────────────────────────────────────────
#  列表与筛选
# ─────────────────────────────────────────────────────────────

@router.get("/", summary="获取 Agent 模板列表")
async def list_agents(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    category: Optional[str] = Query(default=None, description="分类 slug"),
    tag: Optional[str] = Query(default=None, description="标签 slug"),
    sort: str = Query(default="newest", description="排序：newest/popular/rating/downloads"),
    pricing: str = Query(default="all", description="定价筛选：free/paid/all"),
    db: AsyncSession = Depends(get_db),
):
    """
    分页获取已发布的 Agent 模板列表。

    支持按分类、标签筛选，以及多种排序方式。
    """
    query = (
        select(AgentTemplate)
        .where(AgentTemplate.status == "PUBLISHED")
    )

    # 按分类筛选
    if category:
        cat_result = await db.execute(
            select(Category).where(Category.slug == category)
        )
        cat = cat_result.scalar_one_or_none()
        if cat:
            query = query.where(AgentTemplate.category_id == cat.id)

    # 按定价筛选
    if pricing == "free":
        query = query.where(AgentTemplate.pricing_model == "FREE")
    elif pricing == "paid":
        query = query.where(AgentTemplate.pricing_model != "FREE")

    # 排序
    if sort == "popular":
        query = query.order_by(AgentTemplate.total_deployments.desc())
    elif sort == "rating":
        query = query.order_by(AgentTemplate.avg_rating.desc())
    elif sort == "downloads":
        query = query.order_by(AgentTemplate.total_deployments.desc())
    else:  # newest
        query = query.order_by(AgentTemplate.created_at.desc())

    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    agents = result.scalars().all()

    # 构建响应列表
    items = [_build_agent_response(a) for a in agents]

    return paginated_response(data=items, page=page, page_size=page_size, total=total)


@router.get("/featured", summary="获取精选推荐 Agent")
async def get_featured_agents(
    limit: int = Query(default=10, ge=1, le=50, description="返回数量"),
    db: AsyncSession = Depends(get_db),
):
    """获取精选推荐（is_featured=True）的已发布 Agent 模板。"""
    query = (
        select(AgentTemplate)
        .where(AgentTemplate.status == "PUBLISHED", AgentTemplate.is_featured == True)
        .order_by(AgentTemplate.avg_rating.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    agents = result.scalars().all()

    items = [_build_agent_response(a) for a in agents]
    return success_response(data=items)


@router.get("/categories", summary="获取所有分类")
async def get_categories(db: AsyncSession = Depends(get_db)):
    """获取全部分类列表，每个分类包含关联的 Agent 模板数量。"""
    query = (
        select(Category)
        .where(Category.is_active == True)
        .order_by(Category.sort_order.asc())
    )
    result = await db.execute(query)
    categories = result.scalars().all()

    items = []
    for cat in categories:
        # 统计该分类下已发布的模板数量
        count_query = (
            select(func.count())
            .select_from(AgentTemplate)
            .where(
                AgentTemplate.category_id == cat.id,
                AgentTemplate.status == "PUBLISHED",
            )
        )
        agent_count = (await db.execute(count_query)).scalar() or 0
        items.append(
            CategoryResponse(
                id=cat.id,
                slug=cat.slug,
                name=cat.name,
                icon=cat.icon,
                agent_count=agent_count,
            )
        )

    return success_response(data=items)


@router.get("/search", summary="全文搜索 Agent 模板")
async def search_agents(
    q: str = Query(..., min_length=1, max_length=200, description="搜索关键词"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: Optional[str] = Query(default=None),
    sort: str = Query(default="newest"),
    db: AsyncSession = Depends(get_db),
):
    """
    根据关键词搜索 Agent 模板名称和描述。

    使用 LIKE 模糊匹配（生产环境可替换为全文索引或 Elasticsearch）。
    """
    like_pattern = f"%{q}%"
    query = (
        select(AgentTemplate)
        .where(
            AgentTemplate.status == "PUBLISHED",
            AgentTemplate.name.ilike(like_pattern)
            | AgentTemplate.short_description.ilike(like_pattern),
        )
    )

    # 按分类筛选
    if category:
        cat_result = await db.execute(
            select(Category).where(Category.slug == category)
        )
        cat = cat_result.scalar_one_or_none()
        if cat:
            query = query.where(AgentTemplate.category_id == cat.id)

    # 排序
    if sort == "popular" or sort == "downloads":
        query = query.order_by(AgentTemplate.total_deployments.desc())
    elif sort == "rating":
        query = query.order_by(AgentTemplate.avg_rating.desc())
    else:
        query = query.order_by(AgentTemplate.created_at.desc())

    # 统计
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    agents = result.scalars().all()

    items = [_build_agent_response(a) for a in agents]
    return paginated_response(data=items, page=page, page_size=page_size, total=total)


# ─────────────────────────────────────────────────────────────
#  详情
# ─────────────────────────────────────────────────────────────

@router.get("/{slug}", summary="获取 Agent 模板详情")
async def get_agent_detail(
    slug: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """
    根据 slug 获取 Agent 模板详情。

    如果用户已登录，还会返回该用户是否已收藏此模板（is_favorite）。
    """
    result = await db.execute(
        select(AgentTemplate).where(
            AgentTemplate.slug == slug,
            AgentTemplate.status == "PUBLISHED",
        )
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundError(message="Agent 模板不存在或尚未发布")

    # 判断是否已收藏
    is_favorite = False
    if current_user:
        fav_result = await db.execute(
            select(UserFavorite).where(
                UserFavorite.user_id == current_user.id,
                UserFavorite.agent_template_id == agent.id,
            )
        )
        is_favorite = fav_result.scalar_one_or_none() is not None

    resp = _build_agent_detail_response(agent, is_favorite)
    return success_response(data=resp)


# ─────────────────────────────────────────────────────────────
#  收藏
# ─────────────────────────────────────────────────────────────

@router.post("/{slug}/favorite", summary="收藏/取消收藏 Agent 模板")
async def toggle_favorite(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    切换当前用户对指定 Agent 模板的收藏状态。

    若已收藏则取消，若未收藏则添加。返回操作后的收藏状态。
    """
    result = await db.execute(
        select(AgentTemplate).where(AgentTemplate.slug == slug)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundError(message="Agent 模板不存在")

    # 查询当前收藏状态
    fav_result = await db.execute(
        select(UserFavorite).where(
            UserFavorite.user_id == current_user.id,
            UserFavorite.agent_template_id == agent.id,
        )
    )
    existing = fav_result.scalar_one_or_none()

    if existing:
        await db.delete(existing)
        is_favorite = False
        msg = "已取消收藏"
    else:
        new_fav = UserFavorite(
            user_id=current_user.id,
            agent_template_id=agent.id,
        )
        db.add(new_fav)
        is_favorite = True
        msg = "已收藏"

    return success_response(data={"is_favorite": is_favorite}, message=msg)


# ─────────────────────────────────────────────────────────────
#  评价
# ─────────────────────────────────────────────────────────────

@router.get("/{slug}/reviews", summary="获取 Agent 模板评价列表")
async def get_agent_reviews(
    slug: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取指定 Agent 模板的已审核评价列表（分页）。"""
    # 查找模板
    agent_result = await db.execute(
        select(AgentTemplate).where(
            AgentTemplate.slug == slug,
            AgentTemplate.status == "PUBLISHED",
        )
    )
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise NotFoundError(message="Agent 模板不存在或尚未发布")

    # 查询已审核评价
    query = (
        select(Review)
        .where(Review.agent_template_id == agent.id, Review.status == "APPROVED")
        .order_by(Review.created_at.desc())
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    reviews = result.scalars().all()

    items = []
    for r in reviews:
        items.append(
            ReviewResponse(
                id=r.id,
                rating=r.rating,
                content=r.content,
                status=r.status,
                created_at=r.created_at,
                user=ReviewUserBrief(
                    id=r.user.id,
                    username=r.user.username,
                    display_name=r.user.display_name,
                    avatar_url=r.user.avatar_url,
                ),
            )
        )

    return paginated_response(
        data=items, page=page, page_size=page_size, total=total
    )


# ─────────────────────────────────────────────────────────────
#  内部辅助函数
# ─────────────────────────────────────────────────────────────

def _build_agent_response(agent: AgentTemplate) -> AgentResponse:
    """将 AgentTemplate ORM 对象转换为 AgentResponse Pydantic 模型"""
    return AgentResponse(
        id=agent.id,
        slug=agent.slug,
        name=agent.name,
        short_description=agent.short_description,
        cover_image_url=agent.cover_image_url,
        pricing_model=agent.pricing_model,
        base_price=agent.base_price,
        github_stars=agent.github_stars,
        total_deployments=agent.total_deployments,
        avg_rating=agent.avg_rating,
        created_at=agent.created_at,
        author=AuthorBrief(
            id=agent.author.id,
            username=agent.author.username,
            display_name=agent.author.display_name,
            avatar_url=agent.author.avatar_url,
        ),
        category=(
            CategoryBrief(
                id=agent.category.id,
                slug=agent.category.slug,
                name=agent.category.name,
                icon=agent.category.icon,
            )
            if agent.category
            else None
        ),
        tags=[
            TagBrief(id=t.id, slug=t.slug, name=t.name, group_name=t.group_name)
            for t in agent.tags
        ],
    )


def _build_agent_detail_response(
    agent: AgentTemplate, is_favorite: bool
) -> AgentDetailResponse:
    """将 AgentTemplate ORM 对象转换为 AgentDetailResponse Pydantic 模型"""
    from app.schemas.agent import LicenseBrief

    base = _build_agent_response(agent)
    return AgentDetailResponse(
        **base.model_dump(mode="json"),
        description=agent.description,
        license=(
            LicenseBrief(
                id=agent.license.id,
                spdx_id=agent.license.spdx_id,
                name=agent.license.name,
                allows_commercial_use=agent.license.allows_commercial_use,
                requires_disclosure=agent.license.requires_disclosure,
            )
            if agent.license
            else None
        ),
        deploy_type=agent.deploy_type,
        is_favorite=is_favorite,
        github_forks=agent.github_forks,
        github_repo_url=agent.github_repo_url,
    )

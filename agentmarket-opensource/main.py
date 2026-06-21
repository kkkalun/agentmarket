"""
AgentMarket 应用入口
初始化 FastAPI 应用，注册中间件、路由、模板引擎、静态文件
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.config import settings
from app.database import engine, Base
from app.api import auth, agents, orders, admin
from app.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：创建数据库表（开发环境）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 关闭时：释放数据库连接
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="AI Agent 模板聚合平台 API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 注册异常处理器
register_exception_handlers(app)

# CORS 中间件
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板引擎
templates = Jinja2Templates(directory="templates")

# ==================== 认证中间件 ====================

from app.services.auth_service import decode_token
from app.database import async_session_factory as _auth_session_factory

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """从 cookie 或 Authorization header 中读取 JWT，解析后注入 request.state.user"""
    request.state.user = None
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if token:
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
            if user_id and payload.get("type") == "access":
                from sqlalchemy import select
                from app.models.user import User
                async with _auth_session_factory() as session:
                    result = await session.execute(
                        select(User).where(User.id == user_id)
                    )
                    request.state.user = result.scalar_one_or_none()
        except Exception:
            # JWT 过期或无效，静默忽略，视为未登录
            pass

    response = await call_next(request)
    return response

# ==================== 页面路由（服务端渲染） ====================

from types import SimpleNamespace

def _base_ctx(request: Request, **extra) -> dict:
    """构建模板基础上下文，所有页面共享 current_user（导航栏需要）"""
    user = getattr(request.state, "user", None)
    ctx = {"request": request, "current_user": user}
    ctx.update(extra)
    return ctx

def _placeholder_agent():
    """占位 Agent 对象，供详情页在无真实数据时正常渲染"""
    _stats = SimpleNamespace(stars=0, deployments=0, rating=0, reviews_count=0)
    return SimpleNamespace(
        name="示例 Agent", description="暂无数据，请先通过 API 创建 Agent 模板。",
        author_name="未知作者", author_id="", author_avatar=None,
        author_bio="", author_agents_count=0, author_total_deployments=0,
        category_name="未分类", cover_image=None,
        updated_at="—", created_at="—", tags=[],
        readme_html="<p>暂无 README 内容</p>",
        id="", package_name="", pricing_model="FREE",
        price_display="免费", license="MIT",
        latest_version="1.0.0", deploy_types_display="Docker",
        versions=[], stats=_stats,
    )


@app.get("/", response_class=HTMLResponse, tags=["页面"])
async def homepage(request: Request):
    """首页"""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.database import async_session_factory
    from app.models.agent import AgentTemplate

    def _to_card(a):
        return SimpleNamespace(
            id=a.id, name=a.name, description=a.short_description,
            cover_image=a.cover_image_url,
            author_name=a.author.display_name if a.author else "未知",
            author_avatar=a.author.avatar_url if a.author else None,
            category_name=a.category.name if a.category else "通用",
            pricing_model=a.pricing_model.lower() if a.pricing_model else "free",
            tags=[t.name for t in (a.tags or [])],
            is_verified=False,
            stats=SimpleNamespace(
                stars=a.github_stars or 0,
                deployments=a.total_deployments or 0,
                rating=a.avg_rating or 0,
            ),
        )

    _load_opts = (
        selectinload(AgentTemplate.author),
        selectinload(AgentTemplate.category),
        selectinload(AgentTemplate.tags),
    )
    featured, latest = [], []
    async with async_session_factory() as session:
        # 精选推荐
        r1 = await session.execute(
            select(AgentTemplate).options(*_load_opts)
            .where(AgentTemplate.status == "PUBLISHED", AgentTemplate.is_featured == True)
            .order_by(AgentTemplate.avg_rating.desc()).limit(8)
        )
        featured = [_to_card(a) for a in r1.scalars().all()]

        # 最新上线
        r2 = await session.execute(
            select(AgentTemplate).options(*_load_opts)
            .where(AgentTemplate.status == "PUBLISHED")
            .order_by(AgentTemplate.created_at.desc()).limit(4)
        )
        latest = [_to_card(a) for a in r2.scalars().all()]

    return templates.TemplateResponse("index.html", _base_ctx(
        request, featured_agents=featured, latest_agents=latest,
    ))

@app.get("/explore", response_class=HTMLResponse, tags=["页面"])
async def explore_page(request: Request):
    """探索页 - Agent 模板列表"""
    return templates.TemplateResponse("explore/index.html", _base_ctx(
        request, page=1, total_pages=1, total_items=0, page_size=20, base_url="/explore",
    ))

@app.get("/explore/{slug}", response_class=HTMLResponse, tags=["页面"])
async def agent_detail_page(request: Request, slug: str):
    """Agent 模板详情页"""
    from sqlalchemy import select, func
    from sqlalchemy.orm import selectinload
    from app.database import async_session_factory
    from app.models.agent import AgentTemplate
    from app.models.review import Review

    _load_opts = (
        selectinload(AgentTemplate.author),
        selectinload(AgentTemplate.category),
        selectinload(AgentTemplate.tags),
        selectinload(AgentTemplate.license),
        selectinload(AgentTemplate.reviews),
    )

    agent_obj = None
    reviews_list = []
    related_list = []

    async with async_session_factory() as session:
        # 查主 Agent
        r = await session.execute(
            select(AgentTemplate).options(*_load_opts)
            .where(AgentTemplate.slug == slug, AgentTemplate.status == "PUBLISHED")
        )
        agent_obj = r.scalar_one_or_none()

        if agent_obj:
            # 已审核评价
            rr = await session.execute(
                select(Review).options(selectinload(Review.user))
                .where(Review.agent_template_id == agent_obj.id, Review.status == "APPROVED")
                .order_by(Review.created_at.desc()).limit(10)
            )
            reviews_list = [
                SimpleNamespace(
                    author_avatar=rv.user.avatar_url if rv.user else None,
                    author_name=rv.user.display_name if rv.user else "匿名",
                    rating=rv.rating, content=rv.content,
                    created_at=rv.created_at.strftime("%Y-%m-%d") if rv.created_at else "",
                )
                for rv in rr.scalars().all()
            ]

            # 相关推荐（同分类，排除自身）
            if agent_obj.category_id:
                rl = await session.execute(
                    select(AgentTemplate)
                    .where(
                        AgentTemplate.category_id == agent_obj.category_id,
                        AgentTemplate.id != agent_obj.id,
                        AgentTemplate.status == "PUBLISHED",
                    ).limit(4)
                )
                related_list = [
                    SimpleNamespace(id=x.id, name=x.name, description=x.short_description)
                    for x in rl.scalars().all()
                ]

    # 构建模板对象
    if agent_obj:
        a = agent_obj
        tmpl_agent = SimpleNamespace(
            id=a.id, name=a.name, description=a.description or "",
            category_name=a.category.name if a.category else "通用",
            cover_image=a.cover_image_url,
            pricing_model=(a.pricing_model or "FREE").lower(),
            price_display=f"¥{a.base_price}" if a.base_price else "免费",
            author_id=a.author_id,
            author_name=a.author.display_name if a.author else "未知",
            author_avatar=a.author.avatar_url if a.author else None,
            author_bio="", author_agents_count=0, author_total_deployments=0,
            updated_at=a.updated_at.strftime("%Y-%m-%d") if a.updated_at else "",
            created_at=a.created_at.strftime("%Y-%m-%d") if a.created_at else "",
            license=a.license.spdx_id if a.license else "MIT",
            latest_version="1.0.0", package_name=a.slug,
            deploy_types_display=a.deploy_type or "Docker",
            readme_html=f"<p>{a.description}</p>" if a.description else "",
            tags=[t.name for t in (a.tags or [])],
            versions=[],
            stats=SimpleNamespace(
                stars=a.github_stars or 0,
                deployments=a.total_deployments or 0,
                rating=a.avg_rating or 0,
                reviews_count=len(reviews_list),
            ),
        )
    else:
        tmpl_agent = _placeholder_agent()

    return templates.TemplateResponse("explore/detail.html", _base_ctx(
        request, slug=slug, agent=tmpl_agent,
        reviews=reviews_list, related_agents=related_list,
    ))

@app.get("/login", response_class=HTMLResponse, tags=["页面"])
async def login_page(request: Request):
    """登录页"""
    if getattr(request.state, "user", None):
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("auth/login.html", _base_ctx(request))

@app.get("/register", response_class=HTMLResponse, tags=["页面"])
async def register_page(request: Request):
    """注册页"""
    if getattr(request.state, "user", None):
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("auth/register.html", _base_ctx(request))

@app.get("/dashboard", response_class=HTMLResponse, tags=["页面"])
async def dashboard_page(request: Request):
    """用户控制台"""
    if not getattr(request.state, "user", None):
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/login", status_code=302)

    from sqlalchemy import select, func
    from app.database import async_session_factory
    from app.models.misc import UserFavorite
    from app.models.deployment import Deployment
    from app.models.order import Order
    from app.models.review import Review

    user = request.state.user
    stats = SimpleNamespace(favorites=0, deployments=0, orders=0, reviews=0)
    async with async_session_factory() as session:
        # 收藏数
        r1 = await session.execute(
            select(func.count()).select_from(UserFavorite)
            .where(UserFavorite.user_id == user.id)
        )
        stats.favorites = r1.scalar() or 0

        # 部署数
        r2 = await session.execute(
            select(func.count()).select_from(Deployment)
            .where(Deployment.user_id == user.id)
        )
        stats.deployments = r2.scalar() or 0

        # 订单数
        r3 = await session.execute(
            select(func.count()).select_from(Order)
            .where(Order.user_id == user.id)
        )
        stats.orders = r3.scalar() or 0

        # 评价数
        r4 = await session.execute(
            select(func.count()).select_from(Review)
            .where(Review.user_id == user.id)
        )
        stats.reviews = r4.scalar() or 0

    return templates.TemplateResponse("dashboard/index.html", _base_ctx(
        request, user_stats=stats,
    ))

@app.get("/dashboard/settings", response_class=HTMLResponse, tags=["页面"])
async def settings_page(request: Request):
    """用户设置页"""
    if not getattr(request.state, "user", None):
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("dashboard/settings.html", _base_ctx(request))

@app.get("/logout", response_class=HTMLResponse, tags=["页面"])
async def logout_page(request: Request):
    """退出登录：清除 cookie 并重定向到首页"""
    from fastapi.responses import RedirectResponse
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return response

@app.get("/admin", response_class=HTMLResponse, tags=["页面"])
async def admin_dashboard_page(request: Request):
    """管理员控制台"""
    return templates.TemplateResponse("admin/dashboard.html", _base_ctx(
        request, stats=None, pending_agents=[],
    ))

@app.get("/admin/agents", response_class=HTMLResponse, tags=["页面"])
async def admin_agents_page(request: Request):
    """管理员 - Agent 模板管理"""
    return templates.TemplateResponse("admin/agents.html", _base_ctx(
        request, stats=None,
    ))

@app.get("/admin/users", response_class=HTMLResponse, tags=["页面"])
async def admin_users_page(request: Request):
    """管理员 - 用户管理"""
    return templates.TemplateResponse("admin/users.html", _base_ctx(request))

# ==================== HTMX 片段端点 ====================

@app.get("/fragments/agent-grid", response_class=HTMLResponse, tags=["片段"])
async def agent_grid_fragment(
    request: Request,
    q: str = "",
    category: str = "",
    pricing: str = "",
    sort: str = "newest",
    page: int = 1,
    page_size: int = 20,
):
    """
    探索页 HTMX 片段：返回 Agent 卡片网格 HTML。
    接受与 API 相同的查询参数，但返回渲染好的 HTML 片段而非 JSON。
    """
    from sqlalchemy import select, func
    from sqlalchemy.orm import selectinload
    from app.database import async_session_factory
    from app.models.agent import AgentTemplate, Category

    _load_opts = (
        selectinload(AgentTemplate.author),
        selectinload(AgentTemplate.category),
        selectinload(AgentTemplate.tags),
    )

    agents_list = []
    async with async_session_factory() as session:
        query = (
            select(AgentTemplate).options(*_load_opts)
            .where(AgentTemplate.status == "PUBLISHED")
        )

        # 关键词搜索
        if q:
            like = f"%{q}%"
            query = query.where(
                AgentTemplate.name.ilike(like) | AgentTemplate.short_description.ilike(like)
            )

        # 分类筛选
        if category:
            cr = await session.execute(select(Category).where(Category.slug == category))
            cat = cr.scalar_one_or_none()
            if cat:
                query = query.where(AgentTemplate.category_id == cat.id)

        # 定价筛选
        if pricing == "free":
            query = query.where(AgentTemplate.pricing_model == "FREE")
        elif pricing in ("paid", "freemium"):
            query = query.where(AgentTemplate.pricing_model != "FREE")

        # 排序
        if sort in ("popular", "deployments"):
            query = query.order_by(AgentTemplate.total_deployments.desc())
        elif sort == "rating":
            query = query.order_by(AgentTemplate.avg_rating.desc())
        elif sort == "stars":
            query = query.order_by(AgentTemplate.github_stars.desc())
        else:
            query = query.order_by(AgentTemplate.created_at.desc())

        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await session.execute(query)
        rows = result.scalars().all()

        for a in rows:
            agents_list.append(SimpleNamespace(
                id=a.id, slug=a.slug, name=a.name,
                description=a.short_description,
                cover_image=a.cover_image_url,
                author_name=a.author.display_name if a.author else "未知",
                category_name=a.category.name if a.category else "通用",
                pricing_model=(a.pricing_model or "FREE").lower(),
                tags=[t.name for t in (a.tags or [])],
                stats=SimpleNamespace(
                    stars=a.github_stars or 0,
                    deployments=a.total_deployments or 0,
                    rating=a.avg_rating or 0,
                ),
            ))

    return templates.TemplateResponse("fragments/agent_grid.html", {
        "request": request, "agents": agents_list,
    })

# ==================== API 路由 ====================

app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(agents.router, prefix=settings.API_PREFIX)
app.include_router(orders.router, prefix=settings.API_PREFIX)
app.include_router(admin.router, prefix=settings.API_PREFIX)

# ==================== 健康检查 ====================

@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import subprocess
    import sys
    import time

    PORT = 8000

    def kill_port_occupiers(port: int) -> None:
        """启动前清理：杀掉占用指定端口的所有进程（Windows）"""
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True, timeout=5,
            )
            pids = set()
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    if parts:
                        pid = parts[-1]
                        if pid.isdigit() and int(pid) > 0:
                            pids.add(pid)

            if pids:
                print(f"[cleanup] 发现 {len(pids)} 个进程占用端口 {port}，正在清理...")
                for pid in pids:
                    subprocess.run(
                        ["wmic", "process", "where", f"ProcessId={pid}", "delete"],
                        capture_output=True, timeout=5,
                    )
                time.sleep(2)
                print(f"[cleanup] 端口 {port} 已释放")
            else:
                print(f"[cleanup] 端口 {port} 无占用，可直接使用")
        except Exception as e:
            print(f"[cleanup] 端口检查失败（不影响启动）: {e}")

    # 启动前自动清理端口占用
    kill_port_occupiers(PORT)

    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=settings.DEBUG,
    )

"""
认证路由

提供用户注册、登录、令牌刷新、获取当前用户信息和 GitHub OAuth 回调等接口。
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.exceptions import ConflictError, UnauthorizedError
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.utils.response import error_response, success_response

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", summary="用户注册")
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    注册新用户。

    流程：
    1. 检查邮箱和用户名是否已被占用
    2. 对密码进行 bcrypt 哈希
    3. 写入数据库
    4. 返回 JWT 双令牌
    """
    # 检查邮箱或用户名是否已存在
    existing = await db.execute(
        select(User).where(
            or_(User.email == body.email, User.username == body.username)
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError(message="邮箱或用户名已被注册")

    # 创建用户
    user = User(
        email=body.email,
        username=body.username,
        display_name=body.display_name or body.username,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    await db.flush()

    # 生成令牌
    access_token = create_access_token(user.id, user.email, user.role)
    refresh_token = create_refresh_token(user.id, user.email, user.role)

    return success_response(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        ),
        message="注册成功",
    )


@router.post("/login", summary="用户登录")
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    使用邮箱和密码登录。

    流程：
    1. 根据邮箱查询用户
    2. 校验密码哈希
    3. 更新最后登录时间
    4. 返回 JWT 双令牌
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise UnauthorizedError(message="邮箱或密码错误")

    if user.status == "BANNED":
        raise UnauthorizedError(message="账号已被封禁")
    if user.status != "ACTIVE":
        raise UnauthorizedError(message="账号状态异常")

    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    await db.flush()

    access_token = create_access_token(user.id, user.email, user.role)
    refresh_token = create_refresh_token(user.id, user.email, user.role)

    return success_response(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        ),
        message="登录成功",
    )


@router.get("/me", summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    """返回当前已认证用户的个人信息。"""
    return success_response(
        data={
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "display_name": current_user.display_name,
            "avatar_url": current_user.avatar_url,
            "role": current_user.role,
            "status": current_user.status,
            "subscription_plan": current_user.subscription_plan,
            "email_verified_at": current_user.email_verified_at,
            "created_at": current_user.created_at,
        },
    )


@router.post("/refresh", summary="刷新访问令牌")
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    使用刷新令牌换取新的访问令牌。

    流程：
    1. 解码并校验刷新令牌
    2. 确认用户仍然存在且状态正常
    3. 签发新的双令牌
    """
    try:
        payload = decode_token(body.refresh_token)
    except Exception as exc:
        raise UnauthorizedError(message=f"刷新令牌无效：{exc}")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError(message="刷新令牌格式无效")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.status != "ACTIVE":
        raise UnauthorizedError(message="用户不存在或状态异常")

    access_token = create_access_token(user.id, user.email, user.role)
    new_refresh_token = create_refresh_token(user.id, user.email, user.role)

    return success_response(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
        ),
        message="令牌刷新成功",
    )


@router.post("/logout", summary="退出登录")
async def logout():
    """
    退出登录（无状态 JWT 模式）。

    由于采用无状态 JWT，服务端不维护会话。
    客户端只需清除本地存储的令牌即可。
    """
    return success_response(data=None, message="已退出登录")


@router.post("/github/callback", summary="GitHub OAuth 回调")
async def github_callback(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    GitHub OAuth 登录/注册回调。

    流程：
    1. 使用授权码向 GitHub 换取 access_token
    2. 获取 GitHub 用户信息
    3. 查找或创建本地用户
    4. 返回 JWT 双令牌

    TODO: 实际调用 GitHub API 的逻辑已在 github_service 中预留，
          此处提供完整路由骨架，待接入真实 GitHub OAuth 流程。
    """
    # TODO: 实现完整的 GitHub OAuth 流程
    # 1. POST https://github.com/login/oauth/access_token
    # 2. GET https://api.github.com/user
    # 3. 根据 github_id 查找或创建 User
    # 4. 签发令牌
    return success_response(
        data=None,
        message="GitHub OAuth 回调接口（待实现）",
    )

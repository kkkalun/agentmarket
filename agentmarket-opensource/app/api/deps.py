"""
API 依赖注入函数

提供用户认证、可选认证和管理员权限校验等 FastAPI 依赖。
"""

from typing import Optional

from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import User
from app.services.auth_service import decode_token

# OAuth2 密码模式令牌提取（从 Authorization: Bearer <token> 头部）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    获取当前已认证用户（强制登录）。

    从 Authorization 头部提取 JWT 令牌，解码后查询数据库返回用户对象。
    若令牌无效、过期或用户不存在，抛出 UnauthorizedError。
    """
    if not token:
        raise UnauthorizedError(message="缺少认证令牌，请先登录")

    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise UnauthorizedError(message="令牌格式无效")
    except Exception as exc:
        # JWT 过期或签名错误等异常统一转为未认证
        raise UnauthorizedError(message=f"认证失败：{exc}")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError(message="用户不存在或已被删除")
    if user.status == "BANNED":
        raise ForbiddenError(message="账号已被封禁")
    if user.status != "ACTIVE":
        raise UnauthorizedError(message="账号状态异常，请联系管理员")

    return user


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    获取当前用户（可选，未登录时返回 None）。

    与 get_current_user 类似，但在无令牌或令牌无效时不抛异常，而是返回 None。
    适用于「登录用户可见额外信息」等场景。
    """
    if not token:
        return None

    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            return None
    except Exception:
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user and user.status == "ACTIVE":
        return user
    return None


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    要求当前用户具有管理员权限（ADMIN 或 SUPERADMIN）。

    不满足条件时抛出 ForbiddenError。
    """
    if current_user.role not in ("ADMIN", "SUPERADMIN"):
        raise ForbiddenError(message="需要管理员权限才能执行此操作")
    return current_user

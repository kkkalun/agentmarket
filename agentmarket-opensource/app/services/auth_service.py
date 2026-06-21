"""
认证服务模块

提供密码哈希、密码校验、JWT 令牌生成与解码等安全相关工具函数。
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings


def hash_password(password: str) -> str:
    """
    将明文密码进行 bcrypt 哈希处理。

    参数：
        password: 用户输入的明文密码

    返回：
        bcrypt 哈希后的字符串
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    校验明文密码是否与哈希值匹配。

    参数：
        plain: 明文密码
        hashed: 存储的哈希值

    返回：
        匹配返回 True，否则返回 False
    """
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str, email: str, role: str) -> str:
    """
    创建 JWT 访问令牌。

    参数：
        user_id: 用户 ID（写入 sub 字段）
        email: 用户邮箱
        role: 用户角色

    返回：
        JWT 编码后的字符串
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str, email: str, role: str) -> str:
    """
    创建 JWT 刷新令牌。

    参数：
        user_id: 用户 ID
        email: 用户邮箱
        role: 用户角色

    返回：
        JWT 编码后的字符串（有效期较长）
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    解码并校验 JWT 令牌。

    参数：
        token: JWT 编码的字符串

    返回：
        解码后的 payload 字典

    异常：
        JWTError: 令牌过期、签名不匹配或格式错误时抛出
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        raise

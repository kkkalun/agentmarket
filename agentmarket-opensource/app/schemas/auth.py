"""
认证相关 Pydantic Schema

包含注册、登录、令牌刷新等请求/响应数据模型。
"""

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class RegisterRequest(BaseModel):
    """用户注册请求"""

    email: EmailStr
    username: str
    password: str
    display_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """校验用户名：3-30 位，仅允许字母、数字、下划线"""
        if len(v) < 3 or len(v) > 30:
            raise ValueError("用户名长度须在 3-30 个字符之间")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("用户名仅允许字母、数字和下划线")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """校验密码：至少 8 位，必须包含大写字母、小写字母和数字"""
        if len(v) < 8:
            raise ValueError("密码长度不能少于 8 位")
        if not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not re.search(r"[a-z]", v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含至少一个数字")
        return v


class LoginRequest(BaseModel):
    """用户登录请求"""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """令牌响应（JWT 双令牌模式）"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)


class RefreshRequest(BaseModel):
    """刷新令牌请求"""

    refresh_token: str

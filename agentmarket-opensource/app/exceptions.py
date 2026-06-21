"""
自定义异常类与异常处理函数

定义业务异常层次结构，并提供注册到 FastAPI 应用的异常处理器，
确保所有错误均以统一的 JSON 格式返回给客户端。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ─────────────────────────────────────────────────────────────
#  异常基类
# ─────────────────────────────────────────────────────────────

class AppError(Exception):
    """应用级业务异常基类"""

    def __init__(
        self,
        message: str = "服务器内部错误",
        status_code: int = 500,
        code: str | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code or "INTERNAL_ERROR"
        super().__init__(message)


# ─────────────────────────────────────────────────────────────
#  常用业务异常
# ─────────────────────────────────────────────────────────────

class NotFoundError(AppError):
    """请求的资源不存在"""

    def __init__(self, message: str = "资源不存在") -> None:
        super().__init__(message=message, status_code=404, code="NOT_FOUND")


class UnauthorizedError(AppError):
    """未认证（未登录或令牌无效）"""

    def __init__(self, message: str = "请先登录") -> None:
        super().__init__(message=message, status_code=401, code="UNAUTHORIZED")


class ForbiddenError(AppError):
    """已认证但无权执行该操作"""

    def __init__(self, message: str = "无权执行此操作") -> None:
        super().__init__(message=message, status_code=403, code="FORBIDDEN")


class ConflictError(AppError):
    """资源冲突（如唯一约束违反）"""

    def __init__(self, message: str = "资源冲突") -> None:
        super().__init__(message=message, status_code=409, code="CONFLICT")


class ValidationError(AppError):
    """业务层参数校验失败"""

    def __init__(self, message: str = "参数校验失败") -> None:
        super().__init__(message=message, status_code=422, code="VALIDATION_ERROR")


# ─────────────────────────────────────────────────────────────
#  FastAPI 异常处理器
# ─────────────────────────────────────────────────────────────

async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    """统一处理所有 AppError 子类异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "message": exc.message,
            "code": exc.code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def generic_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """兜底：处理所有未被捕获的异常，避免向客户端泄露堆栈信息"""
    import traceback
    traceback.print_exc()  # 开发阶段：打印完整错误到控制台
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "message": "服务器内部错误",
            "code": "INTERNAL_ERROR",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# ─────────────────────────────────────────────────────────────
#  注册函数：在 main.py 中调用
# ─────────────────────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """
    将自定义异常处理器注册到 FastAPI 应用实例。

    用法（在 main.py 中）：
        from app.exceptions import register_exception_handlers
        app = FastAPI(...)
        register_exception_handlers(app)
    """
    app.add_exception_handler(AppError, app_error_handler)          # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore[arg-type]

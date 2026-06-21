"""
统一响应格式工具函数

基于 Pydantic 模型（ApiResponse / PaginatedResponse）构建标准化的 API 响应，
利用 Pydantic v2 的 model_dump(mode="json") 自动处理 datetime 等类型的序列化，
无需额外依赖 jsonable_encoder。
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi.responses import JSONResponse

from app.schemas.common import ApiResponse, PaginatedResponse


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    status_code: int = 200,
) -> JSONResponse:
    """
    构建成功响应。

    内部使用 Pydantic ApiResponse 模型进行类型安全的序列化，
    自动处理 datetime、Decimal 等不可直接 JSON 化的类型。

    参数：
        data: 响应数据（Pydantic 模型、dict、list 或标量均可）
        message: 提示消息
        status_code: HTTP 状态码（默认 200）

    返回：
        JSONResponse 实例
    """
    response = ApiResponse(success=True, data=data, message=message)
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(mode="json"),
    )


def error_response(
    message: str,
    code: Optional[str] = None,
    status_code: int = 400,
) -> JSONResponse:
    """
    构建错误响应。

    参数：
        message: 错误描述
        code: 业务错误码（如 "INVALID_TOKEN"）
        status_code: HTTP 状态码（默认 400）

    返回：
        JSONResponse 实例
    """
    response = ApiResponse(
        success=False, data=None, message=message, code=code or "BAD_REQUEST",
    )
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(mode="json"),
    )


def paginated_response(
    data: list,
    page: int,
    page_size: int,
    total: int,
    message: Optional[str] = None,
) -> JSONResponse:
    """
    构建分页响应。

    内部使用 PaginatedResponse.create() 工厂方法自动计算分页衍生字段
    （total_pages、has_next、has_prev），并通过 Pydantic 序列化保证
    输出 JSON 的类型安全。

    参数：
        data: 当前页数据列表
        page: 当前页码
        page_size: 每页条数
        total: 总记录数
        message: 提示消息

    返回：
        包含分页元数据的 JSONResponse 实例
    """
    response = PaginatedResponse.create(
        data=data, page=page, page_size=page_size, total=total, message=message,
    )
    return JSONResponse(
        status_code=200,
        content=response.model_dump(mode="json"),
    )

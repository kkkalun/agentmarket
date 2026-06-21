"""
通用响应 Schema

提供统一的 API 响应包装结构，支持泛型数据、分页信息和健康检查。
"""

from datetime import datetime, timezone
from math import ceil
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# 泛型类型变量，用于 ApiResponse / PaginatedResponse 的数据载荷
T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应包装"""

    success: bool = Field(default=True, description="请求是否成功")
    data: Optional[T] = Field(default=None, description="响应数据")
    message: Optional[str] = Field(default=None, description="提示消息")
    code: Optional[str] = Field(default=None, description="业务错误码")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="响应时间戳（UTC）",
    )

    model_config = ConfigDict(from_attributes=True)


class PaginationMeta(BaseModel):
    """分页元数据（嵌套在 PaginatedResponse.pagination 中）"""

    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页条数")
    total: int = Field(..., description="总记录数")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应包装（在 ApiResponse 基础上增加嵌套分页元数据）"""

    success: bool = Field(default=True, description="请求是否成功")
    data: Optional[List[T]] = Field(default=None, description="当前页数据列表")
    message: Optional[str] = Field(default=None, description="提示消息")
    code: Optional[str] = Field(default=None, description="业务错误码")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="响应时间戳（UTC）",
    )

    # ── 分页元数据（嵌套对象，保持向后兼容的 JSON 结构） ──────
    pagination: PaginationMeta = Field(..., description="分页信息")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def create(
        cls,
        data: List[T],
        page: int,
        page_size: int,
        total: int,
        message: Optional[str] = None,
    ) -> "PaginatedResponse[T]":
        """
        便捷工厂方法：根据数据列表和分页参数自动计算 total_pages / has_next / has_prev。

        用法：
            return PaginatedResponse.create(
                data=items, page=1, page_size=20, total=100
            )
        """
        total_pages = ceil(total / page_size) if page_size > 0 else 0
        return cls(
            success=True,
            data=data,
            message=message,
            pagination=PaginationMeta(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
            ),
        )


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field(default="ok", description="服务状态")
    uptime: float = Field(..., description="服务运行时长（秒）")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="当前时间戳（UTC）",
    )

    model_config = ConfigDict(from_attributes=True)

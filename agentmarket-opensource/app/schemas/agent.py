"""
Agent 模板相关 Pydantic Schema

包含列表查询、搜索、详情、分类、评价等数据模型。
"""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────────────────────
#  嵌套子模型
# ─────────────────────────────────────────────────────────────

class AuthorBrief(BaseModel):
    """作者简要信息（嵌套在 Agent 响应中）"""

    id: str
    username: str
    display_name: str
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CategoryBrief(BaseModel):
    """分类简要信息（嵌套在 Agent 响应中）"""

    id: str
    slug: str
    name: str
    icon: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TagBrief(BaseModel):
    """标签简要信息（嵌套在 Agent 响应中）"""

    id: str
    slug: str
    name: str
    group_name: str

    model_config = ConfigDict(from_attributes=True)


class LicenseBrief(BaseModel):
    """许可证简要信息（嵌套在 Agent 详情响应中）"""

    id: str
    spdx_id: str
    name: str
    allows_commercial_use: bool
    requires_disclosure: bool

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────
#  查询参数
# ─────────────────────────────────────────────────────────────

class AgentListQuery(BaseModel):
    """Agent 列表查询参数"""

    page: int = Field(default=1, ge=1, description="页码，从 1 开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数，最大 100")
    category: Optional[str] = Field(default=None, description="按分类 slug 筛选")
    tag: Optional[str] = Field(default=None, description="按标签 slug 筛选")
    sort: Literal["newest", "popular", "rating", "downloads"] = Field(
        default="newest", description="排序方式"
    )
    pricing: Literal["free", "paid", "all"] = Field(
        default="all", description="定价筛选"
    )


class AgentSearchQuery(BaseModel):
    """Agent 全文搜索参数"""

    q: str = Field(..., min_length=1, max_length=200, description="搜索关键词")
    page: int = Field(default=1, ge=1, description="页码，从 1 开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")
    category: Optional[str] = Field(default=None, description="按分类 slug 筛选")
    sort: Literal["newest", "popular", "rating", "downloads"] = Field(
        default="newest", description="排序方式"
    )


# ─────────────────────────────────────────────────────────────
#  响应模型
# ─────────────────────────────────────────────────────────────

class AgentResponse(BaseModel):
    """Agent 模板列表项响应"""

    id: str
    slug: str
    name: str
    short_description: str
    cover_image_url: Optional[str] = None
    pricing_model: str
    base_price: float
    github_stars: int
    total_deployments: int
    avg_rating: float
    created_at: datetime
    author: AuthorBrief
    category: Optional[CategoryBrief] = None
    tags: List[TagBrief] = []

    model_config = ConfigDict(from_attributes=True)


class AgentDetailResponse(AgentResponse):
    """Agent 模板详情响应（扩展列表响应）"""

    description: Optional[str] = None
    license: Optional[LicenseBrief] = None
    deploy_type: str
    is_favorite: bool = False
    github_forks: int = 0
    github_repo_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CategoryResponse(BaseModel):
    """分类响应（含模板计数）"""

    id: str
    slug: str
    name: str
    icon: Optional[str] = None
    agent_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ReviewUserBrief(BaseModel):
    """评价者简要信息"""

    id: str
    username: str
    display_name: str
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewResponse(BaseModel):
    """评价响应"""

    id: str
    rating: int
    content: Optional[str] = None
    status: str
    created_at: datetime
    user: ReviewUserBrief

    model_config = ConfigDict(from_attributes=True)

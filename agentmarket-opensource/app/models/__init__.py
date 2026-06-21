"""
数据模型汇总导出

将所有 ORM 模型集中导入，便于 Alembic 自动发现并生成迁移脚本。
"""

from app.models.user import User
from app.models.agent import AgentTemplate, Category, Tag, AgentTemplateTag, License
from app.models.order import Order, OrderItem
from app.models.review import Review
from app.models.deployment import Deployment
from app.models.misc import (
    ComplianceRecord,
    Promotion,
    UserFavorite,
    SystemConfig,
    OperationLog,
)

__all__ = [
    "User",
    "AgentTemplate",
    "Category",
    "Tag",
    "AgentTemplateTag",
    "License",
    "Order",
    "OrderItem",
    "Review",
    "Deployment",
    "ComplianceRecord",
    "Promotion",
    "UserFavorite",
    "SystemConfig",
    "OperationLog",
]

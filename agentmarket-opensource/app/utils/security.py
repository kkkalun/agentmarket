"""
安全与标识工具函数

提供订单号生成、URL slug 生成等与安全/标识相关的工具方法。
"""

import random
import re
import string
from datetime import datetime


def generate_order_no() -> str:
    """
    生成业务订单号。

    格式：AM + 年月日时分秒 + 6 位随机数
    示例：AM20260620143052a8x3k1

    返回：
        唯一的订单号字符串
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"AM{timestamp}{random_suffix}"


def generate_slug(name: str) -> str:
    """
    将名称转换为 URL 友好的 slug。

    规则：
    1. 转为小写
    2. 将空格和特殊字符替换为短横线
    3. 去除首尾短横线
    4. 合并连续的短横线
    5. 末尾追加 4 位随机字符以保证唯一性

    参数：
        name: 原始名称

    返回：
        URL 友好的 slug 字符串

    示例：
        "我的 Agent 模板" -> "我的-agent-模板-a3x9"
        "Hello World!" -> "hello-world-k2m7"
    """
    # 转小写
    slug = name.lower().strip()

    # 将空格、下划线和其他非字母数字字符替换为短横线
    slug = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", slug)

    # 去除首尾短横线
    slug = slug.strip("-")

    # 合并连续短横线
    slug = re.sub(r"-{2,}", "-", slug)

    # 如果处理后为空，则使用纯随机 slug
    if not slug:
        slug = "agent"

    # 追加随机后缀确保唯一性
    random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{slug}-{random_suffix}"

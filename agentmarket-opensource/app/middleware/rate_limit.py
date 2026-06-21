"""
速率限制中间件

基于内存的简易限流器，按客户端 IP 地址统计每分钟请求次数。
适用于开发和小规模部署场景；生产环境建议替换为 Redis + sliding window 方案。
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    简易内存速率限制中间件。

    工作原理：
    - 使用字典记录每个 IP 地址在当前时间窗口（1 分钟）内的请求次数
    - 超过 settings.RATE_LIMIT_PER_MINUTE 时返回 429 Too Many Requests
    - 时间窗口过期后自动重置计数器

    注意事项：
    - 仅适用于单进程部署；多进程/多实例场景请使用 Redis 限流
    - 不保证高并发下的精确性，但足以起到基本的防护作用
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        # 存储结构：{ip: (窗口开始时间戳, 请求次数)}
        self._request_counts: dict[str, tuple[float, int]] = defaultdict(
            lambda: (time.time(), 0)
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        拦截每个请求，检查是否超出速率限制。

        参数：
            request: 当前 HTTP 请求
            call_next: 下一个中间件或路由处理器

        返回：
            正常响应或 429 错误响应
        """
        # 获取客户端 IP（优先从 X-Forwarded-For 获取，兼容反向代理）
        client_ip = self._get_client_ip(request)

        current_time = time.time()
        window_start, count = self._request_counts[client_ip]

        # 如果当前时间已超过窗口期（60 秒），重置计数
        if current_time - window_start > 60:
            self._request_counts[client_ip] = (current_time, 1)
        else:
            # 窗口期内累加
            count += 1
            self._request_counts[client_ip] = (window_start, count)

            # 检查是否超限
            if count > settings.RATE_LIMIT_PER_MINUTE:
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "data": None,
                        "message": "请求过于频繁，请稍后再试",
                        "code": "RATE_LIMIT_EXCEEDED",
                    },
                    headers={
                        "Retry-After": str(int(60 - (current_time - window_start))),
                        "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE),
                        "X-RateLimit-Remaining": "0",
                    },
                )

        # 正常放行
        response = await call_next(request)

        # 在响应头中附加限流信息
        remaining = max(
            0,
            settings.RATE_LIMIT_PER_MINUTE - self._request_counts[client_ip][1],
        )
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """
        提取客户端真实 IP 地址。

        优先从 X-Forwarded-For 头部获取（支持 Nginx 等反向代理），
        若不存在则回退到 request.client.host。
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # X-Forwarded-For 可能包含多个 IP，取第一个（最原始的客户端 IP）
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

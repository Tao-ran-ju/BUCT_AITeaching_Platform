"""HTTP 中间件：访问日志、统一耗时统计。"""
import time
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("access")


class AccessLogMiddleware(BaseHTTPMiddleware):
    """记录每个请求的方法、路径、状态码与耗时。"""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        cost_ms = (time.time() - start) * 1000
        logger.info(
            "%s %s -> %s %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            cost_ms,
        )
        return response

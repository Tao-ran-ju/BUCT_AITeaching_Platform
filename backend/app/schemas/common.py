"""统一响应与分页结构。"""
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """统一 API 响应：{code, message, data}。"""

    code: int = 0
    message: str = "success"
    data: Optional[T] = None


class PageData(BaseModel, Generic[T]):
    """分页数据容器。"""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

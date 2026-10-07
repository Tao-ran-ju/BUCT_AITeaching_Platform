"""统一响应、分页结构，以及时间字段兼容类型。"""
from datetime import datetime
from typing import Annotated, Generic, Optional, TypeVar

from pydantic import BaseModel, BeforeValidator

T = TypeVar("T")


def _unix_to_datetime(value):
    """将 UNIX 时间戳（int/float）转为 datetime；已是 datetime 则原样返回。

    buct_cip 库部分表的 created_at / edited_at 存 UNIX 整数，部分存 datetime，
    出参统一转成 datetime，便于前端与文档展示。
    """
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    return value


# 兼容两类时间字段的类型别名
Timestamp = Annotated[datetime, BeforeValidator(_unix_to_datetime)]


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

"""分页工具：统一的页码 / 页大小参数与分页结果结构。"""
import math


def paginate(items: list, total: int, page: int, page_size: int) -> dict:
    """构造统一分页结构。

    Args:
        items: 当前页数据列表
        total: 符合条件的总记录数
        page: 当前页码（从 1 开始）
        page_size: 每页条数
    """
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if page_size else 0,
    }


def normalize_page(page: int | None, page_size: int | None) -> tuple[int, int]:
    """把可选的 page / page_size 参数归一化成合法值。"""
    page = page if page and page > 0 else 1
    page_size = page_size if page_size and page_size > 0 else 10
    page_size = min(page_size, 100)  # 单页最多 100 条
    return page, page_size

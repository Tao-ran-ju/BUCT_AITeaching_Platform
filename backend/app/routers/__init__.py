"""路由层：接收请求、参数校验、调用服务、返回统一响应。

约定：本层不写业务逻辑；成功响应统一走 ok()，失败抛 AppError
由 main.py 全局异常处理器转成 {code, message, data:null}。
"""
from typing import Any


def ok(data: Any = None, message: str = "success") -> dict:
    """统一成功响应。"""
    return {"code": 0, "message": message, "data": data}

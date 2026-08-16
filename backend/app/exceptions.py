"""全局业务异常定义。

业务代码抛出 AppError 及其子类，由 main.py 中注册的
全局异常处理器统一转换成 {code, message, data} 响应。
"""


class AppError(Exception):
    """业务异常基类。"""

    def __init__(self, code: int = 400, message: str = "请求失败"):
        self.code = code
        self.message = message
        super().__init__(message)

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "data": None}


class ValidateError(AppError):
    """参数校验失败。"""

    def __init__(self, message: str = "参数校验失败"):
        super().__init__(code=422, message=message)


class AuthError(AppError):
    """未登录 / 登录已过期 / Token 非法。"""

    def __init__(self, message: str = "未登录或登录已过期"):
        super().__init__(code=401, message=message)


class ForbiddenError(AppError):
    """已登录但无操作权限。"""

    def __init__(self, message: str = "没有操作权限"):
        super().__init__(code=403, message=message)


class NotFoundError(AppError):
    """资源不存在。"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(code=404, message=message)


class ConflictError(AppError):
    """资源冲突（如用户名已存在）。"""

    def __init__(self, message: str = "资源冲突"):
        super().__init__(code=409, message=message)

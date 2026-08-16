"""全局依赖：数据库会话、当前登录用户、可选用户、超级管理员。"""
from fastapi import Depends, Header, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import AuthError, ForbiddenError
from app.models.user import User
from app.utils.security import decode_token


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str = Header(default=""),
) -> User:
    """解析请求头 Authorization: Bearer <token>，返回当前登录用户。

    校验失败统一抛 AuthError(401)。
    """
    if not authorization.startswith("Bearer "):
        raise AuthError("缺少登录凭证")
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_token(token)
    if not payload:
        raise AuthError("登录已过期，请重新登录")

    user = db.get(User, payload.get("uid"))
    if not user or user.status != "active":
        raise AuthError("账号不存在或已禁用")
    return user


def get_current_user_via_token(
    db: Session = Depends(get_db),
    authorization: str = Header(default=""),
    token: str = Query(default=""),
) -> User:
    """解析用户身份，支持 Authorization 头或 ?token= 查询参数。

    浏览器 <img>/<a> 标签无法携带 Authorization 头，故文件下载/缩略图直链需把
    JWT 放进 ?token= 查询参数。校验逻辑与 get_current_user 完全一致。
    """
    raw = ""
    if authorization.startswith("Bearer "):
        raw = authorization.removeprefix("Bearer ").strip()
    elif token:
        raw = token.strip()
    if not raw:
        raise AuthError("缺少登录凭证")
    payload = decode_token(raw)
    if not payload:
        raise AuthError("登录已过期，请重新登录")

    user = db.get(User, payload.get("uid"))
    if not user or user.status != "active":
        raise AuthError("账号不存在或已禁用")
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """仅允许系统管理员访问。"""
    if user.role != "admin":
        raise ForbiddenError("仅系统管理员可执行此操作")
    return user

"""全局依赖：数据库会话、当前登录用户、可选用户、教师 / 学生 / 管理员。"""
from fastapi import Depends, Header, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import AuthError, ForbiddenError
from app.models.user import ROLE_STUDENT, ROLE_TEACHER, User
from app.utils.security import decode_token


def _resolve_user(db: Session, raw_token: str) -> User:
    """根据原始 token 字符串解析当前用户；失败统一抛 AuthError(401)。"""
    payload = decode_token(raw_token)
    if not payload:
        raise AuthError("登录已过期，请重新登录")
    user = db.get(User, payload.get("uid"))
    if not user or user.status != 0:
        raise AuthError("账号不存在或已禁用")
    return user


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str = Header(default=""),
) -> User:
    """解析请求头 Authorization: Bearer <token>，返回当前登录用户。"""
    if not authorization.startswith("Bearer "):
        raise AuthError("缺少登录凭证")
    return _resolve_user(db, authorization.removeprefix("Bearer ").strip())


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
    return _resolve_user(db, raw)


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """仅允许管理角色访问。学校 user_rft 无独立管理员，教师（role=0）即管理角色。"""
    if user.role != ROLE_TEACHER:
        raise ForbiddenError("仅教师或管理员可执行此操作")
    return user


def get_current_teacher(user: User = Depends(get_current_user)) -> User:
    """仅允许教师访问：作业发布 / 班级管理等教学管理操作。"""
    if user.role != ROLE_TEACHER:
        raise ForbiddenError("仅教师可执行此操作")
    return user


def get_current_student(user: User = Depends(get_current_user)) -> User:
    """仅允许学生访问：提交作业、查看「我的作业/班级」等学生端操作。"""
    if user.role != ROLE_STUDENT:
        raise ForbiddenError("仅学生可执行此操作")
    return user

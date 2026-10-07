"""认证路由：账号密码登录、统一 SSO 换 token、管理员注册建档。"""
import secrets

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_admin
from app.exceptions import ForbiddenError
from app.routers import ok
from app.schemas.user import LoginRequest, SsoRequest, UserCreate
from app.services.user_service import UserService
from app.utils.serializers import user_out

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", summary="账号密码登录")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = UserService.authenticate(db, data.username, data.password)
    token = UserService.issue_token(user)
    return ok({
        "access_token": token,
        "token_type": "bearer",
        "user": user_out(user),
    })


@router.post("/sso/token", summary="统一 SSO：共享密钥换 JWT（教师/学生）")
def sso_token(data: SsoRequest, db: Session = Depends(get_db)):
    """学生端/教师端后端已用学校 SSO 登录后，凭两端约定共享密钥换取教师端 JWT。

    安全约束：SSO_SHARED_SECRET 未配置时 403；密钥常数时间比较；按请求 role 建档
    （教师写 user_rft + teacher_actors，学生仅写 user_rft），密码写入随机不可知值。
    """
    if not settings.SSO_SHARED_SECRET:
        raise ForbiddenError("SSO 未启用")
    if not secrets.compare_digest(data.secret, settings.SSO_SHARED_SECRET):
        raise ForbiddenError("SSO 共享密钥错误")
    if data.role not in (0, 1):
        raise ForbiddenError("角色非法")
    user = UserService.get_or_create_sso_user(db, data.uid, data.name, data.role)
    token = UserService.issue_token(user)
    return ok({
        "access_token": token,
        "token_type": "bearer",
        "user": user_out(user),
    })


@router.post("/register", summary="创建用户（教师/管理员）",
             dependencies=[Depends(get_current_admin)])
def register(data: UserCreate, db: Session = Depends(get_db)):
    user = UserService.create_user(db, data)
    return ok(user_out(user))

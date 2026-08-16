"""认证路由：登录、注册（仅管理员）。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin
from app.routers import ok
from app.schemas.user import LoginRequest, UserCreate, UserOut
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", summary="登录")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = UserService.authenticate(db, data.username, data.password)
    token = UserService.issue_token(user)
    return ok({
        "access_token": token,
        "token_type": "bearer",
        "user": UserOut.model_validate(user),
    })


@router.post("/register", summary="创建用户（管理员）", dependencies=[Depends(get_current_admin)])
def register(data: UserCreate, db: Session = Depends(get_db)):
    user = UserService.create_user(db, data)
    return ok(UserOut.model_validate(user))

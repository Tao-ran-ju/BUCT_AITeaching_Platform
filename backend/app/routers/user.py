"""用户路由：个人资料、改密码、用户列表（教师/管理员）。"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.models.user import User
from app.routers import ok
from app.schemas.user import PasswordChange, UserUpdate
from app.services.user_service import UserService
from app.utils.serializers import user_out

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/me", summary="当前用户信息")
def get_me(user: User = Depends(get_current_user)):
    return ok(user_out(user))


@router.put("/me", summary="更新个人资料")
def update_me(data: UserUpdate, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    updated = UserService.update_profile(db, user, data)
    return ok(user_out(updated))


@router.post("/me/password", summary="修改密码")
def change_password(data: PasswordChange, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    UserService.change_password(db, user, data.old_password, data.new_password)
    return ok(message="密码修改成功")


@router.get("", summary="用户列表", dependencies=[Depends(get_current_admin)])
def list_users(
    role: Optional[int] = Query(None, description="0=教师 1=学生"),
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    result = UserService.list_users(db, page, page_size, role=role, keyword=keyword)
    result["items"] = [user_out(u) for u in result["items"]]
    return ok(result)

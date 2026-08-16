"""用户路由：个人资料、改密码、头像上传、用户管理（管理员）。"""
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.exceptions import ValidateError
from app.models.user import User
from app.routers import ok
from app.schemas.user import PasswordChange, UserOut, UserUpdate
from app.services.user_service import UserService
from app.utils.file_handler import save_upload_file

router = APIRouter(prefix="/users", tags=["用户"])

# 头像大小上限（5MB）
AVATAR_MAX_SIZE = 5 * 1024 * 1024


@router.get("/me", summary="获取当前用户信息")
def get_me(user: User = Depends(get_current_user)):
    return ok(UserOut.model_validate(user))


@router.put("/me", summary="更新个人资料")
def update_me(data: UserUpdate, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    updated = UserService.update_profile(db, user, data)
    return ok(UserOut.model_validate(updated))


@router.post("/me/avatar", summary="上传头像")
def upload_avatar(file: UploadFile = File(...),
                  user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """上传并保存当前用户头像到本地磁盘，经 /uploads 静态路由访问。"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise ValidateError("仅支持图片文件")
    data = file.file.read()
    if len(data) > AVATAR_MAX_SIZE:
        raise ValidateError("头像不能超过 5MB")
    file.file.seek(0)  # save_upload_file 会再次读取文件流
    rel = save_upload_file(file, "avatars")  # 形如 uploads/avatars/<uuid>.png
    updated = UserService.set_avatar(db, user, "/" + rel.lstrip("/"))
    return ok(UserOut.model_validate(updated))


@router.post("/me/password", summary="修改密码")
def change_password(data: PasswordChange, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    UserService.change_password(db, user, data.old_password, data.new_password)
    return ok(message="密码修改成功")


@router.get("", summary="用户列表（管理员）", dependencies=[Depends(get_current_admin)])
def list_users(
    role: Optional[str] = Query(None, pattern="^(admin|teacher|student)$"),
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    result = UserService.list_users(db, page, page_size, role=role, keyword=keyword)
    result["items"] = [UserOut.model_validate(u) for u in result["items"]]
    return ok(result)

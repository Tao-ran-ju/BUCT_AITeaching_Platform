"""资源路由：文件上传、资源列表、可见性设置、删除。"""
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.routers import ok
from app.schemas.resource import ResourceOut, ResourceVisibilityUpdate
from app.services.resource_service import ResourceService

router = APIRouter(prefix="/resources", tags=["教学资源"])


@router.post("", summary="上传资源（multipart）")
async def upload_resource(
    title: str = Form(..., description="资源标题"),
    file: UploadFile = File(...),
    course_id: Optional[int] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resource = ResourceService.upload(db, user, title, file, course_id)
    return ok(ResourceOut.model_validate(resource))


@router.get("", summary="资源列表")
def list_resources(
    course_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = ResourceService.list_resources(db, user, course_id, page, page_size)
    result["items"] = [ResourceOut.model_validate(r) for r in result["items"]]
    return ok(result)


@router.patch("/{resource_id}/visibility", summary="设置资源可见性")
def set_visibility(resource_id: int, data: ResourceVisibilityUpdate,
                   user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    resource = ResourceService.set_visibility(db, resource_id, user, data.visibility)
    return ok(ResourceOut.model_validate(resource))


@router.delete("/{resource_id}", summary="删除资源")
def delete_resource(resource_id: int, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    ResourceService.delete(db, resource_id, user)
    return ok(message="资源已删除")

"""资源路由：文件上传、资源列表、可见性设置、删除、下载与在线预览。"""
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.clients.oss_client import oss_client
from app.database import get_db
from app.dependencies import get_current_user, get_current_user_via_token
from app.exceptions import NotFoundError
from app.models.user import User
from app.routers import ok
from app.schemas.resource import ResourceVisibilityUpdate
from app.services.resource_service import ResourceService

router = APIRouter(prefix="/resources", tags=["教学资源"])

# 需要走 IMM 文档转换的 Office 扩展名
_OFFICE_EXT = {".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"}


def _rel_for_kind(resource, kind: str) -> str:
    """按 kind 取资源的相对存储路径；无对应产物时抛 404。"""
    meta = ResourceService._load_meta(resource)
    if kind == "thumbnail":
        rel = meta.get("thumbnail_path")
    elif kind == "transcoded":
        rel = meta.get("transcoded_path")
    else:
        rel = resource.file_path
    if not rel:
        raise NotFoundError("该资源暂无此文件")
    return rel


def _serve_url(resource, rel: str) -> str:
    """返回可访问地址：已镜像时用 OSS 签名 URL，否则回退本地 /uploads 相对路径。"""
    meta = ResourceService._load_meta(resource)
    if meta.get("oss_key") and oss_client.enabled:
        url = oss_client.signed_url(rel)
        if url:
            return url
    return "/" + rel


@router.post("", summary="上传资源（multipart）")
async def upload_resource(
    title: str = Form(..., description="资源标题"),
    file: UploadFile = File(...),
    course_id: Optional[int] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resource = ResourceService.upload(db, user, title, file, course_id)
    return ok(ResourceService._out(resource))


@router.get("", summary="资源列表")
def list_resources(
    course_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = ResourceService.list_resources(db, user, course_id, page, page_size)
    result["items"] = [ResourceService._out(r) for r in result["items"]]
    return ok(result)


@router.patch("/{resource_id}/visibility", summary="设置资源可见性")
def set_visibility(resource_id: int, data: ResourceVisibilityUpdate,
                   user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    resource = ResourceService.set_visibility(db, resource_id, user, data.visibility)
    return ok(ResourceService._out(resource))


@router.delete("/{resource_id}", summary="删除资源")
def delete_resource(resource_id: int, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    ResourceService.delete(db, resource_id, user)
    return ok(message="资源已删除")


@router.get("/{resource_id}/file", summary="下载/流式访问资源文件（302 到签名或本地地址）")
def get_resource_file(resource_id: int,
                      kind: str = Query("original", pattern="^(original|thumbnail|transcoded)$"),
                      user: User = Depends(get_current_user_via_token),
                      db: Session = Depends(get_db)):
    resource = ResourceService.get_resource(db, resource_id)
    rel = _rel_for_kind(resource, kind)
    return RedirectResponse(url=_serve_url(resource, rel))


@router.get("/{resource_id}/preview", summary="在线预览（返回预览 URL 与类型）")
def preview_resource(resource_id: int, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    resource = ResourceService.get_resource(db, resource_id)
    meta = ResourceService._load_meta(resource)
    rel = resource.file_path
    ext = ("." + rel.rsplit(".", 1)[-1].lower()) if "." in rel else ""
    rt = resource.type  # document/image/video/audio/code/other

    if rt == "video":
        play = meta.get("transcoded_path") or rel  # 优先 H.264 转码产物
        return ok({"url": _serve_url(resource, play), "kind": "video"})
    if rt == "audio":
        return ok({"url": _serve_url(resource, rel), "kind": "audio"})
    if rt == "image":
        return ok({"url": _serve_url(resource, rel), "kind": "image"})
    if rt == "document" and ext == ".pdf":
        return ok({"url": _serve_url(resource, rel), "kind": "pdf"})
    if ext in _OFFICE_EXT:
        # Office 文档：尝试 IMM 转 PDF 在线预览，失败回退下载
        if meta.get("oss_key") and oss_client.enabled:
            url = oss_client.office_to_pdf(rel)
            if url:
                return ok({"url": url, "kind": "pdf"})
        return ok({"url": _serve_url(resource, rel), "kind": "download"})
    # 代码 / 文本 / 其他：仅下载
    return ok({"url": _serve_url(resource, rel), "kind": "download"})

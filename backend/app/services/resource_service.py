"""资源服务：文件上传记录、资源查询、权限可见性（映射到 course_resources）。"""
import json
import logging
import time
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.oss_client import oss_client
from app.exceptions import NotFoundError
from app.models.resource import Resource
from app.models.user import User
from app.services.llm_teaching_service import LLMTeachingService
from app.utils import video_processor
from app.utils.file_handler import save_upload_file
from app.utils.pagination import normalize_page, paginate
from app.utils.text_extract import extract_text

logger = logging.getLogger(__name__)


class ResourceService:
    """教学资源业务逻辑（文件落盘 + 元数据入库 + 可见性控制）。

    学校原表的 7 个旧列（摘要/关键词/时长/缩略图/转码/OSS key/可见性）统一收敛为：
    - 摘要 / 关键词 / 时长 / 缩略图 / 转码 / oss_key → metadata_json（JSON 字符串）
    - 可见性 → permission（teacher_only / student / public）
    """

    @staticmethod
    def _now() -> int:
        return int(time.time())

    @staticmethod
    def _load_meta(resource: Resource) -> dict:
        if not resource.metadata_json:
            return {}
        try:
            data = json.loads(resource.metadata_json)
            return data if isinstance(data, dict) else {}
        except (ValueError, TypeError):
            return {}

    @staticmethod
    def _dump_meta(meta: dict) -> str:
        return json.dumps(meta, ensure_ascii=False)

    @staticmethod
    def _auto_annotate(title: str, path: str) -> tuple[str | None, str | None]:
        """对文本类资源提取正文并生成摘要 + 关键词（失败不阻断上传）。"""
        try:
            text = extract_text(path)
        except Exception as exc:
            logger.warning("资源文本提取失败: %s", exc)
            return None, None
        if not text:
            return None, None
        try:
            tag = LLMTeachingService.auto_tag_resource(text, title)
            return tag.get("summary"), tag.get("keywords")
        except Exception as exc:
            logger.warning("资源自动摘要失败: %s", exc)
            return None, None

    @staticmethod
    def _process_video(path: str) -> tuple[float | None, str | None, str | None]:
        """视频上传后处理：时长探测 + 关键帧抽取 + 转码（任一失败不阻断上传）。"""
        out_dir = str(Path(path).parent)
        try:
            duration = video_processor.probe_duration(path)
        except Exception as exc:
            logger.warning("视频时长探测失败: %s", exc)
            duration = None
        try:
            frames = video_processor.extract_keyframes(path, out_dir, count=1)
        except Exception as exc:
            logger.warning("视频关键帧抽取失败: %s", exc)
            frames = []
        try:
            transcoded = video_processor.transcode_mp4(path, out_dir)
        except Exception as exc:
            logger.warning("视频转码失败: %s", exc)
            transcoded = None
        return duration, (frames[0] if frames else None), transcoded

    @staticmethod
    def _mirror_to_oss(resource: Resource, meta: dict, thumbnail_path: str | None,
                       transcoded_path: str | None) -> None:
        """把原文件及视频产物镜像到 OSS；任一失败仅告警，保持本地回退。

        object key 复用本地相对路径（key == file_path），镜像成功后在 metadata 里记 oss_key。
        """
        if not oss_client.enabled:
            return
        paths = [resource.file_path]
        if thumbnail_path:
            paths.append(thumbnail_path)
        if transcoded_path:
            paths.append(transcoded_path)
        ok_all = True
        for p in paths:
            if not Path(p).exists():
                continue
            if not oss_client.upload_file(p, p):
                ok_all = False
        if ok_all:
            meta["oss_key"] = resource.file_path

    @staticmethod
    def upload(db: Session, user: User, name: str, file, course_id: int | None) -> Resource:
        """保存上传文件并写入资源记录。"""
        sub_dir = f"course/{course_id}" if course_id else f"user/{user.id}"
        path = save_upload_file(file, sub_dir)
        ext = path.rsplit(".", 1)[-1].lower()
        type_map = {
            "pdf": "document", "doc": "document", "docx": "document",
            "ppt": "document", "pptx": "document",
            "png": "image", "jpg": "image", "jpeg": "image",
            "gif": "image", "webp": "image",
            "mp4": "video", "mov": "video", "avi": "video", "mkv": "video",
            "mp3": "audio", "wav": "audio", "m4a": "audio", "flac": "audio",
            "py": "code", "c": "code", "cpp": "code", "java": "code",
        }
        resource_type = type_map.get(ext, "other")

        duration, thumbnail_path, transcoded_path = None, None, None
        if resource_type == "video":
            duration, thumbnail_path, transcoded_path = ResourceService._process_video(path)

        summary, keywords = ResourceService._auto_annotate(name, path)
        meta = {
            "summary": summary,
            "keywords": keywords,
            "duration": duration,
            "thumbnail_path": thumbnail_path,
            "transcoded_path": transcoded_path,
        }

        resource = Resource(
            course_id=course_id,
            name=name,
            type=resource_type,
            file_path=path,
            file_size=getattr(file, "size", 0) or 0,
            permission="student" if course_id else "teacher_only",
            status=0,
            created_at=ResourceService._now(),
            edited_at=ResourceService._now(),
            created_by=user.uid,
        )
        ResourceService._mirror_to_oss(resource, meta, thumbnail_path, transcoded_path)
        resource.metadata_json = ResourceService._dump_meta(meta)
        db.add(resource)
        db.commit()
        db.refresh(resource)
        return resource

    _PERM_TO_VIS = {"public": "public", "student": "course", "teacher_only": "private"}
    _VIS_TO_PERM = {"public": "public", "course": "student", "private": "teacher_only"}

    @staticmethod
    def _out(resource: Resource) -> dict:
        meta = ResourceService._load_meta(resource)
        return {
            "id": resource.id,
            "course_id": resource.course_id,
            "title": resource.name,
            "name": resource.name,
            "resource_type": resource.type,
            "type": resource.type,
            "file_path": resource.file_path,
            "file_size": resource.file_size,
            "visibility": ResourceService._PERM_TO_VIS.get(resource.permission, "course"),
            "permission": resource.permission,
            "summary": meta.get("summary"),
            "keywords": meta.get("keywords"),
            "duration": meta.get("duration"),
            "thumbnail_path": meta.get("thumbnail_path"),
            "transcoded_path": meta.get("transcoded_path"),
            "oss_key": meta.get("oss_key"),
            "status": resource.status,
            "created_by": resource.created_by,
            "metadata": meta,
            "created_at": resource.created_at,
        }

    @staticmethod
    def list_resources(db: Session, user: User, course_id: int | None = None,
                       page: int | None = None, page_size: int | None = None) -> dict:
        """列出教师本人上传的资源（教师端管理自己的资源）。"""
        page, page_size = normalize_page(page, page_size)
        stmt = select(Resource).where(Resource.created_by == user.uid)
        if course_id:
            stmt = stmt.where(Resource.course_id == course_id)
        total = len(db.scalars(stmt).all())
        rows = db.scalars(
            stmt.order_by(Resource.id.desc()).offset((page - 1) * page_size).limit(page_size)
        ).all()
        return paginate(rows, total, page, page_size)

    @staticmethod
    def get_resource(db: Session, resource_id: int) -> Resource:
        resource = db.get(Resource, resource_id)
        if not resource:
            raise NotFoundError("资源不存在")
        return resource

    @staticmethod
    def set_visibility(db: Session, resource_id: int, user: User, visibility: str) -> Resource:
        """修改资源可见性（public / course / private）。"""
        resource = ResourceService.get_resource(db, resource_id)
        resource.permission = ResourceService._VIS_TO_PERM.get(visibility, "teacher_only")
        resource.edited_at = ResourceService._now()
        db.commit()
        db.refresh(resource)
        return resource

    @staticmethod
    def delete(db: Session, resource_id: int, user: User) -> None:
        resource = ResourceService.get_resource(db, resource_id)
        meta = ResourceService._load_meta(resource)
        # 清理存储：本地磁盘 + OSS（原文件 / 缩略图 / 转码产物）
        for rel in (resource.file_path, meta.get("thumbnail_path"), meta.get("transcoded_path")):
            if not rel:
                continue
            if oss_client.enabled:
                oss_client.delete(rel)
            try:
                p = Path(rel)
                if p.is_file():
                    p.unlink()
            except OSError:
                pass
        db.delete(resource)
        db.commit()

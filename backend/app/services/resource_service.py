"""资源服务：文件上传记录、资源查询、权限可见性。"""
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ForbiddenError, NotFoundError
from app.models.resource import Resource
from app.models.user import User
from app.services.llm_teaching_service import LLMTeachingService
from app.utils import video_processor
from app.utils.file_handler import save_upload_file
from app.utils.pagination import normalize_page, paginate
from app.utils.text_extract import extract_text

logger = logging.getLogger(__name__)


class ResourceService:
    """教学资源业务逻辑（文件落盘 + 元数据入库 + 可见性控制）。"""

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
    def upload(db: Session, user: User, title: str, file, course_id: int | None) -> Resource:
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

        summary, keywords = ResourceService._auto_annotate(title, path)
        resource = Resource(
            title=title,
            resource_type=resource_type,
            file_path=path,
            file_size=file.size,
            course_id=course_id,
            uploader_id=user.id,
            visibility="course" if course_id else "private",
            summary=summary,
            keywords=keywords,
            duration=duration,
            thumbnail_path=thumbnail_path,
            transcoded_path=transcoded_path,
        )
        db.add(resource)
        db.commit()
        db.refresh(resource)
        return resource

    @staticmethod
    def list_resources(db: Session, user: User, course_id: int | None = None,
                       page: int | None = None, page_size: int | None = None) -> dict:
        """列出用户可见的资源：公开资源 + 本人上传的资源。"""
        page, page_size = normalize_page(page, page_size)
        stmt = select(Resource).where(
            (Resource.visibility == "public") | (Resource.uploader_id == user.id)
        )
        if course_id:
            stmt = stmt.where(Resource.course_id == course_id)
        total = len(db.scalars(stmt).all())
        rows = db.scalars(
            stmt.order_by(Resource.id.desc()).offset((page - 1) * page_size).limit(page_size)
        ).all()
        return paginate(rows, total, page, page_size)

    @staticmethod
    def get_resource(db: Session, resource_id: int, user: User) -> Resource:
        resource = db.get(Resource, resource_id)
        if not resource:
            raise NotFoundError("资源不存在")
        if resource.visibility != "public" and resource.uploader_id != user.id:
            raise ForbiddenError("无权访问该资源")
        return resource

    @staticmethod
    def set_visibility(db: Session, resource_id: int, user: User, visibility: str) -> Resource:
        resource = ResourceService.get_resource(db, resource_id, user)
        if resource.uploader_id != user.id and user.role != "admin":
            raise ForbiddenError("仅资源上传者可修改可见性")
        resource.visibility = visibility
        db.commit()
        db.refresh(resource)
        return resource

    @staticmethod
    def delete(db: Session, resource_id: int, user: User) -> None:
        resource = ResourceService.get_resource(db, resource_id, user)
        if resource.uploader_id != user.id and user.role != "admin":
            raise ForbiddenError("仅资源上传者可删除")
        db.delete(resource)
        db.commit()
